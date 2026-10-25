"""Collection is driven by the ownership map, never by a hardcoded file list.

The bug this prevents: a file is added to `workspace_files:` and its owner starts
writing it, while the dashboard keeps rendering the set of files someone typed
into a Python module months earlier. The last test is the one that matters — a
path added to the map must surface with no dashboard code change at all.
"""
import importlib
import importlib.util
import shutil
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "founder-os"
DASHBOARD = PLUGIN_ROOT / "scripts" / "dashboard"
EXAMPLE = REPO_ROOT / "examples" / "studio-north"


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


class TestCollect(unittest.TestCase):
    def setUp(self):
        self.view = contracts.load_ownership()
        self.home = Path(tempfile.mkdtemp()) / "founder-os"
        shutil.copytree(EXAMPLE, self.home)

    def test_reads_the_sections_the_map_declares(self):
        sources = collect.collect(self.home, self.view, slug="studio-north")
        self.assertIn("Booked: $31,000", sources.section("metrics.md", "## Close"))
        self.assertIn("B1", sources.section("goals.md", "## Bets"))

    def test_business_name_comes_from_the_charter(self):
        sources = collect.collect(self.home, self.view, slug="studio-north")
        self.assertEqual(sources.name, "Studio North")
        self.assertEqual(sources.timezone, "Europe/London")

    def test_absent_file_is_recorded_not_fatal(self):
        (self.home / "network.md").unlink(missing_ok=True)
        sources = collect.collect(self.home, self.view, slug="studio-north")
        self.assertFalse(sources.files["network.md"].exists)
        self.assertIsNone(sources.section("network.md", "## Map"))

    def test_missing_heading_is_listed(self):
        path = self.home / "offer.md"
        path.write_text("# Offer\n\n## ICP\n\nFounder-led B2B.\n", encoding="utf-8")
        sources = collect.collect(self.home, self.view, slug="studio-north")
        self.assertIn("## Pricing", sources.files["offer.md"].missing)

    def test_unreadable_file_is_marked_and_does_not_raise(self):
        path = self.home / "metrics.md"
        path.write_bytes(b"\xff\xfe\x00invalid")
        sources = collect.collect(self.home, self.view, slug="studio-north")
        self.assertFalse(sources.files["metrics.md"].readable)

    def test_directory_members_are_parsed_not_merely_listed(self):
        sources = collect.collect(self.home, self.view, slug="studio-north")
        paths = [member.path for member in sources.members["decisions/"]]
        self.assertIn("decisions/2026-07-18-raised-sprint-floor.md", paths)
        self.assertEqual(len(sources.members["experiments/"]), 2)
        newest = sources.newest_member("reviews/daily/")
        self.assertEqual(newest.path, "reviews/daily/2026-07-20.md")
        self.assertIn("q-0720a", newest.sections["## The one thing"])

    def test_an_undated_member_is_not_the_newest_brief(self):
        (self.home / "reviews" / "daily" / "notes.md").write_text(
            "# Notes\n", encoding="utf-8")
        sources = collect.collect(self.home, self.view, slug="studio-north")
        self.assertEqual(sources.newest_member("reviews/daily/").path,
                         "reviews/daily/2026-07-20.md")

    def test_a_declared_directory_records_whether_it_exists(self):
        """An empty directory and one that was never created are not the same.

        Both carry an empty members tuple, so without this the reader cannot
        tell an honest zero from a path nobody has created yet.
        """
        (self.home / "drafts" / "proposals").mkdir(parents=True)
        sources = collect.collect(self.home, self.view, slug="studio-north")
        self.assertTrue(sources.directories["decisions/"])
        self.assertTrue(sources.directories["drafts/proposals/"])
        self.assertFalse(sources.directories["drafts/outreach/"])
        self.assertEqual(sources.members["drafts/proposals/"], ())

    def test_a_new_map_entry_surfaces_with_no_code_change(self):
        view = replace(
            self.view,
            workspace_files=self.view.workspace_files + ("licences.md",),
            sections=dict(self.view.sections, **{"licences.md": ("## Renewals",)}),
            owners=dict(self.view.owners, **{"licences.md": "ops-engineer"}),
        )
        (self.home / "licences.md").write_text(
            "# Licences\n\n## Renewals\n\nFigma renews 2026-11-01.\n", encoding="utf-8")
        sources = collect.collect(self.home, view, slug="studio-north")
        self.assertIn("Figma", sources.section("licences.md", "## Renewals"))

    def test_a_dated_heading_keeps_its_suffix_beside_the_section_name(self):
        sources = collect.collect(self.home, self.view, slug="studio-north")
        self.assertIsNotNone(sources.section("metrics.md", "## Close"))
        self.assertEqual(sources.heading("metrics.md", "## Close"),
                         "## Close — 2026-06")

    def test_an_undated_heading_reads_back_exactly_as_written(self):
        sources = collect.collect(self.home, self.view, slug="studio-north")
        self.assertEqual(sources.heading("metrics.md", "## Runway"), "## Runway")
        self.assertIsNone(sources.heading("metrics.md", "## Nothing here"))


