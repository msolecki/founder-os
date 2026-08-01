#!/usr/bin/env python3
"""Preview and safely install Founder OS cadences on a user's machine.

The manager has no shell execution path.  Every scheduler mutation is derived
from a previously serialized preview and guarded by a snapshot digest.
"""

from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shlex
import stat
import subprocess
import sys
import tempfile
from typing import Callable, Dict, Mapping, Optional, Sequence, Tuple


MANIFEST_VERSION = 2
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
BEGIN_MARKER = re.compile(
    br"^# BEGIN (founder-os(?::[A-Za-z0-9][A-Za-z0-9._-]*)?)"
    br"(?: \xe2\x80\x94 .*)?\r?\n?$"
)
END_MARKER = re.compile(
    br"^# END (founder-os(?::[A-Za-z0-9][A-Za-z0-9._-]*)?)\r?\n?$"
)


class CadenceError(Exception):
    pass


@dataclass(frozen=True)
class Cadence:
    workflow: str
    cron: str


@dataclass(frozen=True)
class CadenceConfig:
    host: str
    binary: Path
    workspace: Path
    workdir: Path
    log_root: Path
    slug: Optional[str]

    def __post_init__(self) -> None:
        if self.host not in {"claude", "codex"}:
            raise CadenceError("host must be claude or codex")
        for value in (
            self.binary,
            self.workspace,
            self.workdir,
            self.log_root,
        ):
            if not isinstance(value, Path) or not value.is_absolute():
                raise CadenceError("cadence paths must be absolute")
            if any(character in str(value) for character in ("\x00", "\n", "\r")):
                raise CadenceError("cadence paths cannot contain control lines")
        if self.slug is not None and (
            not isinstance(self.slug, str)
            or SAFE_ID.fullmatch(self.slug) is None
        ):
            raise CadenceError("invalid cadence identity")


BUSINESS_CADENCES = (
    Cadence("daily-brief", "0 8 * * 1-5"),
    Cadence("week-plan", "30 8 * * 1"),
    Cadence("weekly-review", "0 16 * * 5"),
    Cadence("pipeline-review", "0 10 * * 4"),
    Cadence("follow-up-sweep", "0 14 * * 5"),
    Cadence("content-plan", "0 10 * * 3"),
    Cadence("calendar-audit", "0 15 * * 5"),
    Cadence("revenue-review", "0 9 1 * *"),
    Cadence("quarterly-planning", "0 11 1 1,4,7,10 *"),
)
PORTFOLIO_CADENCES = (Cadence("portfolio-review", "15 8 * * 1"),)


def _cadences(config: CadenceConfig) -> Tuple[Cadence, ...]:
    return (
        PORTFOLIO_CADENCES
        if config.slug == "portfolio"
        else BUSINESS_CADENCES
    )


def _marker_identity(slug: Optional[str]) -> str:
    return "founder-os" if slug is None else "founder-os:" + slug


def _file_identity(slug: Optional[str]) -> str:
    return "default" if slug is None else str(slug)


def _normalized_identity(identity: str) -> str:
    if identity == "founder-os":
        return identity
    value = identity
    if value.startswith("founder-os:"):
        value = value.partition(":")[2]
    if SAFE_ID.fullmatch(value) is None:
        raise CadenceError("invalid cadence identity")
    return "founder-os:" + value


def host_argv(config: CadenceConfig, workflow: str) -> Tuple[str, ...]:
    if SAFE_ID.fullmatch(workflow) is None:
        raise CadenceError("invalid workflow")
    if config.host == "claude":
        return (
            str(config.binary),
            "-p",
            "/founder-os:" + workflow,
            "--permission-mode",
            "dontAsk",
            "--allowedTools",
            "mcp__plugin_founder-os_founder-os-state__*",
            "--max-turns",
            "50",
            "--no-session-persistence",
        )
    return (
        str(config.binary),
        "-a",
        "never",
        "exec",
        "--sandbox",
        "workspace-write",
        "--ephemeral",
        "-C",
        str(config.workdir),
        "$founder-os:" + workflow,
    )


