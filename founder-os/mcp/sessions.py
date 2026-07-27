"""Role-scoped, opaque session capabilities for Founder OS MCP reads."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional


_INVALID_CODE = "ROLE_SESSION_INVALID"
_INVALID_ACTION = "Stop and return control to the main thread"


class RoleSessionError(Exception):
    def __init__(self) -> None:
        super().__init__(_INVALID_CODE)
        self.code = _INVALID_CODE
        self.action = _INVALID_ACTION


@dataclass(frozen=True)
class RoleSessionMetadata:
    workspace_id: str
    role: str
    correlation_id: str
    workflow: Optional[str]
    expires_at: float
    status: str
    final_status: Optional[str] = None


class RoleSessionStore:
    """Persist only hashed session capabilities and session metadata."""

    def __init__(
        self,
        data_root: Path,
        packaged_root: Path,
        clock: Callable[[], float],
        ttl_seconds: float,
    ) -> None:
        self._data_root = Path(data_root)
        self._packaged_root = Path(packaged_root).resolve()
        self._clock = clock
        self._ttl_seconds = ttl_seconds

    def open(
        self,
        workspace_id: str,
        role: str,
        correlation_id: str,
        workflow: Optional[str] = None,
    ) -> str:
        if not self._valid_text(workspace_id) or not self._valid_text(correlation_id):
            raise RoleSessionError()
        if role not in self._roles():
            raise RoleSessionError()
        if workflow is not None and not self._valid_workflow(workflow):
            raise RoleSessionError()

        capability = secrets.token_urlsafe(32)
        record = {
            "capability_hash": self._capability_hash(capability),
            "workspace_id": workspace_id,
            "role": role,
            "correlation_id": correlation_id,
            "workflow": workflow,
            "expires_at": self._clock() + self._ttl_seconds,
            "status": "open",
        }
        self._write_record(record)
        return capability

    def resolve(
        self,
        capability: str,
        workspace_id: Optional[str] = None,
        role: Optional[str] = None,
    ) -> RoleSessionMetadata:
        record = self._load_open_record(capability)
        if workspace_id is not None and record["workspace_id"] != workspace_id:
            raise RoleSessionError()
        if role is not None and record["role"] != role:
            raise RoleSessionError()
        return self._metadata(record)

    def close(
        self,
        capability: str,
        final_status: Optional[str] = None,
    ) -> RoleSessionMetadata:
        record = self._load_open_record(capability)
        record["status"] = "closed"
        if final_status is not None:
            record["final_status"] = final_status
        self._write_record(record)
        return self._metadata(record)

    def _load_open_record(self, capability: str) -> dict:
        if not self._valid_text(capability):
            raise RoleSessionError()
        capability_hash = self._capability_hash(capability)
        path = self._record_path(capability_hash)
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            raise RoleSessionError()

        required = {
            "capability_hash",
            "workspace_id",
            "role",
            "correlation_id",
            "workflow",
            "expires_at",
            "status",
        }
        if not isinstance(record, dict) or not required.issubset(record):
            raise RoleSessionError()
        if record["capability_hash"] != capability_hash:
            raise RoleSessionError()
        if record["status"] != "open":
            raise RoleSessionError()

        try:
            expired = self._clock() >= float(record["expires_at"])
        except (TypeError, ValueError):
            raise RoleSessionError()
        if expired:
            record["status"] = "expired"
            self._write_record(record)
            raise RoleSessionError()
        return record

    def _roles(self) -> set[str]:
        agents = self._packaged_root / "agents"
        try:
            roles = {
                path.stem
                for path in agents.iterdir()
                if path.is_file() and path.suffix == ".md"
            }
        except OSError:
            return set()
        return roles if len(roles) == 13 else set()

    def _valid_workflow(self, workflow: str) -> bool:
        if not self._valid_text(workflow):
            return False
        skills = (self._packaged_root / "skills").resolve()
        candidate = (skills / workflow).resolve()
        try:
            candidate.relative_to(skills)
        except ValueError:
            return False
        return candidate.is_dir() and (candidate / "SKILL.md").is_file()

    @staticmethod
    def _valid_text(value: object) -> bool:
        return isinstance(value, str) and bool(value.strip())

    @staticmethod
    def _capability_hash(capability: str) -> str:
        return hashlib.sha256(capability.encode("utf-8")).hexdigest()

    def _record_path(self, capability_hash: str) -> Path:
        return self._data_root / (capability_hash + ".json")

    def _write_record(self, record: dict) -> None:
        capability_hash = record.get("capability_hash")
        if not isinstance(capability_hash, str):
            raise RoleSessionError()
        self._data_root.mkdir(parents=True, exist_ok=True)
        destination = self._record_path(capability_hash)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".session-",
            suffix=".tmp",
            dir=str(self._data_root),
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(record, handle, sort_keys=True, separators=(",", ":"))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, destination)
        except OSError:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass
            raise RoleSessionError()

    @staticmethod
    def _metadata(record: dict) -> RoleSessionMetadata:
        return RoleSessionMetadata(
            workspace_id=record["workspace_id"],
            role=record["role"],
            correlation_id=record["correlation_id"],
            workflow=record["workflow"],
            expires_at=float(record["expires_at"]),
            status=record["status"],
            final_status=record.get("final_status"),
        )
