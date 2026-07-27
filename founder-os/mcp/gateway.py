"""Tool boundary for the Founder OS MCP protocol shell.

State behavior is deliberately deferred. This module owns the public tool
catalogue and is the only place protocol messages may dispatch tool calls.
"""

from __future__ import annotations

from copy import deepcopy
import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional

from .safe_io import SafeStateError, SafeStateIO
from .sessions import RoleSessionError, RoleSessionStore
from .workspaces import WorkspaceResolutionError, WorkspaceResolver


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
    DEFAULT_SESSION_TTL_SECONDS = 300

    def __init__(
        self,
        resolver: Optional[WorkspaceResolver] = None,
        sessions: Optional[RoleSessionStore] = None,
        packaged_root: Optional[Path] = None,
        io_factory: Optional[Callable[[Path, Path], SafeStateIO]] = None,
    ) -> None:
        self._packaged_root = (
            Path(packaged_root).resolve()
            if packaged_root is not None
            else Path(__file__).resolve().parents[1]
        )
        self._resolver = resolver if resolver is not None else WorkspaceResolver()
        self._sessions = (
            sessions
            if sessions is not None
            else RoleSessionStore(
                data_root=self._default_data_root(),
                packaged_root=self._packaged_root,
                clock=time.time,
                ttl_seconds=self.DEFAULT_SESSION_TTL_SECONDS,
            )
        )
        self._io_factory = io_factory

    def tool_schemas(self) -> List[Dict[str, Any]]:
        """Return a detached copy of the public MCP tool schemas."""
        return deepcopy(list(self._TOOL_SCHEMAS))

    def call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch a known tool through its bounded state interface."""
        if name not in self._TOOL_NAMES:
            raise UnknownToolError(name)
        if name == "write_owned_state":
            return self._write_placeholder(name)
        if not isinstance(arguments, Mapping):
            error = (
                WorkspaceResolutionError()
                if name == "resolve_workspace"
                else RoleSessionError()
            )
            return self._error(error)

        try:
            if name == "resolve_workspace":
                payload = self._resolve_workspace(arguments)
            elif name == "open_role_session":
                payload = self._open_role_session(arguments)
            elif name == "list_state":
                payload = self._list_state(arguments)
            elif name == "read_state":
                payload = self._read_state(arguments)
            elif name == "read_reference":
                payload = self._read_reference(arguments)
            else:
                payload = self._close_role_session(arguments)
            return self._success(payload)
        except (WorkspaceResolutionError, RoleSessionError, SafeStateError) as error:
            return self._error(error)
        except (OSError, UnicodeError, TypeError, ValueError, KeyError):
            return self._error(SafeStateError("STATE_IO_ERROR"))

    def _resolve_workspace(self, arguments: Mapping[str, Any]) -> Dict[str, Any]:
        project_dir = arguments.get("project_dir")
        business_slug = arguments.get("business_slug")
        if not self._text(project_dir) or (
            business_slug is not None and not self._text(business_slug)
        ):
            raise WorkspaceResolutionError()
        binding = self._resolver.resolve(Path(project_dir), business_slug)
        return {
            "workspace_id": binding.workspace_id,
            "business_slug": binding.business_slug,
            "display_path": binding.display_path,
        }

    def _open_role_session(self, arguments: Mapping[str, Any]) -> Dict[str, Any]:
        workspace_id = arguments.get("workspace_id")
        role = arguments.get("role")
        correlation_id = arguments.get("correlation_id")
        workflow = arguments.get("workflow")
        if not all(
            self._text(value)
            for value in (workspace_id, role, correlation_id)
        ):
            raise RoleSessionError()
        if workflow is not None and not self._text(workflow):
            raise RoleSessionError()
        self._resolver.get(workspace_id)
        capability = self._sessions.open(
            workspace_id,
            role,
            correlation_id,
            workflow=workflow,
        )
        return {"capability": capability}

    def _list_state(self, arguments: Mapping[str, Any]) -> Dict[str, Any]:
        _, binding = self._session_workspace(arguments.get("capability"))
        pattern = arguments.get("pattern")
        if not self._text(pattern):
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
        return {"paths": self._io(binding.root).list_markdown(pattern)}

    def _read_state(self, arguments: Mapping[str, Any]) -> Dict[str, Any]:
        _, binding = self._session_workspace(arguments.get("capability"))
        paths = arguments.get("paths")
        if not isinstance(paths, list):
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
        return {"files": self._io(binding.root).read_many(paths)}

    def _read_reference(self, arguments: Mapping[str, Any]) -> Dict[str, Any]:
        metadata, binding = self._session_workspace(arguments.get("capability"))
        path = arguments.get("path")
        if not self._text(path):
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
        return {
            "file": self._io(binding.root).read_reference(
                path,
                role=metadata.role,
                workflow=metadata.workflow,
            )
        }

    def _close_role_session(self, arguments: Mapping[str, Any]) -> Dict[str, Any]:
        capability = arguments.get("capability")
        final_status = arguments.get("final_status")
        if not self._text(capability) or (
            final_status is not None and not self._text(final_status)
        ):
            raise RoleSessionError()
        self._sessions.close(capability, final_status=final_status)
        return {"closed": True, "final_status": final_status}

    def _session_workspace(self, capability: object):
        if not self._text(capability):
            raise RoleSessionError()
        metadata = self._sessions.resolve(capability)
        try:
            binding = self._resolver.get(metadata.workspace_id)
        except WorkspaceResolutionError:
            raise RoleSessionError()
        return metadata, binding

    def _io(self, workspace_root: Path) -> SafeStateIO:
        if self._io_factory is None:
            return SafeStateIO(workspace_root, self._packaged_root)
        return self._io_factory(workspace_root, self._packaged_root)

    @staticmethod
    def _text(value: object) -> bool:
        return isinstance(value, str) and bool(value.strip())

    @staticmethod
    def _default_data_root() -> Path:
        configured = os.environ.get("PLUGIN_DATA") or os.environ.get(
            "CLAUDE_PLUGIN_DATA"
        )
        if configured:
            return Path(configured) / "state-gateway"
        return Path.home() / ".founder-os" / "plugin-data" / "state-gateway"

    @staticmethod
    def _success(payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "isError": False,
            "content": [
                {"type": "text", "text": json.dumps(payload, sort_keys=True)}
            ],
            "structuredContent": payload,
        }

    @staticmethod
    def _error(error: Exception) -> Dict[str, Any]:
        payload = {
            "error": {
                "code": error.code,
                "message": "Request could not be completed",
                "action": error.action,
            }
        }
        return {
            "isError": True,
            "content": [
                {"type": "text", "text": json.dumps(payload, sort_keys=True)}
            ],
            "structuredContent": payload,
        }

    @staticmethod
    def _write_placeholder(name: str) -> Dict[str, Any]:
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


TOOL_SCHEMAS = Gateway._TOOL_SCHEMAS
