#!/usr/bin/env python3
"""Remember Codex turn_id -> identity for the ownership guard.

Claude includes ``agent_type`` directly in PreToolUse. Codex identifies every
tool call by ``turn_id``: UserPromptSubmit records the main turn explicitly,
while SubagentStart records the subagent type. Keeping the small mapping in
PLUGIN_DATA lets the same ownership guard enforce both hosts. Unknown input
deliberately fails open here; the guard fails closed for an unmapped Codex
turn.
"""
import itertools
import json
import math
import os
import re
import stat
import sys
import tempfile
import time
from pathlib import Path

SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")
MAIN_AGENT_TYPE = "__founder_os_main__"
MAPPING_TTL_SECONDS = 24 * 60 * 60
MAPPING_SCAN_LIMIT = 256


def _prune_mappings(target_dir, now):
    for path in itertools.islice(target_dir.iterdir(), MAPPING_SCAN_LIMIT):
        if not path.name.endswith(".json"):
            continue
        turn_id = path.name[:-5]
        if not SAFE_ID.fullmatch(turn_id):
            continue
        descriptor = None
        remove = False
        try:
            flags = os.O_RDONLY | os.O_NOFOLLOW
            if hasattr(os, "O_CLOEXEC"):
                flags |= os.O_CLOEXEC
            descriptor = os.open(str(path), flags)
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_size > 16 * 1024:
                continue
            with os.fdopen(descriptor, encoding="utf-8") as handle:
                descriptor = None
                payload = json.load(handle)
            recorded_at = (
                payload.get("recorded_at")
                if isinstance(payload, dict)
                else None
            )
            remove = (
                not isinstance(payload, dict)
                or set(payload) != {"agent_type", "recorded_at"}
                or isinstance(recorded_at, bool)
                or not isinstance(recorded_at, (int, float))
                or not math.isfinite(float(recorded_at))
                or now - float(recorded_at) >= MAPPING_TTL_SECONDS
            )
        except (OSError, ValueError, TypeError, UnicodeError):
            continue
        finally:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
        if remove:
            try:
                path.unlink()
            except OSError:
                pass


def _fsync_directory(path):
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    descriptor = os.open(str(path), flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main():
    try:
        data = json.load(sys.stdin)
    except (ValueError, TypeError):
        return
    if not isinstance(data, dict):
        return
    turn_id = data.get("turn_id")
    if data.get("hook_event_name") == "UserPromptSubmit":
        if "agent_type" in data:
            return
        agent_type = MAIN_AGENT_TYPE
    else:
        agent_type = data.get("agent_type")
        if agent_type == MAIN_AGENT_TYPE:
            return
    if not all(isinstance(v, str) and SAFE_ID.fullmatch(v)
               for v in (turn_id, agent_type)):
        return
    data_root = os.environ.get("PLUGIN_DATA") or os.environ.get("CLAUDE_PLUGIN_DATA")
    if not data_root:
        return
    target_dir = Path(data_root) / "agent-types"
    target_dir.mkdir(parents=True, exist_ok=True)
    now = time.time()
    if not math.isfinite(now):
        return
    _prune_mappings(target_dir, now)
    target = target_dir / (turn_id + ".json")
    temporary_name = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix="." + turn_id + ".",
            suffix=".tmp",
            dir=str(target_dir),
        )
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(
                {"agent_type": agent_type, "recorded_at": now},
                handle,
                separators=(",", ":"),
                sort_keys=True,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, target)
        temporary_name = None
        _fsync_directory(target_dir)
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 - a bookkeeping hook must fail open
        sys.stderr.write("founder-os/record-agent: %s\n" % exc)