class TestDeclaredForTheRoot(unittest.TestCase):
    """A business workspace holds workspace_files; the portfolio holds its own.

    Reading the union against a business root reports `portfolio.md` absent on
    every run of every install, which is a defect the page states as a fact
    about the founder's company.
    """

    def setUp(self):
        self.view = contracts.load_ownership()
        self.home = Path(tempfile.mkdtemp()) / "founder-os"
        shutil.copytree(EXAMPLE, self.home)

    def test_a_business_workspace_is_not_asked_for_portfolio_files(self):
        sources = collect.collect(self.home, self.view, slug="studio-north")
        for path in self.view.portfolio_files:
            self.assertNotIn(path, sources.files, path)
        self.assertIn("charter.md", sources.files)


class TestWorkspaceName(unittest.TestCase):
    def _workspace(self, *parts):
        root = Path(tempfile.mkdtemp()).joinpath(*parts)
        root.mkdir(parents=True)
        (root / "charter.md").write_text(
            "# Charter\n\n## Focus\n\nOne thing.\n", encoding="utf-8")
        return root

    def test_a_workspace_is_named_after_itself_not_its_container(self):
        root = self._workspace("founder-os", "why-consulting")
        sources = collect.collect(root, contracts.load_ownership())
        self.assertEqual(sources.name, "why-consulting")

    def test_the_conventional_wrapper_still_names_the_project(self):
        root = self._workspace("studio-north", "founder-os")
        sources = collect.collect(root, contracts.load_ownership())
        self.assertEqual(sources.name, "studio-north")

    def test_the_charter_still_wins_over_the_directory(self):
        root = self._workspace("founder-os", "why-consulting")
        (root / "charter.md").write_text(
            "# Charter\n\n## Business\n\nWhy Consulting is a studio.\n",
            encoding="utf-8")
        sources = collect.collect(root, contracts.load_ownership())
        self.assertEqual(sources.name, "Why Consulting")


class TestOneScannerForWriteReadAndPage(unittest.TestCase):
    """The write check, the gateway's section read and the page agree.

    Three scanners disagreed: the dashboard closed a four-backtick fence on a
    three-backtick line inside it and took `## Close - x` for `## Close`, so the
    page reported sections the write path refuses and missed ones it accepts.
    """

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(PLUGIN_ROOT))
        from mcp.ownership import OwnershipError, OwnershipSchema
        from mcp.safe_io import SafeStateError, SafeStateIO
        cls.OwnershipError = OwnershipError
        cls.SafeStateError = SafeStateError
        cls.schema = OwnershipSchema.load(
            PLUGIN_ROOT / "references" / "ownership.yaml")
        cls.extract = staticmethod(SafeStateIO._extract_h2_sections)
        cls.declared = contracts.load_ownership().sections["metrics.md"]

    def seen(self, text):
        written = self.schema._headings(text)
        found = self.extract(
            text, tuple(heading[3:] for heading in self.declared))
        page, _raw, _title = collect._split_h2(text, self.declared)
        return written, found, page

    def test_fences_hide_the_same_headings_from_all_three(self):
        text = (
            "# Metrics\n\n"
            "## Close — 2026-07\nBooked: 1\n\n"
            "```py`x\n## Runway\n```\n\n"
            "## Runway\nreal\n\n"
            "````md\n```\n## Profitability\n````\n\n"
            "## Profitability\nreal\n\n"
            "~~~\n## Rate\n~~~\n"
            "## Rate\nreal\n\n"
            "## Signals\nreal\n"
        )
        written, found, page = self.seen(text)
        self.assertEqual(written, ["## Close — 2026-07", "## Runway",
                                   "## Profitability", "## Rate", "## Signals"])
        self.schema.validate_document("metrics.md", text)
        self.assertEqual(sorted(found),
                         sorted(heading[3:] for heading in self.declared))
        self.assertEqual(sorted(page), sorted(self.declared))
        for heading in self.declared:
            self.assertEqual(found[heading[3:]], page[heading])
        self.assertTrue(page["## Runway"].startswith("real"))
        self.assertIn("## Profitability\n````", page["## Runway"])

    def test_a_duplicate_heading_is_refused_on_write_and_read_kept_first_on_page(self):
        text = ("## Close — 2026-07\nfirst\n## Runway\nr\n## Profitability\n"
                "p\n## Rate\nr\n## Signals\ns\n## Close — 2026-08\nsecond\n")
        with self.assertRaises(self.OwnershipError):
            self.schema.validate_document("metrics.md", text)
        with self.assertRaises(self.SafeStateError):
            self.extract(text, ("Close",))
        page = collect._split_h2(text, self.declared)[0]
        self.assertEqual(page["## Close"], "first\n")

    def test_only_an_em_dash_separates_a_heading_suffix(self):
        for separator in (" - ", " – "):
            text = "## Close%s2026-07\nBooked: 1\n" % separator
            _written, found, page = self.seen(text)
            self.assertNotIn("Close", found)
            self.assertNotIn("## Close", page)


if __name__ == "__main__":
    unittest.main()
