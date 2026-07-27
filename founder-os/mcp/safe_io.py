"""Safe, bounded read-only access to workspace state and packaged references."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Dict, List, Optional


class SafeStateError(Exception):
    _ACTIONS = {
        "PATH_OUTSIDE_WORKSPACE": "Refuse without retrying a modified path guess",
        "STATE_IO_ERROR": "Preserve the original file and surface the error",
    }

    def __init__(self, code: str) -> None:
        self.code = code if code in self._ACTIONS else "STATE_IO_ERROR"
        self.action = self._ACTIONS[self.code]
        super().__init__(self.code)


class SafeStateIO:
    _FORBIDDEN = "[]{}?\\"

    def __init__(
        self,
        workspace_root: Path,
        packaged_root: Path,
        *,
        max_results: int = 100,
        max_file_bytes: int = 1024 * 1024,
        max_total_bytes: int = 4 * 1024 * 1024,
    ) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.packaged_root = Path(packaged_root).resolve()
        self.max_results = max_results
        self.max_file_bytes = max_file_bytes
        self.max_total_bytes = max_total_bytes

    def list_markdown(self, pattern: str) -> List[str]:
        self._validate_pattern(pattern)
        paths = []
        try:
            candidates = self.workspace_root.glob(pattern)
            for candidate in candidates:
                try:
                    resolved = candidate.resolve()
                    if not self._inside(resolved, self.workspace_root):
                        continue
                    info = resolved.stat()
                except OSError:
                    continue
                if not stat.S_ISREG(info.st_mode) or resolved.suffix != ".md":
                    continue
                paths.append(resolved.relative_to(self.workspace_root).as_posix())
        except (OSError, ValueError):
            raise SafeStateError("STATE_IO_ERROR")
        paths.sort()
        if len(paths) > self.max_results:
            raise SafeStateError("STATE_IO_ERROR")
        response_size = len(
            json.dumps(paths, separators=(",", ":")).encode("utf-8")
        )
        if response_size > self.max_total_bytes:
            raise SafeStateError("STATE_IO_ERROR")
        return paths

    def read_many(self, paths: List[str]) -> List[Dict[str, object]]:
        if not isinstance(paths, list) or not paths or len(paths) > self.max_results:
            raise SafeStateError("STATE_IO_ERROR")
        result = []
        total = 0
        for path in paths:
            relative = self._validate_file_path(path)
            entry = self._read_file(
                self.workspace_root / relative,
                self.workspace_root,
                relative.as_posix(),
            )
            total += int(entry["size"])
            if total > self.max_total_bytes:
                raise SafeStateError("STATE_IO_ERROR")
            result.append(entry)
        return result

    def read_reference(
        self,
        path: str,
        role: str,
        workflow: Optional[str] = None,
    ) -> Dict[str, object]:
        relative = self._validate_file_path(path)
        allowed = {
            "CLAUDE.md",
            "agents/" + self._authority_segment(role) + ".md",
            "references/ownership.yaml",
            "references/house-rules.md",
            "references/multi-business.md",
            "references/orchestration.md",
        }
        if workflow is not None:
            allowed.add(
                "skills/" + self._authority_segment(workflow) + "/SKILL.md"
            )
        if relative.as_posix() not in allowed:
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
        return self._read_file(
            self.packaged_root / relative,
            self.packaged_root,
            relative.as_posix(),
        )

    def _read_file(
        self,
        candidate: Path,
        root: Path,
        relative_path: str,
    ) -> Dict[str, object]:
        try:
            resolved = candidate.resolve()
        except OSError:
            raise SafeStateError("STATE_IO_ERROR")
        if not self._inside(resolved, root):
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
        try:
            before = resolved.stat()
        except OSError:
            raise SafeStateError("STATE_IO_ERROR")
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_size > self.max_file_bytes
            or before.st_size > self.max_total_bytes
        ):
            raise SafeStateError("STATE_IO_ERROR")

        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(str(resolved), flags)
        except OSError:
            raise SafeStateError("STATE_IO_ERROR")
        try:
            after = os.fstat(descriptor)
            if not stat.S_ISREG(after.st_mode):
                raise SafeStateError("STATE_IO_ERROR")
            limit = min(self.max_file_bytes, self.max_total_bytes)
            with os.fdopen(descriptor, "rb") as handle:
                descriptor = -1
                data = handle.read(limit + 1)
        except OSError:
            raise SafeStateError("STATE_IO_ERROR")
        finally:
            if descriptor != -1:
                os.close(descriptor)

        if len(data) > self.max_file_bytes or len(data) > self.max_total_bytes:
            raise SafeStateError("STATE_IO_ERROR")
        try:
            content = data.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            raise SafeStateError("STATE_IO_ERROR")
        return {
            "path": relative_path,
            "content": content,
            "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data),
            "mtime_ns": after.st_mtime_ns,
        }

    def _validate_pattern(self, pattern: object) -> None:
        if not isinstance(pattern, str) or not pattern or "\x00" in pattern:
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
        if any(character in pattern for character in self._FORBIDDEN):
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
        value = Path(pattern)
        if value.is_absolute() or ".." in value.parts:
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")

    def _validate_file_path(self, path: object) -> Path:
        if not isinstance(path, str) or not path or "\x00" in path:
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
        if "*" in path or any(character in path for character in self._FORBIDDEN):
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
        value = Path(path)
        if value.is_absolute() or ".." in value.parts:
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
        return value

    @staticmethod
    def _authority_segment(value: object) -> str:
        if (
            not isinstance(value, str)
            or not value
            or "/" in value
            or "\\" in value
            or "\x00" in value
            or value in (".", "..")
        ):
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
        return value

    @staticmethod
    def _inside(candidate: Path, root: Path) -> bool:
        try:
            candidate.relative_to(root)
        except ValueError:
            return False
        return True
