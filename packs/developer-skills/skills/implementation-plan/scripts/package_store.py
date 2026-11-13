"""Reserve, inspect, and validate ignored implementation-plan packages."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from urllib.parse import unquote
import uuid


OWNER = "implementation-plan"
SHARED = (
    "README.md", "PLAN.md", "CONTRACTS.md", "PHASES.md", "PROMPTS.md",
    "RUNBOOK.md", "ACCEPTANCE.md", "PROGRESS.md", "HANDOFF.md",
    "BLOCKERS.md", "COMMIT_MESSAGES.md",
)
PHASE_ID = re.compile(r"P\d{2,}")
RUN_ID = re.compile(r"\d{8}T\d{6}Z-[0-9a-f]{12}")
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def safe(path):
    path = Path(os.path.abspath(path))
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"Linked path is not allowed: {part}")
    return path.resolve()


def regular(path):
    path = safe(path)
    if path.exists():
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError(f"Expected one regular file: {path}")
    return path


def git(root, *args):
    try:
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                                text=True, encoding="utf-8", errors="replace")
    except FileNotFoundError as error:
        raise ValueError("Git is unavailable") from error
    return result


def project_root(directory):
    directory = safe(Path(directory).expanduser())
    if not directory.is_dir():
        raise ValueError(f"Project directory does not exist: {directory}")
    result = git(directory, "rev-parse", "--show-toplevel")
    if result.returncode == 0:
        return safe(result.stdout.strip()), True
    if any((part / ".git").exists() for part in (directory, *directory.parents)):
        raise ValueError("Cannot establish the Git root")
    return directory, False


def checked_git(root, *args):
    result = git(root, *args)
    if result.returncode:
        raise ValueError(f"Git could not check {' '.join(args[:2])}: {result.stderr.strip()}")
    return result.stdout


def slugify(feature):
    slug = re.sub(r"[^a-z0-9]+", "-", feature.lower()).strip("-")[:60].strip("-")
    if not slug:
        raise ValueError("Feature needs letters or digits for a folder name")
    return slug


def read_json(path):
    path = regular(path)
    if not path.is_file():
        raise ValueError(f"Missing package metadata: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Invalid package metadata: {path}")
    return value


def write_new(path, value):
    path = regular(path)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=True)
        stream.write("\n")


def locate(package):
    package = safe(package)
    if not RUN_ID.fullmatch(package.name) or package.parent.parent.name != "docs":
        raise ValueError("Expected an exact docs/<feature>/<run-id> package path")
    marker = read_json(package.parent / ".implementation-plan.json")
    if marker != {"schema_version": 1, "owner": OWNER}:
        raise ValueError("Unrecognized feature folder ownership")
    data = read_json(package / ".package.json")
    if data.get("schema_version") != 1 or data.get("owner") != OWNER:
        raise ValueError("Unrecognized package metadata")
    root, is_git = project_root(package.parent.parent.parent)
    if package.parent.parent != safe(root / "docs"):
        raise ValueError("Package does not belong to its project root")
    return root, is_git, package, data


def ignored(root, path):
    result = git(root, "check-ignore", "-q", "--", path.relative_to(root).as_posix())
    if result.returncode not in (0, 1):
        raise ValueError("Git could not verify output exclusion")
    return result.returncode == 0


def ensure_ignore(root, rule, probe, is_git):
    target = regular(root / ".gitignore")
    before = target.read_bytes() if target.exists() else b""
    if before.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise ValueError("Git ignore file must use a Git-compatible text encoding")
    covered = ignored(root, probe) if is_git else before.splitlines()[-1:] == [rule.encode()]
    if not covered:
        newline = b"\r\n" if b"\r\n" in before else b"\n"
        addition = (newline if before and not before.endswith(b"\n") else b"")
        addition += rule.encode() + newline
        if target.exists():
            with target.open("r+b") as stream:
                if stream.read() != before or not os.path.samestat(os.fstat(stream.fileno()), target.stat()):
                    raise ValueError(".gitignore changed during preparation; retry")
                stream.write(addition)
        else:
            with target.open("xb") as stream:
                stream.write(addition)
    if is_git and not ignored(root, probe):
        raise ValueError("Git did not confirm package exclusion")


def validate_options(max_phases, skills, skills_mode, commits):
    if max_phases is not None and max_phases < 1:
        raise ValueError("--max-phases must be positive")
    if skills_mode not in ("auto", "all") or commits not in ("off", "scoped"):
        raise ValueError("Invalid skills mode or commit policy")
    names = [name.strip() for name in (skills or "").split(",") if name.strip()]
    if len(names) != len(set(names)) or any(not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name) for name in names):
        raise ValueError("Skills must be unique lowercase skill names")
    return names


def start(project, feature, max_phases=None, skills="", skills_mode="auto", commits="off", previous=None):
    names = validate_options(max_phases, skills, skills_mode, commits)
    root, is_git = project_root(project)
    docs = safe(root / "docs")
    tracked_docs = bool(checked_git(root, "ls-files", "--", "docs").strip()) if is_git else False
    docs_created = not docs.exists() and not tracked_docs
    if docs.exists() and not docs.is_dir():
        raise ValueError("docs is not a directory")
    if previous:
        prior_root, _, prior_package, prior = locate(previous)
        if prior_root != root:
            raise ValueError("Previous package belongs to another project")
        feature_root = prior_package.parent
        feature = prior["feature"]
    else:
        slug = slugify(feature) + "-implementation"
        feature_root = safe(docs / slug)
        if feature_root.exists():
            try:
                owned = read_json(feature_root / ".implementation-plan.json")
            except ValueError:
                owned = None
            if owned != {"schema_version": 1, "owner": OWNER}:
                feature_root = safe(docs / (slug + "-" + uuid.uuid4().hex[:8]))
        prior_package = None
    if is_git and checked_git(root, "ls-files", "--", feature_root.relative_to(root).as_posix()).strip():
        raise ValueError("Package output is tracked; no files were untracked")
    rule = "/docs/" if docs_created else f"/{feature_root.relative_to(root).as_posix()}/"
    probe = safe(feature_root / "20990101T000000Z-000000000000" / "prompts" / "P01.md")
    ensure_ignore(root, rule, probe, is_git)
    docs.mkdir(exist_ok=True)
    feature_root.mkdir(exist_ok=True)
    marker = feature_root / ".implementation-plan.json"
    if marker.exists():
        if read_json(marker) != {"schema_version": 1, "owner": OWNER}:
            raise ValueError("Unrecognized feature folder ownership")
    else:
        write_new(marker, {"schema_version": 1, "owner": OWNER})
    for _ in range(10):
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:12]
        package = safe(feature_root / run_id)
        try:
            package.mkdir()
            break
        except FileExistsError:
            continue
    else:
        raise ValueError("Could not allocate a unique package directory")
    data = {"schema_version": 1, "owner": OWNER, "feature": feature, "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "max_phases": max_phases, "skills": names, "skills_mode": skills_mode,
            "commits": commits, "previous": str(prior_package) if prior_package else None,
            "phases": {}, "skill_assignments": {}}
    write_new(package / ".package.json", data)
    (package / "prompts").mkdir()
    return {"package": str(package), "git_exclusion_verified": is_git, "ignore_rule": rule}


def inspect(package):
    root, is_git, package, data = locate(package)
    errors = []
    if is_git:
        for path in (package.parent, package / "README.md", package / "prompts" / "P01.md"):
            if not ignored(root, path):
                errors.append(f"Output is not ignored: {path.relative_to(root)}")
        if checked_git(root, "ls-files", "--", package.parent.relative_to(root).as_posix()).strip():
            errors.append("Package output is tracked")
    files = [package / name for name in SHARED]
    for name, path in zip(SHARED, files):
        if not regular(path).is_file():
            errors.append(f"Missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"Empty {name}")
    phases = data.get("phases")
    if not isinstance(phases, dict) or not phases:
        errors.append("No phase prompt map")
    else:
        if data.get("max_phases") is not None and len(phases) > data["max_phases"]:
            errors.append("Phase count exceeds maximum")
        expected_ids = [f"P{index:02d}" for index in range(1, len(phases) + 1)]
        if list(phases) != expected_ids:
            errors.append("Phase IDs must be ordered and contiguous from P01")
        if len(set(phases.values())) != len(phases):
            errors.append("Phase prompts must have distinct files")
        for phase, name in phases.items():
            if not PHASE_ID.fullmatch(phase) or not isinstance(name, str) or not re.fullmatch(r"P\d{2,}_[A-Z0-9_]+\.md", name):
                errors.append(f"Invalid phase prompt mapping: {phase}")
                continue
            prompt = regular(package / "prompts" / name)
            files.append(prompt)
            if not prompt.is_file():
                errors.append(f"Missing prompt for {phase}: {name}")
            elif phase not in prompt.read_text(encoding="utf-8"):
                errors.append(f"Prompt does not identify {phase}: {name}")
    assignments = data.get("skill_assignments")
    names = data.get("skills")
    if not isinstance(names, list) or not isinstance(assignments, dict) or set(assignments) != set(names):
        errors.append("Skill assignments do not match selected skills")
    else:
        for name, assignment in assignments.items():
            assigned = assignment.get("phases") if isinstance(assignment, dict) else None
            reason = assignment.get("reason") if isinstance(assignment, dict) else None
            if not isinstance(assigned, list) or not assigned or not set(assigned) <= set(phases or ()) or not isinstance(reason, str) or not reason.strip():
                errors.append(f"Invalid skill assignment: {name}")
            elif data.get("skills_mode") == "all" and set(assigned) != set(phases):
                errors.append(f"Skill is missing from an all-mode prompt: {name}")
    for path in files:
        if not path.is_file():
            continue
        body = path.read_text(encoding="utf-8")
        for raw in MARKDOWN_LINK.findall(body):
            target = unquote(raw.split("#", 1)[0].split(" ", 1)[0])
            if not target or "://" in target or target.startswith(("mailto:", "/")):
                continue
            linked = safe(path.parent / target)
            if not linked.is_relative_to(package) or not linked.is_file():
                errors.append(f"Broken local link in {path.name}: {raw}")
    return {"package": str(package), "status": data.get("status"), "phases": phases,
            "skills": data.get("skills"), "skill_assignments": data.get("skill_assignments"),
            "errors": errors, "git_exclusion_verified": is_git}


def list_packages(project):
    root, _ = project_root(project)
    docs = safe(root / "docs")
    if not docs.is_dir():
        return []
    packages = []
    for feature in sorted(docs.iterdir()):
        if not feature.is_dir() or not (feature / ".implementation-plan.json").is_file():
            continue
        try:
            if read_json(feature / ".implementation-plan.json") != {"schema_version": 1, "owner": OWNER}:
                continue
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        for run in sorted(feature.iterdir()):
            if not run.is_dir() or not RUN_ID.fullmatch(run.name):
                continue
            try:
                _, _, package, data = locate(run)
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            packages.append({"package": str(package), "feature": data.get("feature"),
                             "status": data.get("status")})
    return packages


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    command = commands.add_parser("start")
    command.add_argument("--project", required=True)
    command.add_argument("--feature", required=True)
    command.add_argument("--max-phases", type=int)
    command.add_argument("--skills", default="")
    command.add_argument("--skills-mode", choices=("auto", "all"), default="auto")
    command.add_argument("--commits", choices=("off", "scoped"), default="off")
    command.add_argument("--previous")
    command = commands.add_parser("list")
    command.add_argument("--project", required=True)
    for name in ("check", "status", "skills", "prompt"):
        command = commands.add_parser(name)
        command.add_argument("--package", required=True)
        if name == "prompt":
            command.add_argument("--phase", required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "start":
            result = start(args.project, args.feature, args.max_phases, args.skills,
                           args.skills_mode, args.commits, args.previous)
        elif args.action == "list":
            result = {"packages": list_packages(args.project)}
        else:
            result = inspect(args.package)
            if args.action == "prompt":
                name = (result["phases"] or {}).get(args.phase)
                if not name:
                    raise ValueError(f"Unknown phase: {args.phase}")
                if result["errors"]:
                    raise ValueError("Package has validation errors")
                if result["status"] != "ready":
                    raise ValueError("Package is still a draft")
                print(regular(Path(args.package) / "prompts" / name).read_text(encoding="utf-8"))
                return 0
            if args.action == "skills":
                result = {key: result[key] for key in ("package", "skills", "skill_assignments")}
            if args.action == "status":
                progress = regular(Path(args.package) / "PROGRESS.md")
                result["progress"] = progress.read_text(encoding="utf-8") if progress.is_file() else None
        print(json.dumps(result, indent=2))
        return 1 if args.action == "check" and result["errors"] else 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
