"""Exit codes, atomic writes, and the two files that must never be committed.

The rule under test that is easy to lose: a run that cannot resolve a workspace
writes nothing at all. A dashboard that leaves a half-written page behind after
failing is worse than one that fails, because the half-written page is the one
the founder opens.
"""
import contextlib
import csv
import importlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "founder-os"
DASHBOARD = PLUGIN_ROOT / "scripts" / "dashboard"
EXAMPLE = REPO_ROOT / "examples" / "studio-north"


def load_main():
    if "fos_dashboard" not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            "fos_dashboard", DASHBOARD / "__init__.py",
            submodule_search_locations=[str(DASHBOARD)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["fos_dashboard"] = package
        spec.loader.exec_module(package)
    return importlib.import_module("fos_dashboard.__main__")


class TestCli(unittest.TestCase):
    def setUp(self):
        self.main = load_main()
        self.workspace = Path(tempfile.mkdtemp()) / "founder-os"
        shutil.copytree(EXAMPLE, self.workspace)

    def _run(self, *args):
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.main.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_json_prints_facts_and_writes_nothing(self):
        code, out, _ = self._run(
            "--home", str(self.workspace), "--now", "2026-07-20", "--json")
        self.assertEqual(code, self.main.EXIT_OK)
        payload = json.loads(out)
        self.assertEqual(payload["today"], "2026-07-20")
        self.assertFalse((self.workspace / "_dashboard").exists())

    def test_a_normal_run_writes_only_inside_dashboard(self):
        before = sorted(p.name for p in self.workspace.iterdir())
        code, _, _ = self._run("--home", str(self.workspace), "--now", "2026-07-20")
        self.assertEqual(code, self.main.EXIT_OK)
        after = sorted(p.name for p in self.workspace.iterdir())
        self.assertEqual(set(after) - set(before), {"_dashboard"})
        self.assertTrue((self.workspace / "_dashboard" / "facts.json").exists())
        self.assertTrue((self.workspace / "_dashboard" / "snapshots.csv").exists())

    def test_gitignore_protects_the_two_regenerable_files_only(self):
        self._run("--home", str(self.workspace), "--now", "2026-07-20")
        text = (self.workspace / "_dashboard" / ".gitignore").read_text(
            encoding="utf-8")
        self.assertIn("index.html", text)
        self.assertIn("facts.json", text)
        self.assertNotIn("snapshots.csv", text)

    def test_running_twice_on_one_day_keeps_one_snapshot_row(self):
        self._run("--home", str(self.workspace), "--now", "2026-07-20")
        self._run("--home", str(self.workspace), "--now", "2026-07-20")
        path = self.workspace / "_dashboard" / "snapshots.csv"
        rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
        self.assertEqual(len(rows), 1)

    def test_unresolvable_workspace_exits_two_and_writes_nothing(self):
        empty = Path(tempfile.mkdtemp()) / "nowhere"
        code, _, err = self._run("--home", str(empty), "--now", "2026-07-20")
        self.assertEqual(code, self.main.EXIT_UNRESOLVED)
        self.assertIn("founder-os-init", err)
        self.assertFalse(empty.exists())

    def test_non_iso_now_is_refused(self):
        code, _, err = self._run(
            "--home", str(self.workspace), "--now", "20 July 2026")
        self.assertEqual(code, self.main.EXIT_UNRESOLVED)
        self.assertIn("YYYY-MM-DD", err)

    def test_unreadable_file_still_produces_a_page_and_exit_zero(self):
        (self.workspace / "metrics.md").write_bytes(b"\xff\xfe\x00")
        code, _, _ = self._run("--home", str(self.workspace), "--now", "2026-07-20")
        self.assertEqual(code, self.main.EXIT_OK)
        payload = json.loads(
            (self.workspace / "_dashboard" / "facts.json").read_text(
                encoding="utf-8"))
        checks = [item["check"] for item in payload["integrity"]]
        self.assertIn("file-unreadable", checks)


class TestPage(unittest.TestCase):
    def setUp(self):
        self.main = load_main()
        self.workspace = Path(tempfile.mkdtemp()) / "founder-os"
        shutil.copytree(EXAMPLE, self.workspace)

    def _run(self, *args):
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.main.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_a_normal_run_writes_the_page(self):
        self._run("--home", str(self.workspace), "--now", "2026-07-20")
        page = self.workspace / "_dashboard" / "index.html"
        self.assertTrue(page.exists())
        self.assertIn("Studio North", page.read_text(encoding="utf-8"))

    def test_out_overrides_the_destination(self):
        target = Path(tempfile.mkdtemp()) / "elsewhere" / "page.html"
        self._run("--home", str(self.workspace), "--now", "2026-07-20",
                  "--out", str(target))
        self.assertTrue(target.exists())


class TestRunnableAsACommand(unittest.TestCase):
    """`python3 <plugin>/scripts/dashboard` is the interface the skill documents.

    Run that way the package directory is the entry point, not an import, so
    `__main__` has no parent and every relative import in it would raise. The
    unit tests above import the module and would never see it.
    """

    def test_the_package_directory_runs_as_a_command(self):
        workspace = Path(tempfile.mkdtemp()) / "founder-os"
        shutil.copytree(EXAMPLE, workspace)
        result = subprocess.run(
            [sys.executable, str(DASHBOARD),
             "--home", str(workspace), "--now", "2026-07-20"],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("index.html", result.stdout)
        self.assertTrue((workspace / "_dashboard" / "facts.json").exists())


class TestPackaging(unittest.TestCase):
    def test_skill_exists_with_frontmatter(self):
        skill = PLUGIN_ROOT / "skills" / "dashboard" / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        self.assertIn("name: dashboard", text)

    def test_skill_declares_no_writes_because_it_owns_nothing(self):
        text = (PLUGIN_ROOT / "skills" / "dashboard" / "SKILL.md").read_text(
            encoding="utf-8")
        self.assertNotIn("writes:", text.split("---")[1])

    def test_skill_is_system_and_standalone(self):
        spec = importlib.util.spec_from_file_location(
            "fos_package", REPO_ROOT / "scripts" / "_package.py")
        package = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(package)
        self.assertIn("dashboard", package.SYSTEM_SKILLS)
        self.assertIn("dashboard", package.STANDALONE_SKILLS)



if __name__ == "__main__":
    unittest.main()
