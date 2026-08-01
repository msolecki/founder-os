"""Line-oriented JSON-RPC transport for the Founder OS local MCP server."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, TextIO

from .gateway import Gateway, UnknownToolError


JSON_RPC_VERSION = "2.0"
MCP_PROTOCOL_VERSION = "2025-06-18"
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

    def handle_message(self, message: dict) -> Optional[dict]:
        """Handle one decoded message, returning no response for notifications."""
        if not isinstance(message, dict):
            return _error(None, -32600, "Invalid Request")

        request_id = message.get("id")
        is_notification = "id" not in message
        method = message.get("method")

        if not isinstance(method, str):
            return (
                None
                if is_notification
                else _error(request_id, -32600, "Invalid Request")
            )

        if method == "notifications/initialized":
            return None

        if method == "initialize":
            if is_notification:
                return None
            return _response(
                request_id,
                {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": SERVER_VERSION,
                    },
                },
            )

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
