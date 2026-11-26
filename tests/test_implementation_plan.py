"""Exercise implementation package storage in disposable projects."""

from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
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
        """Build a flat schema-3 fixture to keep legacy compatibility exercised."""
        (package / "prompts").mkdir(exist_ok=True)
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
        metadata.update(schema_version=3, profile="detailed", parallel_mode="off")
        metadata["phases"] = {"P01": "P01_BUILD.md"}
        if metadata["schema_version"] >= 3:
            metadata["dependencies"] = {"P01": []}
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

    def test_feature_folders_sort_by_creation_time_and_revisions_keep_their_folder(self):
        with patch.object(store, "datetime") as clock:
            clock.now.return_value = datetime(2026, 11, 20, 6, 37, 18, tzinfo=timezone.utc)
            first = Path(store.start(self.root, "Queue and Operations")["package"])
            clock.now.return_value = datetime(2026, 11, 21, 8, 10, 5, tzinfo=timezone.utc)
            second = Path(store.start(self.root, "Hiring")["package"])
            revision = Path(store.start(self.root, "Ignored title", previous=first)["package"])
        self.assertEqual(first.parent.name, "20261120T063718Z-queue-and-operations")
        self.assertEqual(second.parent.name, "20261121T081005Z-hiring")
        self.assertLess(first.parent.name, second.parent.name)
        self.assertEqual(revision.parent, first.parent)

    def test_existing_feature_folder_name_remains_revisable(self):
        current = Path(store.start(self.root, "Queue and Operations")["package"])
        old_folder = current.parent.with_name("queue-and-operations-implementation")
        current.parent.rename(old_folder)
        old_package = old_folder / current.name
        self.assertEqual(store.locate(old_package)[2], old_package)
        revision = Path(store.start(self.root, "Ignored title", previous=old_package)["package"])
        self.assertEqual(revision.parent, old_folder)
        self.assertTrue(old_package.exists())

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
        self.assertNotIn("Missing ORIGINAL_PLAN.md", store.inspect(session)["errors"])

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
        self.assertNotIn("Missing ORIGINAL_PLAN.md", store.inspect(package)["errors"])
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
        original = b"/.implementation-plans/*\n!/.implementation-plans/20261120T063718Z-hiring/\n"
        (self.root / ".gitignore").write_bytes(original)
        with patch.object(store, "datetime") as clock:
            clock.now.return_value = datetime(2026, 11, 20, 6, 37, 18, tzinfo=timezone.utc)
            package = Path(store.start(self.root, "Hiring")["package"])
        self.assertEqual((self.root / ".gitignore").read_bytes(), original + b"/.implementation-plans/\n")
        self.assertEqual(store.inspect(package)["git_exclusion_verified"], True)

    def test_unowned_name_gets_unique_folder_and_tracked_output_is_refused(self):
        self.init_git()
        store.start(self.root, "Roster")
        existing = self.root / store.OUTPUT / "20261120T063718Z-hiring"
        existing.mkdir(parents=True)
        (existing / "existing.txt").write_text("unrelated")
        with patch.object(store, "datetime") as clock:
            clock.now.return_value = datetime(2026, 11, 20, 6, 37, 18, tzinfo=timezone.utc)
            first = Path(store.start(self.root, "Hiring")["package"])
        self.assertNotEqual(first.parent, existing)
        self.assertTrue(first.parent.name.startswith(existing.name + "-"))
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
        data["dependencies"]["P02"] = ["P01"]
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
            for relative in ("references/balanced-planning.md", "references/execution.md", "references/light-planning.md", "references/parallel-planning.md", "scripts/package_store.py"):
                self.assertEqual((installed.parent.parent / relative).read_bytes(), (SCRIPT.parent.parent / relative).read_bytes())

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

    def save_light(self, package):
        messages = (
            "# Narrow change\n\nScope and acceptance: preserve request history.\n\n"
            "## Commit draft\n\n```text\nfix(requests): preserve history\n\n"
            "Retain existing decisions when updating request details. Checks NOT_RUN.\n```\n\n"
            "## P01\n\nRead this plan, implement only the request-history correction, "
            "run the affected request tests, record results here and stop.\n"
        )
        (package / "PLAN.md").write_text(messages, encoding="utf-8")
        if not (package / store.ORIGINAL_PLAN).exists():
            (package / store.ORIGINAL_PLAN).write_text("# Preserve request history\n", encoding="utf-8")
        metadata = json.loads((package / ".package.json").read_text())
        metadata.update(phases={"P01": "PLAN.md#P01"}, dependencies={"P01": []}, status="ready")
        (package / ".package.json").write_text(json.dumps(metadata), encoding="utf-8")

    def save_parallel(self, package, worktrees=False):
        self.save_complete(package)
        metadata = json.loads((package / ".package.json").read_text())
        metadata.update(
            status="ready", phases={"P01": "P01_BUILD.md", "P02": "P02_BUILD.md", "P03": "P03_VERIFY.md"},
            parallel_mode="worktree" if worktrees else "analysis",
            dependencies={"P01": [], "P02": [], "P03": ["P01", "P02"]},
            parallel_groups={"G01": ["P01", "P02"]},
            parallel_reason="Independent request and reporting owners; integration waits for both.",
            parallel_tasks={},
        )
        for phase in metadata["phases"]:
            (package / "prompts" / metadata["phases"][phase]).write_text(f"Implement {phase} only.\n", encoding="utf-8")
            metadata["parallel_tasks"][phase] = {
                "owned_paths": [f"src/{phase}.py"], "write_resources": [f"test-db:{phase}"],
                "read_set": ["PLAN.md", "CONTRACTS.md"], "reason": f"Own {phase}'s isolated component.",
            }
        if worktrees:
            base = self.git("rev-parse", "HEAD")
            for phase in ("P01", "P02"):
                metadata["parallel_tasks"][phase].update(
                    repository=str(self.root), base_commit=base, branch=f"task/{phase}",
                    worktree=str(self.root.parent / f"{self.root.name}-{phase}"),
                )
            metadata["merges"] = {
                f"M{index:02d}": {"phases": [phase], "owner_phase": "P03", "repository": str(self.root),
                                  "target_branch": self.git("branch", "--show-current"), "target_commit": base,
                                  "depends_on": [] if index == 1 else ["M01"]}
                for index, phase in enumerate(("P01", "P02"), 1)
            }
            (package / store.MERGE_FILE).write_text(
                "# Merge prompts\n\n## M01\n\nIntegrate the request correction; verify and stop.\n\n"
                "```text\n## M99\nThis is a fenced example, not a merge section.\n```\n\n---\n\n"
                "## M02\n\nIntegrate reporting after M01; verify and stop.\n", encoding="utf-8")
        (package / ".package.json").write_text(json.dumps(metadata), encoding="utf-8")
        return metadata

    def initialize_commit(self):
        self.init_git()
        self.git("config", "user.name", "Package Tests")
        self.git("config", "user.email", "package-tests@example.invalid")
        (self.root / "base.txt").write_text("base\n", encoding="utf-8")
        self.git("add", "base.txt")
        self.git("commit", "-qm", "test: establish integration baseline")

    def test_light_package_has_one_document_for_plan_execution_and_tracking(self):
        self.init_git()
        package = Path(store.start(self.root, "Narrow change", profile="light")["package"])
        self.save_light(package)
        self.assertFalse((package / "prompts").exists())
        self.assertEqual(store.inspect(package)["errors"], [])
        before = {p.relative_to(package): p.read_bytes() for p in package.rglob("*") if p.is_file()}
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(store.main(["prompt", "--package", str(package), "--phase", "P01"]), 0)
            self.assertEqual(store.main(["status", "--package", str(package)]), 0)
        self.assertIn("request-history correction", output.getvalue())
        self.assertEqual(before, {p.relative_to(package): p.read_bytes() for p in package.rglob("*") if p.is_file()})

    def test_light_revision_inherits_and_can_expand_without_mutating_original(self):
        first = Path(store.start(self.root, "Narrow change", profile="light", skills="migration")["package"])
        self.save_light(first)
        inherited = Path(store.start(self.root, "Ignored", previous=first)["package"])
        data = json.loads((inherited / ".package.json").read_text())
        self.assertEqual((data["profile"], data["skills"], data["phase_count"]), ("light", ["migration"], 1))
        expanded = Path(store.start(self.root, "Ignored", previous=first, profile="detailed", phase_count=2)["package"])
        self.assertEqual(json.loads((expanded / ".package.json").read_text())["profile"], "detailed")
        self.assertEqual(json.loads((first / ".package.json").read_text())["profile"], "light")

    def test_invalid_modes_stop_before_output_or_ignore_writes(self):
        for options in ({"profile": "light", "parallel_mode": "analysis"},
                        {"profile": "light", "phase_count": 2}, {"parallel_mode": "unknown"},
                        {"parallel_mode": "worktree"}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                store.start(self.root, "Invalid", **options)
            self.assertFalse((self.root / store.OUTPUT).exists())
            self.assertFalse((self.root / ".gitignore").exists())

    def test_older_detailed_schemas_remain_readable_without_rewrite(self):
        package = Path(store.start(self.root, "Legacy")["package"])
        self.save_complete(package)
        metadata = json.loads((package / ".package.json").read_text())
        for schema in (1, 2):
            metadata["schema_version"] = schema
            for name in ("profile", "parallel_mode", "dependencies", "parallel_tasks", "parallel_groups", "merges", "parallel_reason"):
                metadata.pop(name, None)
            (package / ".package.json").write_text(json.dumps(metadata), encoding="utf-8")
            before = (package / ".package.json").read_bytes()
            self.assertEqual(store.inspect(package)["errors"], [])
            self.assertEqual((package / ".package.json").read_bytes(), before)

    def test_parallel_analysis_checks_dependencies_and_shared_owners(self):
        package = Path(store.start(self.root, "Independent work", parallel_mode="analysis")["package"])
        metadata = self.save_parallel(package)
        self.assertEqual(store.inspect(package)["errors"], [])
        invalid = [
            ("dependencies", {"P01": ["P03"], "P02": [], "P03": ["P01"]}, "Cycle"),
            ("dependencies", {"P01": [], "P02": ["P01"], "P03": ["P02"]}, "cannot run together"),
            ("dependencies", {"P01": [], "P02": ["P99"], "P03": []}, "Invalid phase dependencies"),
        ]
        for key, value, error in invalid:
            changed = dict(metadata, **{key: value})
            (package / ".package.json").write_text(json.dumps(changed), encoding="utf-8")
            self.assertTrue(any(error in item for item in store.inspect(package)["errors"]))
        for field, value, error in (("owned_paths", ["src/P01.py"], "Overlapping ownership"),
                                    ("write_resources", ["test-db:P01"], "Shared mutable resource"),
                                    ("read_set", ["missing.md"], "read-set file")):
            changed = json.loads(json.dumps(metadata))
            changed["parallel_tasks"]["P02"][field] = value
            (package / ".package.json").write_text(json.dumps(changed), encoding="utf-8")
            self.assertTrue(any(error in item for item in store.inspect(package)["errors"]))

    def test_parallel_planning_can_record_no_safe_split(self):
        package = Path(store.start(self.root, "Coupled work", parallel_mode="analysis")["package"])
        metadata = self.save_parallel(package)
        metadata["parallel_groups"] = {}
        metadata["parallel_reason"] = "All components share a mutable service; execute sequentially."
        (package / ".package.json").write_text(json.dumps(metadata), encoding="utf-8")
        self.assertEqual(store.inspect(package)["errors"], [])

    def test_repository_and_path_aliases_cannot_hide_overlapping_ownership(self):
        package = Path(store.start(self.root, "Independent work", parallel_mode="analysis")["package"])
        metadata = self.save_parallel(package)
        metadata["parallel_tasks"]["P02"]["repository"] = str(self.root) + "/"
        metadata["parallel_tasks"]["P02"]["owned_paths"] = ["src/./P01.py"]
        (package / ".package.json").write_text(json.dumps(metadata), encoding="utf-8")
        self.assertTrue(any("Overlapping ownership" in item for item in store.inspect(package)["errors"]))

    def test_worktree_plan_and_merge_retrieval_leave_git_untouched(self):
        self.initialize_commit()
        package = Path(store.start(self.root, "Isolated tasks", parallel_mode="worktree")["package"])
        self.save_parallel(package, worktrees=True)
        before = (self.git("status", "--porcelain"), self.git("branch"), self.git("worktree", "list", "--porcelain"))
        contents = {p.relative_to(package): p.read_bytes() for p in package.rglob("*") if p.is_file()}
        self.assertEqual(store.inspect(package)["errors"], [])
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(store.main(["prompt", "--package", str(package), "--phase", "M01"]), 0)
        self.assertIn("request correction", output.getvalue())
        self.assertNotIn("Integrate reporting", output.getvalue())
        self.assertEqual(contents, {p.relative_to(package): p.read_bytes() for p in package.rglob("*") if p.is_file()})
        self.assertEqual(before, (self.git("status", "--porcelain"), self.git("branch"), self.git("worktree", "list", "--porcelain")))
        self.assertEqual([p.name for p in (package / "prompts").glob("MERGE*")], ["MERGE_PROMPTS.md"])

    def test_merge_file_sections_and_dependencies_are_checked(self):
        self.initialize_commit()
        package = Path(store.start(self.root, "Isolated tasks", parallel_mode="worktree")["package"])
        metadata = self.save_parallel(package, worktrees=True)
        path = package / store.MERGE_FILE
        original = path.read_text(encoding="utf-8")
        path.write_text(original.replace("## M02", "## M03"), encoding="utf-8")
        self.assertIn("Merge sections must match merge IDs exactly", store.inspect(package)["errors"])
        path.write_text(original + "\n## M01\nDuplicate\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Duplicate prompt section"):
            store.inspect(package)
        path.write_text(original, encoding="utf-8")
        metadata["merges"]["M01"]["depends_on"] = ["M02"]
        (package / ".package.json").write_text(json.dumps(metadata), encoding="utf-8")
        self.assertIn("Cycle in merge dependencies", store.inspect(package)["errors"])

    def test_worktree_identity_and_merge_coverage_are_checked(self):
        self.initialize_commit()
        package = Path(store.start(self.root, "Isolated tasks", parallel_mode="worktree")["package"])
        metadata = self.save_parallel(package, worktrees=True)
        metadata["parallel_tasks"]["P02"]["worktree"] = metadata["parallel_tasks"]["P01"]["worktree"]
        metadata["merges"]["M02"]["phases"] = ["P01"]
        (package / ".package.json").write_text(json.dumps(metadata), encoding="utf-8")
        errors = store.inspect(package)["errors"]
        self.assertIn("Parallel worktrees and branches must be distinct", errors)
        self.assertIn("Each isolated phase needs exactly one merge operation", errors)

    def test_worktree_baselines_and_merge_owner_prerequisites_are_checked(self):
        self.initialize_commit()
        package = Path(store.start(self.root, "Isolated tasks", parallel_mode="worktree")["package"])
        metadata = self.save_parallel(package, worktrees=True)
        metadata["parallel_tasks"]["P01"]["base_commit"] = "0" * 40
        metadata["merges"]["M01"]["target_commit"] = "0" * 40
        metadata["dependencies"]["P03"] = ["P02"]
        (package / ".package.json").write_text(json.dumps(metadata), encoding="utf-8")
        errors = store.inspect(package)["errors"]
        for message in ("Worktree baseline is not an existing commit: P01",
                        "Merge baseline is not an existing commit: M01",
                        "Merge owner must depend on its source phases: M01"):
            self.assertIn(message, errors)

    def test_multiple_merge_files_and_nested_worktrees_are_rejected(self):
        self.initialize_commit()
        package = Path(store.start(self.root, "Isolated tasks", parallel_mode="worktree")["package"])
        metadata = self.save_parallel(package, worktrees=True)
        metadata["parallel_tasks"]["P02"]["worktree"] = str(Path(metadata["parallel_tasks"]["P01"]["worktree"]) / "nested")
        (package / ".package.json").write_text(json.dumps(metadata), encoding="utf-8")
        (package / "prompts/M01_EXTRA.md").write_text("Duplicate integration file\n", encoding="utf-8")
        errors = store.inspect(package)["errors"]
        self.assertIn("Parallel worktree directories cannot be nested", errors)
        self.assertIn("All merge prompts must use the single MERGE_PROMPTS.md file", errors)

    def test_parallel_revision_inherits_mode_policies_and_can_disable_parallel(self):
        self.initialize_commit()
        package = Path(store.start(self.root, "Isolated tasks", parallel_mode="worktree", skills="migration", max_phases=4, phase_count=3)["package"])
        revised = Path(store.start(self.root, "Ignored", previous=package)["package"])
        data = json.loads((revised / ".package.json").read_text())
        self.assertEqual((data["parallel_mode"], data["skills"], data["max_phases"], data["phase_count"]),
                         ("worktree", ["migration"], 4, 3))
        sequential = Path(store.start(self.root, "Ignored", previous=package, parallel_mode="off")["package"])
        data = json.loads((sequential / ".package.json").read_text())
        self.assertEqual(data["parallel_mode"], "off")
        self.assertEqual(data["merges"], {})

    def test_malformed_counts_and_merge_owner_report_errors_instead_of_crashing(self):
        self.initialize_commit()
        package = Path(store.start(self.root, "Isolated tasks", parallel_mode="worktree")["package"])
        metadata = self.save_parallel(package, worktrees=True)
        metadata["max_phases"] = "three"
        metadata["phase_count"] = []
        metadata["merges"]["M01"]["owner_phase"] = []
        (package / ".package.json").write_text(json.dumps(metadata), encoding="utf-8")
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(store.main(["check", "--package", str(package)]), 1)
        self.assertIn("Invalid maximum phase count", output.getvalue())
        self.assertIn("Invalid merge operation: M01", output.getvalue())

    def test_cli_selects_light_and_parallel_profiles(self):
        for arguments, expected in ((["--profile", "light"], ("light", "off")),
                                    (["--parallel-ready"], ("balanced", "analysis"))):
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(store.main(["start", "--project", str(self.root), "--feature", "Task"] + arguments), 0)
            data = json.loads((Path(json.loads(output.getvalue())["package"]) / ".package.json").read_text())
            self.assertEqual((data["profile"], data["parallel_mode"]), expected)

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

    def save_balanced(self, package, count=1):
        metadata = json.loads((package / ".package.json").read_text(encoding="utf-8"))
        metadata.update(status="ready", phase_count=count,
                        phases={f"P{i:02d}": f"phase-{i:02d}/PROMPT.md" for i in range(1, count + 1)},
                        dependencies={f"P{i:02d}": [] if i == 1 else [f"P{i-1:02d}"]
                                      for i in range(1, count + 1)},
                        parallel_reason="One shared service requires sequential implementation; no safe split.")
        (package / "PLAN.md").write_text("# Scope\n\nKeep saved report data private.\n", encoding="utf-8")
        (package / "STATUS.md").write_text(
            "# Status\n\n## Current\n\n| Task | State | Evidence |\n|---|---|---|\n" +
            "".join(f"| P{i:02d} | NOT_STARTED | NOT_RUN |\n" for i in range(1, count + 1)) +
            "\nNext: implement the first ready task.\n\n## History\n\nARCHIVED_DETAIL\n", encoding="utf-8")
        (package / "DECISIONS.md").write_text("# Decisions\n\nNo execution decisions yet.\n", encoding="utf-8")
        (package / "PROMPTS.md").write_text(
            "# Task index\n\n" + "".join(f"[{task}]({name}): separate session; prerequisites apply; sequential.\n"
                                          for task, name in metadata["phases"].items()), encoding="utf-8")
        for task, name in metadata["phases"].items():
            prompt = package / name
            prompt.parent.mkdir(exist_ok=True)
            prompt.write_text(
                f"# {task} request history\n\nImplement {task} only; keep permissions intact.\n\n"
                "```text\nfeat: preserve request history\n\n"
                "Retain owner-scoped requests before download so users can find pending output.\n\n"
                "Verification: NOT_RUN; run the affected request tests.\n```\n", encoding="utf-8")
        metadata["skill_assignments"] = {
            name: {"phases": list(metadata["phases"]), "reason": "Own the selected task"}
            for name in metadata["skills"]}
        (package / ".package.json").write_text(json.dumps(metadata), encoding="utf-8")
        return metadata

    def test_balanced_default_is_compact_and_does_not_create_output_placeholders(self):
        self.init_git()
        package = Path(store.start(self.root, "Report history", phase_count=1)["package"])
        data = json.loads((package / ".package.json").read_text())
        self.assertEqual((data["schema_version"], data["profile"], data["parallel_mode"], data["commits"]),
                         (4, "balanced", "worktree", "off"))
        self.assertEqual({p.name for p in package.iterdir()}, {".package.json"})
        self.save_balanced(package)
        self.assertEqual(store.inspect(package)["errors"], [])
        self.assertEqual(len([p for p in package.rglob("*") if p.is_file()]), 6)
        self.assertFalse((package / "phase-01/outputs").exists())
        self.assertIn("Implement P01 only", store.stored_prompt(package, data | {"phases": {"P01": "phase-01/PROMPT.md"}}, "P01"))

    def test_detailed_retains_existing_contract_and_non_git_balanced_uses_analysis(self):
        package = Path(store.start(self.root, "Report history")["package"])
        self.assertEqual(json.loads((package / ".package.json").read_text())["parallel_mode"], "analysis")
        detailed = Path(store.start(self.root, "Full plan", profile="detailed")["package"])
        self.assertEqual(json.loads((detailed / ".package.json").read_text())["schema_version"], 3)
        self.assertTrue((detailed / "prompts").is_dir())
        self.assertIn("Missing CONTRACTS.md", store.inspect(detailed)["errors"])

    def test_balanced_status_is_bounded_and_dependency_readiness_is_recorded_only(self):
        package = Path(store.start(self.root, "Report history")["package"])
        metadata = self.save_balanced(package, 2)
        output = io.StringIO()
        before = {p.relative_to(package): p.read_bytes() for p in package.rglob("*") if p.is_file()}
        with redirect_stdout(output):
            self.assertEqual(store.main(["status", "--package", str(package)]), 0)
        result = json.loads(output.getvalue())
        self.assertNotIn("ARCHIVED_DETAIL", output.getvalue())
        self.assertTrue(result["tasks"]["P01"]["can_start_separately"])
        self.assertEqual(result["tasks"]["P02"]["waiting_for"], ["P01"])
        self.assertTrue(result["recorded_only"])
        status = package / "STATUS.md"
        status.write_text(status.read_text().replace("P01 | NOT_STARTED", "P01 | COMPLETE"), encoding="utf-8")
        self.assertTrue(store.status_summary(package, metadata)["tasks"]["P02"]["can_start_separately"])
        status.write_bytes(before[Path("STATUS.md")])
        self.assertEqual(before, {p.relative_to(package): p.read_bytes() for p in package.rglob("*") if p.is_file()})
        self.assertIn("ARCHIVED_DETAIL", store.status_summary(package, metadata, history=True)["history"])

    def test_balanced_bad_paths_and_stale_current_state_are_rejected(self):
        package = Path(store.start(self.root, "Report history")["package"])
        metadata = self.save_balanced(package)
        for name in ("../outside.md", "phase-02/PROMPT.md", "phases/P01-test/PROMPT.md", "phase-01/other.md"):
            changed = metadata | {"phases": {"P01": name}}
            (package / ".package.json").write_text(json.dumps(changed), encoding="utf-8")
            self.assertIn("Invalid phase prompt mapping: P01", store.inspect(package)["errors"])
        (package / ".package.json").write_text(json.dumps(metadata), encoding="utf-8")
        path = package / "STATUS.md"
        body = path.read_text()
        path.write_text(body.replace("NOT_STARTED", "COMPLETE") + "\n", encoding="utf-8")
        self.assertEqual(store.inspect(package)["errors"], [])
        path.write_text(body.replace("| P01 | NOT_STARTED | NOT_RUN |", "| P01 | INVALID | |"), encoding="utf-8")
        self.assertTrue(any("valid state" in e for e in store.inspect(package)["errors"]))
        path.write_text(body.replace("## History", "| P01 | COMPLETE | |\n\n## History"), encoding="utf-8")
        self.assertIn("STATUS.md has duplicate current task states", store.inspect(package)["errors"])

    def test_balanced_revision_inherits_policies_without_rewriting_legacy(self):
        package = Path(store.start(self.root, "Report history", commits="auto", phase_count=1)["package"])
        self.save_balanced(package)
        before = {p.relative_to(package): p.read_bytes() for p in package.rglob("*") if p.is_file()}
        revised = Path(store.start(self.root, "Ignored", previous=package)["package"])
        metadata = json.loads((revised / ".package.json").read_text())
        self.assertEqual((metadata["profile"], metadata["parallel_mode"], metadata["commits"]),
                         ("balanced", "analysis", "auto"))
        self.assertEqual(before, {p.relative_to(package): p.read_bytes() for p in package.rglob("*") if p.is_file()})

    def test_balanced_file_snapshot_is_required_but_chat_plan_is_not_duplicated(self):
        source = self.root / "requirements.md"
        source.write_bytes(b"# Requirements\r\nKeep report ownership.\r\n")
        package = Path(store.start(self.root, "Report history", source_plan=source)["package"])
        self.save_balanced(package)
        self.assertEqual(store.inspect(package)["errors"], [])
        (package / store.ORIGINAL_PLAN).unlink()
        self.assertIn("Missing ORIGINAL_PLAN.md", store.inspect(package)["errors"])
        with self.assertRaisesRegex(ValueError, "Previous original plan is missing"):
            store.start(self.root, "Ignored", previous=package)

    def test_balanced_parallel_workers_wait_for_merged_prerequisites_and_retrieve_one_merge(self):
        self.initialize_commit()
        package = Path(store.start(self.root, "Report outputs", commits="auto")["package"])
        metadata = self.save_balanced(package, 3)
        base = self.git("rev-parse", "HEAD")
        metadata.update(dependencies={"P01": [], "P02": [], "P03": ["P01", "P02"]},
                        parallel_groups={"G01": ["P01", "P02"]},
                        parallel_reason="Independent PDF and workbook owners with isolated test stores.")
        metadata["parallel_tasks"] = {
            task: {"owned_paths": [f"src/{task}.py"], "write_resources": [f"db:{task}"],
                   "read_set": ["PLAN.md", metadata["phases"][task]], "reason": "Separate renderer owner",
                   "repository": str(self.root), "branch": f"task/{task}", "base_commit": base,
                   "worktree": str(self.root.parent / f"{self.root.name}-{task}")}
            for task in ("P01", "P02")}
        metadata["merges"] = {
            "M01": {"phases": ["P01", "P02"], "owner_phase": "P03", "repository": str(self.root),
                    "target_branch": self.git("branch", "--show-current"), "target_commit": base, "depends_on": []}}
        (package / "MERGE_PROMPTS.md").write_text("# Merge rules\n\n## M01\n\nMerge named sources, verify, preserve evidence and clean owned worktrees.\n", encoding="utf-8")
        (package / ".package.json").write_text(json.dumps(metadata), encoding="utf-8")
        before = self.git("worktree", "list", "--porcelain")
        self.assertEqual(store.inspect(package)["errors"], [])
        self.assertIn("clean owned worktrees", store.stored_prompt(package, metadata, "M01"))
        status = package / "STATUS.md"
        status.write_text(status.read_text().replace("P01 | NOT_STARTED", "P01 | COMPLETE")
                          .replace("P02 | NOT_STARTED", "P02 | MERGED"), encoding="utf-8")
        self.assertEqual(store.status_summary(package, metadata)["tasks"]["P03"]["waiting_for"], ["P01"])
        status.write_text(status.read_text().replace("P01 | COMPLETE", "P01 | MERGED"), encoding="utf-8")
        self.assertTrue(store.status_summary(package, metadata)["tasks"]["P03"]["can_start_separately"])
        self.assertEqual(self.git("worktree", "list", "--porcelain"), before)

    def test_status_summary_ignores_fenced_heading_examples(self):
        body = "## Current\n\nNext step.\n```text\n## History\nexample\n```\nStill current.\n## History\nold logs\n"
        self.assertIn("Still current", store.markdown_section(body, "Current"))
        self.assertNotIn("old logs", store.markdown_section(body, "Current"))


if __name__ == "__main__":
    unittest.main()
