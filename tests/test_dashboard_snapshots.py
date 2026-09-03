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

    def test_signals_below_normal_is_empty_when_a_line_could_not_be_read(self):
        """A tally over the lines that parsed is a confident wrong number.

        The column has one meaning — how many signals read below normal — and
        a section the reader could not finish cannot answer it. An empty cell
        says we did not look; a 2 says the founder has two problems.
        """
        def unreadable(home):
            text = (home / "metrics.md").read_text(encoding="utf-8")
            (home / "metrics.md").write_text(
                text.replace(
                    "- Proposals sent — source: drafts/proposals/ ## Sent — 0 "
                    "— normal 1-2 — last four: 1, 1, 0, 0",
                    "- Proposals sent — we sent one this week"),
                encoding="utf-8")
        facts = example_facts(unreadable)
        self.assertFalse(
            [item for item in facts.panels["signals"].facts
             if item.key == "signal_count"][0].known)
        self.assertEqual(
            snapshots.row_from(facts)["signals_below_normal"], "")

    def test_every_field_is_present_in_every_row(self):
        row = snapshots.row_from(example_facts())
        self.assertEqual(sorted(row), sorted(snapshots.FIELDS))


class TestTheCountedInventoryIsTheDeclaredSet(unittest.TestCase):
    """Three columns count the map's paths, and the map does not grow.

    `files_present`, `files_missing` and `sections_missing` are a series a
    founder keeps week over week. Counting the members of the declared
    directories instead puts every archived daily review in the denominator,
    so the same workspace scores differently in month six than in month one
    and the history stops being comparable to itself.
    """

    @staticmethod
    def archive(count=39):
        def mutate(home):
            for index in range(count):
                (home / "reviews" / "daily" / ("2026-06-%02d.md" % (index + 1))
                 ).write_text("# Daily\n\n## The one thing\n\nShip.\n",
                              encoding="utf-8")
        return mutate

    def test_an_archive_does_not_move_the_file_counts(self):
        base = snapshots.row_from(example_facts())
        grown = snapshots.row_from(example_facts(self.archive()))
        for column in ("files_present", "files_missing", "sections_missing"):
            self.assertEqual(grown[column], base[column], column)

    def test_the_counts_are_the_declared_paths_and_nothing_else(self):
        view = contracts.load_ownership()
        declared = [path for path in view.workspace_files
                    if not path.endswith("/")]
        row = snapshots.row_from(example_facts())
        self.assertEqual(int(row["files_present"]) + int(row["files_missing"]),
                         len(declared))

    def test_an_archived_member_is_still_reported_in_the_findings(self):
        facts = example_facts(self.archive(1))
        self.assertIn(
            "reviews/daily/2026-06-01.md ## Rotting",
            [item.cite for item in facts.findings])


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


