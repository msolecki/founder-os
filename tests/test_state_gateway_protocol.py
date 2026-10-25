"""Contract tests for the Founder OS local stdio MCP protocol shell."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPOSITORY_ROOT / "founder-os"
ENTRYPOINT = PACKAGE_ROOT / "mcp" / "founder_os_state.py"
TOOL_NAMES = (
    "resolve_workspace",
    "open_role_session",
    "list_state",
    "read_state",
    "read_reference",
    "read_portfolio_inputs",
    "write_owned_state",
    "close_role_session",
)


def _request(request_id: int, method: str, params: object | None = None) -> dict:
    message = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        message["params"] = params
    return message


def _line(message: dict) -> str:
    return json.dumps(message, separators=(",", ":"))


def _initialize(request_id: int, version: str = "2025-11-25") -> dict:
    return _request(
        request_id,
        "initialize",
        {
            "protocolVersion": version,
            "capabilities": {},
            "clientInfo": {"name": "contract-test", "version": "1.0"},
        },
    )


def _run_gateway(*messages: object) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    package_path = str(PACKAGE_ROOT)
    existing_python_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        package_path
        if not existing_python_path
        else package_path + os.pathsep + existing_python_path
    )
    return subprocess.run(
        [sys.executable, str(ENTRYPOINT)],
        cwd=REPOSITORY_ROOT,
        env=environment,
        input="\n".join(
            item if isinstance(item, str) else _line(item) for item in messages
        )
        + "\n",
        capture_output=True,
        check=False,
        text=True,
    )


def _run_gateway_bytes(payload: bytes) -> subprocess.CompletedProcess[str]:
    """Like `_run_gateway`, for input text mode cannot carry (invalid UTF-8)."""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(PACKAGE_ROOT)
    environment["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        [sys.executable, str(ENTRYPOINT)],
        cwd=REPOSITORY_ROOT,
        env=environment,
        input=payload + b"\n",
        capture_output=True,
        check=False,
    )
    return subprocess.CompletedProcess(
        completed.args,
        completed.returncode,
        completed.stdout.decode("utf-8"),
        completed.stderr.decode("utf-8", errors="replace"),
    )


class ProtocolServerContractTests(unittest.TestCase):
    def setUp(self) -> None:
        sys.path.insert(0, str(PACKAGE_ROOT))

    def tearDown(self) -> None:
        sys.path.remove(str(PACKAGE_ROOT))

    def test_handle_message_routes_tool_calls_only_through_gateway(self) -> None:
        from mcp.protocol import ProtocolServer

        class RecordingGateway:
            def __init__(self) -> None:
                self.calls: list[tuple[str, object]] = []

            def tool_schemas(self) -> list[dict]:
                return [
                    {
                        "name": "resolve_workspace",
                        "description": "Resolve the local Founder OS workspace.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                            "additionalProperties": False,
                        },
                    }
                ]

            def call(self, name: str, arguments: object) -> dict:
                self.calls.append((name, arguments))
                return {"content": [{"type": "text", "text": "dispatched"}]}

        gateway = RecordingGateway()
        server = ProtocolServer(gateway)
        server.handle_message(_initialize(1))
        server.handle_message(
            {"jsonrpc": "2.0", "method": "notifications/initialized"}
        )

        response = server.handle_message(
            _request(7, "tools/call", {"name": "resolve_workspace", "arguments": {}})
        )

        self.assertEqual(
            gateway.calls,
            [("resolve_workspace", {})],
            "ProtocolServer must delegate tool execution to Gateway.call().",
        )
        self.assertEqual(
            response,
            {
                "jsonrpc": "2.0",
                "id": 7,
                "result": {"content": [{"type": "text", "text": "dispatched"}]},
            },
        )


class StdioGatewayContractTests(unittest.TestCase):
    def test_initialize_negotiates_both_supported_versions_and_falls_back_latest(self) -> None:
        for requested, negotiated in (
            ("2025-06-18", "2025-06-18"),
            ("2025-11-25", "2025-11-25"),
            ("2099-01-01", "2025-11-25"),
        ):
            with self.subTest(requested=requested):
                completed = _run_gateway(_initialize(1, requested))
                self.assertEqual(completed.returncode, 0, completed.stderr)
                responses = [
                    json.loads(line) for line in completed.stdout.splitlines()
                ]
                self.assertEqual(len(responses), 1)
                response = responses[0]
                self.assertEqual(response["jsonrpc"], "2.0")
                self.assertEqual(response["id"], 1)
                self.assertEqual(
                    response["result"]["protocolVersion"], negotiated
                )
                self.assertEqual(
                    response["result"]["serverInfo"]["name"],
                    "founder-os-state",
                )
                self.assertEqual(
                    response["result"]["capabilities"], {"tools": {}}
                )

    def test_initialized_notification_is_silent_and_tools_list_has_exact_tools(self) -> None:
        completed = _run_gateway(
            _initialize(1),
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            _request(2, "tools/list"),
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        responses = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual([response["id"] for response in responses], [1, 2])
        tools = responses[1]["result"]["tools"]
        self.assertEqual(tuple(tool["name"] for tool in tools), TOOL_NAMES)
        self.assertEqual(len(tools), len(TOOL_NAMES))
        for tool in tools:
            self.assertIsInstance(tool.get("description"), str)
            self.assertTrue(tool["description"])
            self.assertIsInstance(tool.get("inputSchema"), dict)
            self.assertEqual(tool["inputSchema"].get("type"), "object")

    def test_tools_call_is_dispatched_by_the_running_gateway(self) -> None:
        completed = _run_gateway(
            _initialize(1),
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            _request(
                2,
                "tools/call",
                {"name": "resolve_workspace", "arguments": {}},
            ),
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        responses = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual(responses[-1]["id"], 2)
        result = responses[-1]["result"]
        self.assertIn("content", result)
        self.assertIsInstance(result["content"], list)

    def test_unknown_tool_returns_a_json_rpc_error(self) -> None:
        completed = _run_gateway(
            _initialize(1),
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            _request(2, "tools/call", {"name": "missing_tool", "arguments": {}}),
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        responses = [json.loads(line) for line in completed.stdout.splitlines()]
        error = responses[-1]["error"]
        self.assertEqual(responses[-1]["id"], 2)
        # The method exists, so an unknown tool name is Invalid params.
        self.assertEqual(error["code"], -32602)

    def test_ping_is_answered_before_initialize_and_null_ids_are_rejected(self) -> None:
        completed = _run_gateway(
            _request(1, "ping"),
            {"jsonrpc": "2.0", "id": None, "method": "ping"},
            _initialize(2),
            _request(3, "ping"),
        )
        responses = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual({"jsonrpc": "2.0", "id": 1, "result": {}}, responses[0])
        self.assertEqual(-32600, responses[1]["error"]["code"])
        self.assertIn("result", responses[2])
        self.assertEqual({"jsonrpc": "2.0", "id": 3, "result": {}}, responses[3])

    def test_malformed_json_returns_parse_error_and_diagnostic_stays_on_stderr(self) -> None:
        completed = _run_gateway('{"jsonrpc":"2.0","id":1,"method":')

        self.assertEqual(completed.returncode, 0, completed.stderr)
        responses = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual(len(responses), 1)
        self.assertIsNone(responses[0]["id"])
        self.assertEqual(responses[0]["error"]["code"], -32700)
        self.assertTrue(completed.stderr.strip())

    def test_bad_lines_cost_a_parse_error_and_the_next_request_is_served(self) -> None:
        cases = {
            "deep nesting": b"[" * 100000,
            "invalid utf-8": b"\xff\xfe\xfd",
        }
        for label, bad_line in cases.items():
            with self.subTest(case=label):
                completed = _run_gateway_bytes(
                    bad_line + b"\n" + _line(_request(2, "ping")).encode()
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                responses = [
                    json.loads(line) for line in completed.stdout.splitlines()
                ]
                self.assertEqual(-32700, responses[0]["error"]["code"])
                self.assertIsNone(responses[0]["id"])
                self.assertEqual({"jsonrpc": "2.0", "id": 2, "result": {}}, responses[1])

    def test_lifecycle_blocks_tools_until_initialized_and_rejects_reinitialize(self) -> None:
        completed = _run_gateway(
            _request(1, "tools/list"),
            _initialize(2),
            _request(3, "tools/list"),
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            _request(4, "tools/list"),
            _initialize(5),
        )
        responses = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual([item["id"] for item in responses], [1, 2, 3, 4, 5])
        self.assertEqual(responses[0]["error"]["code"], -32002)
        self.assertIn("result", responses[1])
        self.assertEqual(responses[2]["error"]["code"], -32002)
        self.assertEqual(len(responses[3]["result"]["tools"]), 8)
        self.assertEqual(responses[4]["error"]["code"], -32600)

    def test_ping_requires_ready_lifecycle_and_returns_empty_result(self) -> None:
        completed = _run_gateway(
            _initialize(1),
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            _request(2, "ping", {"_meta": {"progressToken": "probe"}}),
        )
        responses = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual(responses[-1], {"jsonrpc": "2.0", "id": 2, "result": {}})

    def test_list_and_ping_validate_mcp_request_params(self) -> None:
        completed = _run_gateway(
            _initialize(1),
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            _request(2, "tools/list", []),
            _request(3, "tools/list", {"cursor": "never-issued"}),
            _request(4, "tools/list", {"_meta": {"trace": "local"}}),
            _request(5, "ping", {"unexpected": True}),
        )
        responses = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual(-32602, responses[1]["error"]["code"])
        # MCP allows a pagination cursor; one page holds every tool.
        self.assertEqual(8, len(responses[2]["result"]["tools"]))
        self.assertEqual(8, len(responses[3]["result"]["tools"]))
        self.assertEqual(-32602, responses[4]["error"]["code"])

    def test_tools_list_refuses_a_non_string_cursor_and_other_params(self) -> None:
        completed = _run_gateway(
            _initialize(1),
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            _request(2, "tools/list", {"cursor": 7}),
            _request(3, "tools/list", {"cursor": "x", "extra": True}),
        )
        responses = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual(-32602, responses[1]["error"]["code"])
        self.assertEqual(-32602, responses[2]["error"]["code"])

    def test_notification_method_sent_as_request_receives_an_error(self) -> None:
        completed = _run_gateway(
            _initialize(1),
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            _request(9, "notifications/cancelled", {"requestId": 1}),
        )
        responses = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual(2, len(responses))
        self.assertEqual(9, responses[-1]["id"])
        self.assertEqual(-32601, responses[-1]["error"]["code"])

    def test_invalid_json_rpc_envelope_and_initialize_params_are_rejected(self) -> None:
        completed = _run_gateway(
            {"jsonrpc": "1.0", "id": 1, "method": "initialize", "params": {}},
            _request(2, "initialize", {"protocolVersion": "2025-11-25"}),
            {"jsonrpc": "2.0", "id": True, "method": "initialize", "params": {}},
        )
        responses = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual([item["error"]["code"] for item in responses], [-32600, -32602, -32600])

    def test_stdout_is_strictly_one_json_rpc_object_per_line(self) -> None:
        completed = _run_gateway(
            _initialize(1),
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            _request(2, "tools/list"),
            _request(3, "tools/call", {"name": "resolve_workspace", "arguments": {}}),
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        lines = completed.stdout.splitlines()
        self.assertEqual(len(lines), 3)
        for line in lines:
            self.assertTrue(line.startswith("{"), line)
            self.assertTrue(line.endswith("}"), line)
            response = json.loads(line)
            self.assertEqual(response["jsonrpc"], "2.0")



class NativeWindowsTests(unittest.TestCase):
    def test_native_windows_exits_with_wsl_guidance_before_importing_fcntl(self) -> None:
        import contextlib
        import io
        import runpy
        from unittest import mock

        stderr = io.StringIO()
        with mock.patch.object(sys, "platform", "win32"), \
                contextlib.redirect_stderr(stderr), \
                self.assertRaises(SystemExit) as raised:
            runpy.run_path(str(ENTRYPOINT), run_name="__main__")

        self.assertEqual(raised.exception.code, 1)
        self.assertIn("wsl --install", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
