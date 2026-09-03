"""Theme correctness, checked mechanically because it fails silently.

The classic artifact bug is a colour whose only definition sits inside a media
query or a `[data-theme]` block: the viewer whose OS setting is "system" gets one
theme's text on the other theme's background, and nothing errors. These tests
assert every token is defined in all three states.
"""
import base64
import hashlib
import importlib
import importlib.util
import re
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace


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

    def test_the_gap_between_segments_costs_no_width(self):
        # `.fill` does not shrink, so segments whose widths sum to 100% fill the
        # track exactly. A flex `gap` would push that past the box and
        # `overflow: hidden` would clip the tail, drawing a week that exactly
        # fits as one that falls short. Separators have to be painted, not laid
        # out.
        track = re.search(r"\.track\s*\{([^}]*)\}", theme.STYLESHEET).group(1)
        self.assertNotRegex(track, r"gap:\s*(?!0)")

    def test_track_segments_do_not_shrink_to_fit(self):
        # `.track` is a flex row. Without this, segments that sum past 100% are
        # rescaled by the browser until they fit, so an over-committed week
        # draws pixel-identical to a week that is exactly full and every
        # segment's width stops matching the hours it stands for.
        rule = re.search(r"\.fill\s*\{([^}]*)\}", theme.STYLESHEET).group(1)
        self.assertIn("flex-shrink: 0", rule)

    def test_bet_hues_are_the_validated_pairs(self):
        self.assertEqual(theme.TOKENS["light"]["--bet-1"], "#0a6e9a")
        self.assertEqual(theme.TOKENS["light"]["--bet-2"], "#6d7c15")
        self.assertEqual(theme.TOKENS["dark"]["--bet-1"], "#2f9dcc")
        self.assertEqual(theme.TOKENS["dark"]["--bet-2"], "#82992a")


