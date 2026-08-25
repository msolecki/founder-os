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


if __name__ == "__main__":
    unittest.main()
