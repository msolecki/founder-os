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


COUNTED = ("Counted from: pipeline.md ## Won | amount >= 15000 | target 3\n")


class TestCountedFromGrammar(unittest.TestCase):
    def test_full_expression(self):
        spec = analyze.parse_counted_from(
            "pipeline.md ## Won | amount >= 15000 | target 3")
        self.assertEqual(spec.path, "pipeline.md")
        self.assertEqual(spec.section, "## Won")
        self.assertEqual(spec.minimum, 15000.0)
        self.assertEqual(spec.target, 3.0)

    def test_path_and_section_only(self):
        spec = analyze.parse_counted_from("drafts/proposals/ ## Sent")
        self.assertEqual(spec.path, "drafts/proposals/")
        self.assertEqual(spec.section, "## Sent")
        self.assertIsNone(spec.minimum)

    def test_anything_outside_the_grammar_is_refused(self):
        for bad in ("pipeline.md", "count the won deals",
                    "pipeline.md ## Won | roughly 3",
                    "pipeline.md ## Won | amount > 15000"):
            self.assertIsNone(analyze.parse_counted_from(bad), bad)


class TestBetsPanel(unittest.TestCase):
    def test_days_to_judgment_without_any_new_field(self):
        panel, bets, _ = analyze.build_bets(example_sources(), TODAY)
        first = bets[0]
        self.assertEqual(first.key, "B1")
        self.assertEqual(first.judgment, date(2026, 9, 30))
        self.assertEqual(fact(panel, "B1.days_to_judgment").number, 72.0)

    def test_without_opened_there_is_no_elapsed_bar(self):
        _, bets, _ = analyze.build_bets(example_sources(), TODAY)
        self.assertIsNone(bets[0].elapsed)

    def test_opened_gives_an_exact_elapsed_fraction(self):
        def add_opened(home):
            text = (home / "goals.md").read_text(encoding="utf-8")
            (home / "goals.md").write_text(
                text.replace("Judgment date: 2026-09-30",
                             "Opened: 2026-07-01\n\nJudgment date: 2026-09-30", 1),
                encoding="utf-8")
        _, bets, _ = analyze.build_bets(example_sources(add_opened), TODAY)
        self.assertAlmostEqual(bets[0].elapsed, 19 / 91, places=3)
        self.assertFalse(bets[0].elapsed_assumed)

    def test_counted_from_produces_progress_against_a_target(self):
        def add_counted(home):
            text = (home / "goals.md").read_text(encoding="utf-8")
            (home / "goals.md").write_text(
                text.replace("Downside cap: 40 founder hours",
                             COUNTED + "\nDownside cap: 40 founder hours", 1),
                encoding="utf-8")
        _, bets, _ = analyze.build_bets(example_sources(add_counted), TODAY)
        self.assertEqual(bets[0].progress, 0.0)
        self.assertEqual(bets[0].target, 3.0)

    def test_unparseable_counted_from_raises_a_finding_not_a_guess(self):
        def bad(home):
            text = (home / "goals.md").read_text(encoding="utf-8")
            (home / "goals.md").write_text(
                text.replace("Downside cap: 40 founder hours",
                             "Counted from: the won deals\n\n"
                             "Downside cap: 40 founder hours", 1),
                encoding="utf-8")
        _, bets, _ = analyze.build_bets(example_sources(bad), TODAY)
        self.assertIsNone(bets[0].progress)

    def test_kill_date_is_read_from_the_kill_condition(self):
        _, bets, _ = analyze.build_bets(example_sources(), TODAY)
        self.assertEqual(bets[0].kill_date, date(2026, 8, 31))
        self.assertEqual(fact(
            analyze.build_bets(example_sources(), TODAY)[0],
            "B1.days_to_kill").number, 42.0)


