"""Tests for founder-os/hooks/ownership-guard.py.

The guard lives at a dashed path no import statement reaches, so it is loaded
by file location. Loading it does not run main(): the module guards on
__name__ == "__main__" and only reads stdin there.
"""
import importlib.util
import unittest
from pathlib import Path

GUARD_PATH = (Path(__file__).resolve().parents[1]
              / "founder-os" / "hooks" / "ownership-guard.py")


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


if __name__ == "__main__":
    unittest.main()
