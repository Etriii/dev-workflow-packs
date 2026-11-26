"""Reserve, inspect, and validate ignored implementation-plan packages."""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
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
PHASED_SHARED = ("PLAN.md", "STATUS.md", "PROMPTS.md", "DECISIONS.md")
PROFILES = ("balanced", "detailed", "light")
ORIGINAL_PLAN = "ORIGINAL_PLAN.md"
SOURCE_DOCUMENT = "SOURCE_DOCUMENT.pdf"
PHASE_ID = re.compile(r"P\d{2,}")
MERGE_ID = re.compile(r"M\d{2,}")
MERGE_FILE = "prompts/MERGE_PROMPTS.md"
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
    if data.get("schema_version") not in (1, 2, 3, 4) or data.get("owner") != OWNER:
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


def start(project, feature, max_phases=None, skills=None, skills_mode=None, commits=None, previous=None, source_plan=None, phase_count=None, source_document=None, test_scope=None, profile=None, parallel_mode=None):
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
    if skills is None:
        skills = ",".join(prior.get("skills", [])) if prior else ""
    if max_phases is None and prior:
        max_phases = prior.get("max_phases")
    if phase_count is None and prior:
        phase_count = prior.get("phase_count")
    if profile is None:
        profile = prior.get("profile", "detailed") if prior else "balanced"
    if parallel_mode is None:
        parallel_mode = (prior.get("parallel_mode", "off") if prior else
                         "off" if profile != "balanced" else "worktree" if is_git else "analysis")
    if profile not in PROFILES or parallel_mode not in ("off", "analysis", "worktree"):
        raise ValueError("Invalid planning profile or parallel mode")
    if profile == "light":
        if parallel_mode != "off" or phase_count not in (None, 1):
            raise ValueError("Light planning requires one phase and parallel mode off")
        phase_count = 1
    if parallel_mode == "worktree" and not is_git:
        raise ValueError("Worktree planning requires a Git repository")
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
        if (isinstance(prior.get("source_plan"), dict) and prior["source_plan"].get("origin") == "file"
                and not (prior_package / ORIGINAL_PLAN).is_file()):
            raise ValueError("Previous original plan is missing")
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
    data = {"schema_version": 4 if profile == "balanced" else 3,
            "owner": OWNER, "feature": feature, "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "max_phases": max_phases, "phase_count": phase_count,
            "skills": names, "skills_mode": skills_mode, "test_scope": test_scope,
            "commits": commits, "previous": str(prior_package) if prior_package else None,
            "phases": {}, "skill_assignments": {}, "source_plan": source,
            "source_document": document, "profile": profile, "parallel_mode": parallel_mode,
            "dependencies": {}, "parallel_groups": {}, "parallel_tasks": {},
            "parallel_reason": "", "merges": {}}
    write_new(package / ".package.json", data)
    if original is not None:
        with (package / ORIGINAL_PLAN).open("xb") as stream:
            stream.write(original)
    if document_bytes is not None:
        with (package / SOURCE_DOCUMENT).open("xb") as stream:
            stream.write(document_bytes)
    if profile == "detailed":
        (package / "prompts").mkdir()
    return {"package": str(package), "git_exclusion_verified": is_git, "ignore_rule": rule}


def prompt_sections(path):
    """Extract addressable level-two sections without interpreting fenced examples."""
    sections = {}
    current = None
    fence = None
    for line in regular(path).read_text(encoding="utf-8").splitlines(keepends=True):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
        if fence is None and not marker and line.startswith("## "):
            match = re.fullmatch(r"## ([PM]\d{2,})\s*", line.strip())
            current = match[1] if match else None
            if current:
                if current in sections:
                    raise ValueError(f"Duplicate prompt section: {current} in {path.name}")
                sections[current] = []
        if current:
            sections[current].append(line)
    return {key: "".join(lines) for key, lines in sections.items()}


def dependency_graph(value, ids, label, errors):
    if not isinstance(value, dict) or set(value) != set(ids):
        errors.append(f"{label} must map every ID exactly once")
        return {}
    for key, parents in value.items():
        if (not isinstance(parents, list) or any(not isinstance(item, str) for item in parents)
                or len(parents) != len(set(parents)) or not set(parents) <= set(ids) or key in parents):
            errors.append(f"Invalid {label}: {key}")
            return {}
    pending = set(ids)
    while pending:
        ready = {key for key in pending if not set(value[key]) & pending}
        if not ready:
            errors.append(f"Cycle in {label}")
            return {}
        pending -= ready
    return value


