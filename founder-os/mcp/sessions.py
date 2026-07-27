"""Role-scoped, opaque session capabilities for Founder OS MCP reads."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import secrets
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional


_INVALID_CODE = "ROLE_SESSION_INVALID"
_INVALID_ACTION = "Stop and return control to the main thread"
_CAPABILITY_HASH_PATTERN = re.compile(r"[0-9a-f]{64}")
_BASE_RECORD_FIELDS = frozenset(
    {
        "capability_hash",
        "workspace_id",
        "role",
        "correlation_id",
        "workflow",
        "expires_at",
        "status",
    }
)
_ALLOWED_STATUSES = frozenset({"open", "closed", "expired"})


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
        if not self._valid_text(workspace_id):
            raise RoleSessionError()
        if not self._valid_text(correlation_id):
            raise RoleSessionError()
        if role not in self._roles():
            raise RoleSessionError()
        if workflow is not None and not self._valid_workflow(workflow):
            raise RoleSessionError()

        now = self._now()
        if (
            isinstance(self._ttl_seconds, bool)
            or not isinstance(self._ttl_seconds, (int, float))
            or not math.isfinite(float(self._ttl_seconds))
            or float(self._ttl_seconds) <= 0
        ):
            raise RoleSessionError()

        expires_at = now + float(self._ttl_seconds)
        if not math.isfinite(expires_at) or expires_at <= now:
            raise RoleSessionError()

        capability = secrets.token_urlsafe(32)
        record = {
            "capability_hash": self._capability_hash(capability),
            "workspace_id": workspace_id,
            "role": role,
            "correlation_id": correlation_id,
            "workflow": workflow,
            "expires_at": expires_at,
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
        if final_status is not None and not self._valid_text(final_status):
            raise RoleSessionError()

        record = self._load_open_record(capability)
        record["status"] = "closed"
        if final_status is not None:
            record["final_status"] = final_status
        self._write_record(record)
        return self._metadata(record)

    def _load_open_record(self, capability: str) -> dict[str, object]:
        if not self._valid_text(capability):
            raise RoleSessionError()

        capability_hash = self._capability_hash(capability)
        path = self._record_path(capability_hash)
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError):
            raise RoleSessionError()

        if not self._valid_record(record, expected_hash=capability_hash):
            raise RoleSessionError()
        if record["status"] != "open":
            raise RoleSessionError()

        now = self._now()
        expires_at = float(record["expires_at"])
        if now >= expires_at:
            record["status"] = "expired"
            self._write_record(record)
            raise RoleSessionError()
        return record

    def _valid_record(
        self,
        record: object,
        *,
        expected_hash: Optional[str] = None,
    ) -> bool:
        if not isinstance(record, dict):
            return False

        status = record.get("status")
        if not isinstance(status, str) or status not in _ALLOWED_STATUSES:
            return False

        fields = set(record)
        if status in ("open", "expired"):
            if fields != _BASE_RECORD_FIELDS:
                return False
        elif fields not in (
            _BASE_RECORD_FIELDS,
            _BASE_RECORD_FIELDS | {"final_status"},
        ):
            return False

        capability_hash = record.get("capability_hash")
        if (
            not isinstance(capability_hash, str)
            or _CAPABILITY_HASH_PATTERN.fullmatch(capability_hash) is None
            or (
                expected_hash is not None
                and capability_hash != expected_hash
            )
        ):
            return False

        if not self._valid_text(record.get("workspace_id")):
            return False
        if not self._valid_text(record.get("correlation_id")):
            return False

        role = record.get("role")
        if not isinstance(role, str) or role not in self._roles():
            return False

        workflow = record.get("workflow")
        if workflow is not None and (
            not isinstance(workflow, str)
            or not self._valid_workflow(workflow)
        ):
            return False

        expires_at = record.get("expires_at")
        if (
            isinstance(expires_at, bool)
            or not isinstance(expires_at, (int, float))
            or not math.isfinite(float(expires_at))
        ):
            return False

        if "final_status" in record and not self._valid_text(
            record["final_status"]
        ):
            return False
        return True

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

    def _now(self) -> float:
        try:
            value = self._clock()
        except Exception:
            raise RoleSessionError()
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        ):
            raise RoleSessionError()
        return float(value)

    @staticmethod
    def _valid_text(value: object) -> bool:
        return (
            isinstance(value, str)
            and bool(value.strip())
            and "\x00" not in value
        )

    @staticmethod
    def _capability_hash(capability: str) -> str:
        return hashlib.sha256(capability.encode("utf-8")).hexdigest()

    def _record_path(self, capability_hash: str) -> Path:
        return self._data_root / (capability_hash + ".json")

    def _write_record(self, record: dict[str, object]) -> None:
        if not self._valid_record(record):
            raise RoleSessionError()

        temporary_name: Optional[str] = None
        try:
            self._data_root.mkdir(parents=True, exist_ok=True)
            destination = self._record_path(str(record["capability_hash"]))
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=".session-",
                suffix=".tmp",
                dir=str(self._data_root),
            )
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(
                    record,
                    handle,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, destination)
            temporary_name = None
        except (OSError, TypeError, ValueError):
            raise RoleSessionError()
        finally:
            if temporary_name is not None:
                try:
                    os.unlink(temporary_name)
                except OSError:
                    pass

    @staticmethod
    def _metadata(record: dict[str, object]) -> RoleSessionMetadata:
        final_status = record.get("final_status")
        return RoleSessionMetadata(
            workspace_id=str(record["workspace_id"]),
            role=str(record["role"]),
            correlation_id=str(record["correlation_id"]),
            workflow=(
                str(record["workflow"])
                if record["workflow"] is not None
                else None
            ),
            expires_at=float(record["expires_at"]),
            status=str(record["status"]),
            final_status=(
                str(final_status) if final_status is not None else None
            ),
        )
