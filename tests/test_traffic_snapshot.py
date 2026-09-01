"""The traffic series: dedup by date, and machines kept out of the trend.

The measured baseline that motivated this file: 2026-08-12 recorded 41 clones
and zero unique views. Reported as adoption that is a growth story; it is
`actions/checkout` plus `/plugin marketplace update`. These tests pin the rule
that keeps the two apart, and the dedup that makes a fourteen-day sliding window
into a series at all.
"""
import contextlib
import csv
import importlib.util
import io
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def load(name):
    path = REPO_ROOT / "scripts" / ("%s.py" % name)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


snapshot = load("traffic_snapshot")
report = load("traffic_report")


def clones(*entries):
    return {"clones": [
        {"timestamp": "%sT00:00:00Z" % day, "count": count, "uniques": uniques}
        for day, count, uniques in entries
    ]}


def views(*entries):
    return {"views": [
        {"timestamp": "%sT00:00:00Z" % day, "count": count, "uniques": uniques}
        for day, count, uniques in entries
    ]}


REPOSITORY = {"stargazers_count": 3, "forks_count": 1}


class TestMerge(unittest.TestCase):
    def test_a_first_run_writes_one_row_per_day(self):
        rows = snapshot.merge(
            {},
            clones(("2026-08-10", 25, 5), ("2026-08-11", 34, 4)),
            views(("2026-08-10", 69, 12), ("2026-08-11", 0, 0)),
            REPOSITORY,
            "2026-08-11",
        )
        self.assertEqual([row["date"] for row in rows],
                         ["2026-08-10", "2026-08-11"])
        self.assertEqual(rows[0]["clones_uniques"], "5")

    def test_a_second_run_the_same_day_updates_rather_than_duplicates(self):
        first = snapshot.merge({}, clones(("2026-08-11", 34, 4)),
                               views(("2026-08-11", 5, 2)), REPOSITORY,
                               "2026-08-11")
        series = {row["date"]: row for row in first}

        second = snapshot.merge(series, clones(("2026-08-11", 41, 6)),
                                views(("2026-08-11", 9, 3)), REPOSITORY,
                                "2026-08-11")

        self.assertEqual(len(second), 1)
        self.assertEqual(second[0]["clones_count"], "41")
        self.assertEqual(second[0]["views_uniques"], "3")

    def test_the_measured_automation_day_is_flagged(self):
        """2026-08-12: 41 clones, zero unique views. Not people."""
        rows = snapshot.merge({}, clones(("2026-08-12", 41, 3)),
                              views(("2026-08-12", 0, 0)), REPOSITORY,
                              "2026-08-12")
        self.assertEqual(rows[0]["automation_suspected"], "true")

    def test_a_day_with_a_real_viewer_is_never_flagged(self):
        rows = snapshot.merge({}, clones(("2026-08-10", 25, 5)),
                              views(("2026-08-10", 69, 12)), REPOSITORY,
                              "2026-08-10")
        self.assertEqual(rows[0]["automation_suspected"], "false")

    def test_a_quiet_day_below_the_clone_floor_is_not_automation(self):
        rows = snapshot.merge({}, clones(("2026-08-10", 4, 2)),
                              views(("2026-08-10", 0, 0)), REPOSITORY,
                              "2026-08-10")
        self.assertEqual(rows[0]["automation_suspected"], "false")

    def test_stars_are_stamped_on_the_snapshot_date_only(self):
        """A star count is a reading taken now, not a fact about last Tuesday."""
        rows = snapshot.merge({}, clones(("2026-08-10", 4, 2)),
                              views(("2026-08-10", 6, 3)), REPOSITORY,
                              "2026-08-11")
        by_date = {row["date"]: row for row in rows}
        self.assertEqual(by_date["2026-08-10"]["stars"], "")
        self.assertEqual(by_date["2026-08-11"]["stars"], "3")

    def test_an_earlier_star_reading_is_never_overwritten(self):
        series = {row["date"]: row for row in snapshot.merge(
            {}, clones(), views(), {"stargazers_count": 3, "forks_count": 1},
            "2026-08-11")}

        rows = snapshot.merge(series, clones(), views(),
                              {"stargazers_count": 9, "forks_count": 2},
                              "2026-08-18")

        by_date = {row["date"]: row for row in rows}
        self.assertEqual(by_date["2026-08-11"]["stars"], "3")
        self.assertEqual(by_date["2026-08-18"]["stars"], "9")