def text_list(value, allow_empty=False):
    return (isinstance(value, list) and (allow_empty or bool(value))
            and all(isinstance(item, str) and item.strip() for item in value)
            and len(value) == len(set(value)))


def ancestors(graph, key):
    result = set()
    pending = list(graph[key])
    while pending:
        node = pending.pop()
        if node not in result:
            result.add(node)
            pending.extend(graph[node])
    return result


def relative_owner(value):
    path = PurePosixPath(value)
    return (not path.is_absolute() and value not in ("", ".")
            and not any(part.casefold() in ("..", ".git") for part in path.parts)
            and not any(char in value for char in "\\:*?[]"))


def phased(data):
    return data["schema_version"] >= 4 and data.get("profile") == "balanced"


def merge_file(data):
    return "MERGE_PROMPTS.md" if phased(data) else MERGE_FILE


def phase_file(package, data, name):
    return regular(package / name if phased(data) else package / "prompts" / name)


def markdown_section(body, title):
    """Read one current summary without returning the execution archive."""
    selected, fence, lines = False, None, []
    for line in body.splitlines(keepends=True):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
        if fence is None and not marker and line.startswith("## "):
            if selected:
                break
            selected = line.strip() == "## " + title
            continue
        if selected:
            lines.append(line)
    return "".join(lines).strip()


def phase_states(body):
    return dict(re.findall(r"^\|\s*(P\d{2,})\s*\|\s*([A-Z_]+)\s*\|", body, re.MULTILINE))


def status_summary(package, data, history=False):
    name = "PLAN.md" if data.get("profile") == "light" else "STATUS.md" if phased(data) else "PROGRESS.md"
    path = regular(package / name)
    body = path.read_text(encoding="utf-8") if path.is_file() else ""
    current = (markdown_section(body, "Current") or markdown_section(body, "Status")
               or (markdown_section(body, "Progress") if data.get("profile") == "light" else ""))
    if not current:
        current = "No current summary recorded; inspect the identified status file."
    result = {"status_file": name, "summary": current[:6000],
              "summary_truncated": len(current) > 6000, "recorded_only": True}
    if history:
        result["history"] = body
    if phased(data):
        states = phase_states(markdown_section(body, "Current"))
        graph = data.get("dependencies", {})
        groups = data.get("parallel_groups", {})
        groups = groups if isinstance(groups, dict) else {}
        valid_groups = [group for group in groups.values() if text_list(group)]
        grouped = {item for group in valid_groups for item in group}
        startability = {}
        for task, parents in graph.items() if isinstance(graph, dict) else ():
            if not isinstance(parents, list) or any(not isinstance(parent, str) for parent in parents):
                continue
            waiting = [parent for parent in parents if states.get(parent) not in
                       (("MERGED",) if parent in grouped and data.get("parallel_mode") == "worktree"
                        else ("COMPLETE", "MERGED"))]
            peers = [peer for group in valid_groups if task in group
                     for peer in group if peer != task]
            state = states.get(task, "UNKNOWN")
            startability[task] = {"state": state, "waiting_for": waiting, "concurrent_with": peers,
                                 "can_start_separately": state == "NOT_STARTED" and not waiting,
                                 "live_preflight_required": True}
        result["tasks"] = startability
    return result


def inspect_phased(package, data, phases, files, errors):
    status = regular(package / "STATUS.md")
    if status.is_file():
        current = markdown_section(status.read_text(encoding="utf-8"), "Current")
        states = phase_states(current)
        allowed = {"NOT_STARTED", "IN_PROGRESS", "PAUSED", "BLOCKED", "VERIFIED",
                   "MERGE_PENDING", "MERGED", "COMPLETE", "REVERTED"}
        if set(states) != set(phases) or any(value not in allowed for value in states.values()):
            errors.append("STATUS.md Current table must record every task exactly once with a valid state")
        ids = re.findall(r"^\|\s*(P\d{2,})\s*\|", current, re.MULTILINE)
        if len(ids) != len(set(ids)):
            errors.append("STATUS.md has duplicate current task states")
    index = regular(package / "PROMPTS.md")
    index_body = index.read_text(encoding="utf-8") if index.is_file() else ""
    for task, name in phases.items():
        if not isinstance(name, str) or not relative_owner(name):
            continue
        if name not in index_body:
            errors.append(f"PROMPTS.md must link the stored task prompt: {task}")
        decision = regular((package / name).parent / "DECISIONS.md")
        if decision.is_file():
            files.append(decision)


