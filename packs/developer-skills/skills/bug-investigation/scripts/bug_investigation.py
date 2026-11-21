"""Validate bug-investigation options and gather selected local Git evidence."""

from __future__ import annotations

import argparse
import difflib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


class InvestigationError(ValueError):
    pass


SENSITIVE_PARTS = {"node_modules", ".venv", "__pycache__", "dist", "build"}
SENSITIVE_NAME = re.compile(r"(?:^|/)(?:\.env(?:\..*)?|credentials?(?:\..*)?|.*\.(?:key|pem|p12))$", re.IGNORECASE)


def safe_name(name: str) -> bool:
    normalized = name.replace("\\", "/")
    return not (SENSITIVE_NAME.search(normalized) or any(part in SENSITIVE_PARTS for part in normalized.split("/")))


def git(path: Path, *args: str, check: bool = True) -> bytes:
    result = subprocess.run(["git", "-C", str(path), *args], capture_output=True)
    if check and result.returncode:
        raise InvestigationError(result.stderr.decode("utf-8", "replace").strip() or "Git command failed")
    return result.stdout if result.returncode == 0 else b""


def repo_root(path: Path) -> Path:
    if not path.is_dir():
        raise InvestigationError(f"Missing repository directory: {path}")
    root = git(path, "rev-parse", "--show-toplevel", check=False).strip()
    if not root:
        raise InvestigationError(f"Not a Git repository: {path}")
    return Path(os.fsdecode(root)).resolve()


def config_path(explicit: str | None, cwd: Path) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    override = os.getenv("CHANGE_REPORT_HOME")
    if override:
        return (Path(override).expanduser().resolve() / "projects.json")
    root = repo_root(cwd)
    location = os.fsdecode(git(root, "rev-parse", "--git-path", "change-report/projects.json").strip())
    return (root / location).resolve()


def load_projects(path: Path) -> dict:
    if not path.exists():
        return {"schema_version": 1, "projects": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("projects"), dict):
        raise InvestigationError(f"Invalid project registry: {path}")
    for alias, members in data["projects"].items():
        if not isinstance(alias, str) or not alias or not isinstance(members, dict) or not members:
            raise InvestigationError(f"Invalid project entry: {alias!r}")
        if any(not isinstance(name, str) or not name or not isinstance(value, str) or not value for name, value in members.items()):
            raise InvestigationError(f"Invalid project member in: {alias}")
    return data


def parse_members(values: list[str]) -> dict[str, str]:
    if not values:
        raise InvestigationError("At least one NAME=PATH member is required")
    members = {}
    for value in values:
        name, separator, path = value.partition("=")
        if not separator or not name or not path or name in members:
            raise InvestigationError(f"Invalid or duplicate member: {value!r}")
        members[name] = path
    return members


def set_project(path: Path, alias: str, values: list[str]) -> dict:
    if not alias:
        raise InvestigationError("Project alias is required")
    members = parse_members(values)
    data = load_projects(path)
    if alias in data["projects"]:
        raise InvestigationError(f"Project already exists: {alias}")
    # Relative inputs stay portable to the registry; explicit absolute paths stay explicit.
    normalized = {}
    for name, value in members.items():
        candidate = Path(value).expanduser()
        if candidate.is_absolute():
            normalized[name] = str(candidate.resolve())
        else:
            normalized[name] = os.path.relpath((Path.cwd() / candidate).resolve(), path.parent)
    data["projects"][alias] = normalized
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return {"registry": str(path), "project": alias, "members": normalized}


def selected_repos(path: Path | None, alias: str | None, cwd: Path, require_complete: bool = False) -> dict:
    if alias:
        if path is None:
            raise InvestigationError("Project registry required")
        projects = load_projects(path)["projects"]
        if alias not in projects:
            raise InvestigationError(f"Unknown project: {alias}")
        chosen = projects[alias].items()
    else:
        chosen = [(cwd.name, str(cwd))]
    members = []
    seen = set()
    for name, value in chosen:
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            candidate = ((path.parent if alias else cwd) / candidate).resolve()
        try:
            root = repo_root(candidate)
            if root in seen:
                raise InvestigationError(f"Duplicate repository root: {root}")
            seen.add(root)
            branch = os.fsdecode(git(root, "branch", "--show-current").strip())
            members.append({"name": name, "root": str(root), "branch": branch, "available": True})
        except InvestigationError as error:
            members.append({"name": name, "path": str(candidate), "available": False, "reason": str(error)})
    complete = all(member["available"] for member in members)
    if require_complete and not complete:
        raise InvestigationError("Repository selection incomplete: " + "; ".join(
            f"{m['name']}: {m['reason']}" for m in members if not m["available"]))
    return {"project": alias, "complete": complete, "repositories": members}