def _log_path(config: CadenceConfig, workflow: str) -> Path:
    root = config.log_root
    if config.slug is not None:
        root = root / config.slug
    return root / (workflow + ".log")


def _host_path(config: CadenceConfig, *, system: bool = False) -> str:
    suffix = ":/usr/bin:/bin:/usr/sbin:/sbin" if system else ":/usr/bin:/bin"
    return str(config.binary.parent) + suffix


def _cron_command(config: CadenceConfig, workflow: str) -> str:
    def quote(value: str) -> str:
        # cron interprets percent before invoking the shell, even inside quotes.
        return shlex.quote(value).replace("%", r"\%")

    argv = " ".join(quote(value) for value in host_argv(config, workflow))
    return (
        "cd {workdir} && umask 077 && "
        "PATH={path} FOUNDER_OS_HOME={workspace} {argv} >> {log} 2>&1"
    ).format(
        workdir=quote(str(config.workdir)),
        path=quote(_host_path(config)),
        workspace=quote(str(config.workspace)),
        argv=argv,
        log=quote(str(_log_path(config, workflow))),
    )


def render_cron_blocks(config: CadenceConfig, date: str) -> str:
    try:
        dt.date.fromisoformat(date)
    except (TypeError, ValueError):
        raise CadenceError("date must be YYYY-MM-DD")
    identity = _marker_identity(config.slug)
    lines = [
        "# BEGIN {0} — cadence-manager {1}".format(identity, date)
    ]
    for cadence in _cadences(config):
        lines.append(cadence.cron + " " + _cron_command(config, cadence.workflow))
    lines.append("# END " + identity)
    return "\n".join(lines) + "\n"


def _filter_crontab(
    current: bytes,
    remove_identities: Optional[set[str]],
    remove_all: bool = False,
) -> bytes:
    if not isinstance(current, bytes):
        raise CadenceError("crontab must be bytes")
    kept = []
    active: Optional[str] = None
    remove_active = False
    for line in current.splitlines(keepends=True):
        begin = BEGIN_MARKER.fullmatch(line)
        end = END_MARKER.fullmatch(line)
        marker_like = line.startswith((b"# BEGIN founder-os", b"# END founder-os"))
        if marker_like and begin is None and end is None:
            raise CadenceError("malformed Founder OS fence")
        if begin is not None:
            if active is not None:
                raise CadenceError("nested Founder OS fence")
            active = begin.group(1).decode("ascii")
            remove_active = remove_all or (
                remove_identities is not None and active in remove_identities
            )
            if not remove_active:
                kept.append(line)
            continue
        if end is not None:
            identity = end.group(1).decode("ascii")
            if active is None or identity != active:
                raise CadenceError("mismatched Founder OS fence")
            if not remove_active:
                kept.append(line)
            active = None
            remove_active = False
            continue
        if active is None or not remove_active:
            kept.append(line)
    if active is not None:
        raise CadenceError("unclosed Founder OS fence")
    return b"".join(kept)


def merge_crontab(
    current: bytes,
    block: bytes,
    identity: str,
    *,
    migrate_legacy: bool = False,
) -> bytes:
    target = _normalized_identity(identity)
    remove_identities = {target}
    if migrate_legacy and target != "founder-os":
        remove_identities.add("founder-os")
    base = _filter_crontab(current, remove_identities)
    parsed_block = _filter_crontab(block, set())
    block_begins = [
        match.group(1).decode("ascii")
        for line in block.splitlines(keepends=True)
        for match in [BEGIN_MARKER.fullmatch(line)]
        if match is not None
    ]
    if parsed_block != block or block_begins != [target]:
        raise CadenceError("preview block identity mismatch")
    if base and not base.endswith(b"\n"):
        base += b"\n"
    return base + block


def remove_crontab(current: bytes, identity: str) -> bytes:
    if identity == "all":
        return _filter_crontab(current, None, remove_all=True)
    return _filter_crontab(current, {_normalized_identity(identity)})


