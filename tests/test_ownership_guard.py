"""Tests for founder-os/hooks/ownership-guard.py.

The guard lives at a dashed path no import statement reaches, so it is loaded
by file location. Loading it does not run main(): the module guards on
__name__ == "__main__" and only reads stdin there.
"""
import builtins
import importlib.util
import json
import os
import subprocess
import sys
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


def run_codex_hook(payload, data_root):
    env = {**os.environ,
           "FOUNDER_OS_HOME": str(PLUGIN_ROOT),
           "PLUGIN_ROOT": str(PLUGIN_ROOT),
           "PLUGIN_DATA": str(data_root)}
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
        self.assertIn("strategist", result.stdout)

    def test_notebookedit_by_wrong_agent_is_denied(self):
        p = run_hook({"agent_type": "pipeline-coach",
                      "tool_name": "NotebookEdit",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {
                          "notebook_path": str(PLUGIN_ROOT / "goals.md")}})
        self.assertIn("deny", p.stdout, p.stderr)
        self.assertIn("strategist", p.stdout)

    def test_write_case_bypass_is_denied(self):
        p = run_hook({"agent_type": "pipeline-coach",
                      "tool_name": "Write",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {
                          "file_path": str(PLUGIN_ROOT / "Goals.md")}})
        self.assertIn("deny", p.stdout)
        self.assertIn("strategist", p.stdout)

    def test_main_thread_is_always_allowed(self):
        p = run_hook({"tool_name": "NotebookEdit",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {
                          "notebook_path": str(PLUGIN_ROOT / "goals.md")}})
        self.assertEqual(p.stdout.strip(), "")
        self.assertEqual(p.returncode, 0)

    def test_codex_apply_patch_uses_turn_mapping(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            mapping = Path(td) / "agent-types"
            mapping.mkdir()
            (mapping / "turn-1.json").write_text(
                json.dumps({"agent_type": "pipeline-coach"}), encoding="utf-8")
            payload = {
                "turn_id": "turn-1",
                "tool_name": "apply_patch",
                "cwd": str(PLUGIN_ROOT),
                "tool_input": {"command": (
                    "*** Begin Patch\n"
                    "*** Update File: goals.md\n"
                    "@@\n-old\n+new\n"
                    "*** End Patch\n")},
            }
            p = run_codex_hook(payload, td)
        self.assertIn("deny", p.stdout)
        self.assertIn("strategist", p.stdout)

    def test_codex_apply_patch_owner_is_allowed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            mapping = Path(td) / "agent-types"
            mapping.mkdir()
            (mapping / "turn-2.json").write_text(
                json.dumps({"agent_type": "strategist"}), encoding="utf-8")
            payload = {
                "turn_id": "turn-2",
                "tool_name": "apply_patch",
                "cwd": str(PLUGIN_ROOT),
                "tool_input": {"command": (
                    "*** Begin Patch\n"
                    "*** Update File: goals.md\n"
                    "@@\n-old\n+new\n"
                    "*** End Patch\n")},
            }
            p = run_codex_hook(payload, td)
        self.assertEqual(p.stdout.strip(), "")
        self.assertEqual(p.returncode, 0)


class TestPatchPaths(unittest.TestCase):
    def setUp(self):
        self.guard = load_guard()

    def test_all_patch_markers_are_extracted_in_first_seen_order(self):
        command = ("*** Begin Patch\n"
                   "*** Add File: add.md\n"
                   "*** Update File: update.md\n"
                   "*** Delete File: delete.md\n"
                   "*** Move to: moved.md\n"
                   "*** Update File: update.md\n"
                   "*** End Patch\n")
        self.assertEqual(
            self.guard._patch_paths(command),
            ["add.md", "update.md", "delete.md", "moved.md"])

    def test_non_string_patch_is_empty(self):
        self.assertEqual(self.guard._patch_paths(None), [])

    def test_tool_paths_accepts_alternate_patch_payload_keys(self):
        self.assertEqual(
            self.guard._tool_paths("apply_patch", {
                "patch": "*** Update File: alternate.md\n"}),
            ["alternate.md"])


class TestAgentTypeFor(unittest.TestCase):
    def setUp(self):
        self.guard = load_guard()

    def test_invalid_turn_id_returns_none(self):
        self.assertIsNone(self.guard.agent_type_for({"turn_id": "bad/id"}))

    def test_missing_plugin_data_returns_none(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(self.guard.agent_type_for({"turn_id": "turn-1"}))

    def test_missing_mapping_returns_none(self):
        with mock.patch.dict(os.environ, {"PLUGIN_DATA": "/tmp/no-such-data"},
                             clear=False):
            self.assertIsNone(self.guard.agent_type_for({"turn_id": "turn-1"}))


class TestOutboundGuard(unittest.TestCase):
    """House rule 0 at the tool layer — the half of the hook nothing covered.

    The guard's own docstring calls check_outbound 'the only reason [Bash
    routing-around] isn't trivial today'. A matcher typo there would have
    shipped silently: every prior test exercised ownership, none exercised
    outbound.
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

    def test_websearch_is_not_outbound_here(self):
        # Deliberately narrower than the validator's OUTBOUND_TOOLS: a live
        # WebSearch is not a send, and denying it mid-run is a false deny.
        p = run_hook({"agent_type": "cfo", "tool_name": "WebSearch",
                      "cwd": str(REPO_ROOT), "tool_input": {}})
        self.assertEqual(p.stdout.strip(), "")
        self.assertEqual(p.returncode, 0)

    def test_bash_on_main_thread_is_allowed(self):
        p = run_hook({"tool_name": "Bash", "cwd": str(REPO_ROOT),
                      "tool_input": {"command": "ls"}})
        self.assertEqual(p.stdout.strip(), "")
        self.assertEqual(p.returncode, 0)


class TestOwnershipAllowPaths(unittest.TestCase):
    """The positive cases: the guard must stay out of honest work's way."""

    def test_owner_writing_its_own_file_is_allowed(self):
        p = run_hook({"agent_type": "strategist", "tool_name": "Write",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {"file_path": str(PLUGIN_ROOT / "goals.md")}})
        self.assertEqual(p.stdout.strip(), "")
        self.assertEqual(p.returncode, 0)

    def test_unmapped_custom_agent_is_denied_on_an_owned_path(self):
        # "One owner per file" guards against exactly this: a writer the map
        # has never heard of.
        p = run_hook({"agent_type": "someones-custom-agent", "tool_name": "Write",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {"file_path": str(PLUGIN_ROOT / "goals.md")}})
        self.assertIn("deny", p.stdout)
        self.assertIn("strategist", p.stdout)

    def test_unmapped_path_in_workspace_is_allowed(self):
        # A scratch file has no owner to be stolen from.
        p = run_hook({"agent_type": "cfo", "tool_name": "Write",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {"file_path": str(PLUGIN_ROOT / "scratch.md")}})
        self.assertEqual(p.stdout.strip(), "")
        self.assertEqual(p.returncode, 0)

    def test_path_outside_workspace_is_allowed(self):
        p = run_hook({"agent_type": "cfo", "tool_name": "Write",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {"file_path": "/tmp/elsewhere.md"}})
        self.assertEqual(p.stdout.strip(), "")
        self.assertEqual(p.returncode, 0)


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

    def test_missing_ownership_map_is_allowed(self):
        # Copy the guard somewhere with no references/ownership.yaml in sight,
        # so both lookup roots come up empty.
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
            self.assertEqual(p.stdout.strip(), "")
            self.assertEqual(p.returncode, 0)
            self.assertIn("guard is off", p.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestFallbackParser(unittest.TestCase):
    """_parse_owns_without_yaml must agree with PyYAML on the real map —
    otherwise the no-PyYAML machines run a different ownership policy."""

    def setUp(self):
        self.guard = load_guard()
        self.text = (PLUGIN_ROOT / "references" / "ownership.yaml").read_text(
            encoding="utf-8")

    def test_parses_the_real_map_identically_to_pyyaml(self):
        import yaml
        expected = yaml.safe_load(self.text)["owns"]
        got = self.guard._parse_owns_without_yaml(self.text)
        self.assertEqual(got, expected)

    def test_load_ownership_without_pyyaml_matches_pyyaml_map(self):
        import yaml
        owns = yaml.safe_load(self.text)["owns"]
        expected = {
            path.strip(): agent
            for agent, paths in owns.items()
            for path in paths
            if isinstance(path, str) and path.strip()
        }
        with mock.patch.object(self.guard, "yaml", None):
            got = self.guard.load_ownership()
        self.assertEqual(got, expected)

    def test_garbage_returns_none_rather_than_a_guess(self):
        self.assertIsNone(self.guard._parse_owns_without_yaml(
            "owns:\n  - a list where an agent should be\n"))
        self.assertIsNone(self.guard._parse_owns_without_yaml("no owns here\n"))

    def test_same_indent_sequence_matches_pyyaml(self):
        text = "owns:\n  strategist:\n  - goals.md\n  - metrics.md\n"
        self.assertEqual(
            self.guard._parse_owns_without_yaml(text),
            {"strategist": ["goals.md", "metrics.md"]})


class TestOwnershipHotPath(unittest.TestCase):
    def test_workspace_roots_are_computed_once_for_multiple_paths(self):
        guard = load_guard()
        with mock.patch.object(guard, "load_ownership", return_value={}), \
                mock.patch.object(guard, "workspace_roots", return_value=[] ) as roots:
            guard.check_ownership("cfo", "apply_patch", {
                "command": "*** Begin Patch\n"
                            "*** Update File: a.md\n"
                            "*** Update File: b.md\n"
                            "*** End Patch\n"}, "/tmp/workspace")
        roots.assert_called_once_with("/tmp/workspace")


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

    def test_registry_roots_without_pyyaml_match_yaml_result(self):
        import tempfile
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
                "portfolio: %s\n" % (acme, portfolio)))
            guard = load_guard()
            with mock.patch.object(guard, "yaml", None), \
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
            self.assertIn("cfo", r.stdout)


if __name__ == "__main__":
    unittest.main()
