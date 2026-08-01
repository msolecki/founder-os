"""Role-scoped, opaque session capabilities for Founder OS MCP reads."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import secrets
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional, Set


_INVALID_CODE = "ROLE_SESSION_INVALID"
_INVALID_ACTION = "Stop and return control to the main thread"
_CAPABILITY_HASH_PATTERN = re.compile(r"[0-9a-f]{64}")
_BASE_RECORD_FIELDS = frozenset(
    {
        "capability_hash",
        "workspace_id",
        "workspace_kind",
        "role",
        "correlation_id",
        "workflow",
        "expires_at",
        "status",
    }
)
_ALLOWED_STATUSES = frozenset({"open", "closed", "expired"})
_BUSINESS_WORKSPACE_KINDS = frozenset({"single-business", "business"})
_WORKSPACE_KINDS = _BUSINESS_WORKSPACE_KINDS | {"portfolio"}
_AUTHORITY_SEGMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


class RoleSessionError(Exception):
    def __init__(self) -> None:
        super().__init__(_INVALID_CODE)
        self.code = _INVALID_CODE
        self.action = _INVALID_ACTION


class JournalError(Exception):
    def __init__(self) -> None:
        super().__init__("STATE_IO_ERROR")
        self.code = "STATE_IO_ERROR"
        self.action = "Preserve the original file and surface the error"


@dataclass(frozen=True)
class RoleSessionMetadata:
    workspace_id: str
    workspace_kind: str
    role: str
    correlation_id: str
    workflow: str
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
        self._role_workflow_cache: Optional[Dict[str, Set[str]]] = None

    def open(
        self,
        workspace_id: str,
        role: str,
        correlation_id: str,
        workflow: str,
        workspace_kind: str,
    ) -> str:
        if not self._valid_text(workspace_id):
            raise RoleSessionError()
        if not self._valid_text(correlation_id):
            raise RoleSessionError()
        if not self._valid_role_workflow(role, workflow):
            raise RoleSessionError()
        if not self._valid_role_workspace(role, workspace_kind):
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
            "workspace_kind": workspace_kind,
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
        workflow = record.get("workflow")
        if (
            not isinstance(role, str)
            or not isinstance(workflow, str)
            or not self._valid_role_workflow(role, workflow)
        ):
            return False

        workspace_kind = record.get("workspace_kind")
        if (
            not isinstance(workspace_kind, str)
            or not self._valid_role_workspace(role, workspace_kind)
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

    def preflight_journal(self) -> int:
        descriptor: Optional[int] = None
        try:
            if not hasattr(os, "O_NOFOLLOW"):
                raise OSError("O_NOFOLLOW is required")
            self._data_root.mkdir(parents=True, exist_ok=True)
            flags = (
                os.O_WRONLY
                | os.O_CREAT
                | os.O_APPEND
                | os.O_NOFOLLOW
            )
            if hasattr(os, "O_NONBLOCK"):
                flags |= os.O_NONBLOCK
            if hasattr(os, "O_CLOEXEC"):
                flags |= os.O_CLOEXEC
            descriptor = os.open(
                str(self._data_root / "operations.jsonl"),
                flags,
                0o600,
            )
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise OSError("journal is not a regular file")
            return descriptor
        except (OSError, TypeError, ValueError):
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            raise JournalError()

    def append_journal(
        self,
        metadata: RoleSessionMetadata,
        *,
        path: str,
        operation: str,
        result: str,
        before_sha256: Optional[str],
        after_sha256: Optional[str],
        descriptor: Optional[int] = None,
    ) -> None:
        if (
            not isinstance(metadata, RoleSessionMetadata)
            or not self._valid_text(path)
            or operation not in {"create", "replace"}
            or not self._valid_text(result)
        ):
            raise JournalError()
        for digest in (before_sha256, after_sha256):
            if digest is not None and re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                raise JournalError()

        event = {
            "timestamp": self._now(),
            "correlation_id": metadata.correlation_id,
            "role": metadata.role,
            "workspace_id": metadata.workspace_id,
            "path": path,
            "operation": operation,
            "result": result,
            "before_sha256": before_sha256,
            "after_sha256": after_sha256,
        }
        encoded = (
            json.dumps(
                event,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        owns_descriptor = descriptor is None
        try:
            if descriptor is None:
                descriptor = self.preflight_journal()
            offset = 0
            while offset < len(encoded):
                written = os.write(descriptor, encoded[offset:])
                if written <= 0:
                    raise OSError("short journal write")
                offset += written
            os.fsync(descriptor)
        except JournalError:
            raise
        except (OSError, TypeError, ValueError, RoleSessionError):
            raise JournalError()
        finally:
            if owns_descriptor and descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass

    def _roles(self) -> set[str]:
        return set(self._role_workflows())

    def _role_workflows(self) -> Dict[str, Set[str]]:
        if self._role_workflow_cache is not None:
            return self._role_workflow_cache

        agents = self._packaged_root / "agents"
        parsed: Dict[str, Set[str]] = {}
        try:
            paths = sorted(
                path
                for path in agents.iterdir()
                if path.is_file() and path.suffix == ".md"
            )
            for path in paths:
                text = path.read_text(encoding="utf-8")
                parsed_role = self._parse_agent_frontmatter(text)
                if parsed_role is None:
                    return {}
                name, workflows = parsed_role
                if name != path.stem or name in parsed:
                    return {}
                parsed[name] = workflows
        except (OSError, UnicodeError):
            return {}
        if len(parsed) != 13:
            return {}
        self._role_workflow_cache = parsed
        return parsed

    def _parse_agent_frontmatter(
        self,
        text: str,
    ) -> Optional[tuple[str, Set[str]]]:
        lines = text.splitlines()
        if not lines or lines[0] != "---":
            return None
        try:
            end = lines.index("---", 1)
        except ValueError:
            return None

        name: Optional[str] = None
        workflows: Set[str] = set()
        in_skills = False
        for line in lines[1:end]:
            if line.startswith("name:"):
                if name is not None:
                    return None
                name = line.partition(":")[2].strip()
                in_skills = False
            elif line == "skills:":
                in_skills = True
            elif in_skills and line.startswith("  - "):
                workflow = line[4:].strip()
                if not self._valid_workflow(workflow):
                    return None
                workflows.add(workflow)
            elif line and not line[0].isspace():
                in_skills = False

        if (
            name is None
            or _AUTHORITY_SEGMENT.fullmatch(name) is None
            or not workflows
        ):
            return None
        return name, workflows

    def _valid_role_workflow(self, role: object, workflow: object) -> bool:
        return (
            isinstance(role, str)
            and isinstance(workflow, str)
            and workflow in self._role_workflows().get(role, set())
        )

    @staticmethod
    def _valid_role_workspace(role: str, workspace_kind: object) -> bool:
        if not isinstance(workspace_kind, str) or workspace_kind not in _WORKSPACE_KINDS:
            return False
        if role == "portfolio-manager":
            return workspace_kind == "portfolio"
        return workspace_kind in _BUSINESS_WORKSPACE_KINDS

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
            workspace_kind=str(record["workspace_kind"]),
            role=str(record["role"]),
            correlation_id=str(record["correlation_id"]),
            workflow=str(record["workflow"]),
            expires_at=float(record["expires_at"]),
            status=str(record["status"]),
            final_status=(
                str(final_status) if final_status is not None else None
            ),
        )