class TestBriefPanel(unittest.TestCase):
    def test_reads_the_newest_daily_review(self):
        panel = analyze.build_brief(example_sources(), TODAY)
        self.assertIn("Acme proposal scope", fact(panel, "one_thing").display)
        self.assertEqual(fact(panel, "rotting_count").number, 1.0)
        self.assertIn("website redesign", fact(panel, "trade").display)

    def test_brief_age_in_days(self):
        panel = analyze.build_brief(example_sources(), date(2026, 7, 23))
        self.assertEqual(fact(panel, "brief_age_days").number, 3.0)

    def test_no_brief_at_all_is_missing(self):
        def clear(home):
            for item in (home / "reviews" / "daily").glob("*.md"):
                item.unlink()
        panel = analyze.build_brief(example_sources(clear), TODAY)
        self.assertEqual(panel.status, analyze.STATUS_MISSING)


class TestSignalsPanel(unittest.TestCase):
    def test_three_signals_with_bands_and_series(self):
        panel, signals, _ = analyze.build_signals(example_sources())
        self.assertEqual(len(signals), 3)
        proof = [s for s in signals if s.name == "Proof hours worked"][0]
        self.assertEqual(proof.value, 2.0)
        self.assertEqual((proof.low, proof.high), (5.0, 7.0))
        self.assertEqual(proof.series, (6.0, 5.0, 4.0, 2.0))
        self.assertEqual(proof.state, "below")
        self.assertEqual(proof.source, "week.md ## Ledger")

    def test_a_signal_inside_its_band_reads_in(self):
        def raise_it(home):
            text = (home / "metrics.md").read_text(encoding="utf-8")
            (home / "metrics.md").write_text(
                text.replace("## Live — 2 — normal 3-5", "## Live — 4 — normal 3-5"),
                encoding="utf-8")
        _, signals, _ = analyze.build_signals(example_sources(raise_it))
        self.assertEqual(signals[0].state, "in")

    def test_signal_count_is_a_fact(self):
        panel, _, _ = analyze.build_signals(example_sources())
        self.assertEqual(fact(panel, "signal_count").number, 3.0)


class TestWeekPanel(unittest.TestCase):
    def test_arithmetic_and_blocks(self):
        panel, blocks = analyze.build_week(example_sources())
        self.assertEqual(fact(panel, "available_hours").number, 40.0)
        self.assertEqual(fact(panel, "delivery_hours").number, 24.0)
        self.assertEqual(fact(panel, "planned_hours").number, 9.0)
        self.assertEqual(len(blocks), 5)

    def test_planned_hours_split_by_bet(self):
        panel, _ = analyze.build_week(example_sources())
        self.assertEqual(fact(panel, "planned.B1").number, 4.5)
        self.assertEqual(fact(panel, "planned.B2").number, 4.5)

    def test_missing_arithmetic_is_unknown_not_zero(self):
        def strip(home):
            (home / "week.md").write_text(
                "# Week of 2026-07-20\n\n## Arithmetic\n\n"
                "## Shape\n\nDeep hours 09:00-11:30.\n",
                encoding="utf-8")
        panel, _ = analyze.build_week(example_sources(strip))
        self.assertFalse(fact(panel, "available_hours").known)


class TestCashPanel(unittest.TestCase):
    def test_close_figures(self):
        panel = analyze.build_cash(example_sources(), TODAY)
        self.assertEqual(fact(panel, "booked").number, 31000.0)
        self.assertEqual(fact(panel, "collected").number, 24000.0)
        self.assertEqual(fact(panel, "effective_rate").number, 214.0)
        self.assertEqual(fact(panel, "cash_on_hand").number, 68000.0)
        self.assertEqual(fact(panel, "runway_months").number, 9.7)

    def test_close_age_is_measured_from_the_closed_date(self):
        panel = analyze.build_cash(example_sources(), TODAY)
        self.assertEqual(fact(panel, "close_age_days").number, 19.0)


