#!/usr/bin/env python3
"""Generate founder-os/COMMANDS.md from the package itself.

The user-facing catalogue — every skill, who runs it, when it fires — is
exactly the kind of hand-maintained table this package refuses to keep: a
second map that goes stale silently (ownership.yaml's comment block explains
why at length). So it is not hand-maintained. This script derives it from the
skills' own frontmatter, the agents' `skills[]`, and the cadence table in
setup-cadences, and CI fails when the committed file differs from what the
package would generate (`--check`).

Usage:
    python3 scripts/generate_commands.py [root]          # write COMMANDS.md
    python3 scripts/generate_commands.py [root] --check  # exit 1 if stale
"""
import re
import sys
from pathlib import Path

import yaml

# Keep in sync with scripts/validate_package.py — same sets, same meaning.
SYSTEM_SKILLS = {"founder-os-init", "founder-os-doctor", "context-load",
                 "guardrails", "state-integrity", "ingestion-gate",
                 "setup-cadences"}
STANDALONE_SKILLS = {"setup-cadences"}

HEADER = """\
# Commands

<!-- GENERATED FILE — do not edit. `python3 scripts/generate_commands.py`
     regenerates it from the agents' and skills' own frontmatter; CI fails
     when this file and the package disagree. A hand edit here is a second
     map, and second maps go stale silently. -->

Every skill is a slash command: `/founder-os:<name>` (the bare `/<name>` works
until another package claims it). On a multi-business install, pass the
business slug first — `/founder-os:daily-brief acme`.

Don't know which command? Ask the **chief-of-staff** — routing is its decision.
"""


def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        raise ValueError("%s: missing YAML frontmatter" % path)
    return (yaml.safe_load(m.group(1)) or {}), m.group(2)


def load(root):
    agents = {}
    for p in sorted((root / "agents").glob("*.md")):
        fm, _ = parse_frontmatter(p)
        agents[p.stem] = fm
    skills = {}
    for d in sorted((root / "skills").iterdir()):
        f = d / "SKILL.md"
        if d.is_dir() and f.exists():
            fm, _ = parse_frontmatter(f)
            skills[d.name] = fm
    return agents, skills


def cadence_schedule(root):
    """{skill-slug: human 'when'} from the setup-cadences table."""
    p = root / "skills" / "setup-cadences" / "SKILL.md"
    if not p.exists():
        return {}
    out = {}
    for m in re.finditer(r"^\|\s*`/([a-z0-9-]+)`\s*\|([^|]*)\|\s*`[^`]+`\s*\|\s*$",
                         p.read_text(encoding="utf-8"), re.M):
        out[m.group(1)] = m.group(2).strip()
    return out


def render(root):
    agents, skills = load(root)
    schedule = cadence_schedule(root)
    holder = {}
    for slug in sorted(agents):
        for s in agents[slug].get("skills") or []:
            if s not in SYSTEM_SKILLS:
                holder[s] = slug

    lines = [HEADER]

    lines.append("## The cadences\n")
    lines.append("Scheduled by `/setup-cadences`; every one also works typed"
                 " by hand.\n")
    lines.append("| Command | When | Run by |")
    lines.append("|---|---|---|")
    for s, when in schedule.items():
        who = holder.get(s, "—")
        lines.append("| `/%s` | %s | %s |" % (s, when, who))
    lines.append("")

    lines.append("## By agent\n")
    for slug in sorted(agents):
        fm = agents[slug]
        role = [s for s in fm.get("skills") or [] if s not in SYSTEM_SKILLS]
        if not role:
            continue
        lines.append("### %s\n" % slug)
        desc = (fm.get("description") or "").strip()
        if desc:
            lines.append("%s\n" % desc)
        lines.append("| Command | What it does |")
        lines.append("|---|---|")
        for s in role:
            sdesc = (skills.get(s, {}).get("description") or "").strip()
            lines.append("| `/%s` | %s |" % (s, sdesc))
        lines.append("")

    lines.append("## System commands\n")
    lines.append("Cross-cutting; not tied to one agent's decision.\n")
    lines.append("| Command | What it does |")
    lines.append("|---|---|")
    for s in sorted(SYSTEM_SKILLS):
        if s in skills:
            sdesc = (skills[s].get("description") or "").strip()
            note = " *(standalone — run it yourself)*" if s in STANDALONE_SKILLS else ""
            lines.append("| `/%s` | %s%s |" % (s, sdesc, note))
    lines.append("")
    return "\n".join(lines)


def main():
    args = [a for a in sys.argv[1:] if a != "--check"]
    check = "--check" in sys.argv[1:]
    root = Path(args[0] if args else "founder-os")
    if not root.is_dir():
        print("FAIL: plugin root '%s' not found" % root)
        return 1
    out = root / "COMMANDS.md"
    text = render(root)
    if check:
        current = out.read_text(encoding="utf-8") if out.exists() else ""
        if current != text:
            print("FAIL: %s is stale — run scripts/generate_commands.py" % out)
            return 1
        print("%s is current" % out)
        return 0
    out.write_text(text, encoding="utf-8")
    print("wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