def _launchd_calendar(workflow: str):
    values = {
        "week-plan": {"Weekday": 1, "Hour": 8, "Minute": 30},
        "weekly-review": {"Weekday": 5, "Hour": 16, "Minute": 0},
        "pipeline-review": {"Weekday": 4, "Hour": 10, "Minute": 0},
        "follow-up-sweep": {"Weekday": 5, "Hour": 14, "Minute": 0},
        "content-plan": {"Weekday": 3, "Hour": 10, "Minute": 0},
        "calendar-audit": {"Weekday": 5, "Hour": 15, "Minute": 0},
        "revenue-review": {"Day": 1, "Hour": 9, "Minute": 0},
        "portfolio-review": {"Weekday": 1, "Hour": 8, "Minute": 15},
    }
    if workflow == "daily-brief":
        return [
            {"Weekday": weekday, "Hour": 8, "Minute": 0}
            for weekday in range(1, 6)
        ]
    if workflow == "quarterly-planning":
        return [
            {"Month": month, "Day": 1, "Hour": 11, "Minute": 0}
            for month in (1, 4, 7, 10)
        ]
    return values[workflow]


def _unit_stem(config: CadenceConfig, workflow: str) -> str:
    return "com.founder-os.{0}.{1}".format(
        _file_identity(config.slug), workflow
    )


def render_launchd(config: CadenceConfig) -> Dict[str, bytes]:
    artifacts = {}
    for cadence in _cadences(config):
        stem = _unit_stem(config, cadence.workflow)
        log = str(_log_path(config, cadence.workflow))
        document = {
            "Label": stem,
            "ProgramArguments": list(host_argv(config, cadence.workflow)),
            "EnvironmentVariables": {
                "FOUNDER_OS_HOME": str(config.workspace),
                "PATH": _host_path(config, system=True),
            },
            "WorkingDirectory": str(config.workdir),
            "StandardOutPath": log,
            "StandardErrorPath": log,
            "StartCalendarInterval": _launchd_calendar(cadence.workflow),
            "Umask": 0o077,
        }
        artifacts[stem + ".plist"] = plistlib.dumps(
            document, fmt=plistlib.FMT_XML, sort_keys=True
        )
    return artifacts


def _systemd_quote(value: str, *, command: bool = False) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    if command:
        escaped = escaped.replace("$", "$$")
    return '"' + escaped.replace("%", "%%") + '"'


def _systemd_calendar(workflow: str) -> str:
    return {
        "daily-brief": "Mon..Fri *-*-* 08:00:00",
        "week-plan": "Mon *-*-* 08:30:00",
        "weekly-review": "Fri *-*-* 16:00:00",
        "pipeline-review": "Thu *-*-* 10:00:00",
        "follow-up-sweep": "Fri *-*-* 14:00:00",
        "content-plan": "Wed *-*-* 10:00:00",
        "calendar-audit": "Fri *-*-* 15:00:00",
        "revenue-review": "*-*-01 09:00:00",
        "quarterly-planning": "*-01,04,07,10-01 11:00:00",
        "portfolio-review": "Mon *-*-* 08:15:00",
    }[workflow]


