"""Exercise implementation package storage in disposable projects."""

from contextlib import redirect_stdout, redirect_stderr
from importlib.util import module_from_spec, spec_from_file_location
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "packs/developer-skills/skills/implementation-plan/scripts/package_store.py"
SPEC = spec_from_file_location("implementation_package_store", SCRIPT)
store = module_from_spec(SPEC)
sys.modules[SPEC.name] = store
SPEC.loader.exec_module(store)


class PackageStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="implementation-plan-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def init_git(self):
        self.git("init", "-q")

    def save_complete(self, package):
        for name in store.SHARED:
            (package / name).write_text(f"# {name}\n", encoding="utf-8")
        (package / "prompts" / "P01_BUILD.md").write_text("Implement P01 only.\n", encoding="utf-8")
        metadata = json.loads((package / ".package.json").read_text(encoding="utf-8"))
        metadata["phases"] = {"P01": "P01_BUILD.md"}
        metadata["skill_assignments"] = {
            name: {"phases": ["P01"], "reason": "Relevant to the selected phase"}
            for name in metadata["skills"]
        }
        (package / ".package.json").write_text(json.dumps(metadata), encoding="utf-8")

    def test_missing_docs_ignores_docs_and_keeps_revisions(self):
        self.init_git()
        first = store.start(self.root, "Hiring and Workforce", 3, "caveman,ultimate-ui-ux")
        package = Path(first["package"])
        self.assertEqual((self.root / ".gitignore").read_bytes(), b"/docs/\n")
        self.assertTrue(first["git_exclusion_verified"])
        self.save_complete(package)
        self.assertEqual(store.inspect(package)["errors"], [])
        second = store.start(self.root, "Ignored new title", 3, "caveman,ultimate-ui-ux",
                             previous=package)
        next_package = Path(second["package"])
        self.assertEqual(next_package.parent, package.parent)
        self.assertNotEqual(next_package, package)
        self.assertEqual(json.loads((next_package / ".package.json").read_text())["previous"], str(package))
        self.assertTrue((package / "PLAN.md").exists())
        self.assertEqual((self.root / ".gitignore").read_bytes(), b"/docs/\n")

    def test_existing_tracked_docs_gets_narrow_rule(self):
        self.init_git()
        docs = self.root / "docs"
        docs.mkdir()
        (docs / "existing.md").write_text("keep\n", encoding="utf-8")
        self.git("add", "docs/existing.md")
        before = (docs / "existing.md").read_bytes()
        result = store.start(docs, "Hiring")
        self.assertEqual((self.root / ".gitignore").read_bytes(), b"/docs/hiring-implementation/\n")
        self.assertEqual((docs / "existing.md").read_bytes(), before)
        self.assertIn("docs/existing.md", self.git("ls-files"))
        self.assertTrue(result["git_exclusion_verified"])

    def test_existing_untracked_docs_preserves_existing_ignore_bytes(self):
        self.init_git()
        (self.root / "docs").mkdir()
        (self.root / "docs" / "personal.md").write_text("keep", encoding="utf-8")
        original = b"# Existing\r\n/cache/\r\n"
        (self.root / ".gitignore").write_bytes(original)
        store.start(self.root, "Roster")
        self.assertEqual((self.root / ".gitignore").read_bytes(), original + b"/docs/roster-implementation/\r\n")
        self.assertEqual((self.root / "docs" / "personal.md").read_text(), "keep")

    def test_deleted_but_indexed_docs_still_gets_narrow_rule(self):
        self.init_git()
        docs = self.root / "docs"
        docs.mkdir()
        (docs / "indexed.md").write_text("preserve in index", encoding="utf-8")
        self.git("add", "docs/indexed.md")
        (docs / "indexed.md").unlink()
        docs.rmdir()
        store.start(self.root, "Roster")
        self.assertEqual((self.root / ".gitignore").read_bytes(), b"/docs/roster-implementation/\n")
        self.assertIn("docs/indexed.md", self.git("ls-files"))

    def test_ignore_exception_gets_effective_final_rule(self):
        self.init_git()
        (self.root / "docs").mkdir()
        original = b"/docs/*\n!/docs/hiring-implementation/\n"
        (self.root / ".gitignore").write_bytes(original)
        package = Path(store.start(self.root, "Hiring")["package"])
        self.assertEqual((self.root / ".gitignore").read_bytes(), original + b"/docs/hiring-implementation/\n")
        self.assertEqual(store.inspect(package)["git_exclusion_verified"], True)

    def test_unowned_name_gets_unique_folder_and_tracked_output_is_refused(self):
        self.init_git()
        existing = self.root / "docs" / "hiring-implementation"
        existing.mkdir(parents=True)
        (existing / "existing.txt").write_text("unrelated")
        first = Path(store.start(self.root, "Hiring")["package"])
        self.assertNotEqual(first.parent, existing)
        self.assertEqual((existing / "existing.txt").read_text(), "unrelated")
        self.git("add", "-f", first.parent.relative_to(self.root).as_posix() + "/.implementation-plan.json")
        with self.assertRaisesRegex(ValueError, "tracked"):
            store.start(self.root, "Hiring", previous=first)

    def test_non_git_and_invalid_options(self):
        result = store.start(self.root, "Scheduling", commits="off")
        self.assertFalse(result["git_exclusion_verified"])
        self.assertEqual((self.root / ".gitignore").read_bytes(), b"/docs/\n")
        with self.assertRaisesRegex(ValueError, "positive"):
            store.start(self.root, "Scheduling", max_phases=0)
        with self.assertRaisesRegex(ValueError, "unique"):
            store.start(self.root, "Scheduling", skills="migration,migration")

    def test_missing_files_and_phase_cap_are_reported(self):
        self.init_git()
        package = Path(store.start(self.root, "Offer", max_phases=1)["package"])
        self.assertIn("Missing PLAN.md", store.inspect(package)["errors"])
        self.save_complete(package)
        self.assertEqual(store.inspect(package)["errors"], [])
        data = json.loads((package / ".package.json").read_text())
        data["phases"]["P02"] = "P02_EXTRA.md"
        (package / ".package.json").write_text(json.dumps(data))
        self.assertIn("Phase count exceeds maximum", store.inspect(package)["errors"])

    def test_broken_links_and_skill_assignments_are_reported(self):
        self.init_git()
        package = Path(store.start(self.root, "Offer", skills="migration")["package"])
        self.save_complete(package)
        (package / "PLAN.md").write_text("# Plan\n\n[missing](absent.md)\n", encoding="utf-8")
        self.assertTrue(any("Broken local link" in error for error in store.inspect(package)["errors"]))
        (package / "PLAN.md").write_text("# Plan\n\n[phases](PHASES.md)\n", encoding="utf-8")
        data = json.loads((package / ".package.json").read_text())
        data["skill_assignments"] = {}
        (package / ".package.json").write_text(json.dumps(data))
        self.assertIn("Skill assignments do not match selected skills", store.inspect(package)["errors"])

    def test_read_only_commands_do_not_change_package_and_prompt_requires_ready(self):
        self.init_git()
        package = Path(store.start(self.root, "Hiring")["package"])
        self.save_complete(package)
        before = {path.relative_to(package): path.read_bytes() for path in package.rglob("*") if path.is_file()}
        with redirect_stderr(io.StringIO()):
            self.assertEqual(store.main(["prompt", "--package", str(package), "--phase", "P01"]), 1)
        data = json.loads((package / ".package.json").read_text())
        data["status"] = "ready"
        (package / ".package.json").write_text(json.dumps(data), encoding="utf-8")
        before = {path.relative_to(package): path.read_bytes() for path in package.rglob("*") if path.is_file()}
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(store.main(["check", "--package", str(package)]), 0)
            self.assertEqual(store.main(["status", "--package", str(package)]), 0)
            self.assertEqual(store.main(["skills", "--package", str(package)]), 0)
            self.assertEqual(store.main(["prompt", "--package", str(package), "--phase", "P01"]), 0)
            self.assertEqual(store.main(["list", "--project", str(self.root)]), 0)
        self.assertIn("Implement P01 only.", output.getvalue())
        self.assertIn(package.name, output.getvalue())
        after = {path.relative_to(package): path.read_bytes() for path in package.rglob("*") if path.is_file()}
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
