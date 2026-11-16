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
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "packs/developer-skills/skills/implementation-plan/scripts/package_store.py"
SPEC = spec_from_file_location("implementation_package_store", SCRIPT)
store = module_from_spec(SPEC)
sys.modules[SPEC.name] = store
SPEC.loader.exec_module(store)


class PackageStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="implementation-plan-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / "user-config.json"
        config_patch = patch.object(store, "config_path", return_value=self.config)
        config_patch.start()
        self.addCleanup(config_patch.stop)

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def init_git(self):
        self.git("init", "-q")

    def save_complete(self, package):
        for name in store.SHARED:
            (package / name).write_text(f"# {name}\n", encoding="utf-8")
        (package / "COMMIT_MESSAGES.md").write_text(
            "# Draft messages\n\nRepository: application\n\n```text\n"
            "feat(requests): record approval decisions\n\n"
            "Preserve the final signer's decision so request history remains auditable.\n\n"
            "- Store the signer and decision time with the request.\n"
            "- Verify approval and rejection paths after implementation; NOT_RUN.\n"
            "```\n", encoding="utf-8"
        )
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
        data.pop("test_scope")
        (package / ".package.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(store.inspect(package)["errors"], [])
        self.assertEqual(store.inspect(package)["test_scope"], "focused")

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

    def test_subject_only_commit_drafts_fail_package_check(self):
        package = Path(store.start(self.root, "Requests", commits="off")["package"])
        self.save_complete(package)
        messages = package / "COMMIT_MESSAGES.md"
        messages.write_text(
            "# Draft commit subjects\n\n- P01: feat: add approval history\n",
            encoding="utf-8",
        )
        self.assertTrue(any("subject-only lists" in error for error in store.inspect(package)["errors"]))
        messages.write_text(
            "# Draft messages\n\n```text\nfeat(requests): add approval history\n```\n",
            encoding="utf-8",
        )
        self.assertTrue(any("needs a body" in error for error in store.inspect(package)["errors"]))

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

    def test_test_scope_defaults_to_focused_and_revisions_inherit_or_override(self):
        self.init_git()
        first = Path(store.start(self.root, "Offer")["package"])
        self.save_complete(first)
        self.assertEqual(store.inspect(first)["test_scope"], "focused")
        full = Path(store.start(self.root, "Offer", previous=first,
                                test_scope="full")["package"])
        self.save_complete(full)
        self.assertEqual(store.inspect(full)["test_scope"], "full")
        inherited = Path(store.start(self.root, "Offer", previous=full)["package"])
        self.save_complete(inherited)
        self.assertEqual(store.inspect(inherited)["test_scope"], "full")
        metadata = json.loads((inherited / ".package.json").read_text(encoding="utf-8"))
        metadata["test_scope"] = "everything"
        (inherited / ".package.json").write_text(json.dumps(metadata), encoding="utf-8")
        self.assertIn("Invalid test scope", store.inspect(inherited)["errors"])

    def test_commit_policy_defaults_off_and_auto_survives_revision(self):
        self.init_git()
        default = Path(store.start(self.root, "Offer")["package"])
        self.assertEqual(json.loads((default / ".package.json").read_text())["commits"], "off")
        auto = Path(store.start(self.root, "Offer", previous=default,
                                commits="auto")["package"])
        self.save_complete(auto)
        self.assertEqual(json.loads((auto / ".package.json").read_text())["commits"], "auto")
        self.assertEqual(store.inspect(auto)["errors"], [])
        inherited = Path(store.start(self.root, "Offer", previous=auto)["package"])
        self.assertEqual(json.loads((inherited / ".package.json").read_text())["commits"], "auto")
        disabled = Path(store.start(self.root, "Offer", previous=inherited,
                                    commits="off")["package"])
        self.assertEqual(json.loads((disabled / ".package.json").read_text())["commits"], "off")

    def test_user_config_applies_to_new_packages_without_changing_revisions(self):
        self.init_git()
        config = {
            "schema_version": 1,
            "defaults_at_setup": {"commits": "off", "test_scope": "focused", "skills_mode": "auto"},
            "current": {"commits": "auto", "test_scope": "full", "skills_mode": "all"},
        }
        self.config.write_text(json.dumps(config), encoding="utf-8")
        first = Path(store.start(self.root, "Offer")["package"])
        first_data = json.loads((first / ".package.json").read_text(encoding="utf-8"))
        self.assertEqual((first_data["commits"], first_data["test_scope"], first_data["skills_mode"]),
                         ("auto", "full", "all"))
        config["current"] = {"commits": "off", "test_scope": "focused", "skills_mode": "auto"}
        self.config.write_text(json.dumps(config), encoding="utf-8")
        revised = Path(store.start(self.root, "Offer", previous=first)["package"])
        revised_data = json.loads((revised / ".package.json").read_text(encoding="utf-8"))
        self.assertEqual((revised_data["commits"], revised_data["test_scope"], revised_data["skills_mode"]),
                         ("auto", "full", "all"))
        explicit = Path(store.start(self.root, "Other", commits="scoped", test_scope="full",
                                    skills_mode="all")["package"])
        explicit_data = json.loads((explicit / ".package.json").read_text(encoding="utf-8"))
        self.assertEqual((explicit_data["commits"], explicit_data["test_scope"], explicit_data["skills_mode"]),
                         ("scoped", "full", "all"))
        self.config.write_text("not JSON", encoding="utf-8")
        later_revision = Path(store.start(self.root, "Offer", previous=first)["package"])
        self.assertEqual(json.loads((later_revision / ".package.json").read_text(encoding="utf-8"))["commits"],
                         "auto")

    def test_invalid_user_config_stops_before_package_writes(self):
        self.init_git()
        self.config.write_text('{"schema_version": 1, "current": {"commits": "auto"}}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Invalid implementation-plan config structure"):
            store.start(self.root, "Offer")
        self.assertFalse((self.root / store.OUTPUT).exists())
        self.assertFalse((self.root / ".gitignore").exists())
        self.config.write_text(json.dumps({
            "schema_version": 1,
            "defaults_at_setup": {"commits": "off", "test_scope": "focused", "skills_mode": "auto"},
            "current": {"commits": "invalid", "test_scope": "focused", "skills_mode": "auto"},
        }), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "current.commits"):
            store.start(self.root, "Offer")
        self.assertFalse((self.root / store.OUTPUT).exists())

    def test_config_template_is_in_both_agent_copies(self):
        result = subprocess.run([
            sys.executable, "-B", str(ROOT / "tools/install_skills.py"),
            "--pack", "developer-skills", "--agent", "both", "--project", str(self.root),
            "--skills", "implementation-plan", "--yes",
        ], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        source = SCRIPT.parent.parent / "assets/config.json"
        for agent_dir in (".agents", ".claude"):
            installed = self.root / agent_dir / "skills/implementation-plan/assets/config.json"
            self.assertEqual(installed.read_bytes(), source.read_bytes())

    def test_cli_accepts_auto_commit_policy(self):
        self.init_git()
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(store.main(["start", "--project", str(self.root),
                                         "--feature", "Offer", "--commits", "auto"]), 0)
        package = Path(json.loads(output.getvalue())["package"])
        self.assertEqual(json.loads((package / ".package.json").read_text())["commits"], "auto")

    def test_cli_records_full_test_scope_and_rejects_invalid_value(self):
        self.init_git()
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(store.main(["start", "--project", str(self.root),
                                         "--feature", "Offer", "--test-scope", "full"]), 0)
        package = Path(json.loads(output.getvalue())["package"])
        self.assertEqual(json.loads((package / ".package.json").read_text(encoding="utf-8"))["test_scope"], "full")
        with self.assertRaisesRegex(ValueError, "focused or full"):
            store.start(self.root, "Other", test_scope="everything")
        self.assertFalse((self.root / store.OUTPUT / "other-implementation").exists())

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