def relative_luminance(colour):
    channels = [int(colour[index:index + 2], 16) / 255
                for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045
              else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(foreground, background):
    first = relative_luminance(foreground)
    second = relative_luminance(background)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


class TestContrast(unittest.TestCase):
    """The ink tokens against the two surfaces the page actually paints.

    `--ink-faint` colours the citation line and every "not recorded" value —
    the two pieces of text this package argues the reader must be able to read.
    Checked mechanically because a contrast failure looks fine to whoever picked
    the colour on the monitor they picked it on.
    """

    AA_NORMAL = 4.5

    def test_every_ink_token_meets_aa_on_both_surfaces(self):
        for palette in ("light", "dark"):
            tokens = theme.TOKENS[palette]
            for ink in ("--ink", "--ink-soft", "--ink-faint"):
                for ground in ("--surface", "--paper"):
                    ratio = contrast_ratio(tokens[ink], tokens[ground])
                    self.assertGreaterEqual(
                        round(ratio, 2), self.AA_NORMAL,
                        "%s %s on %s is %.2f:1" % (palette, ink, ground, ratio))


class TestPolicy(unittest.TestCase):
    """The page's own script is named by hash, so nothing else may run."""

    def test_the_policy_does_not_permit_arbitrary_inline_script(self):
        script_src = re.search(r"script-src ([^;]+);", theme.CSP).group(1)
        self.assertNotIn("unsafe-inline", script_src)

    def test_the_hash_in_the_policy_is_the_script_the_page_emits(self):
        html = build_example_page()
        script = re.search(r"<script>(.*?)</script>", html, re.S).group(1)
        digest = base64.b64encode(
            hashlib.sha256(script.encode("utf-8")).digest()).decode("ascii")
        self.assertIn("'sha256-%s'" % digest, html)


EXAMPLE = REPO_ROOT / "examples" / "studio-north"
GOLDEN = REPO_ROOT / "tests" / "fixtures" / "dashboard" / "today.golden.html"
TODAY = date(2026, 7, 20)


def build_payload(slug="studio-north", mutate=None):
    contracts = load_dashboard("contracts")
    collect = load_dashboard("collect")
    analyze = load_dashboard("analyze")
    home = Path(tempfile.mkdtemp()) / "founder-os"
    shutil.copytree(EXAMPLE, home)
    if mutate is not None:
        mutate(home)
    sources = collect.collect(home, contracts.load_ownership(), slug=slug)
    facts = analyze.build_facts(
        sources, TODAY, "2026-07-20T09:04:12+01:00", contracts.load_thresholds())
    return contracts.Business(slug=slug, home=home, status="active"), facts


def rename(name):
    def mutate(home):
        charter = (home / "charter.md").read_text(encoding="utf-8")
        (home / "charter.md").write_text(
            charter.replace("Studio North is a", "%s is a" % name, 1),
            encoding="utf-8")
    return mutate


def views(html):
    """slug -> whether the section is hidden, in document order."""
    return [(match.group(1), bool(match.group(2))) for match in re.finditer(
        r'<section class="view" id="business-([^"]+)"( hidden)?>', html)]


def build_example_page():
    render = load_dashboard("render")
    return render.render([build_payload()],
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


class TestBusinessSelection(unittest.TestCase):
    """`active_slug` is the whole point of the CLI's positional argument.

    The failure it guards is silent: the founder asks for one business and is
    shown another company's numbers under that request, with no error anywhere.
    """

    def setUp(self):
        self.render = load_dashboard("render")
        self.pages = [build_payload("acme", rename("Acme Co")),
                      build_payload("zeta", rename("Zeta Works"))]

    def page(self, active_slug, **kwargs):
        return self.render.render(self.pages, generated="g",
                                  active_slug=active_slug, **kwargs)

    def test_the_requested_business_is_the_visible_view(self):
        html = self.page("zeta")
        self.assertEqual(views(html), [("acme", True), ("zeta", False)])

    def test_the_title_and_masthead_name_the_requested_business(self):
        html = self.page("zeta")
        self.assertIn("<title>Zeta Works — Founder OS</title>", html)
        self.assertNotIn("Acme Co — Founder OS", html)

    def test_a_slug_matching_nothing_falls_back_to_the_first_business(self):
        html = self.page("nordwind")
        self.assertEqual(views(html), [("acme", False), ("zeta", True)])

    def test_every_business_is_reachable_from_a_switcher(self):
        html = self.page("zeta")
        controls = re.findall(r'data-business="([^"]+)"', html)
        self.assertEqual(sorted(controls), ["acme", "zeta"])
        script = re.search(r"<script>(.*?)</script>", html, re.S).group(1)
        self.assertIn("data-business", script)
        self.assertIn("hidden", script)

    def test_the_handler_shows_the_view_the_button_names(self):
        """No engine here runs the script, so the logic is read instead.

        Substring checks for "data-business" and "hidden" pass against a
        handler with its test inverted, which would hide the business the
        founder clicked and show every other one.
        """
        script = re.search(r"<script>(.*?)</script>", self.page("zeta"),
                           re.S).group(1)
        self.assertIn("views[i].hidden=views[i].id!==('business-'+slug);",
                      script)
        self.assertIn(
            "buttons[j].getAttribute('data-business')===slug?'true':'false'",
            script)

    def test_the_switcher_marks_the_requested_business_as_selected(self):
        html = self.page("zeta")
        # Matched per button rather than by attribute order: the order is the
        # renderer's business, and pinning it here failed the moment a third
        # attribute was added between these two.
        selected = [
            re.search(r'data-business="([^"]+)"', button).group(1)
            for button in re.findall(r"<button\b[^>]*>", html)
            if 'aria-selected="true"' in button and "data-business=" in button]
        self.assertEqual(selected, ["zeta"])

    def test_the_switcher_carries_each_business_name_for_the_masthead(self):
        """The name travels with the button or the header cannot follow it.

        The script renames the masthead and the tab title on a switch; without
        `data-name` it has nothing to rename them to, and the page shows one
        company's figures under another company's name.
        """
        html = self.page("zeta")
        buttons = [button for button in re.findall(r"<button\b[^>]*>", html)
                   if "data-business=" in button]
        self.assertTrue(buttons)
        for button in buttons:
            with self.subTest(button=button):
                self.assertRegex(button, r'data-name="[^"]+"')
        self.assertIn('<span id="business-name">', html)

    def test_a_single_business_page_carries_no_switcher(self):
        html = self.render.render([self.pages[0]], generated="g",
                                  active_slug="acme")
        self.assertNotIn('<nav class="switch"', html)
        self.assertNotIn('data-business="', html)
        self.assertEqual(views(html), [("acme", False)])


class TestPausedDisclosure(unittest.TestCase):
    """The masthead line that says a business was left out of the page.

    Nothing else on the page discloses it, so if this regresses the page reads
    as the whole company while omitting part of it.
    """

    def setUp(self):
        self.render = load_dashboard("render")
        self.pages = [build_payload("acme", rename("Acme Co"))]

    def page(self, paused):
        return self.render.render(self.pages, generated="g", active_slug="acme",
                                  paused=paused)

    def test_one_paused_business_is_disclosed(self):
        self.assertIn("1 paused business excluded", self.page(1))

    def test_two_paused_businesses_are_disclosed_in_the_plural(self):
        self.assertIn("2 paused businesses excluded", self.page(2))

    def test_nothing_is_claimed_when_none_were_paused(self):
        self.assertNotIn("paused", self.page(0))


def _cell(html, label):
    """The value cell of the `label` row in any "Show the numbers" table."""
    match = re.search(r"<tr><td>%s</td>(.*?)</tr>" % re.escape(label), html)
    return None if match is None else match.group(1)


class TestCashTable(unittest.TestCase):
    """The cash table prints values, not the markup a value is wrapped in."""

    def test_an_unreadable_cash_figure_reads_as_words_in_the_table(self):
        def strip(home):
            (home / "metrics.md").write_text("# Metrics\n", encoding="utf-8")
        render = load_dashboard("render")
        html = render.render([build_payload("x", strip)], generated="g",
                             active_slug="x")
        self.assertNotIn("&lt;span", html)
        # Marked, not merely printed: an unreadable figure has to look
        # different from a figure, or the reader takes "not recorded" for a
        # measurement the same way a zero would be taken for one.
        self.assertEqual(
            _cell(html, "Runway (months)"),
            '<td><span class="unknown">not recorded</span></td>')

    def test_a_reason_the_workspace_gives_is_marked_as_not_a_figure(self):
        analyze = load_dashboard("analyze")
        render = load_dashboard("render")
        cite = "metrics.md ## Close"
        panel = analyze.Panel(
            id="cash", title="Cash and rate", status=analyze.STATUS_OK,
            facts=(analyze.unknown("cash_on_hand", cite,
                                   "not calculated this month"),),
            citations=(cite,))
        html = render._cash(SimpleNamespace(panels={"cash": panel}, details={}))
        self.assertEqual(
            _cell(html, "Cash on hand"),
            '<td><span class="unknown">not calculated this month</span></td>')

    def test_an_ampersand_in_a_cash_value_is_escaped_exactly_once(self):
        # Built from a Panel rather than a workspace so the assertion is about
        # the table's escaping and nothing else the parser might decide.
        analyze = load_dashboard("analyze")
        render = load_dashboard("render")
        cite = "metrics.md ## Close"
        panel = analyze.Panel(
            id="cash", title="Cash and rate", status=analyze.STATUS_OK,
            facts=(analyze.number_fact("booked", 31000.0,
                                       "$31,000 for Smith & Sons", cite),),
            citations=(cite,))
        html = render._cash(SimpleNamespace(panels={"cash": panel}, details={}))
        self.assertNotIn("&amp;amp;", html)
        self.assertEqual(_cell(html, "Booked"), "<td>$31,000 for Smith &amp; Sons</td>")


class TestContestedPipeline(unittest.TestCase):
    """Two currencies are never summed, so the page must show both readings.

    In this state the panel's own facts already say "not recorded"; without the
    contested block the page reports a measured pipeline as unmeasured while the
    workspace holds two figures.
    """

    def setUp(self):
        def mix(home):
            text = (home / "pipeline.md").read_text(encoding="utf-8")
            (home / "pipeline.md").write_text(
                text.replace("Amount: $15,000 [VALIDATE]", "Amount: €15,000", 1),
                encoding="utf-8")
        render = load_dashboard("render")
        self.business, self.facts = build_payload("x", mix)
        self.html = render.render([(self.business, self.facts)], generated="g",
                                  active_slug="x")

    def test_both_readings_are_on_the_page(self):
        self.assertIn("Two readings disagree", self.html)
        self.assertIn("$18,000", self.html)
        self.assertIn("€15,000", self.html)

    def test_the_field_that_would_settle_it_is_named(self):
        settle = self.facts.panels["pipeline"].settle_with
        self.assertTrue(settle)
        self.assertIn(settle, self.html)


class TestBetMeter(unittest.TestCase):
    """A bet that declares `Counted from:` gets a meter and shows its target."""

    def setUp(self):
        def counted(home):
            text = (home / "goals.md").read_text(encoding="utf-8")
            (home / "goals.md").write_text(
                text.replace(
                    "Judgment date: 2026-09-30",
                    "Judgment date: 2026-09-30\n\nCounted from: pipeline.md "
                    "## Live | amount >= 15000 | target 3", 1),
                encoding="utf-8")
        render = load_dashboard("render")
        self.business, self.facts = build_payload("x", counted)
        self.html = render.render([(self.business, self.facts)], generated="g",
                                  active_slug="x")

    def test_the_workspace_really_produces_a_counted_bet(self):
        bet = self.facts.details["bets"][0]
        self.assertEqual((bet.progress, bet.target), (2.0, 3.0))

    def test_the_meter_is_drawn_at_the_counted_fraction(self):
        self.assertIn("2 of 3", self.html)
        self.assertIn("width:66.67%", self.html.replace(" ", ""))

    def test_the_target_is_printed_beside_the_count(self):
        self.assertIn("<th>Target</th>", self.html)
        self.assertIn("<td>2</td><td>3</td>", self.html)


class TestJudgedBets(unittest.TestCase):
    """A bet that has been judged must not read as one still running.

    `kill-or-continue` writes the verdict into the block and never deletes it,
    so the verdict line is the workspace's record that the bet is over. With no
    countdown fact left to print, the card fell through to "Judged in not
    recorded" — this module's sentence for a judgment date nobody wrote — about
    a bet whose goals.md records both the date and the verdict.
    """

    KILLED = ("Killed: 2026-08-01 — 0 sprints signed against a threshold of 3 "
              "→ capacity to B2")

    def page(self, verdict):
        def judged(home):
            text = (home / "goals.md").read_text(encoding="utf-8")
            (home / "goals.md").write_text(
                text.replace("Judgment date: 2026-09-30",
                             "Judgment date: 2026-09-30\n\n" + verdict, 1),
                encoding="utf-8")
        render = load_dashboard("render")
        return render.render([build_payload("x", judged)], generated="g",
                             active_slug="x")

    def test_a_killed_bet_states_the_verdict_the_workspace_recorded(self):
        html = self.page(self.KILLED)
        self.assertIn("capacity to B2", html)

    def test_a_killed_bet_does_not_claim_its_judgment_is_unrecorded(self):
        html = self.page(self.KILLED)
        self.assertNotIn('Judged in <span class="unknown">not recorded</span>',
                         html)

    def test_the_verdict_reaches_the_numbers_table_too(self):
        html = self.page(self.KILLED)
        self.assertIn("<th>Verdict</th>", html)
        self.assertIn("<td>killed</td>", html)

    def test_a_bet_with_no_verdict_still_counts_down(self):
        html = self.page("Cost: 40 h")
        self.assertIn("Judged in 72 days", html)


class TestBetWindow(unittest.TestCase):
    """The instruction has to name a field a skill in this package writes."""

    def test_the_missing_window_names_the_field_the_scaffold_writes(self):
        html = build_example_page()
        self.assertIn("window not recorded", html)
        self.assertIn("Start date:", html)
        self.assertNotIn("Opened:", html)


class TestBetTargetCell(unittest.TestCase):
    """A target recorded as zero is a number, not a blank."""

    def test_a_target_the_workspace_records_as_zero_prints_as_zero(self):
        def counted(home):
            text = (home / "goals.md").read_text(encoding="utf-8")
            (home / "goals.md").write_text(
                text.replace(
                    "Judgment date: 2026-09-30",
                    "Judgment date: 2026-09-30\n\nCounted from: pipeline.md "
                    "## Live | amount >= 15000 | target 0", 1),
                encoding="utf-8")
        render = load_dashboard("render")
        business, facts = build_payload("x", counted)
        self.assertEqual((facts.details["bets"][0].progress,
                          facts.details["bets"][0].target), (2.0, 0.0))
        html = render.render([(business, facts)], generated="g", active_slug="x")
        row = re.search(r"<tr><td>B1</td>.*?</tr>", html).group(0)
        self.assertIn("<td>2</td><td>0</td>", row)


class TestBandlessSignal(unittest.TestCase):
    """`range: not yet` is signal-check's own form under four readings."""

    def setUp(self):
        def young(home):
            text = (home / "metrics.md").read_text(encoding="utf-8")
            (home / "metrics.md").write_text(
                text.replace(
                    "- Proposals sent — source: drafts/proposals/ ## Sent — 0 "
                    "— normal 1-2 — last four: 1, 1, 0, 0",
                    "- Proposals sent — source: drafts/proposals/ ## Sent — 0 "
                    "— range: not yet — last four: 1, 0", 1),
                encoding="utf-8")
        render = load_dashboard("render")
        self.html = render.render([build_payload("x", young)], generated="g",
                                  active_slug="x")

    def test_the_signal_is_on_the_page(self):
        self.assertIn("Proposals sent", self.html)

    def test_the_band_reads_as_words_not_as_a_range(self):
        table = re.search(r"<th>Signal</th>.*?</table>", self.html, re.S).group(0)
        row = re.search(r"<tr><td>Proposals sent</td>.*?</tr>", table).group(0)
        self.assertIn("not recorded", row)
        self.assertNotIn("–", row)


class TestSignalTable(unittest.TestCase):
    """Every cell has to sit under the heading that names it."""

    def setUp(self):
        def widen(home):
            text = (home / "metrics.md").read_text(encoding="utf-8")
            (home / "metrics.md").write_text(
                text.replace("last four: 1, 1, 0, 0",
                             "last four: 1, 1, 0, 0, 2, 3", 1),
                encoding="utf-8")
        render = load_dashboard("render")
        self.html = render.render([build_payload("x", widen)], generated="g",
                                  active_slug="x")
        self.table = re.search(
            r"<th>Signal</th>.*?</table>", self.html, re.S).group(0)

    def test_the_header_covers_the_widest_series(self):
        headers = re.findall(r"<th>([^<]*)</th>", self.table)
        self.assertEqual(headers,
                         ["Signal", "1", "2", "3", "4", "5", "6",
                          "Normal", "Source"])

    def test_every_row_has_one_cell_per_header(self):
        headers = re.findall(r"<th>([^<]*)</th>", self.table)
        rows = re.findall(r"<tr>((?:<td>.*?</td>)+)</tr>", self.table)
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(len(re.findall(r"<td>", row)), len(headers), row)

    def test_the_normal_band_never_lands_under_a_week_number(self):
        headers = re.findall(r"<th>([^<]*)</th>", self.table)
        rows = re.findall(r"<tr>((?:<td>.*?</td>)+)</tr>", self.table)
        for row in rows:
            cells = re.findall(r"<td>(.*?)</td>", row)
            band = cells[headers.index("Normal")]
            self.assertRegex(band, r"^[\d.]+–[\d.]+$")


def over_sentence(html):
    match = re.search(r'<p class="over">(.*?)</p>', html, re.S)
    return None if match is None else match.group(1)


class TestOverCommittedWeek(unittest.TestCase):
    """A week that does not fit must not draw as a week that exactly fits."""

    def setUp(self):
        def overcommit(home):
            text = (home / "week.md").read_text(encoding="utf-8")
            (home / "week.md").write_text(
                text.replace("Available 40h · Committed delivery 24h",
                             "Available 40h · Committed delivery 38h", 1),
                encoding="utf-8")
        render = load_dashboard("render")
        self.html = render.render([build_payload("x", overcommit)],
                                  generated="g", active_slug="x")

    def test_the_overflow_names_the_two_figures_the_workspace_records(self):
        # `## Arithmetic` records the 38h of delivery and the 40h available;
        # `## Blocks` sums to the 9h of planned work. Their total, 47h, is
        # written in no file, so the sentence states the parts, not the total.
        self.assertEqual(
            over_sentence(self.html),
            "Over-committed: 38h delivery plus 9h in blocks against "
            "40h available.")

    def test_no_figure_on_the_page_is_the_unsourced_total(self):
        self.assertNotIn("47h", self.html)

    def test_the_overflow_is_marked_up_so_it_can_be_styled(self):
        self.assertIn('class="over"', self.html)

    def test_a_week_that_fits_claims_no_overflow(self):
        render = load_dashboard("render")
        html = render.render([build_payload("x")], generated="g", active_slug="x")
        self.assertNotIn('class="over"', html)


def exact_fit(home):
    """A week whose hours land exactly on the hours available.

    Delivery 15.5h and blocks of 7.75h and 6.75h sum to the 30h available.
    Each fraction of 30h is inexact in binary, so a warning built by adding
    the fractions up sees 1.0000000000000002 and calls the week over-committed.
    """
    text = (home / "week.md").read_text(encoding="utf-8")
    for before, after in (
            ("Available 40h · Committed delivery 24h · Free 16h "
             "· Planned 9h (56% of free)",
             "Available 30h · Committed delivery 15.5h · Free 14.5h "
             "· Planned 14.5h (100% of free)"),
            ("| Mon | 09:00–11:30 |", "| Mon | 09:00–13:15 |"),
            ("| Wed | 09:00–11:30 |", "| Wed | 09:00–13:45 |"),
            ("| Thu | 10:00–11:00 |", "| Thu | 10:00–11:30 |"),
            ("| Fri | 14:00–15:00 |", "| Fri | 14:00–16:00 |")):
        assert before in text, before
        text = text.replace(before, after, 1)
    (home / "week.md").write_text(text, encoding="utf-8")


class TestExactlyFullWeek(unittest.TestCase):
    """The boundary: a week that fills the hours available is not over it."""

    def setUp(self):
        render = load_dashboard("render")
        self.business, self.facts = build_payload("x", exact_fit)
        self.html = render.render([(self.business, self.facts)], generated="g",
                                  active_slug="x")

    def hours(self, key):
        panel = self.facts.panels["week"]
        return next(item.number for item in panel.facts if item.key == key)

    def test_the_workspace_really_lands_on_the_boundary(self):
        booked = (self.hours("delivery_hours") + self.hours("planned.B1")
                  + self.hours("planned.B2"))
        self.assertEqual(self.hours("available_hours"), 30.0)
        self.assertEqual(booked, 30.0)

    def test_a_week_that_exactly_fits_is_not_called_over_committed(self):
        self.assertIsNone(over_sentence(self.html))


class TestAnUnreadableSignalIsVisible(unittest.TestCase):
    """A measure the analyzer could not read must not vanish from the page.

    It produces no card and no row by construction, so the panel's note is the
    only place the reader can learn a line was dropped. Without it the founder
    sees two signals where metrics.md records three and nothing says so.
    """

    def _page(self, line):
        def mutate(home):
            path = home / "metrics.md"
            text = path.read_text(encoding="utf-8")
            head, marker, rest = text.partition("## Signals")
            body, sep, tail = rest.partition("\n## ")
            path.write_text(head + marker + body.rstrip() + "\n" + line + "\n"
                            + sep + tail, encoding="utf-8")
        render = load_dashboard("render")
        return render.render([build_payload(mutate=mutate)],
                             generated="g", active_slug="studio-north")

    def test_a_line_outside_the_grammar_is_reported_on_the_page(self):
        html = self._page("- Case studies shipped are moving in the right way")
        self.assertIn("could not be read", html)

    def test_a_band_that_will_not_convert_is_reported_not_crashed(self):
        html = self._page(
            "- Cases — source: content.md ## Shipped — 2 — normal 3..5")
        self.assertIn("could not be read", html)


class TestATieredAmountKeepsItsTier(unittest.TestCase):
    """house-rules.md:89 — a VALIDATE figure may be written, carrying its tier.

    The shipped example records Northwind's amount as
    `$15,000 [VALIDATE] (per founder's call note, 2026-07-10 ...)`. The page
    added it into a bare headline total, which is the surface most likely to be
    quoted back at the founder and the one place the stamp cannot be seen.
    """

    def test_the_pipeline_panel_says_part_of_the_total_is_unvalidated(self):
        html = build_example_page()
        self.assertIn("[VALIDATE]", html)
        self.assertIn("counted in this total", html)

    def test_a_workspace_with_no_tiered_amount_carries_no_note(self):
        def mutate(home):
            path = home / "pipeline.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(" [VALIDATE]", ""),
                encoding="utf-8")
        render = load_dashboard("render")
        html = render.render([build_payload(mutate=mutate)], generated="g",
                             active_slug="studio-north")
        self.assertNotIn("[VALIDATE]", html)
        self.assertNotIn("counted in this total", html)


class TestGolden(unittest.TestCase):
    def test_page_matches_the_reviewed_fixture(self):
        self.assertEqual(build_example_page(), GOLDEN.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
