"""Reserve, inspect, and validate ignored implementation-plan packages."""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
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
OUTPUT = ".implementation-plans"
LEGACY_OUTPUT = "docs"
STORE_MARKER = {"schema_version": 1, "owner": OWNER}
SHARED = (
    "README.md", "PLAN.md", "CONTRACTS.md", "PHASES.md", "PROMPTS.md",
    "RUNBOOK.md", "ACCEPTANCE.md", "PROGRESS.md", "HANDOFF.md",
    "BLOCKERS.md", "COMMIT_MESSAGES.md",
)
ORIGINAL_PLAN = "ORIGINAL_PLAN.md"
SOURCE_DOCUMENT = "SOURCE_DOCUMENT.pdf"
PHASE_ID = re.compile(r"P\d{2,}")
RUN_ID = re.compile(r"\d{8}T\d{6}Z-[0-9a-f]{12}")
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
COMMIT_BLOCK = re.compile(r"^```(?:text|commit)?[ \t]*\r?\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL)
COMMIT_SUBJECT = re.compile(r"^(?:feat|fix|refactor|chore|docs|test|perf|ci)(?:\([^)\r\n]+\))?!?: [^\r\n]+$")
BUILTIN_SETTINGS = {"commits": "off", "test_scope": "focused", "skills_mode": "auto"}
SETTING_VALUES = {"commits": ("off", "scoped", "auto"),
                  "test_scope": ("focused", "full"), "skills_mode": ("auto", "all")}


def config_path():
    return Path.home() / ".config" / "implementation-plan" / "config.json"


def user_settings():
    path = regular(config_path())
    if not path.exists():
        return BUILTIN_SETTINGS.copy()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid implementation-plan config JSON: {path}: {error}") from error
    if (not isinstance(data, dict)
            or set(data) != {"schema_version", "defaults_at_setup", "current"}
            or type(data["schema_version"]) is not int
            or data["schema_version"] != 1):
        raise ValueError(f"Invalid implementation-plan config structure: {path}")
    for section in ("defaults_at_setup", "current"):
        values = data[section]
        if not isinstance(values, dict) or set(values) != set(BUILTIN_SETTINGS):
            raise ValueError(f"Invalid implementation-plan config {section}: {path}")
        for name, value in values.items():
            if value not in SETTING_VALUES[name]:
                raise ValueError(f"Invalid implementation-plan config {section}.{name}: {path}")
    return data["current"].copy()


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
    output_name = package.parent.parent.name
    if not RUN_ID.fullmatch(package.name) or output_name not in (OUTPUT, LEGACY_OUTPUT):
        raise ValueError("Expected an exact implementation package path")
    if output_name == OUTPUT and read_json(package.parent.parent / ".implementation-plan-store.json") != STORE_MARKER:
        raise ValueError("Unrecognized package store ownership")
    marker = read_json(package.parent / ".implementation-plan.json")
    if marker != STORE_MARKER:
        raise ValueError("Unrecognized feature folder ownership")
    data = read_json(package / ".package.json")
    if data.get("schema_version") not in (1, 2) or data.get("owner") != OWNER:
        raise ValueError("Unrecognized package metadata")
    root, is_git = project_root(package.parent.parent.parent)
    if package.parent.parent != safe(root / output_name):
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


def validate_options(max_phases, skills, skills_mode, commits, phase_count=None, test_scope="focused"):
    if max_phases is not None and max_phases < 1:
        raise ValueError("--max-phases must be positive")
    if phase_count is not None and (phase_count < 1 or (max_phases is not None and phase_count > max_phases)):
        raise ValueError("--phase-count must be positive and within --max-phases")
    if skills_mode not in ("auto", "all") or commits not in ("off", "scoped", "auto"):
        raise ValueError("Invalid skills mode or commit policy")
    if test_scope not in ("focused", "full"):
        raise ValueError("--test-scope must be focused or full")
    names = [name.strip() for name in (skills or "").split(",") if name.strip()]
    if len(names) != len(set(names)) or any(not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name) for name in names):
        raise ValueError("Skills must be unique lowercase skill names")
    return names


def source_snapshot(path):
    source = regular(path)
    if not source.is_file():
        raise ValueError(f"Source plan does not exist: {source}")
    content = source.read_bytes()
    try:
        body = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("Source plan must be UTF-8 Markdown") from error
    if not body.strip() or "\x00" in body:
        raise ValueError("Source plan must contain nonempty Markdown text")
    return content


