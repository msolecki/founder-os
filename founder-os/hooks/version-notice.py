#!/usr/bin/env python3
"""SessionStart hook (startup): one line after an install or an update.

Claude Code has no install or update hook, so a version marker in the plugin
data directory stands in for one. The line goes to the founder
(`systemMessage`) and to the agent (`additionalContext`); nothing else is
printed, and nothing reaches the network.

Fails open: every unexpected state exits 0 with no output. Skips headless and
SDK runs, where nobody reads a notice.
"""
import json
import os
import re
import sys

CHANGELOG = "https://msolecki.github.io/founder-os/changelog.html"
CONTEXT = ("Founder OS showed the founder this notice at session start; "
           "act on it only if they ask:\n")


def owned_dir(path):
    st = os.lstat(path)
    return not os.path.islink(path) and st.st_uid == os.getuid()


def notice(seen, version):
    if seen:
        return "Founder OS updated %s -> %s. What's new: %s" % (
            seen[:32], version, CHANGELOG)
    return "Founder OS %s is installed. What's new: %s" % (version, CHANGELOG)


def main():
    if os.environ.get("FOUNDER_OS_NOTICES") == "off":
        return 0
    if os.environ.get("CLAUDE_CODE_ENTRYPOINT", "").startswith("sdk-"):
        return 0
    source = re.search(r'"source"\s*:\s*"([^"]*)"', sys.stdin.read())
    if source and source.group(1) != "startup":
        return 0

    root = (os.environ.get("CLAUDE_PLUGIN_ROOT")
            or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    with open(os.path.join(root, ".claude-plugin", "plugin.json"),
              encoding="utf-8") as f:
        version = str(json.load(f).get("version", ""))
    if not re.fullmatch(r"[0-9A-Za-z.+-]{1,32}", version):
        return 0

    # Without a marker the notice would repeat every session, so nothing
    # prints unless the marker can be written.
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or "%s/founder-os-%d" % (
        os.environ.get("TMPDIR") or "/tmp", os.getuid())
    marker_dir = os.path.join(base, "notices")
    old = os.umask(0o077)
    try:
        os.makedirs(marker_dir, exist_ok=True)
    finally:
        os.umask(old)
    if not (owned_dir(marker_dir) and owned_dir(os.path.dirname(marker_dir))):
        return 0
    marker = os.path.join(marker_dir, "version")
    try:
        with open(marker, "rb") as f:
            seen = f.read(64).decode("utf-8", "replace").strip()
    except OSError:
        seen = ""
    if seen == version:
        return 0

    msg = notice(seen, version)
    sys.stdout.write(json.dumps({
        "systemMessage": msg,
        "hookSpecificOutput": {"hookEventName": "SessionStart",
                               "additionalContext": CONTEXT + msg},
    }))
    sys.stdout.flush()
    # Marker last: a notice that failed to print is not throttled away.
    with open(marker, "w", encoding="utf-8") as f:
        f.write(version + "\n")
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception:
        code = 0
    sys.exit(code)
