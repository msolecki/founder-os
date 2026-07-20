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
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps({"agent_type": agent_type}) + "\n", encoding="utf-8")
    os.replace(tmp, target)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 - a bookkeeping hook must fail open
        sys.stderr.write("founder-os/record-agent: %s\n" % exc)