def line_ranges(before: bytes | None, after: bytes | None) -> tuple[list[str], list[str], bool]:
    if any(blob is not None and b"\0" in blob for blob in (before, after)):
        return [], [], True
    try:
        old = (before or b"").decode("utf-8").splitlines()
        new = (after or b"").decode("utf-8").splitlines()
    except UnicodeDecodeError:
        return [], [], True
    old_ranges, new_ranges = [], []
    for tag, a, b, c, d in difflib.SequenceMatcher(a=old, b=new, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        if b > a:
            old_ranges.append(str(a + 1) if b == a + 1 else f"{a + 1}-{b}")
        if d > c:
            new_ranges.append(str(c + 1) if d == c + 1 else f"{c + 1}-{d}")
    return old_ranges, new_ranges, False


def worktree_changes(root: Path) -> dict:
    baseline = bool(git(root, "rev-parse", "--verify", "HEAD", check=False).strip())
    rows = []
    if baseline:
        parts = git(root, "diff", "--name-status", "-z", "--find-renames", "HEAD", "--").split(b"\0")
        index = 0
        while index < len(parts) and parts[index]:
            status = os.fsdecode(parts[index]); index += 1
            if status.startswith("R"):
                old_path = os.fsdecode(parts[index]); new_path = os.fsdecode(parts[index + 1]); index += 2
                rows.append(("Renamed", new_path, old_path))
            else:
                name = os.fsdecode(parts[index]); index += 1
                rows.append(({"A": "Added", "M": "Modified", "D": "Deleted"}.get(status[0], "Modified"), name, None))
    tracked = {os.fsdecode(part) for part in git(root, "ls-files", "-z").split(b"\0") if part}
    untracked = {os.fsdecode(part) for part in git(root, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0") if part}
    existing = {name for _, name, _ in rows}
    rows += [("Added", name, None) for name in sorted(untracked - existing)]
    if not baseline:
        rows += [("Added", name, None) for name in sorted(tracked - existing)]
    changes = []
    omitted = 0
    for status, name, old_path in rows:
        if not safe_name(name) or (old_path and not safe_name(old_path)):
            omitted += 1
            continue
        target = (root / name).resolve()
        if not target.is_relative_to(root) or (root / name).is_symlink() or (target.exists() and not target.is_file()):
            raise InvestigationError(f"Unsafe worktree path: {name}")
        before = git(root, "show", f"HEAD:{old_path or name}", check=False) if baseline and status != "Added" else None
        after = target.read_bytes() if target.is_file() and status != "Deleted" else None
        old_ranges, new_ranges, binary = line_ranges(before, after)
        changes.append({"status": status, "path": name.replace("\\", "/"), "old_path": old_path.replace("\\", "/") if old_path else None,
                        "old_lines": old_ranges, "new_lines": new_ranges, "binary": binary})
    return {"repository": root.name, "root": str(root), "basis": "HEAD to current worktree", "changes": changes,
            "omitted_sensitive_or_generated": omitted}


def parse_request(argv: list[str]) -> dict:
    for selector in ("--group", "--project", "--save"):
        if argv.count(selector) > 1:
            raise InvestigationError(f"Duplicate option: {selector}")
    parser = argparse.ArgumentParser(prog="bug-investigation", add_help=False, allow_abbrev=False)
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--detailed", action="store_true")
    parser.add_argument("--group", choices=("role", "page"))
    parser.add_argument("--history", action="store_true")
    parser.add_argument("--project")
    parser.add_argument("--save")
    parser.add_argument("problem", nargs="*")
    try:
        args = parser.parse_intermixed_args(argv)
    except SystemExit as error:
        raise InvestigationError("Invalid bug-investigation request") from error
    if "help" in args.problem:
        if len(args.problem) != 1 or len(argv) != 1:
            raise InvestigationError("help cannot be combined with a problem or options")
        return {"help": True}
    if any(word == "detailed" for word in args.problem):
        raise InvestigationError("Use --detailed, not positional detailed")
    if any(value is not None and not value.strip() for value in (args.project, args.save)):
        raise InvestigationError("Empty option value")
    return {"problem": " ".join(args.problem), "fix": args.fix, "verify": args.verify,
            "detailed": args.detailed, "group": args.group, "history": args.history,
            "project": args.project, "save": args.save}


def identified_subject(request: dict, active_subject: str | None = None) -> str:
    """Require an explicit or established target; never choose an arbitrary prior run."""
    subject = request.get("problem") or active_subject
    if not subject or not subject.strip():
        raise InvestigationError("Identify the problem or report to investigate or verify")
    return subject.strip()


SECTION_ORDER = [
    "Reported problem", "Findings", "Confirmed cause", "Corrections",
    "Expected behavior and fixes", "Implementation locations", "Data and access",
    "Verification", "Remaining checks", "Recommendations",
]
STATUS = {"Added", "Modified", "Renamed", "Deleted"}
PURPOSE = {"New", "Improvement", "Fix", "Refactor", "Removal", "Unclear"}


def validate_report(body: str, detailed: bool, allow_hashes: bool = False) -> None:
    """Check report shape only; causal and verification claims require source review."""
    if not body.strip() or re.search(r"<[^>\n]+>", body):
        raise InvestigationError("Empty report or unfilled template placeholder")
    if "| Project |" in body or (not allow_hashes and re.search(r"\b[0-9a-f]{40}\b", body)):
        raise InvestigationError("Project table columns and commit hashes are excluded by default")
    if re.search(r"[A-Za-z]:\\", body):
        raise InvestigationError("Use repository-relative report paths")
    headings = re.findall(r"(?m)^### (.+)$", body)
    if not detailed:
        if headings or "| File |" in body:
            raise InvestigationError("Brief reports omit detailed sections and source tables")
        return
    for category in re.split(r"(?m)^\*\*[^*\n]+\*\*\s*$", body):
        order = []
        category_headings = re.findall(r"(?m)^### (.+)$", category)
        for heading in category_headings:
            normalized = heading
            if heading == "Cause not yet confirmed":
                normalized = "Confirmed cause"
            elif heading == "Expected behavior and proposed fixes":
                normalized = "Expected behavior and fixes"
            elif heading == "Origin":
                normalized = "Confirmed cause"
            if normalized not in SECTION_ORDER:
                raise InvestigationError(f"Unknown detailed section: {heading}")
            order.append(SECTION_ORDER.index(normalized))
        if order != sorted(order):
            raise InvestigationError("Detailed sections are out of order")
        if "### Confirmed cause" in category and "### Cause not yet confirmed" in category:
            raise InvestigationError("Choose confirmed or unresolved cause per category")
    rows = body.splitlines()
    for index, row in enumerate(rows):
        if row.startswith("| File | Lines | Status | Type | Change |"):
            for item in rows[index + 2:]:
                if not item.startswith("|"):
                    break
                cells = [cell.strip() for cell in item.strip("|").split("|")]
                if len(cells) != 5 or cells[2] not in STATUS or cells[3] not in PURPOSE:
                    raise InvestigationError("Invalid source table status or type")
                if not re.fullmatch(r"(?:\d+(?:-\d+)?(?: old)?|—)", cells[1]):
                    raise InvestigationError("Invalid source line location")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    parse = sub.add_parser("parse", help="Validate agent-chat request tokens")
    parse.add_argument("tokens", nargs=argparse.REMAINDER)
    project = sub.add_parser("project", help="Read or set the compatible project registry")
    project.add_argument("operation", choices=("list", "set"))
    project.add_argument("--config")
    project.add_argument("--project")
    project.add_argument("members", nargs="*")
    repos = sub.add_parser("repos", help="Resolve selected repositories")
    repos.add_argument("--config")
    repos.add_argument("--project")
    repos.add_argument("--require-complete", action="store_true")
    diff = sub.add_parser("diff", help="Inspect HEAD-to-worktree source ranges")
    diff.add_argument("--repo", default=".")
    validate = sub.add_parser("validate", help="Validate Markdown report structure")
    validate.add_argument("--file", required=True)
    validate.add_argument("--detailed", action="store_true")
    validate.add_argument("--allow-hashes", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.action == "parse":
            result = parse_request(args.tokens[1:] if args.tokens[:1] == ["--"] else args.tokens)
        elif args.action == "diff":
            result = worktree_changes(repo_root(Path(args.repo).resolve()))
        elif args.action == "validate":
            validate_report(Path(args.file).read_text(encoding="utf-8"), args.detailed, args.allow_hashes)
            result = {"valid_structure": True, "evidence_verified": False}
        else:
            cwd = Path.cwd().resolve()
            path = config_path(args.config, cwd) if args.action == "project" or args.project else None
            if args.action == "project" and args.operation == "set":
                result = set_project(path, args.project, args.members)
            elif args.action == "project":
                result = {"registry": str(path), **load_projects(path)}
            else:
                result = selected_repos(path, args.project, cwd, args.require_complete)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (InvestigationError, OSError, json.JSONDecodeError) as error:
        print(f"bug-investigation: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
