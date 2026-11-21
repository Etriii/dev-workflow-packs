"""Git-scope and baseline regression tests for change-report."""

import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "packs/developer-skills/skills/change-report/scripts/change_report.py"


class ChangeReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="change report test ")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / "state"
        self.repo = self.make_repo("Application with spaces")

    def make_repo(self, name):
        repo = self.base / name
        repo.mkdir()
        self.git(repo, "init", "-q")
        self.git(repo, "config", "user.name", "Tester")
        self.git(repo, "config", "user.email", "tester@example.test")
        return repo

    def git(self, repo, *args):
        result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
        if result.returncode:
            raise AssertionError(result.stderr.decode(errors="replace"))
        return result.stdout.decode().strip()

    def write(self, repo, name, text):
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self, repo, message="save"):
        self.git(repo, "add", "-A")
        self.git(repo, "commit", "-qm", message)
        return self.git(repo, "rev-parse", "HEAD")

    def run_helper(self, *args, repo=None, ok=True):
        env = {**os.environ, "CHANGE_REPORT_HOME": str(self.home)}
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), *args], cwd=repo or self.repo, env=env,
                                capture_output=True, text=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        return result.stderr

    def test_clean_auto_latest_initial_and_first_parent_merge(self):
        self.write(self.repo, "main.txt", "one\n")
        first = self.commit(self.repo)
        row = self.run_helper()["repositories"][0]
        self.assertEqual(row["scope"], "latest")
        self.assertIsNone(row["from"])
        self.assertEqual(row["changes"][0]["new_lines"], ["1–1"])
        self.git(self.repo, "branch", "side")
        self.write(self.repo, "main.txt", "one\ntwo\n")
        second = self.commit(self.repo)
        self.git(self.repo, "switch", "-q", "side")
        self.write(self.repo, "side.txt", "side\n")
        self.commit(self.repo)
        self.git(self.repo, "switch", "-q", "-")
        self.git(self.repo, "merge", "--no-ff", "-qm", "merge", "side")
        row = self.run_helper("--scope", "latest")["repositories"][0]
        self.assertEqual(row["from"], second)
        self.assertEqual([change["path"] for change in row["changes"]], ["side.txt"])
        self.assertNotEqual(first, second)

    def test_working_staged_unstaged_untracked_and_no_mutation(self):
        self.write(self.repo, ".gitignore", "ignored.txt\n")
        self.write(self.repo, "a.txt", "a\n")
        self.write(self.repo, "delete.txt", "old\n")
        self.commit(self.repo)
        self.write(self.repo, "a.txt", "b\n")
        self.git(self.repo, "add", "a.txt")
        self.write(self.repo, "a.txt", "c\n")
        (self.repo / "delete.txt").unlink()
        self.write(self.repo, "new file ü.txt", "new\n")
        self.write(self.repo, "ignored.txt", "ignore\n")
        self.write(self.repo, ".env", "PASSWORD=secret\n")
        before_index = self.git(self.repo, "ls-files", "-s")
        before_status = self.git(self.repo, "status", "--porcelain")
        rows = self.run_helper("--scope", "working")["repositories"][0]["changes"]
        self.assertEqual({row["path"] for row in rows}, {"a.txt", "delete.txt", "new file ü.txt"})
        changed = next(row for row in rows if row["path"] == "a.txt")
        deleted = next(row for row in rows if row["path"] == "delete.txt")
        self.assertEqual(changed["new_lines"], ["1–1"])
        self.assertEqual(deleted["old_lines"], ["1–1 old"])
        self.assertEqual(self.git(self.repo, "ls-files", "-s"), before_index)
        self.assertEqual(self.git(self.repo, "status", "--porcelain"), before_status)

    def test_dirty_start_separates_prior_work_and_new_commits(self):
        self.write(self.repo, "flow.txt", "base\n")
        self.commit(self.repo)
        self.write(self.repo, "flow.txt", "prior\n")
        self.write(self.repo, "old untracked.txt", "prior\n")
        before = self.git(self.repo, "status", "--porcelain")
        started = self.run_helper("start", "--context", "task-1")
        stored = (self.home / "runs" / f"{started['token']}.json").read_text(encoding="utf-8")
        self.assertNotIn("prior", stored)
        self.assertEqual(self.git(self.repo, "status", "--porcelain"), before)
        self.write(self.repo, "flow.txt", "prior\nnew\n")
        self.write(self.repo, "new.txt", "new\n")
        self.commit(self.repo)
        row = self.run_helper("--scope", "session", "--token", started["token"], "--context", "task-1")["repositories"][0]
        self.assertEqual({item["path"] for item in row["changes"]}, {"flow.txt", "new.txt"})
        self.assertEqual(next(item for item in row["changes"] if item["path"] == "flow.txt")["new_lines"], ["2–2"])
        self.assertEqual(self.run_helper("--token", started["token"], "--context", "task-1")["scope"], "session")
        self.assertIn("does not match", self.run_helper("--scope", "session", "--token", started["token"], "--context", "other", ok=False))
        self.assertIn("baseline unavailable", self.run_helper("--scope", "session", "--context", "task-1", ok=False))

    def test_preexisting_staged_content_is_not_attributed_when_committed_later(self):
        self.write(self.repo, "staged.txt", "base\n")
        self.commit(self.repo)
        self.write(self.repo, "staged.txt", "already staged\n")
        self.git(self.repo, "add", "staged.txt")
        self.write(self.repo, "staged.txt", "base\n")
        started = self.run_helper("start", "--context", "staged-task")
        baseline = json.loads((self.home / "runs" / f"{started['token']}.json").read_text(encoding="utf-8"))
        self.assertIn("staged.txt", baseline["repositories"][self.repo.name]["staged"])
        self.assertEqual(baseline["repositories"][self.repo.name]["staged"]["staged.txt"]["digest"],
                         hashlib.sha256(b"already staged\n").hexdigest())
        self.write(self.repo, "staged.txt", "already staged\n")
        self.git(self.repo, "commit", "-qm", "commit preexisting staged work")
        row = self.run_helper("--scope", "session", "--token", started["token"], "--context", "staged-task")
        self.assertEqual(row["repositories"][0]["changes"], [])
        self.assertTrue(row["empty"])

    def test_direct_revisions_working_renames_deletions_and_empty(self):
        self.write(self.repo, "old.txt", "alpha\nbeta\n")
        self.write(self.repo, "remove.txt", "gone\n")
        first = self.commit(self.repo)
        self.git(self.repo, "mv", "old.txt", "renamed.txt")
        self.write(self.repo, "renamed.txt", "alpha\nbeta\ngamma\n")
        (self.repo / "remove.txt").unlink()
        self.write(self.repo, "added.txt", "new\n")
        second = self.commit(self.repo)
        rows = self.run_helper("--from", first, "--to", second)["repositories"][0]["changes"]
        self.assertEqual({row["status"] for row in rows}, {"Added", "Deleted", "Renamed"})
        rename = next(row for row in rows if row["status"] == "Renamed")
        self.assertEqual((rename["old_path"], rename["path"], rename["new_lines"]), ("old.txt", "renamed.txt", ["3–3"]))
        self.write(self.repo, "added.txt", "new\nmore\n")
        row = self.run_helper("--from", first, "--to", "working")["repositories"][0]
        self.assertTrue(row["working"])
        self.assertEqual(next(item for item in row["changes"] if item["path"] == "added.txt")["new_lines"], ["1–2"])
        self.assertTrue(self.run_helper("--from", first, "--to", first)["empty"])
        self.assertIn("Invalid revision", self.run_helper("--from", "not-a-revision", ok=False))
        self.assertIn("requires --from", self.run_helper("--to", "working", ok=False))

    def test_multiple_histories_external_path_unavailable_and_dedup(self):
        external = self.make_repo("Outside shared folder")
        self.write(self.repo, "front.txt", "front\n")
        self.write(external, "back.txt", "back\n")
        self.commit(self.repo)
        self.commit(external)
        self.run_helper("project", "set", "--project", "product", f"frontend={self.repo}", f"backend={external}", f"duplicate={self.repo}")
        report = self.run_helper("--project", "product", "--scope", "latest")
        self.assertEqual(len(report["repositories"]), 2)
        self.assertEqual({row["name"] for row in report["repositories"]}, {"frontend", "backend"})
        self.assertEqual(len(self.run_helper("--all", "--scope", "latest")["repositories"]), 2)
        front = self.git(self.repo, "rev-parse", "HEAD")
        back = self.git(external, "rev-parse", "HEAD")
        report = self.run_helper("--project", "product", "--repo-from", f"frontend={front}",
                                 "--repo-from", f"backend={back}")
        self.assertTrue(report["empty"])
        self.assertIn("must match", self.run_helper("--project", "product", "--repo-from", "wrong=HEAD", ok=False))
        self.assertIn("conflicts", self.run_helper("--all", "--project", "product", ok=False))
        external.rename(self.base / "moved")
        self.assertIn("selection incomplete", self.run_helper("--project", "product", ok=False))

    def test_no_commits_working_and_secret_snapshot_limit(self):
        self.assertIn("No commits", self.run_helper("--scope", "latest", ok=False))
        self.write(self.repo, "a.txt", "plain\n")
        self.assertEqual(self.run_helper("--scope", "working")["repositories"][0]["changes"][0]["status"], "Added")
        self.write(self.repo, "safe-name.txt", "PASSWORD=secret\n")
        started = self.run_helper("start", "--context", "secret-case")
        self.assertEqual(started["limitations"][self.repo.name], ["safe-name.txt"])
        self.write(self.repo, "safe-name.txt", "PASSWORD=secret2\n")
        row = self.run_helper("--scope", "session", "--token", started["token"], "--context", "secret-case")["repositories"][0]
        self.assertEqual(row["limitations"], ["safe-name.txt"])
        self.assertNotIn("safe-name.txt", {item["path"] for item in row["changes"]})

    def test_default_state_is_in_git_metadata_and_nongit_directory_fails(self):
        self.write(self.repo, "a.txt", "a\n")
        env = {key: value for key, value in os.environ.items() if key != "CHANGE_REPORT_HOME"}
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "start", "--context", "local-run"],
                                cwd=self.repo, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        token = json.loads(result.stdout)["token"]
        self.assertTrue((self.repo / ".git" / "change-report" / "runs" / f"{token}.json").exists())
        self.assertEqual(self.git(self.repo, "status", "--porcelain"), "?? a.txt")
        result = subprocess.run([sys.executable, "-B", str(SCRIPT)], cwd=self.base, env=env,
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not a git repository", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
