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
        if not (package / store.ORIGINAL_PLAN).exists():
            (package / store.ORIGINAL_PLAN).write_text("# Session plan\n", encoding="utf-8")
        (package / "prompts" / "P01_BUILD.md").write_text("Implement P01 only.\n", encoding="utf-8")
        metadata = json.loads((package / ".package.json").read_text(encoding="utf-8"))
        metadata["phases"] = {"P01": "P01_BUILD.md"}
        metadata["skill_assignments"] = {
            name: {"phases": ["P01"], "reason": "Relevant to the selected phase"}
            for name in metadata["skills"]
        }
        (package / ".package.json").write_text(json.dumps(metadata), encoding="utf-8")

    def test_new_store_is_ignored_and_revisions_preserve_history(self):
        self.init_git()
        first = store.start(self.root, "Hiring and Workforce", 3, "caveman,ultimate-ui-ux")
        package = Path(first["package"])
        self.assertEqual(package.parent.parent.name, store.OUTPUT)
        self.assertFalse((self.root / "docs").exists())
        self.assertEqual((self.root / ".gitignore").read_bytes(), b"/.implementation-plans/\n")
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
        self.assertEqual((self.root / ".gitignore").read_bytes(), b"/.implementation-plans/\n")

    def test_existing_tracked_docs_are_untouched(self):
        self.init_git()
        docs = self.root / "docs"
        docs.mkdir()
        (docs / "existing.md").write_text("keep\n", encoding="utf-8")
        self.git("add", "docs/existing.md")
        before = (docs / "existing.md").read_bytes()
        result = store.start(docs, "Hiring")
        self.assertEqual((self.root / ".gitignore").read_bytes(), b"/.implementation-plans/\n")
        self.assertEqual((docs / "existing.md").read_bytes(), before)
        self.assertIn("docs/existing.md", self.git("ls-files"))
        self.assertTrue(result["git_exclusion_verified"])

    def test_file_plan_is_copied_exactly_and_checked(self):
        self.init_git()
        source = self.root / "codex-plan.md"
        original = b"# Plan\r\n\r\n[External note](../note.md)\r\n"
        source.write_bytes(original)
        package = Path(store.start(self.root, "Hiring", source_plan=source)["package"])
        self.assertEqual((package / store.ORIGINAL_PLAN).read_bytes(), original)
        self.save_complete(package)
        self.assertEqual(store.inspect(package)["errors"], [])
        revised = Path(store.start(self.root, "Ignored title", previous=package)["package"])
        self.assertEqual((revised / store.ORIGINAL_PLAN).read_bytes(), original)
        self.save_complete(revised)
        self.assertEqual(store.inspect(revised)["errors"], [])
        (package / store.ORIGINAL_PLAN).write_text("# Changed\n", encoding="utf-8")
        self.assertIn("Original plan differs from its source snapshot", store.inspect(package)["errors"])
        with self.assertRaisesRegex(ValueError, "Previous original plan differs"):
            store.start(self.root, "Ignored title", previous=package)

    def test_cli_accepts_source_plan_and_requires_session_plan(self):
        self.init_git()
        source = self.root / "claude-plan.md"
        source.write_text("# Source plan\n", encoding="utf-8")
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(store.main(["start", "--project", str(self.root),
                                         "--feature", "Hiring", "--source-plan", str(source)]), 0)
        package = Path(json.loads(output.getvalue())["package"])
        self.assertEqual((package / store.ORIGINAL_PLAN).read_bytes(), source.read_bytes())
        session = Path(store.start(self.root, "Scheduling")["package"])
        self.assertIn("Missing ORIGINAL_PLAN.md", store.inspect(session)["errors"])

    def test_invalid_source_plan_does_not_create_output(self):
        self.init_git()
        source = self.root / "bad-plan.md"
        source.write_bytes(b"\xff\xfe")
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            store.start(self.root, "Hiring", source_plan=source)
        self.assertFalse((self.root / store.OUTPUT).exists())
        self.assertFalse((self.root / ".gitignore").exists())

    def test_pdf_requirements_are_preserved_with_a_session_plan(self):
        self.init_git()
        source = self.root / "programmer-instructions.pdf"
        original = b"%PDF-1.4\nsource requirements\n%%EOF\n"
        source.write_bytes(original)
        package = Path(store.start(self.root, "System Fixes", source_document=source)["package"])
        self.assertEqual((package / store.SOURCE_DOCUMENT).read_bytes(), original)
        self.assertIn("Missing ORIGINAL_PLAN.md", store.inspect(package)["errors"])
        self.save_complete(package)
        self.assertEqual(store.inspect(package)["errors"], [])
        revised = Path(store.start(self.root, "Ignored title", previous=package)["package"])
        self.assertEqual((revised / store.SOURCE_DOCUMENT).read_bytes(), original)
        self.assertEqual((revised / store.ORIGINAL_PLAN).read_bytes(),
                         (package / store.ORIGINAL_PLAN).read_bytes())
        (package / store.SOURCE_DOCUMENT).write_bytes(b"%PDF-1.4\nchanged\n")
        self.assertIn("Source PDF differs from its snapshot", store.inspect(package)["errors"])
        with self.assertRaisesRegex(ValueError, "Previous source PDF differs"):
            store.start(self.root, "Ignored title", previous=package)

    def test_invalid_pdf_or_conflicting_sources_do_not_create_output(self):
        self.init_git()
        source = self.root / "instructions.pdf"
        source.write_bytes(b"not a PDF")
        with self.assertRaisesRegex(ValueError, "not a PDF"):
            store.start(self.root, "System Fixes", source_document=source)
        with self.assertRaisesRegex(ValueError, "Choose one source"):
            store.start(self.root, "System Fixes", source_plan=source,
                        source_document=source)
        self.assertFalse((self.root / store.OUTPUT).exists())
        self.assertFalse((self.root / ".gitignore").exists())

    def test_cli_accepts_pdf_source(self):
        source = self.root / "instructions.pdf"
        source.write_bytes(b"%PDF-1.4\n%%EOF\n")
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(store.main(["start", "--project", str(self.root),
                                         "--feature", "System Fixes", "--source-document",
                                         str(source)]), 0)
        package = Path(json.loads(output.getvalue())["package"])
        self.assertEqual((package / store.SOURCE_DOCUMENT).read_bytes(), source.read_bytes())

    def test_legacy_package_remains_readable_without_original_plan(self):
        package = Path(store.start(self.root, "Hiring")["package"])
        self.save_complete(package)
        (package / store.ORIGINAL_PLAN).unlink()
        data = json.loads((package / ".package.json").read_text(encoding="utf-8"))
        data["schema_version"] = 1
        data.pop("source_plan")
        (package / ".package.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(store.inspect(package)["errors"], [])

    def test_existing_untracked_docs_preserves_existing_ignore_bytes(self):
        self.init_git()
        (self.root / "docs").mkdir()
        (self.root / "docs" / "personal.md").write_text("keep", encoding="utf-8")
        original = b"# Existing\r\n/cache/\r\n"
        (self.root / ".gitignore").write_bytes(original)
        store.start(self.root, "Roster")
        self.assertEqual((self.root / ".gitignore").read_bytes(), original + b"/.implementation-plans/\r\n")
        self.assertEqual((self.root / "docs" / "personal.md").read_text(), "keep")

    def test_deleted_but_indexed_docs_are_untouched(self):
        self.init_git()
        docs = self.root / "docs"
        docs.mkdir()
        (docs / "indexed.md").write_text("preserve in index", encoding="utf-8")
        self.git("add", "docs/indexed.md")
        (docs / "indexed.md").unlink()
        docs.rmdir()
        store.start(self.root, "Roster")
        self.assertEqual((self.root / ".gitignore").read_bytes(), b"/.implementation-plans/\n")
        self.assertFalse(docs.exists())
        self.assertIn("docs/indexed.md", self.git("ls-files"))

    def test_ignore_exception_gets_effective_final_rule(self):
        self.init_git()
        (self.root / store.OUTPUT).mkdir()
        original = b"/.implementation-plans/*\n!/.implementation-plans/hiring-implementation/\n"
        (self.root / ".gitignore").write_bytes(original)
        package = Path(store.start(self.root, "Hiring")["package"])
        self.assertEqual((self.root / ".gitignore").read_bytes(), original + b"/.implementation-plans/\n")
        self.assertEqual(store.inspect(package)["git_exclusion_verified"], True)

    def test_unowned_name_gets_unique_folder_and_tracked_output_is_refused(self):
        self.init_git()
        store.start(self.root, "Roster")
        existing = self.root / store.OUTPUT / "hiring-implementation"
        existing.mkdir(parents=True)
        (existing / "existing.txt").write_text("unrelated")
        first = Path(store.start(self.root, "Hiring")["package"])
        self.assertNotEqual(first.parent, existing)
        self.assertEqual((existing / "existing.txt").read_text(), "unrelated")
        self.git("add", "-f", first.parent.relative_to(self.root).as_posix() + "/.implementation-plan.json")
        with self.assertRaisesRegex(ValueError, "tracked"):
            store.start(self.root, "Hiring", previous=first)

    def test_unowned_store_is_refused_before_ignore_changes(self):
        self.init_git()
        output = self.root / store.OUTPUT
        output.mkdir()
        (output / "unrelated.txt").write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "ownership marker"):
            store.start(self.root, "Hiring")
        self.assertFalse((self.root / ".gitignore").exists())
        self.assertEqual((output / "unrelated.txt").read_text(), "keep")

    def test_legacy_docs_package_can_be_read_and_revised_in_new_store(self):
        self.init_git()
        current = Path(store.start(self.root, "Hiring")["package"])
        legacy = self.root / "docs" / "hiring-implementation" / current.name
        legacy.mkdir(parents=True)
        (legacy.parent / ".implementation-plan.json").write_text(
            json.dumps(store.STORE_MARKER), encoding="utf-8"
        )
        (legacy / ".package.json").write_bytes((current / ".package.json").read_bytes())
        with (self.root / ".gitignore").open("ab") as stream:
            stream.write(b"/docs/hiring-implementation/\n")
        self.assertEqual(store.locate(legacy)[2], legacy)
        self.assertIn(str(legacy), [item["package"] for item in store.list_packages(self.root)])
        revised = Path(store.start(self.root, "Ignored title", previous=legacy)["package"])
        self.assertEqual(revised.parent.parent.name, store.OUTPUT)
        self.assertEqual(json.loads((revised / ".package.json").read_text())["previous"], str(legacy))
        self.assertTrue((legacy / ".package.json").exists())

    def test_non_git_and_invalid_options(self):
        result = store.start(self.root, "Scheduling", commits="off")
        self.assertFalse(result["git_exclusion_verified"])
        self.assertEqual((self.root / ".gitignore").read_bytes(), b"/.implementation-plans/\n")
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

    def test_selected_phase_count_is_exact_and_respects_cap(self):
        self.init_git()
        package = Path(store.start(self.root, "Offer", max_phases=3, phase_count=2)["package"])
        self.save_complete(package)
        self.assertIn("Phase count differs from selected count", store.inspect(package)["errors"])
        (package / "prompts" / "P02_VERIFY.md").write_text("Verify P02 only.\n", encoding="utf-8")
        data = json.loads((package / ".package.json").read_text(encoding="utf-8"))
        data["phases"]["P02"] = "P02_VERIFY.md"
        (package / ".package.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(store.inspect(package)["errors"], [])
        with self.assertRaisesRegex(ValueError, "within --max-phases"):
            store.start(self.root, "Offer", max_phases=1, phase_count=2)

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
