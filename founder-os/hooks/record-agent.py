#!/usr/bin/env python3
"""Remember Codex turn_id -> agent_type for the ownership guard.

Claude includes ``agent_type`` directly in PreToolUse. Codex provides it at
SubagentStart and then identifies later tool calls by ``turn_id``. Keeping the
small mapping in PLUGIN_DATA lets the same ownership guard enforce both hosts.
Unknown input deliberately fails open.
"""
import json
import os
import re
import sys
import tempfile
from pathlib import Path

SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")


def main():
    try:
        data = json.load(sys.stdin)
    except (ValueError, TypeError):
        return
    if not isinstance(data, dict):
        return
    turn_id = data.get("turn_id")
    agent_type = data.get("agent_type")
    if not all(isinstance(v, str) and SAFE_ID.fullmatch(v)
               for v in (turn_id, agent_type)):
        return
    data_root = os.environ.get("PLUGIN_DATA") or os.environ.get("CLAUDE_PLUGIN_DATA")
    if not data_root:
        return
    target_dir = Path(data_root) / "agent-types"
    target_dir.mkdir(parents=True, exist_ok=True)
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
                {"agent_type": agent_type},
                handle,
                separators=(",", ":"),
                sort_keys=True,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, target)
        temporary_name = None
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