class TestQueuePanel(unittest.TestCase):
    def setUp(self):
        self.thresholds = contracts.load_thresholds()

    def test_counts_against_declared_caps(self):
        panel = analyze.build_queue(example_sources(), self.thresholds)
        self.assertEqual(fact(panel, "doing").number, 1.0)
        self.assertEqual(fact(panel, "doing_cap").number, 3.0)
        self.assertEqual(fact(panel, "queued").number, 2.0)
        self.assertEqual(fact(panel, "queued_cap").number, 15.0)
        self.assertEqual(fact(panel, "blocked").number, 0.0)

    def test_blocked_says_none_and_counts_zero_not_unknown(self):
        panel = analyze.build_queue(example_sources(), self.thresholds)
        self.assertTrue(fact(panel, "blocked").known)

    def test_over_cap_is_reported(self):
        def overfill(home):
            text = (home / "queue.md").read_text(encoding="utf-8")
            extra = "".join("- [q-x%d] filler — bet: B1\n" % n for n in range(5))
            (home / "queue.md").write_text(
                text.replace("## Doing\n\n", "## Doing\n\n" + extra, 1),
                encoding="utf-8")
        panel = analyze.build_queue(example_sources(overfill), self.thresholds)
        self.assertEqual(fact(panel, "over_cap").number, 1.0)


def write(home, relative, text):
    target = home / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def edit(relative, old, new, count=1):
    def mutate(home):
        text = (home / relative).read_text(encoding="utf-8")
        assert old in text, old
        (home / relative).write_text(text.replace(old, new, count),
                                     encoding="utf-8")
    return mutate


def findings_about(sources, check):
    facts = analyze.build_facts(sources, TODAY, "generated",
                                contracts.load_thresholds())
    return [item for item in facts.findings if item.check == check]


class TestPipelineReadsOnlyRecordedMoney(unittest.TestCase):
    """A total the workspace never wrote is worse than no total at all.

    Every case here is an entry whose money is not recorded. The contract is
    that the panel says so — the failures these pin all printed a confident
    dollar figure built out of a year, a quarter number, or one deal's price
    standing in for two.
    """

    def test_a_title_without_a_currency_marker_is_not_money(self):
        mutate = edit(
            "pipeline.md",
            "### Northwind — premium strategy sprint — $15,000 — qualified",
            "### Northwind — Q3 2026 offsite — qualified")
        def drop_amount(home):
            mutate(home)
            text = (home / "pipeline.md").read_text(encoding="utf-8")
            (home / "pipeline.md").write_text(
                text.replace(
                    "Amount: $15,000 [VALIDATE] (per founder's call note, "
                    "2026-07-10 — validate:\nconfirm budget with Tom on the "
                    "next call by 2026-07-22)\n\n", ""),
                encoding="utf-8")
        panel = analyze.build_pipeline(example_sources(drop_amount), TODAY)
        amount = fact(panel, "live_amount")
        self.assertIsNone(amount.number)
        self.assertFalse(amount.known)

    def test_an_entry_with_no_amount_makes_the_total_unknown(self):
        def drop_amount(home):
            edit("pipeline.md",
                 "### Northwind — premium strategy sprint — $15,000 — qualified",
                 "### Northwind — premium strategy sprint — qualified")(home)
            edit("pipeline.md",
                 "Amount: $15,000 [VALIDATE] (per founder's call note, "
                 "2026-07-10 — validate:\nconfirm budget with Tom on the next "
                 "call by 2026-07-22)\n\n", "")(home)
        panel = analyze.build_pipeline(example_sources(drop_amount), TODAY)
        self.assertEqual(fact(panel, "live_count").number, 2.0)
        self.assertFalse(fact(panel, "live_amount").known)
        self.assertIn("1 of 2", fact(panel, "live_amount").display)

    def test_a_marked_and_an_unmarked_amount_are_never_added_together(self):
        panel = analyze.build_pipeline(
            example_sources(edit("pipeline.md", "Amount: $15,000 [VALIDATE]",
                                 "Amount: 15,000")), TODAY)
        self.assertEqual(panel.status, analyze.STATUS_CONTESTED)
        self.assertEqual(len(panel.readings), 2)
        self.assertTrue(panel.settle_with)

    def test_contested_still_reports_what_the_currency_does_not_touch(self):
        panel = analyze.build_pipeline(
            example_sources(edit("pipeline.md", "Amount: $15,000 [VALIDATE]",
                                 "Amount: €15,000")), TODAY)
        self.assertEqual(panel.status, analyze.STATUS_CONTESTED)
        self.assertEqual(fact(panel, "overdue_count").number, 1.0)
        self.assertTrue(fact(panel, "coverage").known)


