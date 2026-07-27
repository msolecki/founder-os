"""Safe, bounded read-only access to workspace state and packaged references."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Callable, Dict, List, Optional


class SafeStateError(Exception):
    _ACTIONS = {
        "PATH_OUTSIDE_WORKSPACE": (
            "Refuse without retrying a modified path guess"
        ),
        "STATE_IO_ERROR": "Preserve the original file and surface the error",
    }

    def __init__(self, code: str) -> None:
        self.code = (
            code if code in self._ACTIONS else "STATE_IO_ERROR"
        )
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
        before_component_open: Optional[
            Callable[[str, int], None]
        ] = None,
    ) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.packaged_root = Path(packaged_root).resolve()
        self.max_results = max_results
        self.max_file_bytes = max_file_bytes
        self.max_total_bytes = max_total_bytes
        self._before_component_open = before_component_open
        self._workspace_fd = -1
        self._packaged_fd = -1

        if (
            before_component_open is not None
            and not callable(before_component_open)
        ):
            raise SafeStateError("STATE_IO_ERROR")

        try:
            self._workspace_fd = self._open_trusted_directory(
                self.workspace_root
            )
            self._packaged_fd = self._open_trusted_directory(
                self.packaged_root
            )
        except SafeStateError:
            self.close()
            raise

    def close(self) -> None:
        for attribute in ("_workspace_fd", "_packaged_fd"):
            descriptor = getattr(self, attribute, -1)
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
                setattr(self, attribute, -1)

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def list_markdown(self, pattern: str) -> List[str]:
        self._validate_pattern(pattern)
        paths: List[str] = []
        try:
            candidates = self.workspace_root.glob(pattern)
            for candidate in candidates:
                try:
                    resolved = candidate.resolve()
                    if not self._inside(resolved, self.workspace_root):
                        continue
                    if resolved.suffix != ".md":
                        continue
                    relative = resolved.relative_to(self.workspace_root)
                    descriptor = self._open_relative(
                        self._workspace_fd,
                        relative,
                        relative.as_posix(),
                    )
                    try:
                        info = os.fstat(descriptor)
                    finally:
                        os.close(descriptor)
                    if not stat.S_ISREG(info.st_mode):
                        continue
                    paths.append(relative.as_posix())
                except (OSError, ValueError, SafeStateError):
                    continue
        except (OSError, ValueError):
            raise SafeStateError("STATE_IO_ERROR")

        paths.sort()
        if len(paths) > self.max_results:
            raise SafeStateError("STATE_IO_ERROR")
        if (
            len(
                json.dumps(
                    paths,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
            > self.max_total_bytes
        ):
            raise SafeStateError("STATE_IO_ERROR")
        return paths

    def read_many(
        self,
        paths: List[str],
    ) -> List[Dict[str, object]]:
        if (
            not isinstance(paths, list)
            or not paths
            or len(paths) > self.max_results
        ):
            raise SafeStateError("STATE_IO_ERROR")

        result: List[Dict[str, object]] = []
        total = 0
        for path in paths:
            relative = self._validate_file_path(path)
            entry = self._read_file(
                relative,
                self._workspace_fd,
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
                "skills/"
                + self._authority_segment(workflow)
                + "/SKILL.md"
            )
        if relative.as_posix() not in allowed:
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
        return self._read_file(
            relative,
            self._packaged_fd,
            relative.as_posix(),
        )

    def _read_file(
        self,
        relative: Path,
        root_fd: int,
        relative_path: str,
    ) -> Dict[str, object]:
        descriptor = self._open_relative(
            root_fd,
            relative,
            relative_path,
        )
        try:
            info = os.fstat(descriptor)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_size > self.max_file_bytes
                or info.st_size > self.max_total_bytes
            ):
                raise SafeStateError("STATE_IO_ERROR")

            limit = min(self.max_file_bytes, self.max_total_bytes)
            with os.fdopen(descriptor, "rb") as handle:
                descriptor = -1
                data = handle.read(limit + 1)
        except SafeStateError:
            raise
        except OSError:
            raise SafeStateError("STATE_IO_ERROR")
        finally:
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except OSError:
                    pass

        if (
            len(data) > self.max_file_bytes
            or len(data) > self.max_total_bytes
        ):
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
            "mtime_ns": info.st_mtime_ns,
        }

    def _open_relative(
        self,
        root_fd: int,
        relative: Path,
        relative_path: str,
    ) -> int:
        self._require_secure_primitives()
        components = relative.parts
        if root_fd < 0 or not components:
            raise SafeStateError("STATE_IO_ERROR")

        try:
            parent_fd = os.dup(root_fd)
        except OSError:
            raise SafeStateError("STATE_IO_ERROR")

        try:
            for index, component in enumerate(components):
                if component in ("", ".", ".."):
                    raise SafeStateError("PATH_OUTSIDE_WORKSPACE")

                if self._before_component_open is not None:
                    try:
                        self._before_component_open(relative_path, index)
                    except OSError:
                        raise SafeStateError("STATE_IO_ERROR")

                final_component = index == len(components) - 1
                flags = os.O_RDONLY | os.O_NOFOLLOW
                if hasattr(os, "O_CLOEXEC"):
                    flags |= os.O_CLOEXEC
                if final_component:
                    if hasattr(os, "O_NONBLOCK"):
                        flags |= os.O_NONBLOCK
                else:
                    flags |= os.O_DIRECTORY

                try:
                    child_fd = os.open(
                        component,
                        flags,
                        dir_fd=parent_fd,
                    )
                except OSError as error:
                    raise self._open_error(error)

                os.close(parent_fd)
                parent_fd = child_fd

            result = parent_fd
            parent_fd = -1
            return result
        finally:
            if parent_fd >= 0:
                try:
                    os.close(parent_fd)
                except OSError:
                    pass

    @classmethod
    def _open_trusted_directory(cls, root: Path) -> int:
        cls._require_secure_primitives()
        if not root.is_absolute():
            raise SafeStateError("STATE_IO_ERROR")

        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC

        try:
            descriptor = os.open(os.path.sep, flags)
        except OSError:
            raise SafeStateError("STATE_IO_ERROR")

        try:
            for component in root.parts[1:]:
                if component in ("", ".", ".."):
                    raise SafeStateError("STATE_IO_ERROR")
                try:
                    child_fd = os.open(
                        component,
                        flags,
                        dir_fd=descriptor,
                    )
                except OSError as error:
                    raise cls._open_error(error)
                os.close(descriptor)
                descriptor = child_fd

            result = descriptor
            descriptor = -1
            return result
        finally:
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except OSError:
                    pass

    @staticmethod
    def _require_secure_primitives() -> None:
        supports_dir_fd = getattr(os, "supports_dir_fd", set())
        if (
            not hasattr(os, "O_NOFOLLOW")
            or not hasattr(os, "O_DIRECTORY")
            or os.open not in supports_dir_fd
        ):
            raise SafeStateError("STATE_IO_ERROR")

    @staticmethod
    def _open_error(error: OSError) -> SafeStateError:
        if error.errno in (errno.ELOOP, errno.ENOTDIR):
            return SafeStateError("PATH_OUTSIDE_WORKSPACE")
        return SafeStateError("STATE_IO_ERROR")

    def _validate_pattern(self, pattern: str) -> None:
        if (
            not isinstance(pattern, str)
            or not pattern
            or "\x00" in pattern
        ):
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
        if any(character in pattern for character in self._FORBIDDEN):
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
        value = Path(pattern)
        if value.is_absolute() or ".." in value.parts:
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")

    def _validate_file_path(self, path: str) -> Path:
        if (
            not isinstance(path, str)
            or not path
            or "\x00" in path
        ):
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
        if "*" in path or any(
            character in path for character in self._FORBIDDEN
        ):
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
        value = Path(path)
        if value.is_absolute() or ".." in value.parts:
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
        return value

    @staticmethod
    def _authority_segment(value: str) -> str:
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