def render_systemd(config: CadenceConfig) -> Dict[str, bytes]:
    artifacts = {}
    for cadence in _cadences(config):
        stem = _unit_stem(config, cadence.workflow)
        command = " ".join(
            _systemd_quote(value, command=True)
            for value in host_argv(config, cadence.workflow)
        )
        service = (
            "[Unit]\nDescription=Founder OS {workflow}\n\n"
            "[Service]\nType=oneshot\nUMask=0077\n"
            "WorkingDirectory={workdir}\n"
            "Environment={environment}\nEnvironment={path}\n"
            "ExecStart={command}\n"
            "StandardOutput={log}\nStandardError={log}\n"
        ).format(
            workflow=cadence.workflow,
            workdir=_systemd_quote(str(config.workdir)),
            environment=_systemd_quote(
                "FOUNDER_OS_HOME=" + str(config.workspace)
            ),
            path=_systemd_quote("PATH=" + _host_path(config)),
            command=command,
            log=_systemd_quote(
                "append:" + str(_log_path(config, cadence.workflow))
            ),
        )
        timer = (
            "[Unit]\nDescription=Founder OS {workflow} timer\n\n"
            "[Timer]\nOnCalendar={calendar}\nPersistent=true\n"
            "Unit={stem}.service\n\n[Install]\nWantedBy=timers.target\n"
        ).format(
            workflow=cadence.workflow,
            calendar=_systemd_calendar(cadence.workflow),
            stem=stem,
        )
        artifacts[stem + ".service"] = service.encode("utf-8")
        artifacts[stem + ".timer"] = timer.encode("utf-8")
    return artifacts


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _encode_artifacts(artifacts: Mapping[str, bytes]) -> Dict[str, str]:
    return {
        name: base64.b64encode(artifacts[name]).decode("ascii")
        for name in sorted(artifacts)
    }


def _decode_artifacts(manifest: Mapping[str, object]) -> Dict[str, bytes]:
    raw = manifest.get("artifacts")
    if not isinstance(raw, dict):
        raise CadenceError("manifest artifacts are invalid")
    decoded = {}
    for name, value in raw.items():
        if (
            not isinstance(name, str)
            or not name
            or "/" in name
            or not isinstance(value, str)
        ):
            raise CadenceError("manifest artifact is invalid")
        try:
            decoded[name] = base64.b64decode(value, validate=True)
        except (ValueError, TypeError):
            raise CadenceError("manifest artifact is invalid")
    return decoded


def decode_artifact(manifest: Mapping[str, object], name: str) -> bytes:
    try:
        return _decode_artifacts(manifest)[name]
    except KeyError:
        raise CadenceError("artifact not found")


def _canonical(value: Mapping[str, object]) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def serialize_manifest(manifest: Mapping[str, object]) -> str:
    return _canonical(manifest).decode("utf-8")


def _seal(document: Dict[str, object]) -> Dict[str, object]:
    sealed = dict(document)
    sealed["manifest_sha256"] = _digest(_canonical(document))
    return sealed


def _verify_seal(document: Mapping[str, object]) -> None:
    try:
        checksum = document.get("manifest_sha256")
        bare = dict(document)
        bare.pop("manifest_sha256", None)
        valid = (
            isinstance(checksum, str)
            and checksum == _digest(_canonical(bare))
        )
    except (TypeError, ValueError, UnicodeError, OverflowError):
        valid = False
    if not valid:
        raise CadenceError("manifest checksum mismatch")


def _config_document(config: CadenceConfig) -> Dict[str, object]:
    return {
        "host": config.host,
        "binary": str(config.binary),
        "workspace": str(config.workspace),
        "workdir": str(config.workdir),
        "log_root": str(config.log_root),
        "slug": config.slug,
    }


def _config_from_document(value: object) -> CadenceConfig:
    if not isinstance(value, dict):
        raise CadenceError("manifest config is invalid")
    if set(value) != {
        "host",
        "binary",
        "workspace",
        "workdir",
        "log_root",
        "slug",
    }:
        raise CadenceError("manifest config is invalid")
    try:
        return CadenceConfig(
            host=value["host"],
            binary=Path(value["binary"]),
            workspace=Path(value["workspace"]),
            workdir=Path(value["workdir"]),
            log_root=Path(value["log_root"]),
            slug=value.get("slug"),
        )
    except (KeyError, TypeError):
        raise CadenceError("manifest config is invalid")


def _run(
    runner: Callable[..., object],
    argv: Sequence[str],
) -> object:
    return runner(
        list(argv),
        capture_output=True,
        text=True,
        check=False,
    )