WON_TEMPLATE = """
### Acme — won 2026-08-15 — $18,000 — strategy sprint

Proposal sent: 2026-08-01

### Northwind — won 2026-08-20 — $16,000 — strategy sprint

Proposal sent: 2026-08-02

### Delta — won 2026-08-28 — $21,000 — strategy sprint

Proposal sent: 2026-08-10
"""


def counted_from(line):
    return edit("goals.md", "Downside cap: 40 founder hours",
                "Counted from: %s\n\nDownside cap: 40 founder hours" % line)


def with_won(line, won=WON_TEMPLATE):
    def mutate(home):
        counted_from(line)(home)
        text = (home / "pipeline.md").read_text(encoding="utf-8")
        head, rest = text.split("## Won", 1)
        (home / "pipeline.md").write_text(
            head + "## Won\n" + won + "\n## Dead" + rest.split("## Dead", 1)[1],
            encoding="utf-8")
    return mutate


class TestCountedFromCountsOnlyWhatIsWritten(unittest.TestCase):
    """`Counted from:` decides a bet, so a count it cannot make is None.

    The bar the founder judges a bet against is drawn from this number. A zero
    drawn because an amount could not be read is the same sentence as a zero
    the company earned, and only one of them is true.
    """

    def test_won_entries_are_counted_by_the_amount_in_their_heading(self):
        _, bets, _ = analyze.build_bets(
            example_sources(with_won("pipeline.md ## Won | amount >= 15000 "
                                     "| target 3")), TODAY)
        self.assertEqual(bets[0].progress, 3.0)

    def test_an_unreadable_amount_refuses_the_count_instead_of_scoring_zero(self):
        won = WON_TEMPLATE.replace("won 2026-08-28 — $21,000",
                                   "won 2026-08-28 — price withheld")
        _, bets, _ = analyze.build_bets(
            example_sources(with_won("pipeline.md ## Won | amount >= 15000 "
                                     "| target 3", won)), TODAY)
        self.assertIsNone(bets[0].progress)

    def test_a_directory_counted_bet_counts_the_members_that_report_sent(self):
        def mutate(home):
            counted_from("drafts/proposals/ ## Sent | target 3")(home)
            write(home, "drafts/proposals/acme.md",
                  "# Acme\n\n## Draft\n\nBody.\n\n## Provenance\n\nCall.\n\n"
                  "## Sent\n\nSent by email on 2026-07-16.\n")
            write(home, "drafts/proposals/northwind.md",
                  "# Northwind\n\n## Draft\n\nBody.\n\n## Provenance\n\nCall.\n\n"
                  "## Sent\n\nNone.\n")
        _, bets, _ = analyze.build_bets(example_sources(mutate), TODAY)
        self.assertEqual(bets[0].progress, 1.0)
        self.assertEqual(bets[0].target, 3.0)

    def test_a_directory_that_was_never_created_is_not_a_zero(self):
        _, bets, _ = analyze.build_bets(
            example_sources(counted_from("drafts/proposals/ ## Sent | target 3")),
            TODAY)
        self.assertIsNone(bets[0].progress)

    def test_a_directory_that_exists_and_holds_nothing_counts_zero(self):
        def mutate(home):
            counted_from("drafts/proposals/ ## Sent | target 3")(home)
            (home / "drafts" / "proposals").mkdir(parents=True)
        _, bets, _ = analyze.build_bets(example_sources(mutate), TODAY)
        self.assertEqual(bets[0].progress, 0.0)

    def test_an_unreadable_kill_counted_from_is_reported_as_a_finding(self):
        found = findings_about(
            example_sources(edit("goals.md", "Downside cap: 40 founder hours",
                                 "Kill counted from: the dead deals\n\n"
                                 "Downside cap: 40 founder hours")),
            "counted-from-unreadable")
        self.assertEqual(len(found), 1)
        self.assertIn("Kill counted from", found[0].detail)

    def test_a_filtered_directory_count_does_not_read_money_out_of_prose(self):
        def mutate(home):
            counted_from("drafts/proposals/ ## Sent | amount >= 10000 "
                         "| target 3")(home)
            write(home, "drafts/proposals/acme.md",
                  "# Acme\n\n## Sent\n\nHi Maya, thanks for the call on 16 July. "
                  "Here is the sprint, fixed at $18,000.\n")
            write(home, "drafts/proposals/northwind.md",
                  "# Northwind\n\n## Sent\n\n2026-07-19 — sent by email.\n"
                  "Price: $15,000 fixed.\n")
        _, bets, _ = analyze.build_bets(example_sources(mutate), TODAY)
        self.assertIsNone(bets[0].progress)

    def test_an_unreadable_counted_from_is_reported_as_a_finding(self):
        found = findings_about(
            example_sources(counted_from("the won deals")),
            "counted-from-unreadable")
        self.assertEqual(len(found), 1)
        self.assertIn("goals.md", found[0].cite)


