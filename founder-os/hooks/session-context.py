#!/usr/bin/env python3
"""Inject the canonical Founder OS invariants into Claude and Codex sessions."""
import json
import os
from pathlib import Path


def main():
    root = (os.environ.get("PLUGIN_ROOT")
            or os.environ.get("CLAUDE_PLUGIN_ROOT")
            or str(Path(__file__).resolve().parents[1]))
    guidance = Path(root) / "CLAUDE.md"
    if not guidance.is_file():
        return
    text = guidance.read_text(encoding="utf-8")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": (
            "Founder OS canonical guidance (shared with Claude Code):\n\n" + text
        ),
    }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
