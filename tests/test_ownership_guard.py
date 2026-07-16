"""Tests for founder-os/hooks/ownership-guard.py.

The guard lives at a dashed path no import statement reaches, so it is loaded
by file location. Loading it does not run main(): the module guards on
__name__ == "__main__" and only reads stdin there.
"""
import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

GUARD_PATH = (Path(__file__).resolve().parents[1]
              / "founder-os" / "hooks" / "ownership-guard.py")

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "founder-os"


def run_hook(payload):
    """Run the guard as the hook runtime does: JSON on stdin, deny on stdout."""
    env = {**os.environ,
           "FOUNDER_OS_HOME": str(PLUGIN_ROOT),
           "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)}
    return subprocess.run([sys.executable, str(GUARD_PATH)],
                          input=json.dumps(payload), capture_output=True,
                          text=True, env=env, cwd=str(REPO_ROOT))


def load_guard():
    spec = importlib.util.spec_from_file_location("ownership_guard", GUARD_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestOwnerOfCasefold(unittest.TestCase):
    BY_PATH = {
        "goals.md": "strategist",
        "drafts/outreach/": "pipeline-coach",
        "drafts/": "nobody-broader",   # longest match must still win
    }

    def setUp(self):
        self.guard = load_guard()

    def test_exact_match_still_works(self):
        self.assertEqual(self.guard.owner_of("goals.md", self.BY_PATH),
                         "strategist")

    def test_file_case_variant_is_the_same_file(self):
        self.assertEqual(self.guard.owner_of("Goals.md", self.BY_PATH),
                         "strategist")
        self.assertEqual(self.guard.owner_of("GOALS.MD", self.BY_PATH),
                         "strategist")

    def test_directory_case_variant_is_the_same_directory(self):
        self.assertEqual(
            self.guard.owner_of("Drafts/Outreach/2026-07-16-anna.md",
                                self.BY_PATH),
            "pipeline-coach")

    def test_longest_match_survives_casefold(self):
        self.assertEqual(
            self.guard.owner_of("DRAFTS/OUTREACH/x.md", self.BY_PATH),
            "pipeline-coach")

    def test_uncovered_path_still_returns_none(self):
        self.assertIsNone(self.guard.owner_of("scratch.md", self.BY_PATH))


class TestHookIntegration(unittest.TestCase):
    def test_notebookedit_by_wrong_agent_is_denied(self):
        p = run_hook({"agent_type": "pipeline-coach",
                      "tool_name": "NotebookEdit",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {
                          "notebook_path": str(PLUGIN_ROOT / "goals.md")}})
        self.assertIn("deny", p.stdout)
        self.assertIn("strategist", p.stdout)

    def test_write_case_bypass_is_denied(self):
        p = run_hook({"agent_type": "pipeline-coach",
                      "tool_name": "Write",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {
                          "file_path": str(PLUGIN_ROOT / "Goals.md")}})
        self.assertIn("deny", p.stdout)
        self.assertIn("strategist", p.stdout)

    def test_main_thread_is_always_allowed(self):
        p = run_hook({"tool_name": "NotebookEdit",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {
                          "notebook_path": str(PLUGIN_ROOT / "goals.md")}})
        self.assertEqual(p.stdout.strip(), "")
        self.assertEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()
