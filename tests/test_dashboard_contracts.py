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


if __name__ == "__main__":
    unittest.main()
