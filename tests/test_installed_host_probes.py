"""Contracts for the isolated Claude Code installed-host probe."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import subprocess
import tempfile
import unittest
from unittest import mock

import yaml
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
    def test_probe_script_exists_and_cli_mentions_its_hard_gates(self):
        self.assertTrue(PROBE_SCRIPT.is_file())
        result = subprocess.run(
            [os.fspath(PROBE_SCRIPT), "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for flag in ("--claude", "--require-native-and-fallback"):
            self.assertIn(flag, result.stdout)

    def test_host_environments_are_isolated_from_real_user_configuration(self):
        probe = load_probe_module()
        inherited = {
            "HOME": "/real/home",
            "CLAUDE_CONFIG_DIR": "/real/claude",
            "PLUGIN_DATA": "/real/plugin-data",
            "PATH": os.environ.get("PATH", ""),
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            claude = probe.isolated_environment(root, inherited)

            self.assertTrue(Path(claude["HOME"]).is_relative_to(root))
            self.assertTrue(
                Path(claude["CLAUDE_CONFIG_DIR"]).is_relative_to(root)
            )
            self.assertNotIn("PLUGIN_DATA", claude)
            self.assertTrue(
                Path(claude["XDG_CONFIG_HOME"]).is_relative_to(root)
            )

    def test_install_commands_use_only_the_local_marketplace(self):
        probe = load_probe_module()
        commands = probe.installation_commands(
            REPO_ROOT, "/absolute/host-cli"
        )
        flattened = [item for command in commands for item in command]
        self.assertIn(str(REPO_ROOT), flattened)
        self.assertNotIn("msolecki/founder-os", flattened)
        self.assertTrue(any("marketplace" in command for command in commands))
        self.assertTrue(
            any("founder-os@founder-os" in command for command in commands)
        )

    def test_unavailable_cli_is_a_failure_and_no_host_selection_is_needed(self):
        probe = load_probe_module()
        with self.assertRaisesRegex(probe.ProbeFailure, "claude.*unavailable"):
            probe.require_cli(which=lambda _name: None)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), mock.patch.object(
            probe, "require_cli", side_effect=probe.ProbeFailure("no cli")
        ):
            self.assertEqual(probe.main([]), 1)
        self.assertIn("FAIL: no cli", stderr.getvalue())

    def test_scheduled_dispatch_requires_a_chief_of_staff_write(self):
        probe = load_probe_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            journal = root / "data" / "operations.jsonl"
            journal.parent.mkdir()
            script = (
                'mkdir -p "$FOUNDER_OS_HOME/reviews/daily" && '
                'touch "$FOUNDER_OS_HOME/reviews/daily/2026-10-26.md" && '
                "echo '{\"result\":\"OK\",\"role\":\"%s\","
                "\"path\":\"reviews/daily/2026-10-26.md\"}' >> " + str(journal)
            )
            environment = dict(os.environ)
            self.assertEqual("PASS", probe.check_scheduled_dispatch(
                ["/bin/sh", "-c", script % "chief-of-staff"],
                environment, root / "run", root,
            ))
            journal.write_text("")
            with self.assertRaisesRegex(probe.ProbeFailure, "wrong role"):
                probe.check_scheduled_dispatch(
                    ["/bin/sh", "-c", script % "strategist"],
                    environment, root / "run", root,
                )
            journal.write_text("")
            with self.assertRaisesRegex(probe.ProbeFailure, "no daily review"):
                probe.check_scheduled_dispatch(
                    ["/bin/sh", "-c", "exit 0"], environment, root / "run", root
                )

    def test_pass_record_contains_hashes_but_no_business_content(self):
        probe = load_probe_module()
        record = probe.format_pass_record(
            {
                "version": "3.1.0",
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

    def test_installed_cadence_preview_uses_the_unattended_contract(self):
        probe = load_probe_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            claude = probe.check_cadence_preview(
                PLUGIN_ROOT, root / "claude", root / "workspace"
            )
        self.assertIn("--allowedTools", claude)
        self.assertIn(
            "mcp__plugin_founder-os_founder-os-state__*", claude
        )
        self.assertIn("--no-session-persistence", claude)

    def test_ci_runs_probe_contracts_without_downloading_host_clis(self):
        workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        # The discover run covers this module; a dedicated step ran it twice.
        self.assertIn("python3 -m unittest discover -s tests", workflow)
        # Only the lint job installs the Claude CLI; the test matrix never does.
        test_job = yaml.safe_load(workflow)["jobs"]["test"]
        self.assertNotIn("install claude", yaml.safe_dump(test_job).lower())


if __name__ == "__main__":
    unittest.main()