def _read_crontab(runner: Callable[..., object]) -> bytes:
    result = _run(runner, ("crontab", "-l"))
    returncode = getattr(result, "returncode", None)
    if returncode == 1:
        return b""
    if returncode != 0:
        raise CadenceError("could not read user crontab")
    stdout = getattr(result, "stdout", "")
    if not isinstance(stdout, str):
        raise CadenceError("crontab returned invalid output")
    return stdout.encode("utf-8")


def _scheduler_directory(scheduler: str) -> Path:
    if scheduler == "launchd":
        return Path.home() / "Library" / "LaunchAgents"
    if scheduler == "systemd":
        return Path.home() / ".config" / "systemd" / "user"
    raise CadenceError("scheduler has no artifact directory")


def _selected_names(config: CadenceConfig, scheduler: str) -> set[str]:
    prefix = "com.founder-os.{0}.".format(_file_identity(config.slug))
    suffixes = {".plist"} if scheduler == "launchd" else {".service", ".timer"}
    return {
        prefix + cadence.workflow + suffix
        for cadence in _cadences(config)
        for suffix in suffixes
    }


def _read_file_state(config: CadenceConfig, scheduler: str) -> Dict[str, bytes]:
    directory = _scheduler_directory(scheduler)
    state = {}
    for name in sorted(_selected_names(config, scheduler)):
        path = directory / name
        try:
            info = path.lstat()
        except FileNotFoundError:
            continue
        if not stat.S_ISREG(info.st_mode):
            raise CadenceError("scheduler artifact is not a regular file")
        state[name] = path.read_bytes()
    return state


def _state_bytes(state: Mapping[str, bytes]) -> bytes:
    return _canonical({"files": _encode_artifacts(state)})


def preview(
    config: CadenceConfig,
    scheduler: str,
    *,
    runner: Callable[..., object] = subprocess.run,
    date: Optional[str] = None,
    migrate_legacy: bool = False,
) -> Dict[str, object]:
    date = date or dt.date.today().isoformat()
    if scheduler == "cron":
        current = _read_crontab(runner)
        block = render_cron_blocks(config, date).encode("utf-8")
        identity = config.slug if config.slug is not None else "founder-os"
        artifacts = {
            "crontab": merge_crontab(
                current,
                block,
                identity,
                migrate_legacy=migrate_legacy,
            )
        }
        source = current
    elif scheduler == "launchd":
        state = _read_file_state(config, scheduler)
        source = _state_bytes(state)
        artifacts = render_launchd(config)
    elif scheduler == "systemd":
        state = _read_file_state(config, scheduler)
        source = _state_bytes(state)
        artifacts = render_systemd(config)
    else:
        raise CadenceError("unsupported scheduler")
    document = {
        "version": MANIFEST_VERSION,
        "scheduler": scheduler,
        "identity": _marker_identity(config.slug),
        "config": _config_document(config),
        "source_sha256": _digest(source),
        "artifacts": _encode_artifacts(artifacts),
    }
    if scheduler == "cron":
        document["date"] = date
        document["migrate_legacy"] = migrate_legacy
    return _seal(document)


def _fsync_directory(path: Path) -> None:
    directory_flags = os.O_RDONLY | os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        directory_flags |= os.O_NOFOLLOW
    directory_fd = os.open(str(path), directory_flags)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix="." + path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        _fsync_directory(path.parent)
    finally:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def _atomic_create(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix="." + path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary_path, path, follow_symlinks=False)
        except FileExistsError:
            raise CadenceError("refusing to overwrite an existing file")
        temporary_path.unlink()
        _fsync_directory(path.parent)
    finally:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def snapshot(
    config: CadenceConfig,
    scheduler: str,
    backup_root: Path,
    *,
    runner: Callable[..., object] = subprocess.run,
    timestamp: Optional[str] = None,
) -> Dict[str, object]:
    if not backup_root.is_absolute():
        raise CadenceError("backup root must be absolute")
    try:
        backup_root.resolve().relative_to(config.workspace.resolve())
    except ValueError:
        pass
    else:
        raise CadenceError("backup root cannot be inside the workspace")
    timestamp = timestamp or dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    if re.fullmatch(r"[0-9]{8}-[0-9]{6}", timestamp) is None:
        raise CadenceError("invalid snapshot timestamp")
    if scheduler == "cron":
        source = _read_crontab(runner)
        suffix = ".txt"
    elif scheduler in {"launchd", "systemd"}:
        source = _state_bytes(_read_file_state(config, scheduler))
        suffix = ".json"
    else:
        raise CadenceError("unsupported scheduler")
    backup = backup_root / (
        "{0}-{1}-backup-{2}{3}".format(
            scheduler,
            _file_identity(config.slug),
            timestamp,
            suffix,
        )
    )
    _atomic_create(backup, source)
    return _seal(
        {
            "version": MANIFEST_VERSION,
            "scheduler": scheduler,
            "identity": _marker_identity(config.slug),
            "source_sha256": _digest(source),
            "backup_path": str(backup),
        }
    )


