"""Exercise the portable bug-investigation helper with disposable repositories."""

from contextlib import chdir, redirect_stderr
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "packs/developer-skills/skills/bug-investigation"
spec = importlib.util.spec_from_file_location("bug_investigation", SKILL / "scripts/bug_investigation.py")
bug = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bug)


def git(path: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def repo(path: Path) -> None:
    path.mkdir(parents=True)
    git(path, "init", "-q")
    git(path, "config", "user.name", "Fixture")
    git(path, "config", "user.email", "fixture@example.test")
    (path / "base.txt").write_text("old\nkeep\n", encoding="utf-8")
    (path / "remove.txt").write_text("gone\n", encoding="utf-8")
    (path / "rename.txt").write_text("move\n", encoding="utf-8")
    git(path, "add", ".")
    git(path, "commit", "-qm", "baseline")


class RequestTests(unittest.TestCase):
    def test_modes_order_and_single_problem(self):
        parsed = bug.parse_request(["--detailed", "--fix", "Ticket missing", "--group", "role", "--history"])
        self.assertEqual(parsed["problem"], "Ticket missing")
        self.assertTrue(parsed["fix"] and parsed["detailed"] and parsed["history"])
        self.assertEqual(parsed["group"], "role")
        self.assertEqual(bug.identified_subject(parsed), "Ticket missing")

    def test_verify_uses_only_identifiable_context(self):
        request = bug.parse_request(["--verify", "--detailed"])
        with self.assertRaises(bug.InvestigationError):
            bug.identified_subject(request)
        self.assertEqual(bug.identified_subject(request, "BUG-01 in supplied report"), "BUG-01 in supplied report")
        self.assertTrue(bug.parse_request(["--verify", "--fix"])["fix"])

    def test_options_save_and_invalid_inputs(self):
        request = bug.parse_request(["--project", "storefront", "--save", "docs/bug report.md", "--group", "page"])
        self.assertEqual(request["save"], "docs/bug report.md")
        self.assertEqual(request["project"], "storefront")
        self.assertEqual(request["group"], "page")
        self.assertEqual(bug.parse_request(["help"]), {"help": True})
        for tokens in (["detailed"], ["--group", "feature"], ["--save"], ["--unknown"], ["help", "--fix"]):
            with self.subTest(tokens=tokens), redirect_stderr(io.StringIO()), self.assertRaises(bug.InvestigationError):
                bug.parse_request(tokens)


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.gettempdir()) / f"bug investigation {uuid.uuid4().hex}"
        self.tmp.mkdir()
        self.addCleanup(self.remove_fixture)
        self.parent = self.tmp / "Project with spaces"
        self.parent.mkdir()
        self.api = self.parent / "api"
        self.web = self.parent / "web"
        self.external = self.tmp / "外部 worker"
        for path in (self.api, self.web, self.external):
            repo(path)
        self.config = self.parent / "registry" / "projects.json"

    def remove_fixture(self):
        def retry(function, name, _error):
            os.chmod(name, stat.S_IWRITE)
            function(name)
        shutil.rmtree(self.tmp, onerror=retry)

    def test_project_registry_compatible_relative_and_external_members(self):
        with chdir(self.parent):
            bug.set_project(self.config, "shop", ["api=api", "web=web", f"worker={self.external}"])
        data = bug.load_projects(self.config)
        self.assertEqual(data["schema_version"], 1)
        self.assertFalse(Path(data["projects"]["shop"]["api"]).is_absolute())
        self.assertEqual(Path(data["projects"]["shop"]["worker"]), self.external)
        selected = bug.selected_repos(self.config, "shop", self.parent, True)
        self.assertTrue(selected["complete"])
        self.assertEqual({r["name"] for r in selected["repositories"]}, {"api", "web", "worker"})
        compatibility = subprocess.run(
            ["python", "-B", str(ROOT / "packs/developer-skills/skills/change-report/scripts/change_report.py"), "project", "list"],
            cwd=self.parent, env={**os.environ, "CHANGE_REPORT_HOME": str(self.config.parent), "PYTHONIOENCODING": "utf-8"},
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(compatibility.returncode, 0, compatibility.stderr)
        self.assertEqual(json.loads(compatibility.stdout)["projects"]["shop"], data["projects"]["shop"])
        with self.assertRaises(bug.InvestigationError):
            bug.set_project(self.config, "shop", ["duplicate=web"])
        with self.assertRaises(bug.InvestigationError):
            bug.parse_members(["api=api", "api=web"])

    def test_cli_project_setup_from_non_git_parent(self):
        script = SKILL / "scripts/bug_investigation.py"
        config = self.parent / "cli-projects.json"
        for arguments in (
            ["project", "set", "--config", str(config), "--project", "shop", "api=api", "web=web", f"worker={self.external}"],
            ["project", "list", "--config", str(config)],
            ["repos", "--config", str(config), "--project", "shop", "--require-complete"],
        ):
            result = subprocess.run(["python", "-B", str(script), *arguments], cwd=self.parent,
                                    capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads(result.stdout)["repositories"]), 3)

    def test_missing_member_limits_read_only_coverage_and_blocks_complete_fix(self):
        with chdir(self.parent):
            bug.set_project(self.config, "shop", ["api=api", "missing=absent"])
        result = bug.selected_repos(self.config, "shop", self.parent)
        self.assertFalse(result["complete"])
        self.assertTrue(result["repositories"][0]["available"])
        self.assertFalse(result["repositories"][1]["available"])
        with self.assertRaisesRegex(bug.InvestigationError, "selection incomplete"):
            bug.selected_repos(self.config, "shop", self.parent, True)

    def test_diff_statuses_exact_ranges_and_no_mutation(self):
        (self.api / "base.txt").write_text("new\nkeep\n", encoding="utf-8")
        (self.api / "remove.txt").unlink()
        (self.api / "rename.txt").rename(self.api / "renamed.txt")
        (self.api / "new file.txt").write_text("a\nb\n", encoding="utf-8")
        git(self.api, "add", "-A")
        before = git(self.api, "status", "--porcelain=v1")
        result = bug.worktree_changes(self.api)
        after = git(self.api, "status", "--porcelain=v1")
        self.assertEqual(before, after)
        rows = {entry["status"]: entry for entry in result["changes"] if entry["status"] != "Added"}
        self.assertEqual(rows["Modified"]["new_lines"], ["1"])
        self.assertEqual(rows["Modified"]["old_lines"], ["1"])
        self.assertEqual(rows["Deleted"]["old_lines"], ["1"])
        self.assertEqual(rows["Deleted"]["new_lines"], [])
        self.assertEqual(rows["Renamed"]["old_path"], "rename.txt")
        self.assertEqual(next(r for r in result["changes"] if r["path"] == "new file.txt")["new_lines"], ["1-2"])
        self.assertEqual({r["status"] for r in result["changes"]}, {"Added", "Modified", "Renamed", "Deleted"})

    def test_untracked_unicode_and_binary_locations(self):
        (self.web / "visibilité.txt").write_text("one\n", encoding="utf-8")
        (self.web / "image.bin").write_bytes(b"\x00\x01")
        (self.web / ".env").write_text("SECRET=fixture\n", encoding="utf-8")
        result = bug.worktree_changes(self.web)
        rows = {r["path"]: r for r in result["changes"]}
        self.assertEqual(rows["visibilité.txt"]["new_lines"], ["1"])
        self.assertTrue(rows["image.bin"]["binary"])
        self.assertEqual(rows["image.bin"]["new_lines"], [])
        self.assertNotIn(".env", rows)
        self.assertEqual(result["omitted_sensitive_or_generated"], 1)