QUARTERLY_GOALS = """# Q3 2026

## Bets

Proposed: finish the Acme proposal scope — bet: B1

### Bet 1: Make the premium sprint the default offer

Outcome: signed sprints reaches 3 by 2026-09-30

Cost: 40 h + $2,000

Kill if: qualified proposals is below 2 on 2026-08-31
"""


class TestBetsReadTheVocabularyTheSkillsWrite(unittest.TestCase):
    """goals.md is written by quarterly-planning, so its labels are the contract.

    Reading a vocabulary no skill emits renders every bet on a real workspace
    as blank, and blames the founder for a missing field in the instruction it
    prints.
    """

    def setUp(self):
        def mutate(home):
            (home / "goals.md").write_text(QUARTERLY_GOALS, encoding="utf-8")
        self.panel, self.bets, _ = analyze.build_bets(
            example_sources(mutate), TODAY)

    def test_the_bet_id_is_the_key_the_week_plan_serves(self):
        self.assertEqual(self.bets[0].key, "B1")
        self.assertEqual(self.bets[0].name,
                         "Make the premium sprint the default offer")

    def test_outcome_is_the_threshold(self):
        self.assertEqual(self.bets[0].threshold,
                         "signed sprints reaches 3 by 2026-09-30")

    def test_kill_if_is_the_kill_condition_and_carries_its_date(self):
        self.assertEqual(self.bets[0].kill,
                         "qualified proposals is below 2 on 2026-08-31")
        self.assertEqual(self.bets[0].kill_date, date(2026, 8, 31))

    def test_start_date_opens_the_window(self):
        def mutate(home):
            (home / "goals.md").write_text(
                QUARTERLY_GOALS + "\nStart date: 2026-07-01\n\n"
                "Judgment date: 2026-09-30\n", encoding="utf-8")
        _, bets, _ = analyze.build_bets(example_sources(mutate), TODAY)
        self.assertEqual(bets[0].opened, date(2026, 7, 1))
        self.assertFalse(bets[0].elapsed_assumed)


KILLED = ("Killed: 2026-08-01 — 0 sprints signed against a threshold of 3 "
          "→ capacity to B2")
CONTINUED = ("Continued: 2026-08-01 — 5 signed sprints by 2026-10-31 "
             "(extension 1 of 1)")


