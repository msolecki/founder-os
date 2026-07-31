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

    def test_yaml_loader_prefers_c_safe_loader(self):
        guard = load_guard()
        import yaml
        class FakeLoader: pass
        with mock.patch.object(yaml, "CSafeLoader", FakeLoader), \
                mock.patch.object(yaml, "load", return_value={"owns": {}}) as load:
            self.assertEqual(guard._yaml_load(yaml, "owns: {}\n"), {"owns": {}})
        self.assertIs(load.call_args.kwargs["Loader"], FakeLoader)


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

    def test_codex_apply_patch_owner_is_still_denied_direct_access(self):
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
        self.assertIn("deny", p.stdout)
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

    def test_mapping_symlink_is_not_trusted_as_subagent_identity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            mapping = root / "agent-types"
            mapping.mkdir()
            source = root / "forged.json"
            source.write_text('{"agent_type":"cfo"}\n', encoding="utf-8")
            (mapping / "turn-1.json").symlink_to(source)
            with mock.patch.dict(
                os.environ,
                {"PLUGIN_DATA": temp_dir},
                clear=False,
            ):
                resolved = self.guard.agent_type_for({"turn_id": "turn-1"})

        self.assertIsNone(resolved)

    def test_unresolved_safe_turn_id_is_denied_instead_of_treated_as_main(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_codex_hook(
                {
                    "turn_id": "missing-subagent-turn",
                    "tool_name": "Write",
                    "cwd": str(REPO_ROOT),
                    "tool_input": {
                        "file_path": str(PLUGIN_ROOT / "metrics.md"),
                    },
                },
                temp_dir,
            )

        self.assertIn("deny", result.stdout, result.stderr)

    def test_present_invalid_identity_markers_are_not_treated_as_main(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            for marker in (
                {"agent_type": ""},
                {"agent_type": ["cfo"]},
                {"turn_id": "bad/id"},
                {"turn_id": ["turn-1"]},
            ):
                with self.subTest(marker=marker):
                    result = run_codex_hook(
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

    def test_path_outside_workspace_is_denied(self):
        p = run_hook({"agent_type": "cfo", "tool_name": "Write",
                      "cwd": str(REPO_ROOT),
                      "tool_input": {"file_path": "/tmp/elsewhere.md"}})
        self.assertIn("deny", p.stdout)
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

    def test_overlay_is_honoured_without_pyyaml(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            ws = self._workspace(Path(td), self.OVERLAY)
            guard = load_guard()
            with mock.patch.object(guard, "yaml", None):
                self.assertEqual(guard.local_ownership(str(ws)),
                                 {"partners.md": "network-manager"})

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
        guard = load_guard()
        calls = []
        real = guard._owns_from_text

        def counted(text, source):
            calls.append(source)
            return real(text, source)

        import tempfile
        with tempfile.TemporaryDirectory() as td:
            ws = self._workspace(Path(td), self.OVERLAY)
            with mock.patch.object(guard, "_owns_from_text", counted):
                guard.local_ownership(str(ws))
                guard.local_ownership(str(ws))
        self.assertEqual(len(calls), 1)


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

    def _issue_capability(self, data_root, role="cfo"):
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
        )

    def _deny_payload(self, result):
        self.assertTrue(result.stdout, result.stderr)
        payload = json.loads(result.stdout)
        output = payload["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertTrue(output["permissionDecisionReason"])

    def _gateway_call(self, capability, data_root, agent_type="cfo"):
        return run_codex_hook(
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
            result = run_codex_hook(
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
            result = run_codex_hook(
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
            result = run_codex_hook(
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
            result = run_codex_hook(
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
            result = run_codex_hook(
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
            result = run_codex_hook(
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
                {"PLUGIN_DATA": temp_dir},
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
            result = run_codex_hook(
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
            result = run_codex_hook(
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

    def test_real_codex_turn_identity_roundtrip_allows_normalized_server_name(
        self,
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            capability = self._issue_capability(temp_dir, role="cfo")
            record = subprocess.run(
                [
                    sys.executable,
                    str(PLUGIN_ROOT / "hooks" / "record-agent.py"),
                ],
                input=json.dumps(
                    {
                        "hook_event_name": "SubagentStart",
                        "turn_id": "codex-turn-1",
                        "agent_type": "cfo",
                    }
                ),
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                env={
                    **os.environ,
                    "FOUNDER_OS_HOME": str(PLUGIN_ROOT),
                    "PLUGIN_ROOT": str(PLUGIN_ROOT),
                    "PLUGIN_DATA": temp_dir,
                },
            )
            self.assertEqual(record.returncode, 0, record.stderr)

            result = run_codex_hook(
                {
                    "turn_id": "codex-turn-1",
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
                ("apply_patch", {"patch": "*** Begin Patch"}),
                ("mcp__other__anything", {}),
            ):
                with self.subTest(tool_name=tool_name):
                    result = run_codex_hook(
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
                    result = run_codex_hook(
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

    def test_apply_patch_header_case_does_not_decide_the_overlay(self):
        # An unrecognized header yields no paths, and no paths means
        # check_ownership returns without an opinion — so the verb's case
        # decided whether `_local/` was protected.
        for verb in ("Update", "update", "UPDATE", "uPdAtE"):
            with self.subTest(verb=verb):
                p = run_hook({
                    "agent_type": "general-purpose",
                    "tool_name": "apply_patch",
                    "cwd": str(REPO_ROOT),
                    "tool_input": {
                        "command": "*** Begin Patch\n"
                                   "*** %s File: founder-os/_local/ownership.yaml\n"
                                   "*** End Patch" % verb,
                    },
                })
                self.assertIn("deny", p.stdout)
                self.assertIn("overlay", p.stdout)


if __name__ == "__main__":
    unittest.main()