BRIEF = """**Staff dashboard - /staff/dashboard**

- **Missing tickets:** Different division names hide tickets. Matching should accept the documented variants.

**Verification**

- Source inspection passed. Browser refresh remains unverified.
"""

DETAIL = """**Staff dashboard - /staff/dashboard**

### Reported problem

The user reported missing tickets; expected matching tickets remain visible.

### Findings

| Issue | Finding | Effect |
|---|---|---|
| BUG-01 - Missing tickets | Code compares one division spelling. | Older records are hidden. |
| BUG-02 - Wrong count | The same comparison feeds the count. | Count is low. |

### Confirmed cause

BUG-01 and BUG-02 share a comparison against one spelling.

### Corrections

An earlier claim that the cache caused BUG-01 was wrong; a fixture without cache reproduces it.

### Expected behavior and fixes

| Issue | Expected behavior | Fix |
|---|---|---|
| BUG-01 | Show matching tickets. | Normalize documented variants. |

### Implementation locations

| File | Lines | Status | Type | Change |
|---|---|---|---|---|
| `src/query.py` | 12-16 | Modified | Fix | Normalize division values. |
| `src/query.py` | 20 | Modified | Improvement | Explain count source. |
| `tests/test_query.py` | 8-22 | Added | Fix | Cover old records and role boundary. |
| `src/old.py` → `src/new.py` | 1 | Renamed | Refactor | Keep owner name aligned. |
| `src/obsolete.py` | 3 old | Deleted | Removal | Remove unused comparison. |

### Data and access

Existing records remain; role filtering stays enforced.

### Verification

- Passed: current fixture for BUG-01.
- Failed: current fixture for BUG-02.
- Reported previously; not rerun: browser check before this edit.

### Remaining checks

- Recheck BUG-02 count with an older division name; expected full count.
"""


