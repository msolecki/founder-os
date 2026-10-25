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
    rb'"name":"mcp__plugin_founder-os_founder-os-state__'
    rb'|"(?:skill|subagent_type)":"founder-os:'
    rb'|<command-name>/founder-os:')
TOOL_USE = b'"type":"tool_use"'
BLOB = b'{"type":"api-request-blob"'


def scan(line, n, in_use):
    # A request blob copies earlier turns, which would count twice.
    if line.startswith(BLOB):
        return n, in_use
    return n + line.count(TOOL_USE), in_use or bool(IN_USE.search(line))


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
    marker = os.path.join(marker_dir, sid)

    # The marker directory must be ours and not a link, or another local user
    # could steer the cleanup or plant a scan state.
    old = os.umask(0o077)
    try:
        os.makedirs(marker_dir, exist_ok=True)
    finally:
        os.umask(old)
    if not (owned_dir(marker_dir) and owned_dir(os.path.dirname(marker_dir))):
        return 0

    # Every Stop leaves a scan state, and most sessions never reach the nudge,
    # so the sweep runs here, at most once a day, not only after a nudge.
    now = time.time()
    stamp = os.path.join(marker_dir, ".swept")
    try:
        due = now - os.stat(stamp).st_mtime >= 86400
    except OSError:
        due = True
    if due:
        open(stamp, "w").close()
        for entry in os.scandir(marker_dir):
            try:
                if (entry.is_file(follow_symlinks=False)
                        and now - entry.stat(follow_symlinks=False).st_mtime
                        >= 8 * 86400):
                    os.remove(entry.path)
            except OSError:
                pass
    if os.path.exists(marker):
        return 0

    minimum = os.environ.get("FOUNDER_OS_STOP_NUDGE_MIN", "30")
    minimum = int(minimum) if minimum.isascii() and minimum.isdigit() else 30
    # A transcript can run to hundreds of MB and only grows, so each Stop
    # resumes from the byte offset the previous one reached for this session.
    state_path = marker + ".scan"
    try:
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)
        offset, n, in_use = (int(state["offset"]), int(state["n"]),
                             state["in_use"] is True)
    except (OSError, ValueError, KeyError, TypeError):
        offset, n, in_use = 0, 0, False
    tail = b""
    with open(transcript, "rb") as f:
        if offset > os.fstat(f.fileno()).st_size:
            offset, n, in_use = 0, 0, False  # rewritten: start over
        f.seek(offset)
        for line in f:
            if not line.endswith(b"\n"):
                tail = line  # still being written: count it, do not persist
                break
            offset += len(line)
            n, in_use = scan(line, n, in_use)
    temporary = state_path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as f:
        json.dump({"offset": offset, "n": n, "in_use": in_use}, f)
    os.replace(temporary, state_path)
    n, in_use = scan(tail, n, in_use)
    if n < minimum or not in_use:
        return 0

    open(marker, "w").close()
    try:
        os.remove(state_path)  # the marker ends this session's scanning
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