class TestIssueColumn(unittest.TestCase):
    """The feedback channel's own signal, and the reason A3 exists."""

    def test_issues_land_on_the_day_they_were_opened(self):
        rows = snapshot.merge(
            {}, clones(), views(), REPOSITORY, "2026-08-12",
            issues=["2026-08-10T09:00:00Z", "2026-08-10T17:00:00Z",
                    "2026-08-12T08:00:00Z"],
            issues_since="2026-08-10",
        )
        by_date = {row["date"]: row for row in rows}
        self.assertEqual(by_date["2026-08-10"]["issues_opened"], "2")
        self.assertEqual(by_date["2026-08-12"]["issues_opened"], "1")

    def test_a_quiet_day_inside_the_window_is_zero_not_blank(self):
        """Blank means unmeasured; zero means nobody wrote. Different facts."""
        rows = snapshot.merge(
            {}, clones(), views(), REPOSITORY, "2026-08-12",
            issues=[], issues_since="2026-08-10",
        )
        by_date = {row["date"]: row for row in rows}
        self.assertEqual(by_date["2026-08-11"]["issues_opened"], "0")

    def test_a_day_before_the_window_keeps_its_blank(self):
        series = {row["date"]: row for row in snapshot.merge(
            {}, clones(("2026-07-01", 3, 2)), views(("2026-07-01", 4, 2)),
            REPOSITORY, "2026-07-01")}

        rows = snapshot.merge(series, clones(), views(), REPOSITORY,
                              "2026-08-12", issues=[],
                              issues_since="2026-08-10")

        by_date = {row["date"]: row for row in rows}
        self.assertEqual(by_date["2026-07-01"]["issues_opened"], "")

    def test_an_issue_lands_even_on_a_day_traffic_never_reported(self):
        """The traffic endpoints skip silent days; an issue still happened."""
        rows = snapshot.merge(
            {}, clones(), views(), REPOSITORY, "2026-08-12",
            issues=["2026-08-11T12:00:00Z"], issues_since="2026-08-10",
        )
        self.assertIn("2026-08-11", {row["date"] for row in rows})


