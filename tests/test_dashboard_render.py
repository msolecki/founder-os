"""Theme correctness, checked mechanically because it fails silently.

The classic artifact bug is a colour whose only definition sits inside a media
query or a `[data-theme]` block: the viewer whose OS setting is "system" gets one
theme's text on the other theme's background, and nothing errors. These tests
assert every token is defined in all three states.
"""
import importlib
import importlib.util
import re
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "founder-os"
DASHBOARD = PLUGIN_ROOT / "scripts" / "dashboard"


def load_dashboard(name):
    if "fos_dashboard" not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            "fos_dashboard", DASHBOARD / "__init__.py",
            submodule_search_locations=[str(DASHBOARD)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["fos_dashboard"] = package
        spec.loader.exec_module(package)
    return importlib.import_module("fos_dashboard.%s" % name)


theme = load_dashboard("theme")


class TestTokens(unittest.TestCase):
    def test_light_and_dark_define_the_same_token_names(self):
        self.assertEqual(sorted(theme.TOKENS["light"]),
                         sorted(theme.TOKENS["dark"]))

    def test_every_token_is_defined_three_times(self):
        for name in theme.TOKENS["light"]:
            occurrences = len(re.findall(
                re.escape(name) + r"\s*:", theme.STYLESHEET))
            self.assertEqual(occurrences, 3, name)

    def test_the_three_selectors_are_present_and_guarded(self):
        self.assertIn("@media (prefers-color-scheme: dark)", theme.STYLESHEET)
        self.assertIn(':root:not([data-theme="light"])', theme.STYLESHEET)
        self.assertIn(':root[data-theme="dark"]', theme.STYLESHEET)

    def test_body_paints_its_own_background_from_a_token(self):
        self.assertRegex(theme.STYLESHEET, r"body\s*\{[^}]*background:\s*var\(--paper\)")

    def test_no_web_font_is_requested(self):
        self.assertNotIn("fonts.googleapis.com", theme.STYLESHEET)
        self.assertNotIn("@import", theme.STYLESHEET)

    def test_reduced_motion_is_respected(self):
        self.assertIn("prefers-reduced-motion", theme.STYLESHEET)

    def test_bet_hues_are_the_validated_pairs(self):
        self.assertEqual(theme.TOKENS["light"]["--bet-1"], "#0a6e9a")
        self.assertEqual(theme.TOKENS["light"]["--bet-2"], "#6d7c15")
        self.assertEqual(theme.TOKENS["dark"]["--bet-1"], "#2f9dcc")
        self.assertEqual(theme.TOKENS["dark"]["--bet-2"], "#82992a")


if __name__ == "__main__":
    unittest.main()