def _current_source(
    config: CadenceConfig,
    scheduler: str,
    runner: Callable[..., object],
) -> bytes:
    if scheduler == "cron":
        return _read_crontab(runner)
    return _state_bytes(_read_file_state(config, scheduler))


def _install_crontab(
    content: bytes,
    runner: Callable[..., object],
    directory: Path,
) -> None:
    descriptor, temporary = tempfile.mkstemp(
        prefix=".founder-os-crontab-", suffix=".tmp", dir=str(directory)
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        result = _run(runner, ("crontab", temporary))
        if getattr(result, "returncode", None) != 0:
            raise CadenceError("crontab install failed")
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _ensure_log_directories(config: CadenceConfig) -> None:
    directories = {
        _log_path(config, cadence.workflow).parent
        for cadence in _cadences(config)
    }
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        info = directory.lstat()
        if not stat.S_ISDIR(info.st_mode):
            raise CadenceError("log path is not a directory")
        os.chmod(directory, 0o700, follow_symlinks=False)


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _read_backup(path: Path, workspace: Path) -> bytes:
    if not path.is_absolute() or _inside(path, workspace):
        raise CadenceError("snapshot backup is unsafe")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(str(path), flags)
    except OSError:
        raise CadenceError("snapshot backup is missing")
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise CadenceError("snapshot backup is unsafe")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _expected_artifacts(
    manifest: Mapping[str, object],
    config: CadenceConfig,
    scheduler: str,
    source: bytes,
) -> Dict[str, bytes]:
    if scheduler == "cron":
        date = manifest.get("date")
        migrate_legacy = manifest.get("migrate_legacy")
        if not isinstance(date, str) or not isinstance(migrate_legacy, bool):
            raise CadenceError("cron preview is invalid")
        block = render_cron_blocks(config, date).encode("utf-8")
        identity = config.slug if config.slug is not None else "founder-os"
        return {
            "crontab": merge_crontab(
                source,
                block,
                identity,
                migrate_legacy=migrate_legacy,
            )
        }
    if scheduler == "launchd":
        return render_launchd(config)
    if scheduler == "systemd":
        return render_systemd(config)
    raise CadenceError("unsupported scheduler")


def apply(
    manifest: Mapping[str, object],
    snapshot_document: Mapping[str, object],
    *,
    runner: Callable[..., object] = subprocess.run,
) -> None:
    _verify_seal(manifest)
    _verify_seal(snapshot_document)
    scheduler = manifest.get("scheduler")
    manifest_keys = {
        "version",
        "scheduler",
        "identity",
        "config",
        "source_sha256",
        "artifacts",
        "manifest_sha256",
    }
    if scheduler == "cron":
        manifest_keys.update(("date", "migrate_legacy"))
    if set(manifest) != manifest_keys or set(snapshot_document) != {
        "version",
        "scheduler",
        "identity",
        "source_sha256",
        "backup_path",
        "manifest_sha256",
    }:
        raise CadenceError("manifest shape is invalid")
    if (
        type(manifest.get("version")) is not int
        or manifest.get("version") != MANIFEST_VERSION
        or type(snapshot_document.get("version")) is not int
        or snapshot_document.get("version") != MANIFEST_VERSION
    ):
        raise CadenceError("unsupported manifest version")
    if (
        scheduler != snapshot_document.get("scheduler")
        or manifest.get("identity") != snapshot_document.get("identity")
        or manifest.get("source_sha256")
        != snapshot_document.get("source_sha256")
    ):
        raise CadenceError("preview and snapshot do not match")
    config = _config_from_document(manifest.get("config"))
    if manifest.get("identity") != _marker_identity(config.slug):
        raise CadenceError("manifest identity does not match config")
    current = _current_source(config, str(scheduler), runner)
    if _digest(current) != manifest.get("source_sha256"):
        raise CadenceError("scheduler state changed after preview")
    backup_path = Path(str(snapshot_document.get("backup_path")))
    backup = _read_backup(backup_path, config.workspace)
    if _digest(backup) != snapshot_document.get("source_sha256"):
        raise CadenceError("snapshot backup checksum mismatch")
    artifacts = _decode_artifacts(manifest)
    if artifacts != _expected_artifacts(
        manifest, config, str(scheduler), backup
    ):
        raise CadenceError("preview artifacts do not match the config")
    _ensure_log_directories(config)
    if scheduler == "cron":
        _install_crontab(artifacts["crontab"], runner, backup_path.parent)
        return

    directory = _scheduler_directory(str(scheduler))
    directory.mkdir(parents=True, exist_ok=True)
    for name, content in artifacts.items():
        _atomic_write(directory / name, content)
    if scheduler == "launchd":
        domain = "gui/" + str(os.getuid())
        for name in sorted(artifacts):
            label = name.removesuffix(".plist")
            _run(runner, ("launchctl", "bootout", domain + "/" + label))
            result = _run(runner, ("launchctl", "bootstrap", domain, str(directory / name)))
            if getattr(result, "returncode", None) != 0:
                raise CadenceError("launchd bootstrap failed")
    elif scheduler == "systemd":
        if getattr(
            _run(runner, ("systemctl", "--user", "daemon-reload")),
            "returncode",
            None,
        ) != 0:
            raise CadenceError("systemd daemon-reload failed")
        timers = sorted(name for name in artifacts if name.endswith(".timer"))
        result = _run(
            runner, ("systemctl", "--user", "enable", "--now", *timers)
        )
        if getattr(result, "returncode", None) != 0:
            raise CadenceError("systemd timer enable failed")


def remove(
    config: CadenceConfig,
    scheduler: str,
    identity: str,
    *,
    runner: Callable[..., object] = subprocess.run,
) -> None:
    if identity != "all":
        expected = config.slug if config.slug is not None else "founder-os"
        if _normalized_identity(identity) != _normalized_identity(expected):
            raise CadenceError("removal identity does not match config")
    if scheduler == "cron":
        current = _read_crontab(runner)
        updated = remove_crontab(current, identity)
        with tempfile.TemporaryDirectory() as temporary:
            _install_crontab(updated, runner, Path(temporary))
        return
    directory = _scheduler_directory(scheduler)
    names = _selected_names(config, scheduler)
    if identity == "all":
        pattern = re.compile(r"com\.founder-os\.[A-Za-z0-9._-]+\..+\.(?:plist|service|timer)")
        names = {
            path.name
            for path in directory.iterdir()
            if pattern.fullmatch(path.name)
        } if directory.is_dir() else set()
    if scheduler == "systemd":
        for name in sorted(name for name in names if name.endswith(".timer")):
            result = _run(
                runner,
                ("systemctl", "--user", "disable", "--now", name),
            )
            if getattr(result, "returncode", None) != 0:
                raise CadenceError("systemd timer disable failed")
    for name in sorted(names):
        path = directory / name
        if scheduler == "launchd" and path.exists():
            _run(
                runner,
                ("launchctl", "bootout", "gui/" + str(os.getuid()), str(path)),
            )
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    if scheduler == "systemd":
        result = _run(runner, ("systemctl", "--user", "daemon-reload"))
        if getattr(result, "returncode", None) != 0:
            raise CadenceError("systemd daemon-reload failed")


def smoke(
    config: CadenceConfig,
    workflow: str,
    *,
    runner: Callable[..., object] = subprocess.run,
) -> None:
    environment = {
        "HOME": str(Path.home()),
        "PATH": _host_path(config),
        "FOUNDER_OS_HOME": str(config.workspace),
    }
    result = runner(
        list(host_argv(config, workflow)),
        cwd=str(config.workdir),
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    if getattr(result, "returncode", None) != 0:
        raise CadenceError("cadence smoke failed")


def _write_json(
    path: Path,
    document: Mapping[str, object],
    *,
    forbidden_root: Optional[Path] = None,
) -> None:
    if not path.is_absolute():
        raise CadenceError("manifest output must be absolute")
    if forbidden_root is not None and _inside(path, forbidden_root):
        raise CadenceError("manifest output cannot be inside the workspace")
    _atomic_create(path, _canonical(document) + b"\n")


def _read_json(path: Path) -> Dict[str, object]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        raise CadenceError("could not read manifest")
    if not isinstance(document, dict):
        raise CadenceError("manifest must be an object")
    return document


def _add_config_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", choices=("claude", "codex"), required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--log-root", type=Path, required=True)
    parser.add_argument("--slug")
    parser.add_argument(
        "--scheduler", choices=("cron", "launchd", "systemd"), required=True
    )


def _config_from_args(args: argparse.Namespace) -> CadenceConfig:
    return CadenceConfig(
        host=args.host,
        binary=args.binary.resolve(),
        workspace=args.workspace.resolve(),
        workdir=args.workdir.resolve(),
        log_root=args.log_root.resolve(),
        slug=args.slug,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    preview_parser = commands.add_parser("preview")
    _add_config_arguments(preview_parser)
    preview_parser.add_argument("--date")
    preview_parser.add_argument("--migrate-legacy", action="store_true")
    preview_parser.add_argument("--output", type=Path, required=True)

    snapshot_parser = commands.add_parser("snapshot")
    _add_config_arguments(snapshot_parser)
    snapshot_parser.add_argument("--backup-root", type=Path, required=True)
    snapshot_parser.add_argument("--timestamp")
    snapshot_parser.add_argument("--output", type=Path, required=True)

    apply_parser = commands.add_parser("apply")
    apply_parser.add_argument("--manifest", type=Path, required=True)
    apply_parser.add_argument("--snapshot", type=Path, required=True)

    remove_parser = commands.add_parser("remove")
    _add_config_arguments(remove_parser)
    remove_parser.add_argument("--identity", required=True)

    smoke_parser = commands.add_parser("smoke")
    _add_config_arguments(smoke_parser)
    smoke_parser.add_argument("--workflow", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "preview":
            config = _config_from_args(args)
            document = preview(
                config,
                args.scheduler,
                date=args.date,
                migrate_legacy=args.migrate_legacy,
            )
            _write_json(
                args.output.resolve(),
                document,
                forbidden_root=config.workspace,
            )
            print(serialize_manifest(document))
        elif args.command == "snapshot":
            config = _config_from_args(args)
            document = snapshot(
                config,
                args.scheduler,
                args.backup_root.resolve(),
                timestamp=args.timestamp,
            )
            _write_json(
                args.output.resolve(),
                document,
                forbidden_root=config.workspace,
            )
            print(serialize_manifest(document))
        elif args.command == "apply":
            apply(_read_json(args.manifest), _read_json(args.snapshot))
        elif args.command == "remove":
            remove(
                _config_from_args(args),
                args.scheduler,
                args.identity,
            )
        else:
            smoke(
                _config_from_args(args),
                args.workflow,
            )
    except CadenceError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