def inspect_commit_drafts(path, errors):
    if not path.is_file():
        return
    blocks = [block.replace("\r\n", "\n").strip()
              for block in COMMIT_BLOCK.findall(path.read_text(encoding="utf-8"))]
    drafts = [block for block in blocks if block and COMMIT_SUBJECT.fullmatch(block.splitlines()[0])]
    if not drafts:
        errors.append(f"{path.name} needs copyable Conventional Commit blocks with detailed bodies; subject-only lists are incomplete")
    for draft in drafts:
        subject, _, body = draft.partition("\n\n")
        if not body.strip():
            errors.append(f"Commit message needs a body: {subject}")


def inspect_modes(package, data, phases, files, errors):
    if data["schema_version"] < 3:
        return
    profile, mode = data.get("profile"), data.get("parallel_mode")
    if profile not in PROFILES or (data["schema_version"] < 4 and profile == "balanced") or mode not in ("off", "analysis", "worktree"):
        errors.append("Invalid planning profile or parallel mode")
        return
    if profile == "light" and (mode != "off" or list(phases) != ["P01"]):
        errors.append("Light planning requires one phase and parallel mode off")
    graph = dependency_graph(data.get("dependencies"), phases, "phase dependencies", errors)
    groups, tasks, merges = (data.get(name) for name in ("parallel_groups", "parallel_tasks", "merges"))
    if not all(isinstance(item, dict) for item in (groups, tasks, merges)):
        errors.append("Parallel groups, tasks and merges must be objects")
        return
    if mode == "off":
        if groups or tasks or merges or (package / merge_file(data)).exists():
            errors.append("Sequential planning cannot contain parallel tasks or merges")
        return
    if not isinstance(data.get("parallel_reason"), str) or not data["parallel_reason"].strip():
        errors.append("Parallel planning needs an evidence-based parallel_reason, including when no split is safe")
    members = [item for group in groups.values() if isinstance(group, list)
               for item in group if isinstance(item, str)]
    expected_tasks = set(members) if phased(data) else set(phases)
    if set(tasks) != expected_tasks:
        errors.append("Parallel tasks must describe every grouped phase" if phased(data)
                      else "Parallel tasks must describe every phase")
        return
    valid_tasks = True
    task_roots = {}
    for phase, task in tasks.items():
        if (not isinstance(task, dict) or not text_list(task.get("owned_paths"))
                or not text_list(task.get("write_resources"), allow_empty=True)
                or not text_list(task.get("read_set")) or not isinstance(task.get("reason"), str)
                or not task["reason"].strip()):
            errors.append(f"Incomplete parallel task: {phase}")
            valid_tasks = False
            continue
        if any(not relative_owner(item) for item in task["owned_paths"]):
            errors.append(f"Ownership needs concrete repository-relative paths: {phase}")
        repository = task.get("repository", str(package.parent.parent.parent))
        if not isinstance(repository, str) or not Path(repository).is_absolute():
            errors.append(f"Invalid task repository: {phase}")
            valid_tasks = False
        else:
            task_roots[phase] = str(project_root(repository)[0]).casefold()
        for item in task["read_set"]:
            target = item.split("#", 1)[0]
            if not relative_owner(target) or not regular(package / target).is_file():
                errors.append(f"Missing or unsafe package read-set file: {phase}: {item}")
    members = []
    for group, selected in groups.items():
        if (not re.fullmatch(r"G\d{2,}", group) or not text_list(selected)
                or len(selected) < 2 or not set(selected) <= set(phases)):
            errors.append(f"Invalid parallel group: {group}")
            continue
        members.extend(selected)
        if not graph or not valid_tasks:
            continue
        for index, left in enumerate(selected):
            for right in selected[index + 1:]:
                if right in ancestors(graph, left) or left in ancestors(graph, right):
                    errors.append(f"Dependent phases cannot run together: {group}: {left}, {right}")
                if set(tasks[left]["write_resources"]) & set(tasks[right]["write_resources"]):
                    errors.append(f"Shared mutable resource in {group}: {left}, {right}")
                same_repo = task_roots[left] == task_roots[right]
                if same_repo:
                    for a in tasks[left]["owned_paths"]:
                        for b in tasks[right]["owned_paths"]:
                            a, b = PurePosixPath(a).as_posix().casefold(), PurePosixPath(b).as_posix().casefold()
                            if a == b or a.startswith(b + "/") or b.startswith(a + "/"):
                                errors.append(f"Overlapping ownership in {group}: {left}, {right}")
    if len(members) != len(set(members)):
        errors.append("A phase may belong to only one parallel group")
    if mode != "worktree":
        if merges or (package / merge_file(data)).exists():
            errors.append("Merge prompts require worktree mode")
        return
    directories, branches = [], []
    for phase in set(members):
        task = tasks[phase]
        if not isinstance(task, dict):
            continue
        repository, directory, branch = (task.get(name) for name in ("repository", "worktree", "branch"))
        if (not isinstance(repository, str) or not Path(repository).is_absolute()
                or not isinstance(directory, str) or not Path(directory).is_absolute()
                or not isinstance(branch, str) or not branch.strip()
                or not isinstance(task.get("base_commit"), str)
                or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", task["base_commit"])):
            errors.append(f"Incomplete worktree identity: {phase}")
            continue
        repository, is_git = project_root(repository)
        worktree = safe(directory)
        if not is_git or git(repository, "check-ref-format", "--branch", branch).returncode:
            errors.append(f"Invalid worktree repository or branch: {phase}")
        if git(repository, "cat-file", "-e", task["base_commit"] + "^{commit}").returncode:
            errors.append(f"Worktree baseline is not an existing commit: {phase}")
        if worktree == repository or worktree.is_relative_to(repository) or repository.is_relative_to(worktree):
            errors.append(f"Worktree must be separate from its source repository: {phase}")
        directories.append(str(worktree).casefold())
        branches.append((str(repository).casefold(), branch.casefold()))
    if len(set(directories)) != len(directories) or len(set(branches)) != len(branches):
        errors.append("Parallel worktrees and branches must be distinct")
    for index, directory in enumerate(directories):
        for other in directories[index + 1:]:
            if Path(directory).is_relative_to(Path(other)) or Path(other).is_relative_to(Path(directory)):
                errors.append("Parallel worktree directories cannot be nested")
    merged = []
    merge_graph = {}
    for merge_id, merge in merges.items():
        if (not MERGE_ID.fullmatch(merge_id) or not isinstance(merge, dict)
                or not text_list(merge.get("phases")) or not set(merge["phases"]) <= set(members)
                or not isinstance(merge.get("owner_phase"), str) or merge["owner_phase"] not in phases
                or not isinstance(merge.get("target_branch"), str) or not merge["target_branch"].strip()
                or not isinstance(merge.get("repository"), str) or not Path(merge["repository"]).is_absolute()
                or not isinstance(merge.get("target_commit"), str)
                or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", merge["target_commit"])):
            errors.append(f"Invalid merge operation: {merge_id}")
            continue
        repository, is_git = project_root(merge["repository"])
        if not is_git or git(repository, "check-ref-format", "--branch", merge["target_branch"]).returncode:
            errors.append(f"Invalid merge repository or target branch: {merge_id}")
        if git(repository, "cat-file", "-e", merge["target_commit"] + "^{commit}").returncode:
            errors.append(f"Merge baseline is not an existing commit: {merge_id}")
        if graph and not set(merge["phases"]) <= ancestors(graph, merge["owner_phase"]):
            errors.append(f"Merge owner must depend on its source phases: {merge_id}")
        for phase in merge["phases"]:
            task = tasks[phase]
            if (not isinstance(task, dict) or task.get("repository") != merge["repository"]
                    or task.get("branch") == merge["target_branch"]):
                errors.append(f"Merge source/target identity mismatch: {merge_id}: {phase}")
        merged.extend(merge["phases"])
        merge_graph[merge_id] = merge.get("depends_on")
    if set(merged) != set(members) or len(merged) != len(set(merged)):
        errors.append("Each isolated phase needs exactly one merge operation")
    dependency_graph(merge_graph, merges, "merge dependencies", errors)
    if merges:
        path = regular(package / merge_file(data))
        files.append(path)
        candidates = package.rglob("*.md") if phased(data) else safe(package / "prompts").iterdir()
        for candidate in candidates:
            if candidate != path and (MERGE_ID.match(candidate.stem) or candidate.name.startswith("MERGE")):
                errors.append("All merge prompts must use the single MERGE_PROMPTS.md file")
        if not path.is_file():
            errors.append(f"Missing {merge_file(data)}")
        else:
            sections = prompt_sections(path)
            if set(sections) != set(merges):
                errors.append("Merge sections must match merge IDs exactly")
            for merge_id, body in sections.items():
                if not body.partition("\n")[2].strip():
                    errors.append(f"Empty merge prompt: {merge_id}")
    elif (package / merge_file(data)).exists():
        errors.append("Merge prompt file has no mapped operations")


def stored_prompt(package, data, prompt_id):
    if MERGE_ID.fullmatch(prompt_id):
        if prompt_id not in data.get("merges", {}):
            raise ValueError(f"Unknown merge: {prompt_id}")
        return prompt_sections(package / merge_file(data))[prompt_id]
    name = (data.get("phases") or {}).get(prompt_id)
    if not name:
        raise ValueError(f"Unknown phase: {prompt_id}")
    if data.get("profile") == "light":
        return prompt_sections(package / "PLAN.md")[prompt_id]
    return phase_file(package, data, name).read_text(encoding="utf-8")


def inspect(package):
    root, is_git, package, data = locate(package)
    errors = []
    if is_git:
        for path in (package.parent, package / "README.md", package / "prompts" / "P01.md"):
            if not ignored(root, path):
                errors.append(f"Output is not ignored: {path.relative_to(root)}")
        if checked_git(root, "ls-files", "--", package.parent.relative_to(root).as_posix()).strip():
            errors.append("Package output is tracked")
    light = data.get("profile") == "light" and data["schema_version"] >= 3
    required = ("PLAN.md",) if light else PHASED_SHARED if phased(data) else SHARED
    needs_original = (data["schema_version"] >= 2 and
                      (not phased(data) or (isinstance(data.get("source_plan"), dict)
                                            and data["source_plan"].get("origin") == "file")))
    required += (ORIGINAL_PLAN,) if needs_original else ()
    files = [package / name for name in required]
    for name, path in zip(required, files):
        if not regular(path).is_file():
            errors.append(f"Missing {name}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"Empty {name}")
    if not phased(data):
        inspect_commit_drafts(regular(package / ("PLAN.md" if light else "COMMIT_MESSAGES.md")), errors)
    if data["schema_version"] >= 2:
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
        phases = {}
    else:
        cap, count = data.get("max_phases"), data.get("phase_count")
        if cap is not None and (type(cap) is not int or cap < 1):
            errors.append("Invalid maximum phase count")
        elif cap is not None and len(phases) > cap:
            errors.append("Phase count exceeds maximum")
        if count is not None and (type(count) is not int or count < 1):
            errors.append("Invalid selected phase count")
        elif data["schema_version"] >= 2 and count is not None and len(phases) != count:
            errors.append("Phase count differs from selected count")
        expected_ids = [f"P{index:02d}" for index in range(1, len(phases) + 1)]
        if list(phases) != expected_ids:
            errors.append("Phase IDs must be ordered and contiguous from P01")
        if any(not isinstance(value, str) for value in phases.values()):
            errors.append("Phase prompt mappings must be strings")
        elif len(set(phases.values())) != len(phases):
            errors.append("Phase prompts must have distinct files")
        for phase, name in phases.items():
            if not isinstance(phase, str) or not isinstance(name, str):
                errors.append(f"Invalid phase prompt mapping: {phase}")
                continue
            if light:
                if phase != "P01" or name != "PLAN.md#P01":
                    errors.append("Light prompt must map P01 to PLAN.md#P01")
                elif (package / "PLAN.md").is_file():
                    section = prompt_sections(package / "PLAN.md").get("P01", "")
                    if not section.partition("\n")[2].strip():
                        errors.append("Missing or empty light execution section P01")
                continue
            expected_name = f"phase-{phase[1:]}/PROMPT.md" if phased(data) else None
            valid_name = (name == expected_name if phased(data) else
                          bool(re.fullmatch(r"P\d{2,}_[A-Z0-9_]+\.md", name)))
            if not PHASE_ID.fullmatch(phase) or not valid_name:
                errors.append(f"Invalid phase prompt mapping: {phase}")
                continue
            prompt = phase_file(package, data, name)
            files.append(prompt)
            if not prompt.is_file():
                errors.append(f"Missing prompt for {phase}: {name}")
            elif phase not in prompt.read_text(encoding="utf-8"):
                errors.append(f"Prompt does not identify {phase}: {name}")
            if phased(data):
                inspect_commit_drafts(prompt, errors)
    assignments = data.get("skill_assignments")
    names = data.get("skills")
    if not text_list(names, allow_empty=True) or not isinstance(assignments, dict) or set(assignments) != set(names):
        errors.append("Skill assignments do not match selected skills")
    else:
        for name, assignment in assignments.items():
            assigned = assignment.get("phases") if isinstance(assignment, dict) else None
            reason = assignment.get("reason") if isinstance(assignment, dict) else None
            if not text_list(assigned) or not set(assigned) <= set(phases or ()) or not isinstance(reason, str) or not reason.strip():
                errors.append(f"Invalid skill assignment: {name}")
            elif data.get("skills_mode") == "all" and set(assigned) != set(phases):
                errors.append(f"Skill is missing from an all-mode prompt: {name}")
    inspect_modes(package, data, phases, files, errors)
    if phased(data):
        inspect_phased(package, data, phases, files, errors)
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
            "test_scope": test_scope, "profile": data.get("profile", "detailed"),
            "parallel_mode": data.get("parallel_mode", "off"), "dependencies": data.get("dependencies", {}),
            "merges": data.get("merges", {}), "errors": errors, "git_exclusion_verified": is_git}


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
    command.add_argument("--skills")
    command.add_argument("--skills-mode", choices=("auto", "all"))
    command.add_argument("--commits", choices=("off", "scoped", "auto"))
    command.add_argument("--test-scope", choices=("focused", "full"))
    command.add_argument("--previous")
    command.add_argument("--source-plan")
    command.add_argument("--source-document")
    command.add_argument("--profile", choices=PROFILES)
    command.add_argument("--parallel-ready", nargs="?", const="analysis", choices=("off", "analysis", "worktree"))
    command = commands.add_parser("list")
    command.add_argument("--project", required=True)
    for name in ("check", "status", "skills", "prompt"):
        command = commands.add_parser(name)
        command.add_argument("--package", required=True)
        if name == "prompt":
            command.add_argument("--phase", required=True, help="Stored Pxx execution or Mxx merge prompt ID")
        if name == "status":
            command.add_argument("--history", action="store_true", help="Include the identified ledger, without traversing evidence files")
    args = parser.parse_args(argv)
    try:
        if args.action == "start":
            result = start(args.project, args.feature, args.max_phases, args.skills,
                           args.skills_mode, args.commits, args.previous, args.source_plan,
                            args.phase_count, args.source_document, args.test_scope,
                            args.profile, args.parallel_ready)
        elif args.action == "list":
            result = {"packages": list_packages(args.project)}
        else:
            result = inspect(args.package)
            if args.action == "prompt":
                if result["errors"]:
                    raise ValueError("Package has validation errors")
                if result["status"] != "ready":
                    raise ValueError("Package is still a draft")
                print(stored_prompt(safe(args.package), read_json(Path(args.package) / ".package.json"), args.phase))
                return 0
            if args.action == "skills":
                result = {key: result[key] for key in ("package", "skills", "skill_assignments")}
            if args.action == "status":
                data = read_json(Path(args.package) / ".package.json")
                summary = status_summary(safe(args.package), data, args.history)
                result = {key: result[key] for key in ("package", "status", "profile", "errors")}
                result.update(summary)
        print(json.dumps(result, indent=2))
        return 1 if args.action == "check" and result["errors"] else 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
