"""Exercise request-review's recorded invariants with realistic review states."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "packs/developer-skills/skills/request-review/scripts/review_state.py"
SPEC = importlib.util.spec_from_file_location("review_state", SCRIPT)
review_state = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review_state)


def example(root: Path) -> dict:
    """Fictional multilingual source and three-repository reviewed scope."""
    return {
        "schema_version": 1,
        "repositories": [
            {"name": "web", "path": str(root / "Workspace with spaces/web"), "availability": "available"},
            {"name": "data", "path": str(root / "Workspace with spaces/data"), "availability": "available"},
            {"name": "api", "path": str(root / "external-api"), "availability": "available"},
        ],
        "sources": [
            {"id": "CHAT", "kind": "chat", "reference": "chat feedback", "items": [
                {"id": "S1", "original": "Expired announcements makita sa PACD, ug make its banner look like staff."},
                {"id": "S2", "original": "Hindi ko sure unsay UI sa queue monitor; same access sa signed ticket link?"},
            ]},
            {"id": "PDF", "kind": "pdf", "reference": "requirements.pdf", "pages": [
                {"number": 1, "status": "readable", "methods": ["text", "render", "visual"]},
                {"number": 2, "status": "partial", "methods": ["render", "visual", "ocr"], "unreadable": "small diagram label"},
                {"number": 3, "status": "unreadable", "methods": ["render", "visual"], "unreadable": "scanned handwritten note"},
            ], "items": [
                {"id": "S3", "original": "Expired announcements remain visible on PACD.", "page": 1},
                {"id": "S4", "original": "Ticket link displays personal queue progress.", "page": 2},
            ]},
        ],
        "requests": [
            {"id": "REQ-01", "source_ids": ["S1", "S3"], "english": "Hide expired announcements from PACD active banner.", "category": "Announcements", "type": "Bug report", "assessment": "Suspected defect", "readiness": "Ready to plan", "scope": "included", "locations": [{"kind": "page", "name": "PACD dashboard", "repository": "web", "route": "/pacd/dashboard", "access": "Signed-in PACD staff", "conditions": "Assigned division only"}], "evidence": [{"level": "source", "finding": "Query does not filter expired records."}], "files": [{"repository": "api", "path": "app/notices.py", "existing": True, "action": "Proposed modification", "purpose": "Fix", "lines": "20-27"}], "acceptance": ["Expired notices absent from active banner and present in archive."], "dependencies": [], "unresolved_facts": []},
            {"id": "REQ-02", "source_ids": ["S1"], "english": "Make the PACD banner visually consistent with staff banner.", "category": "Announcements", "type": "Improvement", "assessment": "Proposed change", "readiness": "Ready to plan", "scope": "included", "locations": [{"kind": "page", "name": "PACD dashboard", "repository": "web", "route": "/pacd/dashboard", "access": "Signed-in PACD staff"}], "evidence": [{"level": "source", "finding": "PACD and staff banners use different components."}], "files": [{"repository": "web", "path": "src/Banner.vue", "existing": True, "action": "Proposed modification", "purpose": "Improvement"}], "acceptance": ["PACD banner uses agreed layout without changing staff access."], "dependencies": [], "unresolved_facts": []},
            {"id": "REQ-03", "source_ids": ["S2", "S4"], "english": "Show personal queue progress through a valid signed ticket link; monitor presentation remains undecided.", "category": "Queue", "type": "New feature", "assessment": "Partially implemented", "readiness": "Needs clarification", "scope": "included", "locations": [{"kind": "page", "name": "Ticket status", "repository": "web", "route": "/ticket/status", "access": "Public with a valid signed ticket link"}], "evidence": [{"level": "source", "finding": "Signed token guard exists; queue progress UI is incomplete."}], "files": [{"repository": "web", "path": "src/QueueStatus.vue", "existing": False, "action": "Proposed addition", "purpose": "New"}], "acceptance": ["Valid signed ticket shows only its own queue progress."], "dependencies": [], "unresolved_facts": ["Monitor UI choice not established"]},
        ],
        "decisions": [
            {"id": "D1", "request_ids": ["REQ-01"], "question": "Where should expired notices remain available?", "options": [
                {"id": "1", "label": "Archive only", "effect": "Keeps history outside active banner"},
                {"id": "2", "label": "Active with label", "effect": "Shows expiry in active view"},
                {"id": "3", "label": "Hide everywhere", "effect": "Removes normal navigation"},
            ], "recommended": "1", "rationale": "Existing archive already supports retrieval", "selected": "1", "origin": "default applied", "unresolved_facts": []},
            {"id": "D2", "request_ids": ["REQ-03"], "question": "Which queue monitor UI?", "options": [
                {"id": "1", "label": "Compact status", "effect": "Shows ticket's own progress"},
                {"id": "2", "label": "Full monitor", "effect": "Shows division-wide queue"},
            ], "recommended": "1", "rationale": "Signed-link access is personal", "selected": None, "origin": "pending", "unresolved_facts": ["Monitor data visibility policy unknown"]},
        ],
    }


class ReviewStateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "Workspace with spaces/web/src").mkdir(parents=True)
        (self.root / "Workspace with spaces/data").mkdir(parents=True)
        (self.root / "external-api/app").mkdir(parents=True)
        (self.root / "Workspace with spaces/web/src/Banner.vue").write_text("banner", encoding="utf-8")
        (self.root / "external-api/app/notices.py").write_text("notices", encoding="utf-8")
        self.state = example(self.root)

    def test_compound_translation_duplicate_mapping_pdf_inventory_and_external_repo(self):
        result = review_state.validate_state(self.state, check_files=True)
        self.assertEqual(result, {"requests": 3, "sources": 2, "decisions": 2})
        self.assertEqual(self.state["requests"][0]["source_ids"], ["S1", "S3"])
        self.assertEqual(self.state["requests"][1]["source_ids"], ["S1"])

    def test_unmapped_source_or_missing_pdf_page_fails(self):
        state = deepcopy(self.state)
        state["sources"][1]["items"].append({"id": "S5", "original": "Another caption", "page": 2})
        with self.assertRaisesRegex(review_state.ReviewError, "omitted"):
            review_state.validate_state(state)
        state["sources"][1]["items"][-1]["page"] = 4
        with self.assertRaisesRegex(review_state.ReviewError, "uninventoried"):
            review_state.validate_state(state)

    def test_partial_and_unreadable_pdf_pages_require_detail(self):
        state = deepcopy(self.state)
        del state["sources"][1]["pages"][1]["unreadable"]
        with self.assertRaisesRegex(review_state.ReviewError, "unreadable detail"):
            review_state.validate_state(state)

    def test_default_provenance_and_later_explicit_answer(self):
        state = deepcopy(self.state)
        state["decisions"][0]["selected"] = "2"
        with self.assertRaisesRegex(review_state.ReviewError, "Default must select"):
            review_state.validate_state(state)
        state["decisions"][0]["origin"] = "selected by user"
        state["decisions"][0]["revisions"] = [{"prior": "1", "origin": "default applied", "reason": "Later user answer"}]
        state["requests"][0]["acceptance"] = ["Expired notices appear in active banner with an Expired label."]
        review_state.validate_state(state)

    def test_factual_unknown_cannot_be_defaulted(self):
        state = deepcopy(self.state)
        state["decisions"][1]["origin"] = "default applied"
        state["decisions"][1]["selected"] = "1"
        with self.assertRaisesRegex(review_state.ReviewError, "factual blocker"):
            review_state.validate_state(state)

    def test_local_fix_without_deployment_proof_and_excluded_dependency_remain_recorded(self):
        state = deepcopy(self.state)
        state["requests"][0]["assessment"] = "Already satisfied"
        state["requests"][0]["readiness"] = "Already satisfied"
        state["requests"][0]["evidence"].append({"level": "history", "finding": "Local fix predates review; deployment unverified."})
        state["requests"][1]["scope"] = "excluded"
        state["requests"][1]["readiness"] = "Deferred or excluded by the user"
        state["requests"][2]["dependencies"] = ["REQ-02"]
        state["revision_of"] = "previous-review"
        saved = self.root / "review-state.json"
        saved.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        loaded = json.loads(saved.read_text(encoding="utf-8"))
        review_state.validate_state(loaded, check_files=True)
        self.assertEqual(loaded["requests"][1]["source_ids"], ["S1"])
        self.assertEqual(loaded["requests"][2]["dependencies"], ["REQ-02"])

    def test_proposed_and_existing_paths_are_distinct(self):
        state = deepcopy(self.state)
        state["requests"][2]["files"][0]["lines"] = "1-9"
        with self.assertRaisesRegex(review_state.ReviewError, "cannot have inspected lines"):
            review_state.validate_state(state)
        del state["requests"][2]["files"][0]["lines"]
        state["requests"][0]["files"][0]["path"] = "../other/notices.py"
        with self.assertRaisesRegex(review_state.ReviewError, "repository-relative"):
            review_state.validate_state(state)
        state = deepcopy(self.state)
        state["requests"][2]["files"][0]["path"] = "src/Banner.vue"
        with self.assertRaisesRegex(review_state.ReviewError, "already exists"):
            review_state.validate_state(state, check_files=True)

    def test_missing_existing_file_and_missing_member_are_distinct(self):
        state = deepcopy(self.state)
        state["requests"][0]["files"][0]["path"] = "app/missing.py"
        with self.assertRaisesRegex(review_state.ReviewError, "Existing file missing"):
            review_state.validate_state(state, check_files=True)
        state["repositories"][2]["availability"] = "unavailable"
        review_state.validate_state(state, check_files=True)

    def test_handoff_preserves_sources_ids_english_decisions_and_repositories(self):
        parts = ["# Reviewed requirements"]
        parts += [f"{r['name']} {r['path']}" for r in self.state["repositories"]]
        for source in self.state["sources"]:
            parts.append(source["reference"])
            parts += [page.get("unreadable", "") for page in source.get("pages", [])]
            parts += [f"{item['id']} {item['original']} page {item['page']}" if "page" in item else f"{item['id']} {item['original']}" for item in source["items"]]
        for request in self.state["requests"]:
            parts.append(f"{request['id']} {request['english']} {request['scope']} {' '.join(request['source_ids'])}")
            parts += request["acceptance"] + request["dependencies"] + request["unresolved_facts"]
            parts += [" ".join(str(value) for value in location.values()) for location in request["locations"]]
            parts += [evidence["finding"] for evidence in request["evidence"]]
            parts += [file["path"] for file in request["files"]]
        for decision in self.state["decisions"]:
            parts.append(f"{decision['id']} {decision['origin']} {decision['question']} {decision.get('selected') or ''} {decision['rationale']}")
            parts += [option["label"] for option in decision["options"]]
        body = "\n".join(parts)
        review_state.validate_handoff(self.state, body)
        with self.assertRaisesRegex(review_state.ReviewError, "omits source item"):
            review_state.validate_handoff(self.state, body.replace(self.state["sources"][0]["items"][0]["original"], ""))
        with self.assertRaisesRegex(review_state.ReviewError, "location or access"):
            review_state.validate_handoff(self.state, body.replace("Public with a valid signed ticket link", ""))

    def test_chat_modes_and_quoted_file_tokens(self):
        document = self.root / "requirements with spaces.pdf"
        document.write_bytes(b"%PDF-1.4\n")
        path = str(document)
        self.assertEqual(review_state.parse_request([])["mode"], "default")
        self.assertEqual(review_state.parse_request([path, "--detailed"])["mode"], "detailed")
        self.assertEqual(review_state.parse_request(["--detailed", path])["source"], path)
        self.assertEqual(review_state.parse_request(["--summary"])["mode"], "summary")
        with self.assertRaises(review_state.ReviewError):
            review_state.parse_request(["--summary", path])
        with self.assertRaises(review_state.ReviewError):
            review_state.parse_request(["--questions"])
        with self.assertRaisesRegex(review_state.ReviewError, "not found"):
            review_state.parse_request(["missing requirements.pdf"])


if __name__ == "__main__":
    unittest.main()
