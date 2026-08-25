"""One parser for the registry, one for the ownership map.

The dashboard reads both files and needs different answers from them than the
gateway does. It must not get those answers from its own parser: two readers of
one file drift, and the drift shows up as a business silently missing from a
page that claims to show all of them.
"""
import importlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "founder-os"
DASHBOARD = PLUGIN_ROOT / "scripts" / "dashboard"
sys.path.insert(0, str(PLUGIN_ROOT))

from mcp import workspaces


def load_dashboard(name):
    """Import a dashboard module as a real submodule of a real package.

    The modules import their siblings with `from . import parse`, which needs a
    parent package with a search path. Loading each file as a top-level module
    would make every one of those imports raise.
    """
    if "fos_dashboard" not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            "fos_dashboard", DASHBOARD / "__init__.py",
            submodule_search_locations=[str(DASHBOARD)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["fos_dashboard"] = package
        spec.loader.exec_module(package)
    return importlib.import_module("fos_dashboard.%s" % name)


REGISTRY = """\
businesses:
  acme:
    home: /tmp/acme/founder-os
    status: active
  nordwind:
    home: /tmp/nordwind/founder-os
    status: paused
default: acme
portfolio: /tmp/.founder-os/portfolio
"""


class TestLoadRegistry(unittest.TestCase):
    def _home_with(self, text):
        home = Path(tempfile.mkdtemp())
        (home / ".founder-os").mkdir()
        (home / ".founder-os" / "businesses.yaml").write_text(text, encoding="utf-8")
        return home

    def test_absent_registry_is_none_not_an_error(self):
        self.assertIsNone(workspaces.load_registry(Path(tempfile.mkdtemp())))

    def test_registry_parses_every_business_and_its_status(self):
        registry = workspaces.load_registry(self._home_with(REGISTRY))
        self.assertEqual(sorted(registry["businesses"]), ["acme", "nordwind"])
        self.assertEqual(registry["businesses"]["nordwind"]["status"], "paused")
        self.assertEqual(registry["default"], "acme")
        self.assertEqual(registry["portfolio"], "/tmp/.founder-os/portfolio")

    def test_malformed_registry_raises(self):
        with self.assertRaises(workspaces.WorkspaceResolutionError):
            workspaces.load_registry(self._home_with("businesses:\n\tacme:\n"))


class TestOwnershipView(unittest.TestCase):
    def setUp(self):
        self.contracts = load_dashboard("contracts")

    def test_view_carries_the_packaged_map(self):
        view = self.contracts.load_ownership()
        self.assertIn("metrics.md", view.workspace_files)
        self.assertIn("portfolio.md", view.portfolio_files)
        self.assertIn("_dashboard/", view.derived_paths)
        self.assertEqual(view.owners["metrics.md"], "cfo")
        self.assertIn("## Signals", view.sections["metrics.md"])

    def test_every_workspace_file_has_sections_and_an_owner(self):
        view = self.contracts.load_ownership()
        for path in view.workspace_files:
            self.assertIn(path, view.owners, path)
            self.assertIn(path, view.sections, path)


class TestActiveBusinesses(unittest.TestCase):
    def setUp(self):
        self.contracts = load_dashboard("contracts")

    def _home_with(self, text):
        home = Path(tempfile.mkdtemp())
        (home / ".founder-os").mkdir()
        (home / ".founder-os" / "businesses.yaml").write_text(text, encoding="utf-8")
        return home

    def test_paused_business_is_excluded_and_counted(self):
        businesses, portfolio, paused = self.contracts.active_businesses(
            home=self._home_with(REGISTRY))
        self.assertEqual([b.slug for b in businesses], ["acme"])
        self.assertEqual(paused, 1)
        self.assertEqual(portfolio, Path("/tmp/.founder-os/portfolio"))

    def test_no_registry_falls_back_to_a_single_workspace(self):
        cwd = Path(tempfile.mkdtemp())
        (cwd / "founder-os").mkdir()
        businesses, portfolio, paused = self.contracts.active_businesses(
            home=Path(tempfile.mkdtemp()), cwd=cwd, env={})
        self.assertEqual(len(businesses), 1)
        self.assertEqual(businesses[0].home, cwd / "founder-os")
        self.assertIsNone(portfolio)
        self.assertEqual(paused, 0)


class TestThresholds(unittest.TestCase):
    def test_queue_caps_and_clocks_load(self):
        contracts = load_dashboard("contracts")
        thresholds = contracts.load_thresholds()
        self.assertEqual(thresholds["queue"]["doing_cap"], 3)
        self.assertEqual(thresholds["queue"]["queued_cap"], 15)
        self.assertEqual(thresholds["queue"]["queued_days"], 21)
        self.assertEqual(thresholds["signals"]["cap"], 3)


if __name__ == "__main__":
    unittest.main()
