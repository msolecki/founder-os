"""`derived_files:` is optional, parsed, and excluded from every ownership join.

The parser at mcp/ownership.py compares the document's top-level keys for exact
equality, which means a new key is not an addition but a breaking change: the
gateway stops loading the map and every agent write fails. These tests pin the
key as optional in both directions — an old document without it still loads, and
a document with it does not leak the derived path into owners or sections.
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "founder-os"


def load_module(name, relative):
    spec = importlib.util.spec_from_file_location(name, PLUGIN_ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ownership = load_module("fos_ownership", "mcp/ownership.py")


BASE = """\
workspace_files:
  - charter.md
portfolio_files:
  - portfolio.md
owns:
  chief-of-staff:
    - charter.md
  portfolio-manager:
    - portfolio.md
sections:
  charter.md:
    - "## Business"
  portfolio.md:
    - "## Businesses"
"""

DERIVED = BASE + """\
derived_files:
  - _dashboard/
"""


class TestDerivedFiles(unittest.TestCase):
    def _write(self, text):
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=".yaml", delete=False, encoding="utf-8")
        handle.write(text)
        handle.close()
        return Path(handle.name)

    def test_document_without_derived_files_still_loads(self):
        schema = ownership.OwnershipSchema.load(self._write(BASE))
        self.assertEqual(schema.derived_paths(), ())

    def test_derived_files_parses(self):
        schema = ownership.OwnershipSchema.load(self._write(DERIVED))
        self.assertEqual(schema.derived_paths(), ("_dashboard/",))

    def test_derived_path_may_not_also_be_owned(self):
        text = DERIVED.replace("  - charter.md\n", "  - charter.md\n  - _dashboard/\n", 1)
        with self.assertRaises(ownership.OwnershipError):
            ownership.OwnershipSchema.load(self._write(text))

    def test_unknown_top_level_key_is_still_refused(self):
        with self.assertRaises(ownership.OwnershipError):
            ownership.OwnershipSchema.load(self._write(BASE + "nonsense:\n  - x.md\n"))

    def test_load_document_exposes_the_whole_map(self):
        document = ownership.load_document(self._write(DERIVED))
        self.assertEqual(document["derived_files"], ["_dashboard/"])
        self.assertIn("charter.md", document["workspace_files"])

    def test_packaged_map_loads_through_both_entry_points(self):
        path = PLUGIN_ROOT / "references" / "ownership.yaml"
        schema = ownership.OwnershipSchema.load(path)
        document = ownership.load_document(path)
        self.assertIsInstance(schema.derived_paths(), tuple)
        self.assertIn("metrics.md", document["workspace_files"])


if __name__ == "__main__":
    unittest.main()
