"""Contracts for isolated Claude Code and Codex installed-host probes."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE_SCRIPT = REPO_ROOT / "scripts" / "probe_installed_hosts.py"
PLUGIN_ROOT = REPO_ROOT / "founder-os"


def load_probe_module():
    spec = importlib.util.spec_from_file_location(
        "probe_installed_hosts", PROBE_SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class InstalledHostProbeContractTest(unittest.TestCase):
    def test_probe_script_exists_and_cli_mentions_both_hard_gates(self):
        self.assertTrue(PROBE_SCRIPT.is_file())
        result = subprocess.run(
            [os.fspath(PROBE_SCRIPT), "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for flag in ("--claude", "--codex", "--require-native-and-fallback"):
            self.assertIn(flag, result.stdout)

    def test_host_environments_are_isolated_from_real_user_configuration(self):
        probe = load_probe_module()
        inherited = {
            "HOME": "/real/home",
            "CLAUDE_CONFIG_DIR": "/real/claude",
            "CODEX_HOME": "/real/codex",
            "PLUGIN_DATA": "/real/plugin-data",
            "PATH": os.environ.get("PATH", ""),
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            claude = probe.isolated_environment(root, "claude", inherited)
            codex = probe.isolated_environment(root, "codex", inherited)

            self.assertTrue(Path(claude["HOME"]).is_relative_to(root))
            self.assertTrue(
                Path(claude["CLAUDE_CONFIG_DIR"]).is_relative_to(root)
            )
            self.assertNotIn("CODEX_HOME", claude)
            self.assertTrue(Path(codex["HOME"]).is_relative_to(root))
            self.assertTrue(Path(codex["CODEX_HOME"]).is_relative_to(root))
            self.assertNotIn("CLAUDE_CONFIG_DIR", codex)
            for environment in (claude, codex):
                self.assertNotIn("PLUGIN_DATA", environment)
                self.assertTrue(
                    Path(environment["XDG_CONFIG_HOME"]).is_relative_to(root)
                )

    def test_install_commands_use_only_the_local_marketplace(self):
        probe = load_probe_module()
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                commands = probe.installation_commands(
                    host, REPO_ROOT, "/absolute/host-cli"
                )
                flattened = [item for command in commands for item in command]
                self.assertIn(str(REPO_ROOT), flattened)
                self.assertNotIn("msolecki/founder-os", flattened)
                self.assertTrue(
                    any("marketplace" in command for command in commands)
                )
                self.assertTrue(
                    any(
                        "founder-os@founder-os" in command
                        for command in commands
                    )
                )

    def test_unavailable_cli_and_missing_host_selection_are_failures(self):
        probe = load_probe_module()
        with self.assertRaisesRegex(probe.ProbeFailure, "claude.*unavailable"):
            probe.require_cli("claude", which=lambda _name: None)
        self.assertEqual(probe.main([]), 2)

    def test_pass_record_contains_hashes_but_no_business_content(self):
        probe = load_probe_module()
        record = probe.format_pass_record(
            "claude",
            {
                "version": "2.8.0",
                "initial_sha256": "a" * 64,
                "persisted_sha256": "b" * 64,
                "native": "PASS",
                "fallback": "PASS",
            },
        )
        self.assertIn("claude PASS", record)
        self.assertIn("initial_sha256=" + "a" * 64, record)
        self.assertIn("persisted_sha256=" + "b" * 64, record)
        for content in ("Close", "Runway", "Profitability", "baseline"):
            self.assertNotIn(content, record)

    def test_native_and_fallback_envelopes_are_built_independently(self):
        probe = load_probe_module()
        native, fallback = probe.execution_envelopes(PLUGIN_ROOT)

        self.assertIsNot(native, fallback)
        self.assertEqual(native["role_instructions"], fallback["role_instructions"])
        fallback["role_instructions"] += b"\nrewritten fallback\n"
        agents = probe.package_validator.load_agents(PLUGIN_ROOT)
        errors = probe.package_validator.execution_envelope_errors(
            PLUGIN_ROOT, agents, native, fallback
        )
        self.assertTrue(any("byte-identical" in error for error in errors), errors)

    def test_installed_cadence_preview_uses_host_specific_unattended_contract(self):
        probe = load_probe_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            claude = probe.check_cadence_preview(
                PLUGIN_ROOT, "claude", root / "claude", root / "workspace"
            )
            codex = probe.check_cadence_preview(
                PLUGIN_ROOT, "codex", root / "codex", root / "workspace"
            )
        self.assertIn("--allowedTools", claude)
        self.assertIn(
            "mcp__plugin_founder-os_founder-os-state__*", claude
        )
        self.assertIn("--no-session-persistence", claude)
        self.assertIn("workspace-write", codex)
        self.assertIn("$founder-os:daily-brief", codex)

    def test_ci_runs_probe_contracts_without_downloading_host_clis(self):
        workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "python3 -m unittest tests.test_installed_host_probes -v", workflow
        )
        self.assertNotIn("install claude", workflow.lower())
        self.assertNotIn("install codex", workflow.lower())


if __name__ == "__main__":
    unittest.main()
