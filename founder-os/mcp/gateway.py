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

from .ownership import OwnershipError, OwnershipSchema
from .safe_io import SafeStateError, SafeStateIO
from .sessions import JournalError, RoleSessionError, RoleSessionStore
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
                "required": ["workspace_id", "role", "correlation_id", "workflow"],
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
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "cursor": {"type": "string"},
                },
                "required": ["capability", "pattern"],
                "additionalProperties": False,
            },
        },
        {
            "name": "read_state",
            "description": "Read one or more state records through a capability. Each record carries missing_sections: headings the ownership map declares for that path and the file does not have.",
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
            "name": "read_portfolio_inputs",
            "description": (
                "Read fixed goals and metrics summary sections for one active "
                "business from a portfolio session."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "capability": {"type": "string"},
                    "business_slug": {"type": "string"},
                },
                "required": ["capability", "business_slug"],
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
    _TOOL_ARGUMENTS = {
        schema["name"]: frozenset(schema["inputSchema"]["properties"])
        for schema in _TOOL_SCHEMAS
    }
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
        if not isinstance(arguments, Mapping):
            error = (
                WorkspaceResolutionError()
                if name == "resolve_workspace"
                else RoleSessionError()
            )
            return self._error(error)
        try:
            has_unknown_arguments = bool(
                set(arguments) - self._TOOL_ARGUMENTS[name]
            )
        except (TypeError, ValueError):
            has_unknown_arguments = True
        if has_unknown_arguments:
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
            elif name == "read_portfolio_inputs":
                payload = self._read_portfolio_inputs(arguments)
            elif name == "write_owned_state":
                payload = self._write_owned_state(arguments)
            else:
                payload = self._close_role_session(arguments)
            return self._success(payload)
        except (
            WorkspaceResolutionError,
            RoleSessionError,
            JournalError,
            OwnershipError,
            SafeStateError,
        ) as error:
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
            "workspace_kind": binding.workspace_kind,
        }

    def _open_role_session(self, arguments: Mapping[str, Any]) -> Dict[str, Any]:
        workspace_id = arguments.get("workspace_id")
        role = arguments.get("role")
        correlation_id = arguments.get("correlation_id")
        workflow = arguments.get("workflow")
        if not all(
            self._text(value)
            for value in (workspace_id, role, correlation_id, workflow)
        ):
            raise RoleSessionError()
        binding = self._resolver.get(workspace_id)
        capability = self._sessions.open(
            workspace_id,
            role,
            correlation_id,
            workflow=workflow,
            workspace_kind=binding.workspace_kind,
        )
        return {"capability": capability}

    def _list_state(self, arguments: Mapping[str, Any]) -> Dict[str, Any]:
        _, binding = self._session_workspace(arguments.get("capability"))
        pattern = arguments.get("pattern")
        limit = arguments.get("limit")
        cursor = arguments.get("cursor")
        if not self._text(pattern):
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
        if "cursor" in arguments and not self._text(cursor):
            raise SafeStateError("STATE_IO_ERROR")
        if "limit" in arguments and (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or limit < 1
            or limit > 100
        ):
            raise SafeStateError("STATE_IO_ERROR")
        io_handle = self._io(binding.root)
        try:
            return io_handle.list_markdown_page(
                pattern,
                limit=limit,
                cursor=cursor,
            )
        finally:
            io_handle.close()

    def _ownership_schema(self) -> OwnershipSchema:
        """The parsed ownership map, re-read only when the file changes.

        Every read and every write needs it, and it changes when the package is
        upgraded and at no other time. Parsing the whole map once per gateway
        call made a five-file workflow re-read and re-parse it five times.
        """
        path = self._packaged_root / "references" / "ownership.yaml"
        try:
            stamp = (path.stat().st_mtime_ns, path.stat().st_size)
        except OSError:
            raise OwnershipError("STATE_IO_ERROR")
        cached = getattr(self, "_ownership_cache", None)
        if cached is not None and cached[0] == stamp:
            return cached[1]
        schema = OwnershipSchema.load(path)
        self._ownership_cache = (stamp, schema)
        return schema

    def _read_state(self, arguments: Mapping[str, Any]) -> Dict[str, Any]:
        _, binding = self._session_workspace(arguments.get("capability"))
        paths = arguments.get("paths")
        if not isinstance(paths, list):
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
        io_handle = self._io(binding.root)
        try:
            files = io_handle.read_many(paths)
        finally:
            io_handle.close()
        # An unreadable ownership map fails the read the same way it already
        # fails the write. Reads used to degrade to no `missing_sections` at
        # all, which is a promise quietly withdrawn: a role branching on the
        # field stops seeing upgrade drift and nothing says so.
        schema = self._ownership_schema()
        for entry in files:
            entry["missing_sections"] = list(schema.missing_sections(
                str(entry.get("path") or ""),
                entry.get("content"),
            ))
        return {"files": files}

    def _read_reference(self, arguments: Mapping[str, Any]) -> Dict[str, Any]:
        metadata, binding = self._session_workspace(arguments.get("capability"))
        path = arguments.get("path")
        if not self._text(path):
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
        io_handle = self._io(binding.root)
        try:
            return {
                "file": io_handle.read_reference(
                    path,
                    role=metadata.role,
                    workflow=metadata.workflow,
                )
            }
        finally:
            io_handle.close()

    def _read_portfolio_inputs(
        self,
        arguments: Mapping[str, Any],
    ) -> Dict[str, Any]:
        metadata, binding = self._session_workspace(arguments.get("capability"))
        business_slug = arguments.get("business_slug")
        if (
            metadata.role != "portfolio-manager"
            or metadata.workflow != "portfolio-review"
            or metadata.workspace_kind != "portfolio"
            or not self._text(business_slug)
        ):
            raise RoleSessionError()

        business_root = self._resolver.portfolio_business_root(
            binding, business_slug
        )
        io_handle = self._io(business_root)
        try:
            payload = io_handle.read_fixed_sections(
                {
                    "goals.md": ("Bets",),
                    "metrics.md": ("Close", "Runway"),
                }
            )
        finally:
            io_handle.close()
        return {"business_slug": business_slug, **payload}

    def _write_owned_state(
        self,
        arguments: Mapping[str, Any],
    ) -> Dict[str, Any]:
        capability = arguments.get("capability")
        if not self._text(capability):
            raise RoleSessionError()
        metadata, binding = self._session_workspace(capability)

        raw_path = arguments.get("path")
        journal_path = raw_path if isinstance(raw_path, str) else ""
        create_only = arguments.get("create_only")
        expected_sha256 = arguments.get("expected_sha256")
        operation = "create" if create_only is True else "replace"
        io_handle: Optional[SafeStateIO] = None
        journal_descriptor = self._sessions.preflight_journal()

        try:
            try:
                if not self._text(raw_path):
                    raise OwnershipError("PATH_OUTSIDE_WORKSPACE")
                content = arguments.get("content")
                if not isinstance(content, str):
                    raise OwnershipError("INVALID_DOCUMENT_STRUCTURE")

                valid_expected = (
                    isinstance(expected_sha256, str)
                    and len(expected_sha256) == 64
                    and all(
                        character in "0123456789abcdef"
                        for character in expected_sha256
                    )
                )
                valid_create = create_only is True
                if valid_create == valid_expected:
                    raise OwnershipError("STALE_WRITE")
                if "create_only" in arguments and not valid_create:
                    raise OwnershipError("STALE_WRITE")
                if "expected_sha256" in arguments and not valid_expected:
                    raise OwnershipError("STALE_WRITE")

                schema = self._ownership_schema()
                owner = schema.owner_for(raw_path)
                if owner is None:
                    raise OwnershipError("PATH_OUTSIDE_WORKSPACE")
                if metadata.role != owner:
                    raise OwnershipError("ROLE_NOT_OWNER", owner=owner)
                schema.validate_document(raw_path, content)
                try:
                    content_bytes = content.encode("utf-8", errors="strict")
                except UnicodeEncodeError:
                    raise OwnershipError("INVALID_DOCUMENT_STRUCTURE")

                io_handle = self._io(binding.root)
                payload = io_handle.atomic_replace(
                    raw_path,
                    content_bytes,
                    expected_sha256=(
                        expected_sha256 if valid_expected else None
                    ),
                    create_only=valid_create,
                    declared_directory=schema.directory_for(raw_path),
                )
            except (OwnershipError, SafeStateError) as error:
                if journal_path:
                    self._sessions.append_journal(
                        metadata,
                        path=journal_path,
                        operation=operation,
                        result=error.code,
                        before_sha256=getattr(
                            error,
                            "before_sha256",
                            None,
                        ),
                        after_sha256=getattr(error, "after_sha256", None),
                        descriptor=journal_descriptor,
                    )
                raise
            finally:
                if io_handle is not None:
                    io_handle.close()

            try:
                self._sessions.append_journal(
                    metadata,
                    path=raw_path,
                    operation=str(payload["operation"]),
                    result="OK",
                    before_sha256=payload["before_sha256"],
                    after_sha256=payload["after_sha256"],
                    descriptor=journal_descriptor,
                )
            except Exception:
                # The atomic replace already landed. Reporting failure here
                # would invite a retry that overwrites a successful write.
                pass
            return payload
        finally:
            try:
                os.close(journal_descriptor)
            except OSError:
                pass

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
        self._resolver.validate_binding(binding)
        if metadata.workspace_kind != binding.workspace_kind:
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

TOOL_SCHEMAS = Gateway._TOOL_SCHEMAS
