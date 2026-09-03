"""`derived_files:` is optional, parsed, and excluded from every ownership join.

The parser at mcp/ownership.py compares the document's top-level keys for exact
equality, which means a new key is not an addition but a breaking change: the
gateway stops loading the map and every agent write fails. These tests pin the
key as optional in both directions — an old document without it still loads, and
a document with it does not leak the derived path into owners or sections.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


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



class TestTheWriteGuardReadsTheSameKey(unittest.TestCase):
    """Two readers, one key, and they must not disagree.

    `derived_files:` is parsed twice by design: the gateway reads it through
    `OwnershipSchema` and the PreToolUse hook reads it with its own stdlib
    parser, because a hook that has to import the gateway is a hook that stops
    running the moment the gateway moves. The cost of the second reader is that
    the write boundary could come to depend on which channel an agent used, so
    the two answers are pinned equal here rather than left to agree by habit.
    """

    def _guard(self):
        return load_module("fos_ownership_guard", "hooks/ownership-guard.py")

    def _run_hook(self, rel):
        """The real hook, as the runtime runs it: JSON in, deny on stdout.

        A non-role `agent_type` on purpose — the thirteen roles are denied
        every direct file tool before the map is consulted, so a role payload
        would pass whether `derived_files:` were wired in or not.
        """
        env = {**os.environ,
               "FOUNDER_OS_HOME": str(PLUGIN_ROOT),
               "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)}
        payload = {"agent_type": "explore", "tool_name": "Write",
                   "cwd": str(REPO_ROOT),
                   "tool_input": {"file_path": str(PLUGIN_ROOT / rel)}}
        return subprocess.run(
            [sys.executable, str(PLUGIN_ROOT / "hooks" / "ownership-guard.py")],
            input=json.dumps(payload), capture_output=True, text=True,
            env=env, cwd=str(REPO_ROOT))

    def test_hook_and_schema_derive_the_same_paths_from_the_packaged_map(self):
        guard = self._guard()
        schema = ownership.OwnershipSchema.load(
            PLUGIN_ROOT / "references" / "ownership.yaml")
        entries = schema.derived_paths()
        # Two readers agreeing on nothing is not agreement: without this, the
        # equality below survives deleting `derived_files:` from the map.
        self.assertTrue(entries, "the packaged map declares no derived path")
        with mock.patch.dict(os.environ,
                             {"PLUGIN_ROOT": str(PLUGIN_ROOT),
                              "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)}):
            self.assertEqual(guard.load_derived(), entries)

    def test_the_hook_denies_what_the_schema_calls_derived(self):
        entries = ownership.OwnershipSchema.load(
            PLUGIN_ROOT / "references" / "ownership.yaml").derived_paths()
        self.assertTrue(entries, "the packaged map declares no derived path")
        for entry in entries:
            rel = entry + "anything.txt" if entry.endswith("/") else entry
            p = self._run_hook(rel)
            self.assertIn("deny", p.stdout, "%s: %s" % (entry, p.stderr))
            self.assertIn(entry, p.stdout, entry)


class TestNoAgentOwnsTheDerivedDirectory(unittest.TestCase):
    def test_the_packaged_map_gives_it_no_owner(self):
        document = ownership.load_document(
            PLUGIN_ROOT / "references" / "ownership.yaml")
        owned = {path for paths in document["owns"].values() for path in paths}
        self.assertNotIn("_dashboard/", owned)
        self.assertIn("_dashboard/", document["derived_files"])

    def test_it_declares_no_sections_so_no_write_can_be_structured(self):
        document = ownership.load_document(
            PLUGIN_ROOT / "references" / "ownership.yaml")
        self.assertNotIn("_dashboard/", document["sections"])



if __name__ == "__main__":
    unittest.main()