class TestMergeReadsWhatIsAlreadyThere(unittest.TestCase):
    """The series is the one file a rerun cannot rebuild.

    Every test here is about the same contract: merge either understands the
    file it is about to replace, or it leaves it alone. Silently rewriting a
    file we misread is the one outcome that costs history.
    """

    def _series(self, days=("2026-07-18", "2026-07-19", "2026-07-20")):
        path = Path(tempfile.mkdtemp()) / "snapshots.csv"
        row = snapshots.row_from(example_facts())
        for index, day in enumerate(days):
            snapshots.merge(path, dict(row, date=day, queue_doing=str(index)))
        return path

    def test_a_byte_order_mark_does_not_collapse_the_history(self):
        path = self._series()
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
        snapshots.merge(path, dict(snapshots.row_from(example_facts()),
                                   date="2026-07-21"))
        rows = _rows(path)
        self.assertEqual([r["date"] for r in rows],
                         ["2026-07-18", "2026-07-19", "2026-07-20", "2026-07-21"])
        self.assertEqual([r["queue_doing"] for r in rows[:3]], ["0", "1", "2"])

    def test_an_undecodable_series_is_refused_and_left_untouched(self):
        path = self._series()
        path.write_bytes(path.read_bytes().replace(b"$", b"\xa3"))
        before = path.read_bytes()
        with self.assertRaises(OSError) as caught:
            snapshots.merge(path, dict(snapshots.row_from(example_facts()),
                                       date="2026-07-21"))
        self.assertIn(str(path), str(caught.exception))
        self.assertEqual(path.read_bytes(), before)

    def test_a_csv_error_is_refused_and_left_untouched(self):
        # An over-long field rather than an embedded NUL: CPython dropped the
        # "line contains NUL" error in 3.11, so that byte raises on 3.9 and
        # parses cleanly on the version CI runs. The field limit is the one
        # csv.Error every supported interpreter still agrees on.
        path = self._series()
        path.write_bytes(path.read_bytes()
                         + b"2026-07-21," + b"x" * 200000 + b"\n")
        before = path.read_bytes()
        with self.assertRaises(OSError):
            snapshots.merge(path, dict(snapshots.row_from(example_facts()),
                                       date="2026-07-21"))
        self.assertEqual(path.read_bytes(), before)

    def test_a_header_without_the_key_columns_is_refused(self):
        path = Path(tempfile.mkdtemp()) / "snapshots.csv"
        path.write_text("day,company\n2026-07-18,studio-north\n", encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(OSError):
            snapshots.merge(path, snapshots.row_from(example_facts()))
        self.assertEqual(path.read_bytes(), before)

    def test_an_empty_file_carries_no_history_and_is_written(self):
        path = Path(tempfile.mkdtemp()) / "snapshots.csv"
        path.write_bytes(b"")
        snapshots.merge(path, snapshots.row_from(example_facts()))
        self.assertEqual(len(_rows(path)), 1)

    def test_refusal_is_an_oserror_so_the_command_exits_with_its_write_code(self):
        """__main__ turns OSError into EXIT_WRITE; anything else is a traceback."""
        path = self._series()
        path.write_bytes(path.read_bytes().replace(b"$", b"\xa3"))
        try:
            snapshots.merge(path, snapshots.row_from(example_facts()))
        except OSError:
            pass
        else:
            self.fail("merge accepted a series it could not read")

    def test_a_refusal_claims_nothing_beyond_the_file_it_refused(self):
        """The command writes facts.json for this business before it merges.

        So by the time the refusal is printed — under "Could not update
        <home>/_dashboard" — a sentence about what the run wrote is already
        false. The refusal may speak for this file only.
        """
        undecodable = self._series()
        undecodable.write_bytes(undecodable.read_bytes().replace(b"$", b"\xa3"))
        unparsable = self._series()
        unparsable.write_bytes(unparsable.read_bytes()
                               + b"2026-07-21," + b"x" * 200000 + b"\n")
        for path in (undecodable, unparsable):
            with self.assertRaises(OSError) as caught:
                snapshots.merge(path, dict(snapshots.row_from(example_facts()),
                                           date="2026-07-21"))
            claim = str(caught.exception).replace(str(path), "")
            self.assertIn("left as it is", claim)
            self.assertNotIn(
                "run", claim,
                "the refusal speaks for the run, which has already written "
                "facts.json for this business: %s" % claim)

    def test_a_column_the_older_rows_never_had_keeps_those_rows(self):
        path = self._series(days=("2026-07-18",))
        text = path.read_text(encoding="utf-8").splitlines()
        header = text[0].replace(",integrity_findings", "")
        body = text[1].rsplit(",", 1)[0]
        path.write_text("%s\n%s\n" % (header, body), encoding="utf-8")
        snapshots.merge(path, dict(snapshots.row_from(example_facts()),
                                   date="2026-07-21"))
        rows = _rows(path)
        self.assertEqual([r["date"] for r in rows], ["2026-07-18", "2026-07-21"])
        self.assertEqual(rows[0]["integrity_findings"], "")


class TestAColumnThisCommandDoesNotWrite(unittest.TestCase):
    """The founder keeps this file, so a column they added is theirs.

    Every other refusal in `merge` exists because the series cannot be rebuilt.
    A column the writer does not know about is the same loss, one column wide,
    and it happens on every run after the one that added it.
    """

    def test_a_column_the_founder_added_survives_the_next_merge(self):
        path = Path(tempfile.mkdtemp()) / "snapshots.csv"
        row = snapshots.row_from(example_facts())
        snapshots.merge(path, dict(row, date="2026-07-18"))
        lines = path.read_text(encoding="utf-8").splitlines()
        path.write_text("%s,note\n%s,paid the VAT bill\n"
                        % (lines[0], lines[1]), encoding="utf-8")
        snapshots.merge(path, dict(row, date="2026-07-19"))
        rows = _rows(path)
        self.assertEqual([r["date"] for r in rows],
                         ["2026-07-18", "2026-07-19"])
        self.assertEqual(rows[0]["note"], "paid the VAT bill")
        self.assertEqual(rows[1]["note"], "")


class TestAFounderColumnSurvivesARerun(unittest.TestCase):
    """The header was kept and the contents were not.

    `merge` built each row from the run's own fields, so a column the founder
    added carried its name into every future file and its value into none of
    them — and only for the date being re-merged, which is the ordinary second
    run of a day.
    """

    def _seed(self, note_by_date):
        path = Path(tempfile.mkdtemp()) / "snapshots.csv"
        header = ",".join(list(snapshots.FIELDS) + ["founder_note"])
        lines = [header]
        for day, note in note_by_date.items():
            cells = ["" for _ in snapshots.FIELDS]
            cells[0] = day
            lines.append(",".join(cells + [note]))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def _notes(self, path):
        with path.open(encoding="utf-8") as handle:
            return {row["date"]: row["founder_note"]
                    for row in csv.DictReader(handle)}

    def test_rerunning_a_day_keeps_the_note_on_that_day(self):
        path = self._seed({"2026-07-20": "note-0", "2026-07-21": "note-1"})
        snapshots.merge(path, {"date": "2026-07-21"})
        self.assertEqual(self._notes(path),
                         {"2026-07-20": "note-0", "2026-07-21": "note-1"})

    def test_a_new_day_leaves_the_earlier_notes_alone(self):
        path = self._seed({"2026-07-20": "note-0"})
        snapshots.merge(path, {"date": "2026-07-22"})
        notes = self._notes(path)
        self.assertEqual(notes["2026-07-20"], "note-0")
        self.assertEqual(notes["2026-07-22"], "")


if __name__ == "__main__":
    unittest.main()
