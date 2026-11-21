"""Collect reproducible Git change evidence without changing a repository's index or files."""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid


EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
MAX_SNAPSHOT = 2 * 1024 * 1024
SKIP_PARTS = {".git", "node_modules", "vendor", "dist", "build", "coverage", "__pycache__", ".next", ".nuxt", ".cache", "target"}
SECRET_NAME = re.compile(r"(^|/)(\.env($|\.)|id_rsa|id_ed25519|.*\.(pem|key|p12|pfx|keystore)$|credentials?(\.json|\.ya?ml)?$|secrets?(\.json|\.ya?ml)?$)", re.I)
SECRET_CONTENT = re.compile(rb"(?im)^\s*(?:api[_-]?key|secret|password|private[_-]?key|access[_-]?token)\s*[:=]\s*[^\s#][^\r\n]*")


class ReportError(Exception):
    pass


def git(root: Path, *args: str, check: bool = True) -> bytes:
    process = subprocess.run(["git", "-C", str(root), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and process.returncode:
        message = process.stderr.decode("utf-8", "replace").strip().splitlines()
        raise ReportError(message[-1] if message else f"git {' '.join(args)} failed")
    return process.stdout


def path_text(raw: bytes) -> str:
    return raw.decode("utf-8", "surrogateescape")


def repo_root(path: Path) -> Path:
    if not path.exists():
        raise ReportError(f"Repository unavailable: {path}")
    root = path_text(git(path, "rev-parse", "--show-toplevel")).strip()
    if not root:
        raise ReportError(f"Not a Git repository: {path}")
    return Path(root).resolve()


def head(root: Path) -> str | None:
    value = git(root, "rev-parse", "--verify", "HEAD", check=False).strip()
    return value.decode("ascii") if value else None


def revision(root: Path, value: str) -> str:
    if not value or value.startswith("-"):
        raise ReportError(f"Invalid revision: {value!r}")
    result = git(root, "rev-parse", "--verify", "--end-of-options", f"{value}^{{commit}}", check=False).strip()
    if not result:
        raise ReportError(f"Invalid revision in {root.name}: {value}")
    return result.decode("ascii")


def state_dir() -> Path:
    override = os.getenv("CHANGE_REPORT_HOME")
    if override:
        return Path(override).expanduser().resolve()
    root = repo_root(Path.cwd())
    git_path = path_text(git(root, "rev-parse", "--git-path", "change-report")).strip()
    return (root / git_path).resolve()


def safe_file(name: str) -> bool:
    path = name.replace("\\", "/")
    return (not path.startswith("/") and ".." not in Path(path).parts and not SECRET_NAME.search(path)
            and not any(part in SKIP_PARTS for part in Path(path).parts) and not path.endswith((".pyc", ".log", ".map")))


def untracked(root: Path) -> set[str]:
    return {path_text(p) for p in git(root, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0") if p and safe_file(path_text(p))}


def working_names(root: Path) -> set[str]:
    raw = git(root, "diff", "--name-only", "-z", "HEAD", check=False)
    if head(root) is None:
        raw = git(root, "ls-files", "-z")
    return {path_text(p) for p in raw.split(b"\0") if p and safe_file(path_text(p))} | untracked(root)


def staged_names(root: Path) -> set[str]:
    raw = git(root, "diff", "--cached", "--name-only", "-z", "HEAD", check=False) if head(root) else git(root, "ls-files", "-z")
    return {path_text(p) for p in raw.split(b"\0") if p and safe_file(path_text(p))}


def staged_file(root: Path, name: str) -> bytes | None:
    if not git(root, "ls-files", "--stage", "-z", "--", name):
        return None
    return git(root, "show", f":{name}")


def changed_names(root: Path, before: str | None, after: str | None) -> set[str]:
    if before == after:
        return set()
    old, new = before or EMPTY_TREE, after or EMPTY_TREE
    raw = git(root, "diff", "--name-status", "-z", "--find-renames", old, new)
    parts = raw.split(b"\0")
    names: set[str] = set()
    index = 0
    while index < len(parts) and parts[index]:
        status = path_text(parts[index]); index += 1
        count = 2 if status.startswith(("R", "C")) else 1
        for value in parts[index:index + count]:
            name = path_text(value)
            if safe_file(name):
                names.add(name)
        index += count
    return names


def tracked_at(root: Path, commit: str | None, name: str) -> bytes | None:
    if commit is None:
        return None
    entry = git(root, "ls-tree", "-z", commit, "--", name)
    if not entry:
        return None
    return git(root, "show", f"{commit}:{name}")


def current_file(root: Path, name: str) -> bytes | None:
    file = root / name
    if file.is_symlink() or not file.is_file():
        return None
    return file.read_bytes()


def snapshot(content: bytes) -> dict:
    return {"digest": hashlib.sha256(content).hexdigest(), "binary": b"\0" in content,
            "lines": [hashlib.sha256(line).hexdigest() for line in content.splitlines()]}


def stored_file(record: dict, name: str) -> dict | None:
    return record.get("dirty", {}).get(name)


def same_content(old: bytes | dict | None, new: bytes | dict | None) -> bool:
    if old is None or new is None:
        return old is new
    a = old["digest"] if isinstance(old, dict) else hashlib.sha256(old).hexdigest()
    b = new["digest"] if isinstance(new, dict) else hashlib.sha256(new).hexdigest()
    return a == b


def same_lines(old: bytes | dict | None, new: bytes | dict | None) -> bool:
    return bool(old is not None and new is not None and not is_binary(old) and not is_binary(new)
                and content_lines(old, True) == content_lines(new, True))


def content_lines(value: bytes | dict | None, hashed: bool = False) -> list:
    if value is None:
        return []
    if isinstance(value, dict):
        return value["lines"]
    lines = value.splitlines()
    return [hashlib.sha256(line).hexdigest() for line in lines] if hashed else lines


def is_binary(value: bytes | dict | None) -> bool:
    return bool(value is not None and (value["binary"] if isinstance(value, dict) else b"\0" in value))


def line_ranges(old: bytes | dict | None, new: bytes | dict | None) -> tuple[list[str], list[str]]:
    if is_binary(old) or is_binary(new):
        return [], []
    hashed = isinstance(old, dict) or isinstance(new, dict)
    a, b = content_lines(old, hashed), content_lines(new, hashed)
    old_ranges, new_ranges = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        if i1 != i2:
            old_ranges.append(f"{i1 + 1}–{i2} old")
        if j1 != j2:
            new_ranges.append(f"{j1 + 1}–{j2}")
    return old_ranges, new_ranges


def evidence(root: Path, before: str | None, after: str | None, scope: str, record: dict | None) -> dict:
    if scope == "session":
        candidates = changed_names(root, before, head(root)) | working_names(root) | set(record["dirty"])
    elif after == "working":
        candidates = changed_names(root, before, head(root)) | working_names(root)
    else:
        candidates = changed_names(root, before, after)
    entries = []
    old_only, new_only = [], []
    for name in sorted(candidates):
        if not safe_file(name):
            continue
        if record and name in record.get("omitted", []):
            continue
        old = stored_file(record, name) if record and name in record["dirty"] else tracked_at(root, before, name)
        new = current_file(root, name) if after == "working" else tracked_at(root, after, name)
        staged = record.get("staged", {}).get(name) if record else None
        if record and name in record.get("staged", {}) and (same_content(staged, new) or same_lines(staged, new)):
            continue
        if same_content(old, new):
            continue
        if old is None and new is None:
            continue
        row = {"path": name, "status": "Modified" if old is not None and new is not None else "Deleted" if new is None else "Added",
               "old_lines": [], "new_lines": [], "binary": is_binary(old) or is_binary(new)}
        if record and name in record.get("staged", {}) and not same_content(staged, old):
            row["ambiguous_start"] = True
        row["old_lines"], row["new_lines"] = line_ranges(old, new)
        if not row["binary"] and not row["old_lines"] and not row["new_lines"]:
            row["line_endings_only"] = True
        entries.append(row)
        if old is None:
            new_only.append((row, new))
        if new is None:
            old_only.append((row, old))
    # Match moved files, including edited moves; preserve both paths and both line origins.
    for deleted, old in old_only:
        if deleted not in entries:
            continue
        matches = [(difflib.SequenceMatcher(None, content_lines(old, isinstance(old, dict)),
                                             content_lines(new, isinstance(old, dict)), autojunk=False).ratio(), added, new)
                   for added, new in new_only if added in entries and old and new and len(content_lines(old)) < 10000 and len(content_lines(new)) < 10000]
        if not matches:
            continue
        score, added, new = max(matches, key=lambda item: item[0])
        if score < 0.72:
            continue
        old_ranges, new_ranges = line_ranges(old, new)
        entries.remove(deleted); entries.remove(added)
        entries.append({"path": added["path"], "old_path": deleted["path"], "status": "Renamed", "old_lines": old_ranges,
                        "new_lines": new_ranges, "binary": added["binary"] or deleted["binary"]})
    limitations = list(record.get("omitted", [])) if record else []
    if any(row.get("ambiguous_start") for row in entries):
        limitations.append("Starting index and worktree differed; review marked rows before attributing them to this task")
    return {"repository": root.name, "root": str(root), "scope": scope, "from": before, "to": head(root) if after == "working" else after,
            "working": after == "working", "changes": sorted(entries, key=lambda row: row["path"]),
            "limitations": limitations}


def load_projects() -> dict:
    file = state_dir() / "projects.json"
    if not file.exists():
        return {"schema_version": 1, "projects": {}}
    data = json.loads(file.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("projects"), dict):
        raise ReportError(f"Invalid project configuration: {file}")
    return data


def configured_path(value: str) -> Path:
    path = Path(value).expanduser()
    return (path if path.is_absolute() else state_dir() / path).resolve()


def save_json(file: Path, data: dict) -> None:
    file.parent.mkdir(parents=True, exist_ok=True)
    if file.exists():
        raise ReportError(f"Refusing to overwrite: {file}")
    with file.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def selected_repos(args: argparse.Namespace) -> list[tuple[str, Path]]:
    projects = load_projects()["projects"]
    if args.all and args.project:
        raise ReportError("--all conflicts with --project")
    if args.all:
        if not projects:
            raise ReportError("No configured projects")
        chosen = [(f"{alias}/{name}", configured_path(path)) for alias, members in projects.items() for name, path in members.items()]
    elif args.project:
        if args.project not in projects:
            raise ReportError(f"Unknown project: {args.project}")
        chosen = list((name, configured_path(path)) for name, path in projects[args.project].items())
    else:
        chosen = [(Path.cwd().name, Path.cwd())]
    result, seen = [], set()
    errors = []
    for name, path in chosen:
        try:
            root = repo_root(path)
        except ReportError as error:
            errors.append(f"{name}: {error}")
            continue
        if root not in seen:
            result.append((name, root)); seen.add(root)
    if errors:
        raise ReportError("Repository selection incomplete: " + "; ".join(errors))
    return result


def overrides(values: list[str]) -> dict[str, str]:
    result = {}
    for value in values:
        name, separator, revision_name = value.partition("=")
        if not separator or not name or not revision_name or name in result:
            raise ReportError(f"Invalid repository revision override: {value}")
        result[name] = revision_name
    return result


def start(args: argparse.Namespace, repos: list[tuple[str, Path]]) -> dict:
    if args.from_rev or args.to_rev or args.repo_from or args.repo_to:
        raise ReportError("start does not accept revision options")
    if not args.context or not args.context.strip():
        raise ReportError("start requires a specific --context")
    token = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:12]
    result = {"schema_version": 1, "token": token, "context": args.context, "repositories": {}}
    for name, root in repos:
        dirty = {}; staged = {}; omitted = []
        staged_paths = staged_names(root)
        for path in sorted(working_names(root) | staged_paths):
            content = current_file(root, path)
            if content is None:
                dirty[path] = None
            elif len(content) > MAX_SNAPSHOT or SECRET_CONTENT.search(content):
                omitted.append(path)
            else:
                dirty[path] = snapshot(content)
            if path in staged_paths:
                index_content = staged_file(root, path)
                if index_content is None:
                    staged[path] = None
                elif len(index_content) > MAX_SNAPSHOT or SECRET_CONTENT.search(index_content):
                    omitted.append(path)
                else:
                    staged[path] = snapshot(index_content)
        result["repositories"][name] = {"root": str(root), "head": head(root), "dirty": dirty, "staged": staged, "omitted": sorted(set(omitted))}
    save_json(state_dir() / "runs" / f"{token}.json", result)
    return {"token": token, "context": args.context, "repositories": list(result["repositories"]),
            "limitations": {name: row["omitted"] for name, row in result["repositories"].items() if row["omitted"]}}


def inspect(args: argparse.Namespace, repos: list[tuple[str, Path]]) -> dict:
    scope = args.scope
    if args.to_rev and not args.from_rev and not args.repo_from:
        raise ReportError("--to requires --from")
    if (args.from_rev or args.to_rev or args.repo_from or args.repo_to) and scope != "auto":
        raise ReportError("Explicit revisions conflict with another scope")
    if args.from_rev:
        scope = "revisions"
    if args.to_rev == "working" and not args.from_rev:
        raise ReportError("--to working requires --from")
    if args.repo_from or args.repo_to:
        if scope not in ("revisions", "auto"):
            raise ReportError("Repository revisions require revision scope")
        scope = "revisions"
    from_overrides, to_overrides = overrides(args.repo_from), overrides(args.repo_to)
    names = {name for name, _ in repos}
    if (set(from_overrides) | set(to_overrides)) - names:
        raise ReportError("Revision override names must match selected repositories")
    session = None
    if scope in ("session", "auto") and args.token:
        file = state_dir() / "runs" / f"{args.token}.json"
        if not re.fullmatch(r"\d{8}T\d{6}Z-[0-9a-f]{12}", args.token) or not file.exists():
            raise ReportError("Session baseline unavailable")
        session = json.loads(file.read_text(encoding="utf-8"))
        if not args.context or session.get("context") != args.context:
            raise ReportError("Session context does not match baseline")
        if set(session["repositories"]) != names or any(Path(session["repositories"][name]["root"]).resolve() != root for name, root in repos):
            raise ReportError("Session repositories do not match baseline")
    elif scope == "session":
        raise ReportError("Session baseline unavailable; run start before the task and retain its token and context")
    if scope == "auto":
        scope = "session" if session else "working" if any(working_names(root) for _, root in repos) else "latest"
    output = []
    for name, root in repos:
        current = head(root)
        record = session["repositories"][name] if scope == "session" else None
        if scope == "session":
            before, after = record["head"], "working"
        elif scope == "working":
            before, after = current, "working"
        elif scope == "latest":
            if current is None:
                raise ReportError(f"No commits for latest in {name}")
            parents = path_text(git(root, "rev-list", "--parents", "-n", "1", current)).strip().split()
            before, after = (parents[1] if len(parents) > 1 else None), current
        else:
            source = from_overrides.get(name, args.from_rev)
            if not source:
                raise ReportError(f"Missing --from for {name}")
            before = revision(root, source)
            target = to_overrides.get(name, args.to_rev or "HEAD")
            after = "working" if target == "working" else revision(root, target)
        row = evidence(root, before, after, scope, record)
        row["name"] = name
        output.append(row)
    return {"scope": scope, "repositories": output, "empty": all(not row["changes"] for row in output)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", choices=("inspect", "start", "project", "help"), default="inspect")
    parser.add_argument("project_action", nargs="?", choices=("set", "list"))
    parser.add_argument("members", nargs="*")
    parser.add_argument("--scope", choices=("auto", "working", "latest", "session"), default="auto")
    parser.add_argument("--project")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--from", dest="from_rev")
    parser.add_argument("--to", dest="to_rev")
    parser.add_argument("--repo-from", action="append", default=[])
    parser.add_argument("--repo-to", action="append", default=[])
    parser.add_argument("--token")
    parser.add_argument("--context")
    args = parser.parse_args(argv)
    try:
        if args.action == "help":
            parser.print_help(); return 0
        if args.action == "project":
            data = load_projects()
            if args.project_action == "list":
                result = data
            elif args.project_action == "set" and args.project and args.members:
                members = {}
                for item in args.members:
                    name, separator, path = item.partition("=")
                    if not separator or not name or not path or name in members:
                        raise ReportError(f"Invalid repository member: {item}")
                    root = repo_root(Path(path).expanduser().resolve())
                    try:
                        nearby = root.is_relative_to(repo_root(Path.cwd()).parent)
                        members[name] = os.path.relpath(root, state_dir()) if nearby else str(root)
                    except ValueError:
                        members[name] = str(root)
                data["projects"][args.project] = members
                file = state_dir() / "projects.json"
                file.parent.mkdir(parents=True, exist_ok=True)
                pending = file.with_suffix(".tmp")
                pending.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                pending.replace(file)
                result = {"project": args.project, "repositories": members}
            else:
                raise ReportError("Use project list or project set --project ALIAS name=PATH ...")
        else:
            if args.project_action or args.members:
                raise ReportError("Unexpected positional arguments")
            repos = selected_repos(args)
            result = start(args, repos) if args.action == "start" else inspect(args, repos)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ReportError, OSError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
