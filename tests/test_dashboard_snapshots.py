"""The series is a series only if the same day twice is one row.

`scripts/traffic_snapshot.py` learned this against the GitHub Traffic API: a
dated file that appends produces two answers for one day, and a chart drawn over
it is a chart of how often the script ran. Merge by key, and write nothing for a
value that was not read — an empty cell says "we did not look", a zero says the
company did nothing, and those are different sentences.
"""
import csv
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
snapshots = load_dashboard("snapshots")


def example_facts(mutate=None):
    home = Path(tempfile.mkdtemp()) / "founder-os"
    shutil.copytree(EXAMPLE, home)
    if mutate is not None:
        mutate(home)
    sources = collect.collect(home, contracts.load_ownership(), slug="studio-north")
    return analyze.build_facts(
        sources, TODAY, "2026-07-20T09:04:12+01:00", contracts.load_thresholds())


def _rows(path):
    return list(csv.DictReader(
        path.read_text(encoding="utf-8").splitlines()))


class TestFactsEnvelope(unittest.TestCase):
    def test_every_today_panel_is_present(self):
        facts = example_facts()
        self.assertEqual(
            sorted(facts.panels),
            ["bets", "brief", "cash", "pipeline", "queue", "signals", "week"])

    def test_envelope_carries_hashes_and_citations(self):
        payload = analyze.to_dict(example_facts())
        self.assertEqual(payload["schema"], analyze.SCHEMA)
        pipeline = payload["panels"]["pipeline"]
        self.assertEqual(len(pipeline["hash"]), 7)
        self.assertIn("pipeline.md ## Live", pipeline["citations"])

    def test_envelope_is_json_serialisable(self):
        import json
        json.dumps(analyze.to_dict(example_facts()))


class TestSnapshotRow(unittest.TestCase):
    def test_row_carries_the_readable_figures(self):
        row = snapshots.row_from(example_facts())
        self.assertEqual(row["date"], "2026-07-20")
        self.assertEqual(row["business"], "studio-north")
        self.assertEqual(row["pipeline_live_amount"], "33000")
        self.assertEqual(row["queue_doing"], "1")
        self.assertEqual(row["runway_months"], "9.7")

    def test_unreadable_figure_is_empty_not_zero(self):
        def strip(home):
            (home / "metrics.md").write_text("# Metrics\n", encoding="utf-8")
        row = snapshots.row_from(example_facts(strip))
        self.assertEqual(row["runway_months"], "")
        self.assertEqual(row["cash_on_hand"], "")

    def test_signals_below_normal_counts_only_the_ones_below(self):
        def lift(home):
            text = (home / "metrics.md").read_text(encoding="utf-8")
            (home / "metrics.md").write_text(
                text.replace("## Live — 2 — normal 3-5", "## Live — 4 — normal 3-5"),
                encoding="utf-8")
        self.assertEqual(snapshots.row_from(example_facts())["signals_below_normal"],
                         "3")
        self.assertEqual(
            snapshots.row_from(example_facts(lift))["signals_below_normal"], "2")

    def test_every_field_is_present_in_every_row(self):
        row = snapshots.row_from(example_facts())
        self.assertEqual(sorted(row), sorted(snapshots.FIELDS))


class TestMerge(unittest.TestCase):
    def _path(self):
        return Path(tempfile.mkdtemp()) / "snapshots.csv"

    def test_first_write_creates_a_header_and_one_row(self):
        path = self._path()
        snapshots.merge(path, snapshots.row_from(example_facts()))
        rows = _rows(path)
        self.assertEqual(len(rows), 1)

    def test_same_day_twice_updates_one_row(self):
        path = self._path()
        first = snapshots.row_from(example_facts())
        snapshots.merge(path, first)
        second = dict(first, queue_doing="2")
        snapshots.merge(path, second)
        rows = _rows(path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["queue_doing"], "2")

    def test_two_businesses_on_one_day_are_two_rows(self):
        path = self._path()
        row = snapshots.row_from(example_facts())
        snapshots.merge(path, row)
        snapshots.merge(path, dict(row, business="nordwind"))
        rows = _rows(path)
        self.assertEqual(len(rows), 2)

    def test_rows_stay_sorted_by_date_then_business(self):
        path = self._path()
        row = snapshots.row_from(example_facts())
        snapshots.merge(path, dict(row, date="2026-07-21"))
        snapshots.merge(path, row)
        rows = _rows(path)
        self.assertEqual([r["date"] for r in rows], ["2026-07-20", "2026-07-21"])


if __name__ == "__main__":
    unittest.main()
