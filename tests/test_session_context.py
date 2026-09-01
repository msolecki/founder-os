"""Installed-copy smoke-test contracts."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE_SCRIPT = REPO_ROOT / "scripts" / "smoke_installed_copy.py"
SOURCE_PLUGIN = REPO_ROOT / "founder-os"
SESSION_HOOK = SOURCE_PLUGIN / "hooks" / "session-context.py"


def load_smoke_module():
    spec = importlib.util.spec_from_file_location(
        "smoke_installed_copy", SMOKE_SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestInstalledCopySmokeContract(unittest.TestCase):
    def test_smoke_script_exists(self):
        self.assertTrue(
            SMOKE_SCRIPT.is_file(),
            "Task 4 requires a reusable installed-copy smoke harness",
        )

    def test_all_session_sources_load_guidance_from_installed_copy(self):
        smoke = load_smoke_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            installed = smoke.create_installed_copy(
                SOURCE_PLUGIN, temp_root / "marketplace"
            )
            results = smoke.check_session_context(installed, temp_root)

        self.assertEqual(set(results), set(smoke.SESSION_SOURCES))
        expected_context = (
            smoke.CONTEXT_PREFIX
            + next(iter(results.values()))["installed_guidance"]
        )
        for result in results.values():
            output = result["output"]
            self.assertEqual(
                output["hookSpecificOutput"]["hookEventName"],
                "SessionStart",
            )
            self.assertEqual(
                output["hookSpecificOutput"]["additionalContext"],
                expected_context,
            )

    def test_repository_root_mutation_is_detected(self):
        smoke = load_smoke_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            installed = smoke.create_installed_copy(
                SOURCE_PLUGIN, temp_root / "marketplace"
            )
            with self.assertRaisesRegex(
                smoke.SmokeFailure, "installed-copy guidance"
            ):
                smoke.check_session_context(
                    installed,
                    temp_root,
                    hook_plugin_root=SOURCE_PLUGIN,
                )

    def test_installed_guard_covers_gateway_authority_paths(self):
        smoke = load_smoke_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            installed = smoke.create_installed_copy(
                SOURCE_PLUGIN, temp_root / "marketplace"
            )
            outcomes = smoke.check_ownership_guard(
                installed, temp_root / "workspace"
            )

        self.assertIsNone(outcomes["gateway_allowed"])
        self.assertIsNone(outcomes["native_allowed"])
        self.assertIsNone(outcomes["fallback_allowed"])
        self.assertIsNone(outcomes["main_thread"])
        # claude_namespaced_gateway / claude_reviewer_read /
        # claude_namespaced_direct_denied pin the shapes Claude Code actually
        # sends at runtime (`founder-os:<role>` identities and
        # `mcp__plugin_founder-os_founder-os-state__*` tool names) — added by
        # the 2026-07-30 audit fix (CFG-002).
        self.assertIsNone(outcomes["claude_namespaced_gateway"])
        self.assertIsNone(outcomes["claude_reviewer_read"])
        self.assertEqual(
            set(outcomes),
            {
                "gateway_allowed",
                "native_allowed",
                "fallback_allowed",
                "fallback_direct_denied",
                "claude_namespaced_gateway",
                "claude_reviewer_read",
                "claude_namespaced_direct_denied",
                "claude_namespaced_elevation",
                "direct_file",
                "wrong_role",
                "elevation",
                "claimed_main_thread",
                "main_thread",
                "recorded_main_thread",
                "recorded_turns",
            },
        )
        self.assertEqual(
            outcomes["recorded_turns"],
            {"cfo", "strategist", "__founder_os_main__"},
        )
        for key in (
            "direct_file",
            "fallback_direct_denied",
            "claude_namespaced_direct_denied",
            "claude_namespaced_elevation",
            "wrong_role",
            "elevation",
            "claimed_main_thread",
        ):
            denied = outcomes[key]["hookSpecificOutput"]
            self.assertEqual(denied["permissionDecision"], "deny")

    def test_session_context_warning_is_model_visible_from_installed_hook(self):
        smoke = load_smoke_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            installed = smoke.create_installed_copy(
                SOURCE_PLUGIN, temp_root / "marketplace"
            )
            warning = smoke.check_session_context_warning(installed, temp_root)

        self.assertEqual(
            warning["output"]["hookSpecificOutput"]["additionalContext"],
            warning["stderr"],
        )
        self.assertIn("missing", warning["stderr"])
        self.assertIn("Do not give Founder OS advice", warning["stderr"])

    def test_both_installed_adapters_run_the_complete_role_io_lifecycle(self):
        smoke = load_smoke_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            installed = smoke.create_installed_copy(
                SOURCE_PLUGIN, temp_root / "marketplace"
            )
            reports = {
                host: smoke.check_mcp_lifecycle(
                    installed,
                    temp_root / (host + "-workspace"),
                    host,
                )
                for host in ("claude", "codex")
            }

        for host, report in reports.items():
            with self.subTest(host=host):
                self.assertEqual(report["version"], "2.7.0")
                self.assertEqual(report["tool_count"], 8)
                self.assertEqual(report["wrong_owner"], "ROLE_NOT_OWNER")
                self.assertEqual(report["stale_write"], "STALE_WRITE")
                self.assertEqual(
                    report["bad_structure"], "INVALID_DOCUMENT_STRUCTURE"
                )
                self.assertEqual(report["closed_reuse"], "ROLE_SESSION_INVALID")
                self.assertNotEqual(
                    report["initial_sha256"], report["persisted_sha256"]
                )
                self.assertRegex(report["persisted_sha256"], r"^[0-9a-f]{64}$")

    def test_source_tree_fingerprint_detects_repository_mutation(self):
        smoke = load_smoke_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source"
            source.mkdir()
            target = source / "contract.md"
            target.write_text("before\n", encoding="utf-8")
            before = smoke.tree_fingerprint(source)
            target.write_text("after\n", encoding="utf-8")
            with self.assertRaisesRegex(smoke.SmokeFailure, "source package changed"):
                smoke.assert_tree_unchanged(source, before)

    def test_package_tools_accept_installed_copy(self):
        smoke = load_smoke_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            installed = smoke.create_installed_copy(
                SOURCE_PLUGIN, temp_root / "marketplace"
            )
            results = smoke.check_package_tools(REPO_ROOT, installed)

        self.assertEqual(set(results), {"validator", "commands"})
        self.assertTrue(all(result.returncode == 0 for result in results.values()))

    def test_command_line_smoke_passes(self):
        result = subprocess.run(
            [sys.executable, str(SMOKE_SCRIPT)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("installed-copy smoke: PASS", result.stdout)


class TestInstalledCopySmokeWiring(unittest.TestCase):
    def test_ci_runs_smoke(self):
        workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("python3 scripts/smoke_installed_copy.py", workflow)

    def test_development_guide_documents_smoke(self):
        guide = (REPO_ROOT / "docs" / "development.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("python3 scripts/smoke_installed_copy.py", guide)


class TestSessionContextFailureVisibility(unittest.TestCase):
    def _run_broken_install(self, setup):
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_root = Path(temp_dir) / "installed" / "founder-os"
            plugin_root.mkdir(parents=True)
            setup(plugin_root / "CLAUDE.md")
            env = os.environ.copy()
            env["PLUGIN_ROOT"] = str(plugin_root)
            result = subprocess.run(
                [sys.executable, str(SESSION_HOOK)],
                capture_output=True,
                text=True,
                cwd=temp_dir,
                env=env,
                check=False,
            )
            resolved_root = str(plugin_root.resolve())
        return result, resolved_root

    def test_missing_unreadable_and_invalid_guidance_are_model_visible(self):
        cases = {
            "missing": lambda path: None,
            "unreadable": lambda path: path.mkdir(),
            "invalid UTF-8": lambda path: path.write_bytes(b"\xff\xfe"),
        }
        for expected_reason, setup in cases.items():
            with self.subTest(reason=expected_reason):
                result, resolved_root = self._run_broken_install(setup)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                output = json.loads(result.stdout)
                hook = output["hookSpecificOutput"]
                self.assertEqual(hook["hookEventName"], "SessionStart")
                warning = hook["additionalContext"]
                self.assertEqual(result.stderr, warning + "\n")
                self.assertIn(resolved_root, warning)
                self.assertIn(expected_reason, warning)
                self.assertRegex(
                    warning,
                    r"(?i)do not give Founder OS advice until .*restored",
                )


if __name__ == "__main__":
    unittest.main()
