"""Theme correctness, checked mechanically because it fails silently.

The classic artifact bug is a colour whose only definition sits inside a media
query or a `[data-theme]` block: the viewer whose OS setting is "system" gets one
theme's text on the other theme's background, and nothing errors. These tests
assert every token is defined in all three states.
"""
import importlib
import importlib.util
import re
import shutil
import sys
import tempfile
import unittest
from datetime import date
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


EXAMPLE = REPO_ROOT / "examples" / "studio-north"
GOLDEN = REPO_ROOT / "tests" / "fixtures" / "dashboard" / "today.golden.html"
TODAY = date(2026, 7, 20)


def build_example_page():
    contracts = load_dashboard("contracts")
    collect = load_dashboard("collect")
    analyze = load_dashboard("analyze")
    render = load_dashboard("render")
    home = Path(tempfile.mkdtemp()) / "founder-os"
    shutil.copytree(EXAMPLE, home)
    sources = collect.collect(home, contracts.load_ownership(), slug="studio-north")
    facts = analyze.build_facts(
        sources, TODAY, "2026-07-20T09:04:12+01:00", contracts.load_thresholds())
    business = contracts.Business(slug="studio-north", home=home, status="active")
    return render.render([(business, facts)],
                         generated="2026-07-20T09:04:12+01:00",
                         active_slug="studio-north")


class TestPageStructure(unittest.TestCase):
    def setUp(self):
        self.html = build_example_page()

    def test_is_a_complete_standalone_document(self):
        self.assertTrue(self.html.startswith("<!doctype html>"))
        self.assertIn("<title>", self.html)
        self.assertIn(theme.STYLESHEET, self.html)

    def test_makes_no_external_request(self):
        urls = re.findall(r'https?://[^"\')\s]+', self.html)
        self.assertEqual(urls, [])

    def test_every_today_panel_is_rendered_with_its_citation(self):
        for needle in ("Finish the Acme proposal scope",
                       "pipeline.md ## Live",
                       "metrics.md ## Signals",
                       "week.md ## Blocks",
                       "references/thresholds.yaml",
                       "goals.md ## Bets"):
            self.assertIn(needle, self.html, needle)

    def test_the_four_tabs_are_present_and_only_today_is_active(self):
        self.assertIn("Track record", self.html)
        self.assertIn("Integrity", self.html)
        tablist = re.search(r'<div class="tabs" role="tablist">(.*?)</div>',
                            self.html, re.S).group(1)
        self.assertEqual(tablist.count('aria-selected="true"'), 1)
        self.assertEqual(tablist.count('aria-selected="false"'), 3)

    def test_every_chart_has_a_table_beneath_it(self):
        self.assertGreaterEqual(self.html.count("Show the numbers"), 3)

    def test_unknown_renders_as_words_not_a_zero(self):
        contracts = load_dashboard("contracts")
        collect = load_dashboard("collect")
        analyze = load_dashboard("analyze")
        render = load_dashboard("render")
        home = Path(tempfile.mkdtemp()) / "founder-os"
        shutil.copytree(EXAMPLE, home)
        (home / "metrics.md").write_text("# Metrics\n", encoding="utf-8")
        sources = collect.collect(home, contracts.load_ownership(), slug="x")
        facts = analyze.build_facts(sources, TODAY, "g", contracts.load_thresholds())
        business = contracts.Business(slug="x", home=home, status="active")
        html = render.render([(business, facts)], generated="g", active_slug="x")
        self.assertIn("not recorded", html)
        self.assertIn('class="unknown"', html)

    def test_escapes_markup_found_in_state(self):
        render = load_dashboard("render")
        self.assertEqual(render.escape("<b>&"), "&lt;b&gt;&amp;")

    def test_a_bet_without_an_opened_date_draws_no_elapsed_bar(self):
        # The example records no `Opened:`, so the window fraction is unknown and
        # the page must not draw one from a start date nobody wrote down.
        self.assertNotIn("of the window spent", self.html)


class TestGolden(unittest.TestCase):
    def test_page_matches_the_reviewed_fixture(self):
        self.assertEqual(build_example_page(), GOLDEN.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