class TestBetVerdicts(unittest.TestCase):
    """kill-or-continue writes its verdict into the block and never deletes it.

    So the block staying under `## Bets` is the prescribed post-kill state, and
    a reader that ignores the verdict line reports a company running two bets
    on a day it was running one.
    """

    def test_a_killed_bet_is_not_open(self):
        panel, bets, _ = analyze.build_bets(
            example_sources(edit("goals.md", "Judgment date: 2026-09-30",
                                 "Judgment date: 2026-09-30\n\n" + KILLED)),
            date(2026, 8, 20))
        self.assertEqual(fact(panel, "bets_open").number, 1.0)
        self.assertEqual(bets[0].verdict, "killed")

    def test_a_killed_bet_has_no_countdown_left_to_run(self):
        panel, _, _ = analyze.build_bets(
            example_sources(edit("goals.md", "Judgment date: 2026-09-30",
                                 "Judgment date: 2026-09-30\n\n" + KILLED)),
            date(2026, 8, 20))
        keys = [item.key for item in panel.facts]
        self.assertNotIn("B1.days_to_judgment", keys)
        self.assertNotIn("B1.days_to_kill", keys)
        self.assertIn("B1.verdict", keys)

    def test_a_continued_bet_counts_down_to_its_new_judgment_date(self):
        panel, bets, _ = analyze.build_bets(
            example_sources(edit("goals.md", "Judgment date: 2026-09-30",
                                 "Judgment date: 2026-09-30\n\n" + CONTINUED)),
            date(2026, 8, 20))
        self.assertEqual(bets[0].judgment, date(2026, 10, 31))
        self.assertEqual(fact(panel, "B1.days_to_judgment").number, 72.0)


def signal_line(replacement):
    return edit("metrics.md",
                "- Proposals sent — source: drafts/proposals/ ## Sent — 0 — "
                "normal 1-2 — last four: 1, 1, 0, 0",
                replacement)


class TestSignalsReadEveryLineOrSayTheyCouldNot(unittest.TestCase):
    """signal-check's own template ships a single-value normal.

    A line the grammar rejects used to vanish while `signal_count` stayed a
    confident number, so the week's one below-normal signal was the one the
    page did not mention.
    """

    def test_a_single_value_normal_is_a_range_of_one(self):
        panel, signals, _ = analyze.build_signals(example_sources(signal_line(
            "- Proposals sent — source: drafts/proposals/ ## Sent — 0 — "
            "normal 1 — last four: 1, 1, 0, 0")))
        self.assertEqual(fact(panel, "signal_count").number, 3.0)
        sent = [s for s in signals if s.name == "Proposals sent"][0]
        self.assertEqual((sent.low, sent.high), (1.0, 1.0))
        self.assertEqual(sent.state, "below")

    def test_a_line_the_grammar_cannot_read_is_not_silently_dropped(self):
        panel, signals, _ = analyze.build_signals(example_sources(signal_line(
            "- Proposals sent — we sent one this week")))
        self.assertEqual(len(signals), 2)
        self.assertFalse(fact(panel, "signal_count").known)

    def test_an_unreadable_signal_line_is_reported_as_a_finding(self):
        found = findings_about(
            example_sources(signal_line(
                "- Proposals sent — we sent one this week")),
            "signal-unreadable")
        self.assertEqual(len(found), 1)
        self.assertIn("metrics.md", found[0].cite)

    def test_a_signal_with_no_range_yet_is_read_not_refused(self):
        """signal-check rule 5 mandates this form under four readings."""
        panel, signals, findings = analyze.build_signals(
            example_sources(signal_line(
                "- Proposals sent — source: drafts/proposals/ ## Sent — 0 — "
                "range: not yet — last four: 1, 0")))
        self.assertEqual(findings, ())
        self.assertEqual(fact(panel, "signal_count").number, 3.0)
        sent = [s for s in signals if s.name == "Proposals sent"][0]
        self.assertEqual((sent.low, sent.high), (None, None))
        self.assertEqual(sent.series, (1.0, 0.0))

    def test_a_signal_with_no_range_is_neither_below_nor_above_it(self):
        _, signals, _ = analyze.build_signals(example_sources(signal_line(
            "- Proposals sent — source: drafts/proposals/ ## Sent — 0 — "
            "range: not yet")))
        sent = [s for s in signals if s.name == "Proposals sent"][0]
        self.assertEqual(sent.state, "unknown")
        self.assertEqual(sent.value, 0.0)


