"""Validate request-review chat options and saved review ledgers.

This helper checks structure and references. It cannot assess translation or evidence truth.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys


class ReviewError(ValueError):
    pass


TYPES = {"Bug report", "New feature", "Improvement", "Refactor", "Removal", "Needs clarification"}
ASSESSMENTS = {"Confirmed defect", "Suspected defect", "Existing behavior", "Already satisfied", "Partially implemented", "Not reproduced", "Unable to verify", "Proposed change"}
READINESS = {"Ready to plan", "Needs clarification", "Needs investigation", "Already satisfied", "Deferred or excluded by the user"}
SCOPES = {"included", "excluded", "superseded"}
ACTIONS = {"Inspect", "Proposed modification", "Proposed addition", "Proposed rename", "Proposed removal"}
PURPOSES = {"New", "Improvement", "Fix", "Refactor", "Removal", "Unclear"}


def require(value: object, message: str) -> None:
    if not value:
        raise ReviewError(message)


def text_value(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReviewError(f"{label} must be nonempty text")
    return value


def objects(value: object, label: str) -> list[dict]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ReviewError(f"{label} must be a list of objects")
    return value


def relative_file(value: object) -> str:
    path = text_value(value, "file path").replace("\\", "/")
    posix = PurePosixPath(path)
    if posix.is_absolute() or PureWindowsPath(path).is_absolute() or any(part in {".", ".."} for part in posix.parts) or ":" in path:
        raise ReviewError(f"File path must be repository-relative: {path}")
    return path


def parse_request(tokens: list[str]) -> dict:
    if tokens and tokens[0] == "--":
        tokens = tokens[1:]
    if tokens == ["help"]:
        return {"mode": "help", "source": None}
    detailed = summary = client = False
    positional = []
    for token in tokens:
        if token == "--detailed":
            if detailed:
                raise ReviewError("Duplicate --detailed")
            detailed = True
        elif token == "--summary":
            if summary:
                raise ReviewError("Duplicate --summary")
            summary = True
        elif token == "--client":
            if client:
                raise ReviewError("Duplicate --client")
            client = True
        elif token.startswith("-"):
            raise ReviewError(f"Unknown option: {token}")
        else:
            positional.append(token)
    if len(positional) > 1:
        raise ReviewError("Supply one document path, or paste requests as chat text")
    if summary and (detailed or positional):
        raise ReviewError("--summary cannot start a new review or combine with --detailed")
    if client and summary:
        raise ReviewError("--client cannot combine with --summary")
    if client and positional:
        raise ReviewError("--client uses an identified review and cannot start a new review")
    source = positional[0] if positional else None
    if source and Path(source).suffix.lower() not in {".pdf", ".md", ".txt"}:
        raise ReviewError("Document path must end in .pdf, .md or .txt")
    if source and not Path(source).is_file():
        raise ReviewError(f"Document file not found: {source}")
    if client:
        return {"mode": "client-detailed" if detailed else "client", "source": None}
    return {"mode": "summary" if summary else "detailed" if detailed else "default", "source": source}


def validate_state(state: dict, check_files: bool = False) -> dict:
    if not isinstance(state, dict) or state.get("schema_version") != 1:
        raise ReviewError("Expected review schema_version 1")
    repositories = objects(state.get("repositories"), "repositories")
    sources = objects(state.get("sources"), "sources")
    requests = objects(state.get("requests"), "requests")
    decisions = objects(state.get("decisions"), "decisions")
    require(repositories, "At least one repository is required")
    require(sources, "At least one source is required")
    require(requests, "At least one request is required")
    repo_map = {}
    for repo in repositories:
        name = text_value(repo.get("name"), "repository name")
        if name in repo_map:
            raise ReviewError(f"Duplicate repository: {name}")
        root = Path(text_value(repo.get("path"), f"repository {name} path")).expanduser()
        if repo.get("availability") not in {"available", "unavailable"}:
            raise ReviewError(f"Invalid availability for {name}")
        if check_files and repo["availability"] == "available" and not root.is_dir():
            raise ReviewError(f"Available repository missing: {root}")
        repo_map[name] = repo
    source_items = {}
    pdf_pages = set()
    for source in sources:
        source_id = text_value(source.get("id"), "source ID")
        if source.get("kind") not in {"chat", "pdf", "markdown", "text"}:
            raise ReviewError(f"Invalid source kind: {source_id}")
        text_value(source.get("reference"), f"source {source_id} reference")
        if source["kind"] == "pdf":
            pages = objects(source.get("pages"), f"PDF {source_id} pages")
            require(pages, f"PDF {source_id} needs a page inventory")
            for page in pages:
                number = page.get("number")
                if not isinstance(number, int) or number < 1 or (source_id, number) in pdf_pages:
                    raise ReviewError(f"Invalid or duplicate PDF page: {source_id} {number}")
                pdf_pages.add((source_id, number))
                if page.get("status") not in {"readable", "partial", "unreadable"}:
                    raise ReviewError(f"Invalid PDF page status: {source_id} {number}")
                methods = page.get("methods")
                if not isinstance(methods, list) or any(method not in {"text", "render", "visual", "ocr", "annotations"} for method in methods):
                    raise ReviewError(f"Invalid PDF methods: {source_id} {number}")
                if page["status"] != "readable":
                    text_value(page.get("unreadable"), f"PDF {source_id} page {number} unreadable detail")
        for item in objects(source.get("items"), f"source {source_id} items"):
            item_id = text_value(item.get("id"), "source item ID")
            if item_id in source_items:
                raise ReviewError(f"Duplicate source item: {item_id}")
            text_value(item.get("original"), f"source item {item_id} original")
            if source["kind"] == "pdf" and (source_id, item.get("page")) not in pdf_pages:
                raise ReviewError(f"Source item {item_id} references an uninventoried PDF page")
            source_items[item_id] = source_id
    request_ids = set()
    for request in requests:
        request_id = text_value(request.get("id"), "request ID")
        if not re.fullmatch(r"REQ-[0-9]{2,}", request_id) or request_id in request_ids:
            raise ReviewError(f"Invalid or duplicate request ID: {request_id}")
        request_ids.add(request_id)
        refs = request.get("source_ids")
        if not isinstance(refs, list) or not refs or any(ref not in source_items for ref in refs):
            raise ReviewError(f"Request {request_id} has missing source mappings")
        for key in ("english", "category"):
            text_value(request.get(key), f"{request_id} {key}")
        for key, allowed in (("type", TYPES), ("assessment", ASSESSMENTS), ("readiness", READINESS), ("scope", SCOPES)):
            if request.get(key) not in allowed:
                raise ReviewError(f"Invalid {key} for {request_id}")
        for field in ("acceptance", "dependencies", "unresolved_facts"):
            if not isinstance(request.get(field), list):
                raise ReviewError(f"{request_id} {field} must be a list")
        locations = objects(request.get("locations"), f"{request_id} locations")
        require(locations, f"{request_id} needs a page or workflow location")
        for location in locations:
            if location.get("repository") not in repo_map or location.get("kind") not in {"page", "job", "service", "integration", "configuration"}:
                raise ReviewError(f"Invalid location in {request_id}")
            text_value(location.get("name"), f"{request_id} location name")
            if location["kind"] == "page":
                text_value(location.get("route"), f"{request_id} page route or uncertainty")
                text_value(location.get("access"), f"{request_id} page access or uncertainty")
        evidence_rows = objects(request.get("evidence"), f"{request_id} evidence")
        require(evidence_rows, f"{request_id} needs a finding or explicit evidence limit")
        for evidence in evidence_rows:
            if evidence.get("level") not in {"reported", "source", "test", "runtime", "deployed", "history"}:
                raise ReviewError(f"Invalid evidence level in {request_id}")
            text_value(evidence.get("finding"), f"{request_id} evidence finding")
        for file in objects(request.get("files"), f"{request_id} files"):
            repo = file.get("repository")
            if repo not in repo_map:
                raise ReviewError(f"Unknown file repository in {request_id}: {repo}")
            rel = relative_file(file.get("path"))
            if not isinstance(file.get("existing"), bool) or file.get("action") not in ACTIONS or file.get("purpose") not in PURPOSES:
                raise ReviewError(f"Invalid file action in {request_id}: {rel}")
            if not file["existing"] and file["action"] != "Proposed addition":
                raise ReviewError(f"Proposed file must use Proposed addition: {rel}")
            if file.get("lines") is not None and not file["existing"]:
                raise ReviewError(f"Proposed file cannot have inspected lines: {rel}")
            if file.get("lines") is not None and not re.fullmatch(r"[1-9][0-9]*(?:-[1-9][0-9]*)?", str(file["lines"])):
                raise ReviewError(f"Invalid inspected line range: {repo}/{rel}")
            if check_files and repo_map[repo]["availability"] == "available":
                root = Path(repo_map[repo]["path"]).resolve()
                target = (root / rel).resolve()
                if not target.is_relative_to(root):
                    raise ReviewError(f"File resolves outside repository: {repo}/{rel}")
                if file["existing"] and not target.is_file():
                    raise ReviewError(f"Existing file missing or outside repository: {repo}/{rel}")
                if not file["existing"] and target.exists():
                    raise ReviewError(f"Proposed addition already exists: {repo}/{rel}")
    if set(source_items) - {ref for request in requests for ref in request["source_ids"]}:
        raise ReviewError("Source items omitted from request coverage")
    for request in requests:
        if any(dep not in request_ids for dep in request["dependencies"]):
            raise ReviewError(f"Unknown dependency in {request['id']}")
    decision_ids = set()
    for decision in decisions:
        decision_id = text_value(decision.get("id"), "decision ID")
        if decision_id in decision_ids:
            raise ReviewError(f"Duplicate decision: {decision_id}")
        decision_ids.add(decision_id)
        refs = decision.get("request_ids")
        if not isinstance(refs, list) or not refs or any(ref not in request_ids for ref in refs):
            raise ReviewError(f"Decision {decision_id} has invalid request IDs")
        text_value(decision.get("question"), f"decision {decision_id} question")
        options = objects(decision.get("options"), f"decision {decision_id} options")
        option_ids = set()
        for option in options:
            option_id = text_value(option.get("id"), f"decision {decision_id} option ID")
            text_value(option.get("label"), f"decision {decision_id} option label")
            text_value(option.get("effect"), f"decision {decision_id} option effect")
            if option_id in option_ids:
                raise ReviewError(f"Duplicate option in {decision_id}: {option_id}")
            option_ids.add(option_id)
        if decision.get("recommended") is not None and decision["recommended"] not in option_ids:
            raise ReviewError(f"Unknown recommendation in {decision_id}")
        origin = decision.get("origin")
        selected = decision.get("selected")
        if origin not in {"pending", "default applied", "selected by user", "existing verified requirement"}:
            raise ReviewError(f"Invalid origin in {decision_id}")
        if origin == "pending" and selected is not None:
            raise ReviewError(f"Pending decision has a selection: {decision_id}")
        if origin == "default applied" and (selected != decision.get("recommended") or not selected):
            raise ReviewError(f"Default must select the presented recommendation: {decision_id}")
        if origin in {"selected by user", "existing verified requirement"} and not selected:
            raise ReviewError(f"Recorded answer missing in {decision_id}")
        if origin == "default applied" and decision.get("unresolved_facts"):
            raise ReviewError(f"Cannot default a factual blocker: {decision_id}")
        if origin == "default applied":
            text_value(decision.get("rationale"), f"decision {decision_id} rationale")
    return {"requests": len(requests), "sources": len(sources), "decisions": len(decisions)}


def validate_handoff(state: dict, body: str) -> None:
    """Check that the saved Markdown carries the ledger's irreplaceable content."""
    def contains(value: object, label: str) -> None:
        if str(value) not in body:
            raise ReviewError(f"Handoff omits {label}: {value}")

    if "Reviewed requirements" not in body:
        raise ReviewError("Handoff must be labeled Reviewed requirements")
    for repo in state["repositories"]:
        for value in (repo["name"], repo["path"]):
            contains(value, "repository mapping")
    for source in state["sources"]:
        contains(source["reference"], "source")
        for page in source.get("pages", []):
            if page["status"] != "readable":
                contains(page["unreadable"], "PDF readability limit")
        for item in source["items"]:
            contains(item["id"], "source item ID")
            contains(item["original"], "source item")
            if source["kind"] == "pdf" and f"page {item['page']}" not in body.lower():
                raise ReviewError(f"Handoff omits PDF page: {item['id']}")
    for request in state["requests"]:
        for value in (request["id"], request["english"], request["scope"], *request["source_ids"], *request["acceptance"], *request["dependencies"], *request["unresolved_facts"]):
            contains(value, "request content")
        for location in request["locations"]:
            for key in ("name", "repository", "route", "access", "conditions"):
                if location.get(key):
                    contains(location[key], "location or access")
        for evidence in request["evidence"]:
            contains(evidence["finding"], "evidence finding")
        for file in request["files"]:
            contains(file["path"], "file location")
    for decision in state["decisions"]:
        for value in (decision["id"], decision["origin"], decision["question"], decision.get("selected") or "", decision.get("rationale") or ""):
            if value:
                contains(value, "decision provenance")
        for option in decision["options"]:
            contains(option["label"], "presented option")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    parse = commands.add_parser("parse", help="Check tokens after the chat skill name")
    parse.add_argument("tokens", nargs=argparse.REMAINDER)
    validate = commands.add_parser("validate", help="Validate saved review-state.json")
    validate.add_argument("file", type=Path)
    validate.add_argument("--check-files", action="store_true")
    validate.add_argument("--handoff", type=Path, help="Check required ledger content in saved Markdown")
    args = parser.parse_args()
    try:
        if args.command == "parse":
            result = parse_request(args.tokens)
        else:
            state = json.loads(args.file.read_text(encoding="utf-8"))
            result = validate_state(state, args.check_files)
            if args.handoff:
                validate_handoff(state, args.handoff.read_text(encoding="utf-8"))
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ReviewError, OSError, json.JSONDecodeError) as error:
        print(f"request-review: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
