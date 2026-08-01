"""Line-oriented JSON-RPC transport for the Founder OS local MCP server."""

from __future__ import annotations

import json
import math
from typing import Any, Dict, Optional, TextIO

from .gateway import Gateway, UnknownToolError


JSON_RPC_VERSION = "2.0"
MCP_PROTOCOL_VERSION = "2025-11-25"
MCP_PROTOCOL_VERSIONS = frozenset({"2025-11-25", "2025-06-18"})
SERVER_NAME = "founder-os-state"
SERVER_VERSION = "2.6.0"


def _response(request_id: Any, result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "jsonrpc": JSON_RPC_VERSION,
        "id": request_id,
        "result": result,
    }


def _error(request_id: Any, code: int, message: str) -> Dict[str, Any]:
    return {
        "jsonrpc": JSON_RPC_VERSION,
        "id": request_id,
        "error": {"code": code, "message": message},
    }


class ProtocolServer:
    """Translate JSON-RPC MCP messages into gateway calls."""

    def __init__(self, gateway: Optional[Gateway] = None) -> None:
        self._gateway = gateway if gateway is not None else Gateway()
        self._lifecycle = "new"

    def handle_message(self, message: dict) -> Optional[dict]:
        """Handle one decoded message, returning no response for notifications."""
        if not isinstance(message, dict):
            return _error(None, -32600, "Invalid Request")

        request_id = message.get("id")
        if (
            message.get("jsonrpc") != JSON_RPC_VERSION
            or "result" in message
            or "error" in message
            or ("id" in message and not self._valid_id(request_id))
        ):
            return _error(None, -32600, "Invalid Request")

        is_notification = "id" not in message
        method = message.get("method")

        if not isinstance(method, str):
            return _error(request_id if not is_notification else None, -32600, "Invalid Request")

        if "params" in message and not isinstance(
            message["params"], (dict, list)
        ):
            return (
                None
                if is_notification
                else _error(request_id, -32602, "Invalid params")
            )

        if method == "notifications/initialized":
            if is_notification and self._lifecycle == "initializing":
                self._lifecycle = "ready"
                return None
            if is_notification:
                return None
            return _error(request_id, -32601, "Method not found")

        if method == "initialize":
            if is_notification:
                return None
            if self._lifecycle != "new":
                return _error(request_id, -32600, "Invalid Request")
            params = message.get("params")
            if not self._valid_initialize_params(params):
                return _error(request_id, -32602, "Invalid params")
            requested_version = params["protocolVersion"]
            negotiated_version = (
                requested_version
                if requested_version in MCP_PROTOCOL_VERSIONS
                else MCP_PROTOCOL_VERSION
            )
            self._lifecycle = "initializing"
            return _response(
                request_id,
                {
                    "protocolVersion": negotiated_version,
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": SERVER_VERSION,
                    },
                },
            )

        if self._lifecycle != "ready":
            if is_notification:
                return None
            return _error(request_id, -32002, "Server not initialized")

        if method == "ping":
            if is_notification:
                return None
            params = message.get("params", {})
            if not isinstance(params, dict) or params:
                return _error(request_id, -32602, "Invalid params")
            return _response(request_id, {})

        if method == "notifications/cancelled":
            return None

        if method == "tools/list":
            if is_notification:
                return None
            return _response(request_id, {"tools": self._gateway.tool_schemas()})

        if method == "tools/call":
            if is_notification:
                return None
            params = message.get("params", {})
            if not isinstance(params, dict):
                return _error(request_id, -32602, "Invalid params")
            name = params.get("name")
            arguments = params.get("arguments", {})
            if not isinstance(name, str) or not isinstance(arguments, dict):
                return _error(request_id, -32602, "Invalid params")
            try:
                result = self._gateway.call(name, arguments)
            except UnknownToolError:
                return _error(request_id, -32601, "Method not found")
            return _response(request_id, result)

        return (
            None
            if is_notification
            else _error(request_id, -32601, "Method not found")
        )

    @staticmethod
    def _valid_id(value: object) -> bool:
        return (
            value is None
            or isinstance(value, str)
            or (
                not isinstance(value, bool)
                and isinstance(value, (int, float))
                and math.isfinite(float(value))
            )
        )

    @staticmethod
    def _valid_initialize_params(params: object) -> bool:
        if not isinstance(params, dict):
            return False
        protocol_version = params.get("protocolVersion")
        capabilities = params.get("capabilities")
        client_info = params.get("clientInfo")
        return (
            isinstance(protocol_version, str)
            and bool(protocol_version)
            and isinstance(capabilities, dict)
            and isinstance(client_info, dict)
            and isinstance(client_info.get("name"), str)
            and bool(client_info["name"])
            and isinstance(client_info.get("version"), str)
            and bool(client_info["version"])
        )


def _write_response(stdout: TextIO, response: Dict[str, Any]) -> None:
    stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
    stdout.flush()


def serve(stdin: TextIO, stdout: TextIO, stderr: TextIO) -> int:
    """Serve JSON-RPC requests from stdin until EOF.

    Protocol data is written only to stdout as one JSON object per line.
    Diagnostics are written only to stderr.
    """
    server = ProtocolServer()
    for raw_line in stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as error:
            stderr.write("Malformed JSON-RPC message: {}\n".format(error.msg))
            stderr.flush()
            _write_response(stdout, _error(None, -32700, "Parse error"))
            continue

        try:
            response = server.handle_message(message)
        except Exception as error:  # pragma: no cover - defensive transport guard
            stderr.write("Internal MCP server error: {}\n".format(error))
            stderr.flush()
            request_id = message.get("id") if isinstance(message, dict) else None
            response = _error(request_id, -32603, "Internal error")

        if response is not None:
            _write_response(stdout, response)

    return 0
