"""Safe, bounded read-only access to workspace state and packaged references."""

from __future__ import annotations

import base64
import binascii
import errno
import fcntl
import hashlib
import heapq
import json
import os
import re
import secrets
import stat
from pathlib import Path
from typing import Callable, Dict, List, Mapping, Optional, Tuple


class SafeStateError(Exception):
    _ACTIONS = {
        "PATH_OUTSIDE_WORKSPACE": (
            "Refuse without retrying a modified path guess"
        ),
        "STATE_IO_ERROR": "Preserve the original file and surface the error",
        "STALE_WRITE": "Re-read, reconcile deliberately, then retry once",
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
        before_replace: Optional[Callable[[str], None]] = None,
        before_commit: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.packaged_root = Path(packaged_root).resolve()
        self.max_results = max_results
        self.max_file_bytes = max_file_bytes
        self.max_total_bytes = max_total_bytes
        self._before_component_open = before_component_open
        self._before_replace = before_replace
        self._before_commit = before_commit
        self._workspace_fd = -1
        self._packaged_fd = -1

        if (
            before_component_open is not None
            and not callable(before_component_open)
        ) or (
            before_replace is not None
            and not callable(before_replace)
        ) or (
            before_commit is not None
            and not callable(before_commit)
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
        page = self.list_markdown_page(pattern, limit=self.max_results)
        if page["next_cursor"] is not None:
            raise SafeStateError("STATE_IO_ERROR")
        return list(page["paths"])

    def list_markdown_page(
        self,
        pattern: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Dict[str, object]:
        self._validate_pattern(pattern)
        if (
            isinstance(self.max_results, bool)
            or not isinstance(self.max_results, int)
            or self.max_results <= 0
        ):
            raise SafeStateError("STATE_IO_ERROR")
        page_limit = self.max_results if limit is None else limit
        if (
            isinstance(page_limit, bool)
            or not isinstance(page_limit, int)
            or page_limit < 1
            or page_limit > 100
            or page_limit > self.max_results
        ):
            raise SafeStateError("STATE_IO_ERROR")
        after = self._decode_list_cursor(cursor, pattern)

        def candidates():
            try:
                matches = self.workspace_root.glob(pattern)
                for candidate in matches:
                    try:
                        resolved = candidate.resolve()
                        if not self._inside(resolved, self.workspace_root):
                            continue
                        if resolved.suffix != ".md":
                            continue
                        relative = resolved.relative_to(self.workspace_root)
                        relative_path = relative.as_posix()
                        if after is not None and relative_path <= after:
                            continue
                        descriptor = self._open_relative(
                            self._workspace_fd,
                            relative,
                            relative_path,
                        )
                        if descriptor is None:
                            continue
                        try:
                            info = os.fstat(descriptor)
                        finally:
                            os.close(descriptor)
                        if stat.S_ISREG(info.st_mode):
                            yield relative_path
                    except (OSError, ValueError, SafeStateError):
                        continue
            except (OSError, ValueError):
                raise SafeStateError("STATE_IO_ERROR")

        try:
            paths = heapq.nsmallest(page_limit + 1, candidates())
        except (OSError, TypeError, ValueError):
            raise SafeStateError("STATE_IO_ERROR")

        has_more = len(paths) > page_limit
        page = paths[:page_limit]
        if (
            len(
                json.dumps(
                    page,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
            > self.max_total_bytes
        ):
            raise SafeStateError("STATE_IO_ERROR")
        next_cursor = (
            self._encode_list_cursor(pattern, page[-1])
            if has_more and page
            else None
        )
        return {"paths": page, "next_cursor": next_cursor}

    @staticmethod
    def _encode_list_cursor(pattern: str, after: str) -> str:
        payload = json.dumps(
            {
                "v": 1,
                "pattern_sha256": hashlib.sha256(
                    pattern.encode("utf-8")
                ).hexdigest(),
                "after": after,
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")

    def _decode_list_cursor(
        self,
        cursor: Optional[str],
        pattern: str,
    ) -> Optional[str]:
        if cursor is None:
            return None
        if (
            not isinstance(cursor, str)
            or not cursor
            or len(cursor) > 4096
            or "\x00" in cursor
        ):
            raise SafeStateError("STATE_IO_ERROR")
        try:
            encoded = cursor.encode("ascii")
            padding = b"=" * (-len(encoded) % 4)
            decoded = base64.b64decode(
                encoded + padding,
                altchars=b"-_",
                validate=True,
            )
            payload = json.loads(decoded.decode("utf-8"))
        except (
            binascii.Error,
            json.JSONDecodeError,
            UnicodeError,
            ValueError,
        ):
            raise SafeStateError("STATE_IO_ERROR")
        if not isinstance(payload, dict) or set(payload) != {
            "v",
            "pattern_sha256",
            "after",
        }:
            raise SafeStateError("STATE_IO_ERROR")
        expected_digest = hashlib.sha256(pattern.encode("utf-8")).hexdigest()
        after = payload.get("after")
        version = payload.get("v")
        if (
            isinstance(version, bool)
            or not isinstance(version, int)
            or version != 1
            or payload.get("pattern_sha256") != expected_digest
            or not isinstance(after, str)
            or not after
        ):
            raise SafeStateError("STATE_IO_ERROR")
        relative = self._validate_file_path(after)
        if relative.as_posix() != after or relative.suffix != ".md":
            raise SafeStateError("STATE_IO_ERROR")
        return after

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
        """Read one packaged file a role is entitled to, and nothing else.

        The two plugin manifests are on the list because a role holds no file
        tool: `founder-os-feedback` must quote the shipped version, and the only
        alternative left to it is the version it remembers from training.
        """
        relative = self._validate_file_path(path)
        allowed = {
            "CLAUDE.md",
            "agents/" + self._authority_segment(role) + ".md",
            "references/ownership.yaml",
            "references/house-rules.md",
            "references/multi-business.md",
            "references/orchestration.md",
            ".claude-plugin/plugin.json",
            ".codex-plugin/plugin.json",
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

    def read_fixed_sections(
        self,
        specification: Mapping[str, Tuple[str, ...]],
    ) -> Dict[str, object]:
        """Read only named H2 bodies from a closed, caller-owned specification."""
        if not isinstance(specification, Mapping) or not specification:
            raise SafeStateError("STATE_IO_ERROR")

        sections: List[Dict[str, object]] = []
        missing: List[str] = []
        total = 0
        for path, headings in specification.items():
            if (
                not isinstance(headings, tuple)
                or not headings
                or any(
                    not isinstance(heading, str)
                    or not heading
                    or "\n" in heading
                    or "\r" in heading
                    for heading in headings
                )
            ):
                raise SafeStateError("STATE_IO_ERROR")
            relative = self._validate_file_path(path)
            entry = self._read_file(
                relative,
                self._workspace_fd,
                relative.as_posix(),
                missing_ok=True,
            )
            if entry is None:
                missing.extend(path + "#" + heading for heading in headings)
                continue

            extracted = self._extract_h2_sections(
                str(entry["content"]), headings
            )
            for heading in headings:
                if heading not in extracted:
                    missing.append(path + "#" + heading)
                    continue
                content = extracted[heading]
                total += len(content.encode("utf-8"))
                if total > self.max_total_bytes:
                    raise SafeStateError("STATE_IO_ERROR")
                sections.append(
                    {
                        "path": path,
                        "heading": heading,
                        "content": content,
                        "sha256": entry["sha256"],
                        "mtime_ns": entry["mtime_ns"],
                    }
                )
        return {"sections": sections, "missing": missing}

    @staticmethod
    def _extract_h2_sections(
        content: str,
        headings: Tuple[str, ...],
    ) -> Dict[str, str]:
        wanted = set(headings)
        found: Dict[str, str] = {}
        current: Optional[str] = None
        body: List[str] = []
        fence_character: Optional[str] = None
        fence_length = 0

        def finish() -> None:
            nonlocal current, body
            if current is not None:
                if current in found:
                    raise SafeStateError("STATE_IO_ERROR")
                found[current] = "".join(body)
            current = None
            body = []

        for line in content.splitlines(keepends=True):
            stripped = line.rstrip("\r\n")
            fence = re.match(r"^ {0,3}(`{3,}|~{3,})(?:[^`~].*)?$", stripped)
            if fence_character is None and fence is not None:
                marker = fence.group(1)
                fence_character = marker[0]
                fence_length = len(marker)
            elif fence_character is not None and re.fullmatch(
                r" {0,3}" + re.escape(fence_character)
                + "{" + str(fence_length) + r",}\s*",
                stripped,
            ):
                fence_character = None
                fence_length = 0
            elif fence_character is None:
                match = re.fullmatch(r"## ([^\r\n]+)", stripped)
                if match is not None:
                    finish()
                    heading = match.group(1)
                    current = heading if heading in wanted else None
                    continue

            if current is not None:
                body.append(line)
        finish()
        return found

    @staticmethod
    def _atomic_error(
        code: str,
        before_sha256: Optional[str] = None,
    ) -> SafeStateError:
        error = SafeStateError(code)
        error.before_sha256 = before_sha256
        error.after_sha256 = None
        return error

    def _open_parent(
        self,
        relative: Path,
        relative_path: str,
        declared_directory: Optional[str] = None,
    ) -> Tuple[int, str]:
        """Walk to the target's parent, creating only a declared directory.

        `declared_directory` is a `workspace_files:` entry the caller has
        already resolved as owning this path, and its components are the only
        ones this walk may create. `founder-os-init` scaffolds those entries at
        install time and never runs again, so a workspace older than a newly
        declared directory has no other repair path — while a deeper component
        is still a path that should not exist, and still fails.
        """
        parts = relative.parts
        if self._workspace_fd < 0 or not parts:
            raise SafeStateError("STATE_IO_ERROR")
        creatable = 0
        if declared_directory:
            declared = Path(declared_directory).parts
            # The components created come from `relative`, not from
            # `declared_directory` — the argument only bounds how many. So the
            # two have to be the same path, or a caller passing a deeper
            # unrelated key would license mkdir on components it never named.
            # The one caller today derives it from this very path; this is what
            # keeps that true for the next one.
            if parts[:len(declared)] != declared:
                raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
            creatable = len(declared)
        try:
            current = os.dup(self._workspace_fd)
        except OSError:
            raise SafeStateError("STATE_IO_ERROR")
        try:
            for index, component in enumerate(parts[:-1]):
                if self._before_component_open is not None:
                    self._before_component_open(relative_path, index)
                flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
                if hasattr(os, "O_CLOEXEC"):
                    flags |= os.O_CLOEXEC
                try:
                    next_descriptor = os.open(component, flags, dir_fd=current)
                except FileNotFoundError:
                    if index >= creatable:
                        raise
                    try:
                        os.mkdir(component, 0o700, dir_fd=current)
                    except FileExistsError:
                        pass
                    next_descriptor = os.open(component, flags, dir_fd=current)
                os.close(current)
                current = next_descriptor
            return current, parts[-1]
        except OSError as error:
            try:
                os.close(current)
            except OSError:
                pass
            raise self._open_error(error)

    def atomic_replace(
        self,
        relative_path: str,
        content_bytes: bytes,
        expected_sha256: Optional[str] = None,
        create_only: bool = False,
        declared_directory: Optional[str] = None,
    ) -> Dict[str, object]:
        if (
            not isinstance(content_bytes, bytes)
            or len(content_bytes) > self.max_file_bytes
        ):
            raise SafeStateError("STATE_IO_ERROR")
        has_expected = (
            isinstance(expected_sha256, str)
            and len(expected_sha256) == 64
            and all(
                character in "0123456789abcdef"
                for character in expected_sha256
            )
        )
        if (create_only is True) == has_expected:
            raise SafeStateError("STATE_IO_ERROR")

        relative = self._validate_file_path(relative_path)
        if relative.parts and relative.parts[0] == "_local":
            raise SafeStateError("PATH_OUTSIDE_WORKSPACE")
        parent_descriptor, target_name = self._open_parent(
            relative,
            relative_path,
            declared_directory=declared_directory,
        )
        target_descriptor = -1
        temporary_descriptor = -1
        lock_descriptor = -1
        temporary_name: Optional[str] = None
        before_sha256: Optional[str] = None

        try:
            lock_name = ".founder-os-write-{0}.lock".format(
                hashlib.sha256(target_name.encode("utf-8")).hexdigest()
            )
            lock_flags = os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW
            if hasattr(os, "O_CLOEXEC"):
                lock_flags |= os.O_CLOEXEC
            lock_descriptor = os.open(
                lock_name,
                lock_flags,
                0o600,
                dir_fd=parent_descriptor,
            )
            lock_info = os.fstat(lock_descriptor)
            if (
                not stat.S_ISREG(lock_info.st_mode)
                or lock_info.st_nlink != 1
            ):
                raise SafeStateError("STATE_IO_ERROR")
            fcntl.flock(lock_descriptor, fcntl.LOCK_EX)
            lock_path_info = os.stat(
                lock_name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
            if (
                lock_path_info.st_dev != lock_info.st_dev
                or lock_path_info.st_ino != lock_info.st_ino
            ):
                raise SafeStateError("STATE_IO_ERROR")

            flags = os.O_RDONLY | os.O_NOFOLLOW
            if hasattr(os, "O_NONBLOCK"):
                flags |= os.O_NONBLOCK
            if hasattr(os, "O_CLOEXEC"):
                flags |= os.O_CLOEXEC
            try:
                target_descriptor = os.open(
                    target_name,
                    flags,
                    dir_fd=parent_descriptor,
                )
            except OSError as error:
                if error.errno != errno.ENOENT:
                    raise self._open_error(error)

            if target_descriptor >= 0:
                info = os.fstat(target_descriptor)
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_size > self.max_file_bytes
                ):
                    raise SafeStateError("STATE_IO_ERROR")
                chunks = []
                total = 0
                while total <= self.max_file_bytes:
                    chunk = os.read(
                        target_descriptor,
                        min(65536, self.max_file_bytes + 1 - total),
                    )
                    if not chunk:
                        break
                    chunks.append(chunk)
                    total += len(chunk)
                if total > self.max_file_bytes:
                    raise SafeStateError("STATE_IO_ERROR")
                before_sha256 = hashlib.sha256(b"".join(chunks)).hexdigest()
                os.close(target_descriptor)
                target_descriptor = -1

            if create_only is True:
                operation = "create"
                if before_sha256 is not None:
                    raise self._atomic_error("STALE_WRITE", before_sha256)
            else:
                operation = "replace"
                if (
                    before_sha256 is None
                    or before_sha256 != expected_sha256
                ):
                    raise self._atomic_error("STALE_WRITE", before_sha256)

            temporary_name = ".{0}.{1}.tmp".format(
                target_name,
                secrets.token_hex(16),
            )
            temporary_flags = (
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | os.O_NOFOLLOW
            )
            if hasattr(os, "O_CLOEXEC"):
                temporary_flags |= os.O_CLOEXEC
            temporary_descriptor = os.open(
                temporary_name,
                temporary_flags,
                0o600,
                dir_fd=parent_descriptor,
            )
            offset = 0
            while offset < len(content_bytes):
                written = os.write(
                    temporary_descriptor,
                    content_bytes[offset:],
                )
                if written <= 0:
                    raise OSError("short state write")
                offset += written
            os.fsync(temporary_descriptor)
            os.close(temporary_descriptor)
            temporary_descriptor = -1

            if self._before_replace is not None:
                self._before_replace(relative_path)

            final_sha256: Optional[str] = None
            try:
                target_descriptor = os.open(
                    target_name,
                    flags,
                    dir_fd=parent_descriptor,
                )
            except OSError as error:
                if error.errno != errno.ENOENT:
                    raise self._open_error(error)
            if target_descriptor >= 0:
                final_info = os.fstat(target_descriptor)
                if (
                    not stat.S_ISREG(final_info.st_mode)
                    or final_info.st_size > self.max_file_bytes
                ):
                    raise SafeStateError("STATE_IO_ERROR")
                final_chunks = []
                final_total = 0
                while final_total <= self.max_file_bytes:
                    chunk = os.read(
                        target_descriptor,
                        min(
                            65536,
                            self.max_file_bytes + 1 - final_total,
                        ),
                    )
                    if not chunk:
                        break
                    final_chunks.append(chunk)
                    final_total += len(chunk)
                if final_total > self.max_file_bytes:
                    raise SafeStateError("STATE_IO_ERROR")
                final_sha256 = hashlib.sha256(
                    b"".join(final_chunks)
                ).hexdigest()
                os.close(target_descriptor)
                target_descriptor = -1

            if (
                (operation == "create" and final_sha256 is not None)
                or (
                    operation == "replace"
                    and final_sha256 != before_sha256
                )
            ):
                raise self._atomic_error("STALE_WRITE", final_sha256)

            if self._before_commit is not None:
                self._before_commit(relative_path)

            os.replace(
                temporary_name,
                target_name,
                src_dir_fd=parent_descriptor,
                dst_dir_fd=parent_descriptor,
            )
            temporary_name = None
            os.fsync(parent_descriptor)
            return {
                "path": relative_path,
                "operation": operation,
                "before_sha256": before_sha256,
                "after_sha256": hashlib.sha256(content_bytes).hexdigest(),
            }
        except SafeStateError:
            raise
        except OSError:
            raise self._atomic_error("STATE_IO_ERROR", before_sha256)
        finally:
            if target_descriptor >= 0:
                try:
                    os.close(target_descriptor)
                except OSError:
                    pass
            if temporary_descriptor >= 0:
                try:
                    os.close(temporary_descriptor)
                except OSError:
                    pass
            if temporary_name is not None:
                try:
                    os.unlink(temporary_name, dir_fd=parent_descriptor)
                except OSError:
                    pass
            if lock_descriptor >= 0:
                try:
                    os.close(lock_descriptor)
                except OSError:
                    pass
            try:
                os.close(parent_descriptor)
            except OSError:
                pass

    def _read_file(
        self,
        relative: Path,
        root_fd: int,
        relative_path: str,
        *,
        missing_ok: bool = False,
    ) -> Optional[Dict[str, object]]:
        descriptor = self._open_relative(
            root_fd,
            relative,
            relative_path,
            missing_ok=missing_ok,
        )
        if descriptor is None:
            return None
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
        *,
        missing_ok: bool = False,
    ) -> Optional[int]:
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
                    if missing_ok and error.errno == errno.ENOENT:
                        return None
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
