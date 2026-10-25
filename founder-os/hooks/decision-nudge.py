#!/usr/bin/env python3
"""Stop hook: once per session, after FOUNDER_OS_STOP_NUDGE_MIN tool calls
(default 30) in a session that used Founder OS, asks the agent to offer the
founder `decision-log` for any irreversible decision and `capture` for loose
items. It never prints transcript content: only the call count.

House rule 3 says irreversible decisions get logged, and a long session is
where one gets made and then forgotten when the window closes.

Fails open: every unexpected state exits 0, so a broken reminder never blocks
a session. Skips headless and SDK runs (`claude -p` sets
CLAUDE_CODE_ENTRYPOINT=sdk-cli): nobody is there to answer. If a release drops
that variable, a headless run gets one extra turn — `stop_hook_active` stops a
second, so never a loop.
"""
import json
import os
import re
import sys
import time

# Any of these in the transcript means a Founder OS workspace was in use: a
# gateway call, a packaged workflow, a packaged role, or a typed command.
IN_USE = re.compile(
    r'"name":"mcp__plugin_founder-os_founder-os-state__'
    r'|"(?:skill|subagent_type)":"founder-os:'
    r'|<command-name>/founder-os:')


def field(text, key):
    """First string value of a top-level key; the hook input is flat JSON."""
    m = re.search(r'"%s"\s*:\s*"([^"]*)"' % key, text)
    return m.group(1) if m else ""


def owned_dir(path):
    st = os.lstat(path)
    return not os.path.islink(path) and st.st_uid == os.getuid()


def main():
    if os.environ.get("FOUNDER_OS_STOP_NUDGE") == "off":
        return 0
    if os.environ.get("CLAUDE_CODE_ENTRYPOINT", "").startswith("sdk-"):
        return 0

    text = sys.stdin.buffer.read().decode("utf-8", "replace")
    text = text.replace("\n", " ").replace("\r", " ")
    if (re.search(r'"stop_hook_active"\s*:\s*true', text)
            or re.search(r'"agent_id"\s*:', text)):
        return 0

    sid = field(text, "session_id")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", sid):
        return 0
    transcript = field(text, "transcript_path")
    if not os.path.isfile(transcript):
        return 0

    base = os.environ.get("CLAUDE_PLUGIN_DATA") or "%s/founder-os-%d" % (
        os.environ.get("TMPDIR") or "/tmp", os.getuid())
    marker_dir = os.path.join(base, "stop-nudge")
    if os.path.exists(os.path.join(marker_dir, sid)):
        return 0

    minimum = os.environ.get("FOUNDER_OS_STOP_NUDGE_MIN", "30")
    minimum = int(minimum) if minimum.isascii() and minimum.isdigit() else 30
    # One streaming pass: a transcript can run to hundreds of MB.
    n, in_use = 0, False
    with open(transcript, encoding="utf-8", errors="replace",
              newline="\n") as f:
        for line in f:
            # A request blob copies earlier turns, which would count twice.
            if line.startswith('{"type":"api-request-blob"'):
                continue
            n += line.count('"type":"tool_use"')
            in_use = in_use or bool(IN_USE.search(line))
    if n < minimum or not in_use:
        return 0

    # The marker directory must be ours and not a link, or another local user
    # could steer the cleanup.
    old = os.umask(0o077)
    try:
        os.makedirs(marker_dir, exist_ok=True)
    finally:
        os.umask(old)
    if not (owned_dir(marker_dir) and owned_dir(os.path.dirname(marker_dir))):
        return 0
    open(os.path.join(marker_dir, sid), "w").close()
    now = time.time()
    for entry in os.scandir(marker_dir):
        try:
            if (entry.is_file(follow_symlinks=False)
                    and now - entry.stat(follow_symlinks=False).st_mtime
                    >= 8 * 86400):
                os.remove(entry.path)
        except OSError:
            pass

    # additionalContext, unlike exit 2 or decision "block", continues the turn
    # without a hook error label.
    msg = ("Founder OS: this session made %d tool calls. If the founder made "
           "an irreversible decision in it, offer to log it to decisions/ with "
           "the founder-os:decision-log workflow; offer founder-os:capture for "
           "any loose item still unrecorded. Write nothing they do not "
           "approve. If nothing qualifies, end your turn with no output." % n)
    sys.stdout.write(json.dumps({"hookSpecificOutput": {
        "hookEventName": "Stop", "additionalContext": msg}}))
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception:
        code = 0
    sys.exit(code)