class TestRoundTrip(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)

    def run_snapshot(self, day, clone_rows, view_rows):
        payloads = {
            "clones": clones(*clone_rows),
            "views": views(*view_rows),
            "repository": REPOSITORY,
        }
        for name, payload in payloads.items():
            (self.root / ("%s.json" % name)).write_text(
                json.dumps(payload), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            return snapshot.main([
                "--clones", str(self.root / "clones.json"),
                "--views", str(self.root / "views.json"),
                "--repository", str(self.root / "repository.json"),
                "--out", str(self.root / "metrics" / "traffic.csv"),
                "--date", day,
            ])

    def test_the_file_survives_being_written_twice_the_same_day(self):
        self.run_snapshot("2026-08-11", [("2026-08-11", 34, 4)],
                          [("2026-08-11", 5, 2)])
        self.run_snapshot("2026-08-11", [("2026-08-11", 41, 6)],
                          [("2026-08-11", 9, 3)])

        with (self.root / "metrics" / "traffic.csv").open(
                encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["clones_count"], "41")

    def test_issues_without_a_start_date_fails_instead_of_dropping_them(self):
        """The pair is required in fact; leaving it optional in the parser
        writes a blank column and reports success."""
        for name, payload in (("clones", clones()), ("views", views()),
                              ("repository", REPOSITORY),
                              ("issues", ["2026-08-11T12:00:00Z"])):
            (self.root / ("%s.json" % name)).write_text(
                json.dumps(payload), encoding="utf-8")

        with contextlib.redirect_stderr(io.StringIO()) as captured:
            with self.assertRaises(SystemExit) as raised:
                snapshot.main([
                    "--clones", str(self.root / "clones.json"),
                    "--views", str(self.root / "views.json"),
                    "--repository", str(self.root / "repository.json"),
                    "--issues", str(self.root / "issues.json"),
                    "--out", str(self.root / "metrics" / "traffic.csv"),
                    "--date", "2026-08-11",
                ])

        self.assertNotEqual(0, raised.exception.code)
        self.assertIn("--issues-since", captured.getvalue())
        self.assertFalse((self.root / "metrics" / "traffic.csv").exists())

    def test_the_header_is_the_documented_schema(self):
        self.run_snapshot("2026-08-11", [("2026-08-11", 1, 1)],
                          [("2026-08-11", 1, 1)])
        header = (self.root / "metrics" / "traffic.csv").read_text(
            encoding="utf-8").splitlines()[0]
        self.assertEqual(
            header,
            "date,clones_count,clones_uniques,views_count,views_uniques,"
            "stars,forks,issues_opened,automation_suspected",
        )


class TestReport(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)

    def series(self, rows):
        path = self.root / "traffic.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=snapshot.FIELDS,
                                    lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        return path

    @staticmethod
    def row(day, clones_uniques, views_uniques, flagged="false", **extra):
        base = {field: "" for field in snapshot.FIELDS}
        base.update(date=day, clones_uniques=str(clones_uniques),
                    views_uniques=str(views_uniques),
                    clones_count=str(clones_uniques),
                    views_count=str(views_uniques),
                    automation_suspected=flagged)
        base.update(extra)
        return base

    def test_two_months_compare_window_against_window(self):
        rows = [self.row("2026-06-%02d" % day, 1, 1) for day in range(1, 29)]
        rows += [self.row("2026-07-%02d" % day, 3, 2) for day in range(1, 29)]
        self.series(rows)

        lines = report.report(report.load(self.root / "traffic.csv"),
                              self.root, date(2026, 7, 28))

        # July 1-28 inclusive of today is the recent window; the prior one
        # reaches back to June 3, and June 29-30 were never recorded.
        self.assertIn("Unique cloners, last 28d: 84", lines[0])
        self.assertIn("previous 28d: 26", lines[0])

    def test_a_flagged_day_is_excluded_and_named(self):
        self.series([
            self.row("2026-08-10", 5, 12),
            self.row("2026-08-12", 3, 0, flagged="true"),
        ])

        lines = report.report(report.load(self.root / "traffic.csv"),
                              self.root, date(2026, 8, 12))

        self.assertIn("Unique cloners, last 28d: 5", lines[0])
        self.assertIn("2026-08-12", lines[2])

    def test_a_flagged_day_in_the_prior_window_is_excluded_and_disclosed(self):
        """Dropping automation from one window and disclosing only the other
        prints growth a flat month never had."""
        rows = [self.row("2026-06-%02d" % day, 3, 2,
                         flagged="true" if day < 8 else "false")
                for day in range(3, 29)]
        rows += [self.row("2026-07-%02d" % day, 3, 2) for day in range(1, 29)]
        self.series(rows)

        lines = report.report(report.load(self.root / "traffic.csv"),
                              self.root, date(2026, 7, 28))

        self.assertIn("+0%", lines[0])
        self.assertIn("0 days in the last 28", lines[2])
        self.assertIn("5 day(s) in the previous 28", lines[2])

    def test_new_issues_are_counted_including_automation_days(self):
        """A day whose clones were CI is still a day a person can file an issue."""
        self.series([
            self.row("2026-08-10", 5, 12, issues_opened="1"),
            self.row("2026-08-12", 3, 0, flagged="true", issues_opened="2"),
        ])

        lines = report.report(report.load(self.root / "traffic.csv"),
                              self.root, date(2026, 8, 12))

        self.assertIn("New issues, last 28d: 3", lines[3])

    def test_an_unmeasured_issue_column_says_so_rather_than_reporting_zero(self):
        self.series([self.row("2026-08-10", 5, 12)])
        lines = report.report(report.load(self.root / "traffic.csv"),
                              self.root, date(2026, 8, 10))
        self.assertIn("New issues, last 28d: not recorded", lines[3])

    def test_a_prior_window_with_no_issue_column_says_so_rather_than_zero(self):
        self.series([
            self.row("2026-07-01", 5, 12),
            self.row("2026-08-10", 5, 12, issues_opened="2"),
        ])
        lines = report.report(report.load(self.root / "traffic.csv"),
                              self.root, date(2026, 8, 10))
        self.assertIn("New issues, last 28d: 2 (previous 28d: not recorded)",
                      lines[3])

    def test_a_referrer_snapshot_is_read_when_one_exists(self):
        self.series([self.row("2026-08-10", 5, 12)])
        (self.root / "referrers-2026-08-10.csv").write_text(
            "referrer,count,uniques\nmsolecki.github.io,68,15\nGoogle,4,3\n",
            encoding="utf-8")

        lines = report.report(report.load(self.root / "traffic.csv"),
                              self.root, date(2026, 8, 10))

        self.assertIn("msolecki.github.io 15 uniques", lines[4])

    def test_a_malformed_uniques_value_costs_one_line_not_the_report(self):
        """`_number` exists for exactly this and the sort key skipped it."""
        self.series([self.row("2026-08-10", 5, 12)])
        (self.root / "referrers-2026-08-10.csv").write_text(
            "referrer,count,uniques\nmsolecki.github.io,68,15\n"
            "Google,4,not a number\n",
            encoding="utf-8")

        lines = report.report(report.load(self.root / "traffic.csv"),
                              self.root, date(2026, 8, 10))

        self.assertEqual(5, len(lines))
        self.assertIn("msolecki.github.io 15 uniques", lines[4])

    def test_a_snapshot_older_than_the_window_is_named_not_counted(self):
        """A photograph of June printed beside a 28-day trend reads as part of
        it. The filename was the only thing limiting the damage."""
        self.series([self.row("2026-08-10", 5, 12)])
        (self.root / "referrers-2026-02-10.csv").write_text(
            "referrer,count,uniques\nold-referrer,900,400\n",
            encoding="utf-8")

        lines = report.report(report.load(self.root / "traffic.csv"),
                              self.root, date(2026, 8, 10))

        self.assertNotIn("old-referrer", lines[4])
        self.assertIn("referrers-2026-02-10.csv", lines[4])
        self.assertIn("before the window", lines[4])

    def test_a_missing_referrer_snapshot_says_so_instead_of_guessing(self):
        self.series([self.row("2026-08-10", 5, 12)])
        lines = report.report(report.load(self.root / "traffic.csv"),
                              self.root, date(2026, 8, 10))
        self.assertIn("no referrer snapshot", lines[4])

    def test_an_empty_in_window_snapshot_is_not_reported_as_a_missing_one(self):
        """GitHub answers a quiet week with an empty list, and a header-only
        file is that answer — not the absence of one."""
        self.series([self.row("2026-08-10", 5, 12)])
        (self.root / "referrers-2026-08-10.csv").write_text(
            "referrer,count,uniques\n", encoding="utf-8")

        lines = report.report(report.load(self.root / "traffic.csv"),
                              self.root, date(2026, 8, 10))

        self.assertIn("referrers-2026-08-10.csv", lines[4])
        self.assertIn("lists none", lines[4])
        self.assertNotIn("before the window", lines[4])
        self.assertNotIn("no referrer snapshot", lines[4])

    def test_it_prints_exactly_five_lines(self):
        self.series([self.row("2026-08-10", 5, 12)])
        self.assertEqual(
            len(report.report(report.load(self.root / "traffic.csv"),
                              self.root, date(2026, 8, 10))),
            5,
        )

    def test_a_row_with_no_real_date_costs_the_default_not_the_report(self):
        """`windows()` already skips it; the reporting date has to as well."""
        path = self.series([self.row("2026-08-10", 5, 12)])
        with path.open("a", encoding="utf-8", newline="") as handle:
            handle.write("total,,,,,,,,\n")

        with contextlib.redirect_stdout(io.StringIO()) as captured:
            self.assertEqual(report.main([str(path)]), 0)

        self.assertIn("Unique cloners, last 28d: 5", captured.getvalue())

    def test_a_series_with_no_parsable_date_says_so_instead_of_raising(self):
        path = self.root / "traffic.csv"
        path.write_text("date,clones_uniques\ntotal,4\n", encoding="utf-8")
        with contextlib.redirect_stderr(io.StringIO()) as captured:
            self.assertEqual(report.main([str(path)]), 1)
        self.assertIn("no row with a YYYY-MM-DD date", captured.getvalue())

    def test_a_malformed_today_is_a_message_not_a_traceback(self):
        path = self.series([self.row("2026-08-10", 5, 12)])
        with contextlib.redirect_stderr(io.StringIO()) as captured:
            self.assertEqual(report.main([str(path), "--today", "yesterday"]), 1)
        self.assertIn("YYYY-MM-DD", captured.getvalue())

    def test_a_missing_series_fails_loudly_rather_than_printing_zeroes(self):
        with contextlib.redirect_stderr(io.StringIO()) as captured:
            self.assertEqual(report.main([str(self.root / "absent.csv")]), 1)
        self.assertIn("no series at", captured.getvalue())


class TestWorkflowContract(unittest.TestCase):
    """The parts of the workflow that are load-bearing rather than incidental."""

    def setUp(self):
        import yaml
        self.workflow = yaml.safe_load(
            (REPO_ROOT / ".github" / "workflows" / "traffic-snapshot.yml")
            .read_text(encoding="utf-8")
        )

    def test_it_writes_to_the_orphan_branch_and_never_to_main(self):
        body = " ".join(
            step.get("run", "")
            for step in self.workflow["jobs"]["snapshot"]["steps"]
        )
        self.assertIn("git push -q origin metrics", body)
        self.assertIn("--orphan metrics", body)
        self.assertNotIn("push -q origin main", body)

    def test_it_can_be_run_by_hand_and_weekly(self):
        # PyYAML reads a bare `on:` key as the boolean True.
        triggers = self.workflow.get("on", self.workflow.get(True))
        self.assertIn("workflow_dispatch", triggers)
        self.assertEqual(triggers["schedule"], [{"cron": "0 6 * * 1"}])

    def test_it_asks_for_no_more_permission_than_it_needs(self):
        self.assertEqual(self.workflow["permissions"], {"contents": "write"})


if __name__ == "__main__":
    unittest.main()