class TestCashReadsTheLabelsTheCadencesWrite(unittest.TestCase):
    """runway-forecast and revenue-review own these blocks and name their fields.

    Neither writes `Runway:` or `Closed:`, so a reader that only knows those
    two labels reports "not recorded" for a file that records both.
    """

    def test_runway_is_read_from_the_forecast_label(self):
        panel = analyze.build_cash(example_sources(edit(
            "metrics.md",
            "Runway: 9.7 months at current personal and business burn; "
            "pipeline excluded.",
            "Runway, zero new revenue: 9.7 months — cash zero on 2027-04-20")),
            TODAY)
        self.assertEqual(fact(panel, "runway_months").number, 9.7)

    def test_close_age_falls_back_to_the_month_in_the_heading(self):
        panel = analyze.build_cash(example_sources(edit(
            "metrics.md", "Closed: 2026-07-01\n\n", "")), TODAY)
        age = fact(panel, "close_age_days")
        self.assertTrue(age.known)
        self.assertEqual(age.number, 20.0)

    def test_a_close_age_read_from_the_month_names_what_it_measured(self):
        """One cell, two measurements, and only one of them is the close.

        `Closed:` is the day the close was performed; the heading names only
        the month it covers, and the two can be weeks apart. The number is the
        best the file supports either way, so the page says which it is.
        """
        from_month = analyze.build_cash(example_sources(edit(
            "metrics.md", "Closed: 2026-07-01\n\n", "")), TODAY)
        self.assertEqual(fact(from_month, "close_age_days").display,
                         "20 days from month end")
        performed = analyze.build_cash(example_sources(), TODAY)
        self.assertEqual(fact(performed, "close_age_days").display, "19 days")

    def test_a_close_with_no_date_anywhere_stays_unknown(self):
        def strip(home):
            edit("metrics.md", "Closed: 2026-07-01\n\n", "")(home)
            edit("metrics.md", "## Close — 2026-06", "## Close")(home)
        panel = analyze.build_cash(example_sources(strip), TODAY)
        self.assertFalse(fact(panel, "close_age_days").known)


class TestBriefCountsWhatTheBriefWrote(unittest.TestCase):
    """daily-brief writes `## Triage` as one prose line, never as a list.

    Counting entries in it therefore reported 0 for every brief ever written,
    and reported it as a number the founder could act on.
    """

    def test_triage_reads_the_handed_over_count(self):
        panel = analyze.build_brief(example_sources(edit(
            "reviews/daily/2026-07-20.md", "None required.",
            "+7 items handed to triage")), TODAY)
        self.assertEqual(fact(panel, "triage_count").number, 7.0)

    def test_triage_declared_empty_is_still_zero(self):
        panel = analyze.build_brief(example_sources(), TODAY)
        self.assertEqual(fact(panel, "triage_count").number, 0.0)

    def test_a_triage_line_that_says_neither_is_unknown_not_zero(self):
        panel = analyze.build_brief(example_sources(edit(
            "reviews/daily/2026-07-20.md", "None required.",
            "handed a few things over")), TODAY)
        self.assertFalse(fact(panel, "triage_count").known)

    def test_rotting_counts_the_items_the_brief_did_not_print(self):
        panel = analyze.build_brief(example_sources(edit(
            "reviews/daily/2026-07-20.md",
            "- Northwind reference follow-up — 3 days overdue",
            "- Northwind reference follow-up — 3 days overdue\n"
            "- Acme scope sign-off — 5 days overdue\n"
            "- Delta invoice — 9 days overdue\n"
            "+7 more — handed to triage")), TODAY)
        self.assertEqual(fact(panel, "rotting_count").number, 10.0)