class ReportRulesTests(unittest.TestCase):
    def test_brief_and_detailed_shapes(self):
        bug.validate_report(BRIEF, False)
        bug.validate_report(DETAIL, True)
        with self.assertRaises(bug.InvestigationError):
            bug.validate_report(DETAIL, False)

    def test_multiple_roles_and_unresolved_cause(self):
        body = """**Clerk - /requests**

### Reported problem

BUG-01 is reported by a clerk.

### Cause not yet confirmed

The log is unavailable.

**Manager - /review**

### Reported problem

BUG-02 is reported by a manager.

### Verification

- Blocked: fixture data unavailable.
"""
        bug.validate_report(body, True)
        mixed = body.replace("### Verification\n\n- Blocked", "### Confirmed cause\n\nBUG-02 is confirmed by a local fixture.\n\n### Verification\n\n- Blocked")
        bug.validate_report(mixed, True)

    def test_investigation_only_locations_do_not_claim_changes(self):
        body = """**Data processing**

### Cause not yet confirmed

The source read is incomplete.

### Expected behavior and proposed fixes

Investigate the parser boundary.

### Implementation locations

| File | Lines | Finding or proposed change |
|---|---|---|
| `src/parser.py` | 24 | Inspected parser branch. |
"""
        bug.validate_report(body, True)
        self.assertNotIn("| Status |", body)
        self.assertNotIn("fixed", body)

    def test_history_and_structural_rejections(self):
        historical = DETAIL.replace("### Confirmed cause", "### Origin\n\nOlder data predates rejection.\n\n### Confirmed cause")
        bug.validate_report(historical, True)
        bug.validate_report(DETAIL + "\ncommit 0123456789abcdef0123456789abcdef01234567\n", True, allow_hashes=True)
        for body in (DETAIL.replace("### Findings", "### Recommendations\n\nLater work.\n\n### Findings"),
                     DETAIL.replace("Modified | Fix", "Modified | Guessed"),
                     DETAIL.replace("12-16", "1-999-1000"),
                     DETAIL.replace("`src/query.py`", "`C:\\Users\\Private\\query.py`"),
                     DETAIL + "\n| Project | File |\n|---|---|\n",
                     DETAIL + "\ncommit 0123456789abcdef0123456789abcdef01234567\n",
                     DETAIL + "\n<unfilled placeholder>\n"):
            with self.subTest(body=body[-80:]), self.assertRaises(bug.InvestigationError):
                bug.validate_report(body, True)


if __name__ == "__main__":
    unittest.main()
