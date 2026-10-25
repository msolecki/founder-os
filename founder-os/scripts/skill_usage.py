#!/usr/bin/env python3
"""How often each Founder OS workflow and role ran, from local session history.

Reads the Claude Code transcripts under `${CLAUDE_CONFIG_DIR:-~/.claude}/
projects/**/*.jsonl` and counts three shapes, all of this plugin only: a model
Skill call on `founder-os:<workflow>`, an Agent dispatch of
`founder-os:<role>`, and a typed `/founder-os:<workflow>` command. Prints, per
name, the calls in the last 30 days and the last date it ran, then the names
that never ran.

Read-only, local, stdlib. It prints names, counts and dates — never a
transcript line, a project directory name or a file path, because those
carry the founder's business and their machine's layout.

    python3 <plugin>/scripts/skill_usage.py
"""
import datetime
import json
import os
import re
import sys
from pathlib import Path

PREFIX = "founder-os:"
WINDOW_DAYS = 30
COMMAND = re.compile(r"<command-name>/founder-os:([a-z0-9-]+)</command-name>")


def packaged_names(plugin_root):
    skills = {p.parent.name for p in (plugin_root / "skills").glob("*/SKILL.md")}
    agents = {p.stem for p in (plugin_root / "agents").glob("*.md")}
    return skills, agents


def _calls(record):
    """Plugin names one transcript record invoked."""
    message = record.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return COMMAND.findall(content)
    names = []
    for block in content if isinstance(content, list) else []:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            names += COMMAND.findall(str(block.get("text", "")))
        if block.get("type") != "tool_use":
            continue
        tool_input = block.get("input")
        if not isinstance(tool_input, dict):
            continue
        value = tool_input.get("skill") if block.get("name") == "Skill" else (
            tool_input.get("subagent_type")
            if block.get("name") in ("Agent", "Task") else None)
        # Only a slug is ever kept, so free text after the prefix is never
        # printed back.
        if isinstance(value, str) and re.fullmatch(
                re.escape(PREFIX) + "[a-z0-9-]+", value):
            names.append(value[len(PREFIX):])
    return names


def scan(projects):
    """{name: [dates]}, one entry per distinct message uuid."""
    seen, used = set(), {}
    for path in sorted(Path(projects).glob("**/*.jsonl")):
        try:
            handle = open(path, encoding="utf-8", errors="replace")
        except OSError:
            continue
        with handle:
            for line in handle:
                # Cheap filter first: transcripts run to hundreds of MB.
                if PREFIX not in line:
                    continue
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(record, dict):
                    continue
                # A resumed or forked session repeats earlier lines.
                # A record with no uuid cannot be a repeat we can recognise.
                uuid = record.get("uuid")
                if isinstance(uuid, str):
                    if uuid in seen:
                        continue
                    seen.add(uuid)
                day = str(record.get("timestamp", ""))[:10]
                try:
                    datetime.date.fromisoformat(day)
                except ValueError:
                    continue
                for name in _calls(record):
                    used.setdefault(name, []).append(day)
    return used


def report(used, skills, agents, today):
    cutoff = (today - datetime.timedelta(days=WINDOW_DAYS)).isoformat()
    rows = ["kind | name | calls 30d | last used"]
    for name in sorted(used, key=lambda n: (-len(used[n]), n)):
        if name not in skills | agents:
            continue
        kind = "workflow" if name in skills else "role"
        recent = sum(1 for day in used[name] if day >= cutoff)
        rows.append("%s | %s | %d | %s" % (kind, name, recent, max(used[name])))
    never = sorted((skills | agents) - set(used))
    rows.append("")
    rows.append("Never used (%d): %s" % (len(never), ", ".join(never) or "none"))
    gone = sorted(set(used) - skills - agents)
    if gone:
        rows.append("Seen in history, no longer packaged: " + ", ".join(gone))
    dates = [day for days in used.values() for day in days]
    if dates:
        rows.append("History covers %s to %s." % (min(dates), max(dates)))
    # Cadences run with --no-session-persistence, so they leave no transcript.
    rows.append("Note: scheduled runs are not counted (they keep no session "
                "history), so a cadence workflow can show as never used.")
    return "\n".join(rows)


def main():
    config = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    skills, agents = packaged_names(Path(__file__).resolve().parents[1])
    used = scan(Path(config) / "projects")
    print(report(used, skills, agents, datetime.date.today()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