class TestIntegrityCoversDirectories(unittest.TestCase):
    """Eleven of the twenty-five declared paths are directories.

    Deriving findings from flat files alone means a member file that lost a
    declared section can never appear in the Integrity view, which is the one
    place the page promises to report exactly that.
    """

    def test_a_member_missing_a_declared_section_is_reported(self):
        found = findings_about(
            example_sources(edit("reviews/daily/2026-07-20.md",
                                 "## Triage\n\nNone required.\n", "")),
            "section-missing")
        self.assertIn("reviews/daily/2026-07-20.md ## Triage",
                      [item.cite for item in found])

    def test_members_are_listed_in_the_source_inventory(self):
        facts = analyze.build_facts(example_sources(), TODAY, "generated",
                                    contracts.load_thresholds())
        self.assertIn("reviews/daily/2026-07-20.md",
                      [item["path"] for item in facts.sources])

    def test_a_member_is_listed_without_being_a_declared_path(self):
        """The inventory holds both; only the declared set is countable.

        snapshots.csv counts the declared paths, so a member that entered the
        inventory unmarked would make files_present grow with the archive and
        the series stop being comparable to its own history.
        """
        facts = analyze.build_facts(example_sources(), TODAY, "generated",
                                    contracts.load_thresholds())
        rows = {item["path"]: item for item in facts.sources}
        self.assertTrue(rows["goals.md"]["declared"])
        self.assertFalse(rows["reviews/daily/2026-07-20.md"]["declared"])

    def test_a_declared_directory_that_was_never_created_is_reported_absent(self):
        found = findings_about(example_sources(), "file-absent")
        self.assertIn("drafts/proposals/ is declared but not present",
                      [item.detail for item in found])

    def test_a_declared_directory_that_exists_is_not_reported_absent(self):
        found = findings_about(example_sources(), "file-absent")
        self.assertNotIn("decisions/ is declared but not present",
                         [item.detail for item in found])


class TestProseIsNotZero(unittest.TestCase):
    """A section the reader cannot list is not a section holding nothing.

    Every panel that counts items shared one bug: `split_entries` answered a
    prose section and a `None.` section identically, so the page published a
    confident zero over a citation to the file that named the items. These pin
    the distinction at the panel, which is where the founder actually reads it.
    """

    @staticmethod
    def _prose(path, heading, sentence):
        def mutate(home):
            text = (home / path).read_text(encoding="utf-8")
            head, marker, rest = text.partition(heading)
            body, sep, tail = rest.partition("\n## ")
            (home / path).write_text(
                head + marker + "\n\n" + sentence + "\n" + sep + tail,
                encoding="utf-8")
        return mutate

    def test_a_pipeline_written_as_prose_is_not_zero_deals(self):
        sources = example_sources(self._prose(
            "pipeline.md", "## Live",
            "Acme and Northwind are both live, proposals out with each."))
        panel = analyze.build_pipeline(sources, TODAY)
        by_key = {fact.key: fact for fact in panel.facts}
        for key in ("live_count", "live_amount", "overdue_count"):
            with self.subTest(key=key):
                self.assertFalse(by_key[key].known)
                self.assertIsNone(by_key[key].number)

    def test_a_queue_written_as_prose_is_not_zero_items(self):
        sources = example_sources(self._prose(
            "queue.md", "## Doing",
            "Finishing the Acme sprint and the Northwind proposal."))
        panel = analyze.build_queue(sources, contracts.load_thresholds()["queue"])
        doing = {fact.key: fact for fact in panel.facts}["doing"]
        self.assertFalse(doing.known)
        self.assertIsNone(doing.number)

    def test_bets_written_as_prose_are_not_zero_bets(self):
        sources = example_sources(self._prose(
            "goals.md", "## Bets",
            "We are betting on the premium sprint and on partner referrals."))
        panel, bets, findings = analyze.build_bets(sources, TODAY)
        opened = {fact.key: fact for fact in panel.facts}["bets_open"]
        self.assertFalse(opened.known)
        self.assertEqual(bets, ())
        self.assertTrue(findings)

    def test_signals_written_as_prose_are_not_zero_signals(self):
        sources = example_sources(self._prose(
            "metrics.md", "## Signals",
            "Proposals sent and calls booked both moved this week."))
        panel, signals, findings = analyze.build_signals(sources)
        count = {fact.key: fact for fact in panel.facts}["signal_count"]
        self.assertFalse(count.known)
        self.assertTrue(findings)

    def test_a_declared_empty_section_is_still_a_real_zero(self):
        sources = example_sources(self._prose("queue.md", "## Doing", "None."))
        panel = analyze.build_queue(sources, contracts.load_thresholds()["queue"])
        doing = {fact.key: fact for fact in panel.facts}["doing"]
        self.assertTrue(doing.known)
        self.assertEqual(doing.number, 0.0)


if __name__ == "__main__":
    unittest.main()
