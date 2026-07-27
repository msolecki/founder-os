"""Tool boundary for the Founder OS MCP protocol shell.

State behavior is deliberately deferred. This module owns the public tool
catalogue and is the only place protocol messages may dispatch tool calls.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List


class UnknownToolError(Exception):
    """Raised when an MCP request names a tool outside this gateway's catalog."""


class Gateway:
    """Expose the stable Founder OS MCP tool catalogue."""

    _TOOL_SCHEMAS = (
        {
            "name": "resolve_workspace",
            "description": "Resolve a Founder OS workspace from its local project.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "business_slug": {"type": "string"},
                    "project_dir": {"type": "string"},
                },
                "required": ["project_dir"],
                "additionalProperties": False,
            },
        },
        {
            "name": "open_role_session",
            "description": "Open a capability-scoped Founder OS role session.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string"},
                    "role": {"type": "string"},
                    "correlation_id": {"type": "string"},
                    "workflow": {"type": "string"},
                },
                "required": ["workspace_id", "role", "correlation_id"],
                "additionalProperties": False,
            },
        },
        {
            "name": "list_state",
            "description": "List state records available through a capability.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "capability": {"type": "string"},
                    "pattern": {"type": "string"},
                },
                "required": ["capability", "pattern"],
                "additionalProperties": False,
            },
        },
        {
            "name": "read_state",
            "description": "Read one or more state records through a capability.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "capability": {"type": "string"},
                    "paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                    },
                },
                "required": ["capability", "paths"],
                "additionalProperties": False,
            },
        },
        {
            "name": "read_reference",
            "description": "Read a workspace reference through a capability.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "capability": {"type": "string"},
                    "path": {"type": "string"},
                },
                "required": ["capability", "path"],
                "additionalProperties": False,
            },
        },
        {
            "name": "write_owned_state",
            "description": "Write a role-owned state record through a capability.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "capability": {"type": "string"},
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                    "expected_sha256": {
                        "type": "string",
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "create_only": {"type": "boolean"},
                },
                "required": ["capability", "path", "content"],
                "oneOf": [
                    {"required": ["expected_sha256"]},
                    {
                        "properties": {"create_only": {"const": True}},
                        "required": ["create_only"],
                    },
                ],
                "additionalProperties": False,
            },
        },
        {
            "name": "close_role_session",
            "description": "Close a capability-scoped Founder OS role session.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "capability": {"type": "string"},
                    "final_status": {"type": "string"},
                },
                "required": ["capability"],
                "additionalProperties": False,
            },
        },
    )
    _TOOL_NAMES = frozenset(schema["name"] for schema in _TOOL_SCHEMAS)

    def tool_schemas(self) -> List[Dict[str, Any]]:
        """Return a detached copy of the public MCP tool schemas."""
        return deepcopy(list(self._TOOL_SCHEMAS))

    def call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch a known tool call.

        The protocol shell intentionally exposes no business behavior yet. A
        known tool therefore returns a valid MCP tool error result, preserving
        the boundary that later state implementations will fill in.
        """
        if name not in self._TOOL_NAMES:
            raise UnknownToolError(name)

        return {
            "isError": True,
            "content": [
                {
                    "type": "text",
                    "text": (
                        "The Founder OS state operation '{}' is not implemented "
                        "in this protocol shell."
                    ).format(name),
                }
            ],
        }
