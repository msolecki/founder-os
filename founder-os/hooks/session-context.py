#!/usr/bin/env python3
"""Inject the canonical Founder OS invariants into Claude Code sessions."""
import json
import os
import sys
from pathlib import Path


def _emit_context(text):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": text,
    }}))


def _emit_warning(root, reason):
    diagnostic = (
        "Founder OS context warning: installed guidance is %s under resolved "
        "plugin path %s. Do not give Founder OS advice until "
        "references/guidance.md is restored."
    ) % (reason, root)
    sys.stderr.write(diagnostic + "\n")
    _emit_context(diagnostic)


WINDOWS_UNSUPPORTED = (
    "Founder OS context warning: this session runs on native Windows, where "
    "the Founder OS state server cannot start. Do not run Founder OS "
    "workflows here. Tell the user to install WSL (wsl --install), open "
    "Claude Code inside the WSL shell, and run setup again there."
)


def main():
    if sys.platform == "win32":
        sys.stderr.write(WINDOWS_UNSUPPORTED + "\n")
        _emit_context(WINDOWS_UNSUPPORTED)
        return 0
    configured_root = (
        os.environ.get("PLUGIN_ROOT")
        or os.environ.get("CLAUDE_PLUGIN_ROOT")
        or str(Path(__file__).resolve().parents[1])
    )
    root = Path(configured_root).expanduser().resolve()
    guidance = root / "references" / "guidance.md"
    try:
        text = guidance.read_text(encoding="utf-8")
    except FileNotFoundError:
        _emit_warning(root, "missing")
    except UnicodeDecodeError:
        _emit_warning(root, "invalid UTF-8")
    except OSError:
        _emit_warning(root, "unreadable")
    else:
        _emit_context(
            "Founder OS canonical guidance (shared with Claude Code):\n\n"
            + text
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