def pdf_snapshot(path):
    source = regular(path)
    if not source.is_file():
        raise ValueError(f"Source PDF does not exist: {source}")
    if source.suffix.lower() != ".pdf":
        raise ValueError("Source document must be a PDF file")
    content = source.read_bytes()
    if b"%PDF-" not in content[:1024]:
        raise ValueError("Source document is not a PDF")
    return content


def start(project, feature, max_phases=None, skills="", skills_mode=None, commits=None, previous=None, source_plan=None, phase_count=None, source_document=None, test_scope=None):
    if source_plan and source_document:
        raise ValueError("Choose one source plan or source PDF")
    root, is_git = project_root(project)
    output = safe(root / OUTPUT)
    store_marker = output / ".implementation-plan-store.json"
    if output.exists():
        if not output.is_dir():
            raise ValueError("Implementation package root is not a directory")
        if store_marker.exists():
            if read_json(store_marker) != STORE_MARKER:
                raise ValueError("Unrecognized package store ownership")
        elif any(output.iterdir()):
            raise ValueError("Existing package root has no ownership marker")
    if is_git and checked_git(root, "ls-files", "--", OUTPUT).strip():
        raise ValueError("Package output is tracked; no files were untracked")
    if previous:
        prior_root, _, prior_package, prior = locate(previous)
        if prior_root != root:
            raise ValueError("Previous package belongs to another project")
        feature = prior["feature"]
        slug = prior_package.parent.name
    else:
        slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + slugify(feature)
        prior_package = None
        prior = None
    defaults = None if prior else user_settings()
    if test_scope is None:
        test_scope = prior.get("test_scope", "focused") if prior else defaults["test_scope"]
    if commits is None:
        commits = prior.get("commits", "off") if prior else defaults["commits"]
    if skills_mode is None:
        skills_mode = prior.get("skills_mode", "auto") if prior else defaults["skills_mode"]
    names = validate_options(max_phases, skills, skills_mode, commits, phase_count, test_scope)
    original = None
    source = {"origin": "session"}
    document = None
    document_bytes = None
    if source_plan:
        source_path = regular(source_plan)
        original = source_snapshot(source_path)
        source = {"origin": "file", "path": str(source_path),
                  "sha256": sha256(original).hexdigest()}
    elif source_document:
        source_path = regular(source_document)
        document_bytes = pdf_snapshot(source_path)
        document = {"path": str(source_path), "sha256": sha256(document_bytes).hexdigest()}
    elif prior_package:
        if (prior_package / ORIGINAL_PLAN).is_file():
            original = source_snapshot(prior_package / ORIGINAL_PLAN)
            prior_source = prior.get("source_plan", source)
            if not isinstance(prior_source, dict) or prior_source.get("origin") not in ("file", "session"):
                raise ValueError("Previous source plan metadata is invalid")
            source = prior_source
            if source.get("origin") == "file" and sha256(original).hexdigest() != source.get("sha256"):
                raise ValueError("Previous original plan differs from its source snapshot")
        if prior.get("source_document") is not None:
            document = prior["source_document"]
            if not isinstance(document, dict) or not isinstance(document.get("sha256"), str):
                raise ValueError("Previous source PDF metadata is invalid")
            document_bytes = pdf_snapshot(prior_package / SOURCE_DOCUMENT)
            if sha256(document_bytes).hexdigest() != document["sha256"]:
                raise ValueError("Previous source PDF differs from its snapshot")
    feature_root = safe(output / slug)
    if feature_root.exists():
        try:
            owned = read_json(feature_root / ".implementation-plan.json")
        except ValueError:
            owned = None
        if owned != STORE_MARKER:
            if previous and prior_package.parent.parent.name == OUTPUT:
                raise ValueError("Previous feature folder lost its ownership marker")
            feature_root = safe(output / (slug + "-" + uuid.uuid4().hex[:8]))
    rule = f"/{OUTPUT}/"
    probe = safe(feature_root / "20990101T000000Z-000000000000" / "prompts" / "P01.md")
    ensure_ignore(root, rule, probe, is_git)
    output.mkdir(exist_ok=True)
    if not store_marker.exists():
        write_new(store_marker, STORE_MARKER)
    feature_root.mkdir(exist_ok=True)
    marker = feature_root / ".implementation-plan.json"
    if marker.exists():
        if read_json(marker) != STORE_MARKER:
            raise ValueError("Unrecognized feature folder ownership")
    else:
        write_new(marker, STORE_MARKER)
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
    data = {"schema_version": 2, "owner": OWNER, "feature": feature, "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "max_phases": max_phases, "phase_count": phase_count,
            "skills": names, "skills_mode": skills_mode, "test_scope": test_scope,
            "commits": commits, "previous": str(prior_package) if prior_package else None,
            "phases": {}, "skill_assignments": {}, "source_plan": source,
            "source_document": document}
    write_new(package / ".package.json", data)
    if original is not None:
        with (package / ORIGINAL_PLAN).open("xb") as stream:
            stream.write(original)
    if document_bytes is not None:
        with (package / SOURCE_DOCUMENT).open("xb") as stream:
            stream.write(document_bytes)
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
    required = SHARED + ((ORIGINAL_PLAN,) if data["schema_version"] == 2 else ())
    files = [package / name for name in required]
    for name, path in zip(required, files):
        if not regular(path).is_file():
            errors.append(f"Missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"Empty {name}")
    messages = regular(package / "COMMIT_MESSAGES.md")
    if messages.is_file():
        blocks = [block.replace("\r\n", "\n").strip() for block in COMMIT_BLOCK.findall(messages.read_text(encoding="utf-8"))]
        drafts = [block for block in blocks if block and COMMIT_SUBJECT.fullmatch(block.splitlines()[0])]
        if not drafts:
            errors.append("COMMIT_MESSAGES.md needs copyable Conventional Commit blocks with detailed bodies; subject-only lists are incomplete")
        for draft in drafts:
            subject, _, body = draft.partition("\n\n")
            if not body.strip():
                errors.append(f"Commit message needs a body: {subject}")
    if data["schema_version"] == 2:
        source = data.get("source_plan")
        if not isinstance(source, dict) or source.get("origin") not in ("file", "session"):
            errors.append("Invalid source plan metadata")
        elif source["origin"] == "file":
            expected = source.get("sha256")
            if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
                errors.append("Invalid source plan checksum")
            elif (package / ORIGINAL_PLAN).is_file() and sha256((package / ORIGINAL_PLAN).read_bytes()).hexdigest() != expected:
                errors.append("Original plan differs from its source snapshot")
        document = data.get("source_document")
        if document is not None:
            expected = document.get("sha256") if isinstance(document, dict) else None
            if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
                errors.append("Invalid source PDF checksum")
            else:
                snapshot = regular(package / SOURCE_DOCUMENT)
                if not snapshot.is_file():
                    errors.append(f"Missing {SOURCE_DOCUMENT}")
                elif sha256(snapshot.read_bytes()).hexdigest() != expected:
                    errors.append("Source PDF differs from its snapshot")
    test_scope = data.get("test_scope", "focused")
    if test_scope not in ("focused", "full"):
        errors.append("Invalid test scope")
    if data.get("commits") not in ("off", "scoped", "auto"):
        errors.append("Invalid commit policy")
    phases = data.get("phases")
    if not isinstance(phases, dict) or not phases:
        errors.append("No phase prompt map")
    else:
        if data.get("max_phases") is not None and len(phases) > data["max_phases"]:
            errors.append("Phase count exceeds maximum")
        if data["schema_version"] == 2 and data.get("phase_count") is not None and len(phases) != data["phase_count"]:
            errors.append("Phase count differs from selected count")
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
        if not path.is_file() or path.name == ORIGINAL_PLAN:
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
            "test_scope": test_scope, "errors": errors, "git_exclusion_verified": is_git}


def list_packages(project):
    root, _ = project_root(project)
    packages = []
    for output_name in (OUTPUT, LEGACY_OUTPUT):
        output = safe(root / output_name)
        if not output.is_dir():
            continue
        if output_name == OUTPUT:
            try:
                if read_json(output / ".implementation-plan-store.json") != STORE_MARKER:
                    continue
            except (OSError, ValueError, json.JSONDecodeError):
                continue
        for feature in sorted(output.iterdir()):
            if not feature.is_dir() or not (feature / ".implementation-plan.json").is_file():
                continue
            try:
                if read_json(feature / ".implementation-plan.json") != STORE_MARKER:
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
    command.add_argument("--phase-count", type=int)
    command.add_argument("--skills", default="")
    command.add_argument("--skills-mode", choices=("auto", "all"))
    command.add_argument("--commits", choices=("off", "scoped", "auto"))
    command.add_argument("--test-scope", choices=("focused", "full"))
    command.add_argument("--previous")
    command.add_argument("--source-plan")
    command.add_argument("--source-document")
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
                           args.skills_mode, args.commits, args.previous, args.source_plan,
                           args.phase_count, args.source_document, args.test_scope)
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
