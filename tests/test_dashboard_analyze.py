"""The analyzer's honesty rules, pinned against the example workspace.

Three of these tests exist because of a specific failure the mockup exposed:
a figure derivable from two files that disagree. The analyzer's job at that
point is to refuse to choose, and to say which field would settle it.
"""
import importlib
import importlib.util
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "founder-os"
DASHBOARD = PLUGIN_ROOT / "scripts" / "dashboard"
EXAMPLE = REPO_ROOT / "examples" / "studio-north"
TODAY = date(2026, 7, 20)


def load_dashboard(name):
    if "fos_dashboard" not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            "fos_dashboard", DASHBOARD / "__init__.py",
            submodule_search_locations=[str(DASHBOARD)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["fos_dashboard"] = package
        spec.loader.exec_module(package)
    return importlib.import_module("fos_dashboard.%s" % name)


contracts = load_dashboard("contracts")
collect = load_dashboard("collect")
analyze = load_dashboard("analyze")


def example_sources(mutate=None):
    home = Path(tempfile.mkdtemp()) / "founder-os"
    shutil.copytree(EXAMPLE, home)
    if mutate is not None:
        mutate(home)
    return collect.collect(home, contracts.load_ownership(), slug="studio-north")


def fact(panel, key):
    for item in panel.facts:
        if item.key == key:
            return item
    raise AssertionError("no fact %r in panel %r" % (key, panel.id))


class TestPipelinePanel(unittest.TestCase):
    def test_live_total_and_count(self):
        panel = analyze.build_pipeline(example_sources(), TODAY)
        self.assertEqual(panel.status, analyze.STATUS_OK)
        self.assertEqual(fact(panel, "live_amount").number, 33000.0)
        self.assertEqual(fact(panel, "live_count").number, 2.0)
        self.assertEqual(fact(panel, "live_amount").currency, "$")

    def test_next_action_in_the_past_is_counted_overdue(self):
        panel = analyze.build_pipeline(example_sources(), TODAY)
        self.assertEqual(fact(panel, "overdue_count").number, 1.0)

    def test_missing_section_is_missing_not_zero(self):
        def strip(home):
            (home / "pipeline.md").write_text("# Pipeline\n", encoding="utf-8")
        panel = analyze.build_pipeline(example_sources(strip), TODAY)
        self.assertEqual(panel.status, analyze.STATUS_MISSING)
        self.assertIsNone(fact(panel, "live_amount").number)
        self.assertEqual(fact(panel, "live_amount").display, analyze.NOT_RECORDED)

    def test_declared_empty_section_is_zero_not_missing(self):
        def empty(home):
            text = (home / "pipeline.md").read_text(encoding="utf-8")
            head, rest = text.split("## Live", 1)
            body = rest.split("## Won", 1)[1]
            (home / "pipeline.md").write_text(
                head + "## Live\n\nNone.\n\n## Won" + body, encoding="utf-8")
        panel = analyze.build_pipeline(example_sources(empty), TODAY)
        self.assertEqual(fact(panel, "live_count").number, 0.0)
        self.assertEqual(panel.status, analyze.STATUS_OK)

    def test_two_currencies_are_contested_never_summed(self):
        def mix(home):
            text = (home / "pipeline.md").read_text(encoding="utf-8")
            (home / "pipeline.md").write_text(
                text.replace("Amount: $15,000 [VALIDATE]", "Amount: €15,000", 1),
                encoding="utf-8")
        panel = analyze.build_pipeline(example_sources(mix), TODAY)
        self.assertEqual(panel.status, analyze.STATUS_CONTESTED)
        self.assertEqual(len(panel.readings), 2)
        self.assertIsNotNone(panel.settle_with)


class TestPanelPrimitives(unittest.TestCase):
    def test_unknown_carries_no_number(self):
        item = analyze.unknown("x", "metrics.md ## Close")
        self.assertIsNone(item.number)
        self.assertEqual(item.display, analyze.NOT_RECORDED)

    def test_status_is_partial_when_any_fact_is_unknown(self):
        facts = (analyze.number_fact("a", 1.0, "1", "f.md ## A"),
                 analyze.unknown("b", "f.md ## B"))
        self.assertEqual(analyze.panel_status(facts), analyze.STATUS_PARTIAL)

    def test_a_text_fact_is_known_and_does_not_make_a_panel_partial(self):
        facts = (analyze.text_fact("one_thing", "Finish the Acme proposal scope.",
                                   "reviews/daily/ ## The one thing"),)
        self.assertEqual(analyze.panel_status(facts), analyze.STATUS_OK)

    def test_hash_ignores_unrelated_panels(self):
        first = analyze.build_pipeline(example_sources(), TODAY)
        second = analyze.build_pipeline(example_sources(), TODAY)
        self.assertEqual(analyze.panel_hash(first), analyze.panel_hash(second))

    def test_hash_changes_when_a_fact_changes(self):
        def bump(home):
            text = (home / "pipeline.md").read_text(encoding="utf-8")
            (home / "pipeline.md").write_text(
                text.replace("$18,000", "$19,000"), encoding="utf-8")
        before = analyze.panel_hash(analyze.build_pipeline(example_sources(), TODAY))
        after = analyze.panel_hash(
            analyze.build_pipeline(example_sources(bump), TODAY))
        self.assertNotEqual(before, after)


if __name__ == "__main__":
    unittest.main()
