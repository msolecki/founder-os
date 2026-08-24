"""Contract tests for the Claude and Codex local MCP adapters."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "founder-os"
CLAUDE_MCP_PATH = PLUGIN_ROOT / ".mcp.json"
CODEX_MANIFEST_PATH = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
ENTRY_PATH = PLUGIN_ROOT / "mcp" / "founder_os_state.py"
TOOL_NAMES = {
    "resolve_workspace",
    "open_role_session",
    "list_state",
    "read_state",
    "read_reference",
    "read_portfolio_inputs",
    "write_owned_state",
    "close_role_session",
}

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import validate_package as package_validator


class TestHostMcpAdapters(unittest.TestCase):
    def _claude_server(self):
        with CLAUDE_MCP_PATH.open(encoding="utf-8") as handle:
            config = json.load(handle)
        self.assertEqual(set(config), {"mcpServers"})
        self.assertIn("founder-os-state", config["mcpServers"])
        return config["mcpServers"]["founder-os-state"]

    def _codex_server(self):
        with CODEX_MANIFEST_PATH.open(encoding="utf-8") as handle:
            manifest = json.load(handle)
        self.assertIn("mcpServers", manifest)
        self.assertIn("founder-os-state", manifest["mcpServers"])
        return manifest["mcpServers"]["founder-os-state"]

    def test_both_hosts_declare_the_same_local_stdio_server(self):
        claude = self._claude_server()
        codex = self._codex_server()

        self.assertEqual(claude["command"], codex["command"])
        self.assertEqual(
            claude["args"],
            ["${CLAUDE_PLUGIN_ROOT}/mcp/founder_os_state.py"],
        )
        self.assertEqual(
            codex["args"],
            ["./mcp/founder_os_state.py"],
        )
        self.assertEqual(codex["cwd"], ".")

    def test_codex_declared_command_completes_initialize_handshake(self):
        codex = self._codex_server()
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "host-adapter-test", "version": "1"},
            },
        }

        result = subprocess.run(
            [codex["command"], *codex["args"]],
            input=json.dumps(request) + "\n",
            capture_output=True,
            text=True,
            cwd=PLUGIN_ROOT / codex["cwd"],
            timeout=5,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        response = json.loads(result.stdout.splitlines()[0])
        self.assertEqual(response["id"], 1)
        self.assertEqual(
            response["result"]["serverInfo"]["name"],
            "founder-os-state",
        )

    def test_declared_entry_is_the_single_shared_gateway_entry(self):
        self.assertTrue(ENTRY_PATH.is_file())
        compile(ENTRY_PATH.read_text(encoding="utf-8"), str(ENTRY_PATH), "exec")

        for adapter in (self._claude_server(), self._codex_server()):
            self.assertEqual(adapter["command"], "python3")
            self.assertEqual(len(adapter["args"]), 1)
            self.assertTrue(
                adapter["args"][0].endswith("/mcp/founder_os_state.py")
            )

    def test_gateway_exposes_only_the_contract_tool_set(self):
        sys.path.insert(0, str(PLUGIN_ROOT))
        try:
            from mcp.gateway import Gateway

            discovered = {
                schema["name"] for schema in Gateway().tool_schemas()
            }
        finally:
            sys.path.pop(0)

        self.assertEqual(discovered, TOOL_NAMES)

    def test_package_validator_accepts_both_host_adapter_shapes(self):
        self.assertEqual(
            package_validator.check_host_adapters(PLUGIN_ROOT, {}),
            [],
        )

    def test_package_validator_rejects_adapter_drift(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "founder-os"
            for relative in (
                ".mcp.json",
                ".codex-plugin/plugin.json",
                "mcp/founder_os_state.py",
                "hooks/record-agent.py",
                "hooks/ownership-guard.py",
            ):
                source = PLUGIN_ROOT / relative
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            manifest_path = root / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["mcpServers"]["founder-os-state"]["args"] = [
                "wrong-entry.py"
            ]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = package_validator.check_host_adapters(root, {})

        self.assertTrue(
            any("./mcp/founder_os_state.py" in error for error in errors),
            errors,
        )

    def test_package_validator_rejects_removing_both_adapters(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            errors = package_validator.check_host_adapters(
                Path(temp_dir) / "founder-os",
                {},
            )

        self.assertTrue(any(".mcp.json" in error for error in errors), errors)
        self.assertTrue(
            any(".codex-plugin/plugin.json" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("mcp/founder_os_state.py" in error for error in errors),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
