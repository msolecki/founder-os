#!/usr/bin/env python3
"""Validate the Founder OS agentcompanies/v1 package."""
import re
import sys
from pathlib import Path

import yaml

SYSTEM_SKILLS = {"founder-os-init", "founder-os-doctor", "context-load",
                 "guardrails", "state-integrity", "ingestion-gate"}
# Paperclip runtime enums (packages/shared/src/constants.ts).
CATCH_UP_POLICIES = {"skip_missed", "enqueue_missed_with_cap"}
CONCURRENCY_POLICIES = {"coalesce_if_active", "always_enqueue", "skip_if_active"}
UNIVERSAL_SKILLS = {"guardrails", "state-integrity", "ingestion-gate"}
REQUIRED_COMPANY_FIELDS = ["name", "description", "slug", "schema", "version",
                           "license", "authors", "goals"]


def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        raise ValueError("%s: missing YAML frontmatter" % path)
    return (yaml.safe_load(m.group(1)) or {}), m.group(2)


def load_agents(root):
    agents = {}
    adir = root / "agents"
    if not adir.is_dir():
        return agents
    for d in sorted(adir.iterdir()):
        if d.is_dir() and (d / "AGENTS.md").exists():
            agents[d.name] = parse_frontmatter(d / "AGENTS.md")
    return agents


def check_company(root):
    errs = []
    fm, _ = parse_frontmatter(root / "COMPANY.md")
    for f in REQUIRED_COMPANY_FIELDS:
        if not fm.get(f):
            errs.append("COMPANY.md: missing required field '%s'" % f)
    if fm.get("schema") != "agentcompanies/v1":
        errs.append("COMPANY.md: schema must be 'agentcompanies/v1'")
    if fm.get("slug") != "founder-os":
        errs.append("COMPANY.md: slug must be 'founder-os'")
    return errs


def check_agents(root, agents):
    errs = []
    for slug in sorted(agents):
        fm, body = agents[slug]
        for f in ("name", "title", "skills"):
            if not fm.get(f):
                errs.append("agents/%s: missing '%s'" % (slug, f))
        if "reportsTo" not in fm:
            errs.append("agents/%s: missing 'reportsTo'" % slug)
        rt = fm.get("reportsTo")
        if rt is not None and rt not in agents:
            errs.append("agents/%s: reportsTo '%s' is not a real agent" % (slug, rt))
        skills = fm.get("skills") or []
        for s in skills:
            if not (root / "skills" / s / "SKILL.md").exists():
                errs.append("agents/%s: skill '%s' has no skills/%s/SKILL.md" % (slug, s, s))
        for req in sorted(UNIVERSAL_SKILLS):
            if req not in skills:
                errs.append("agents/%s: must list universal skill '%s'" % (slug, req))
    return errs


def check_role_skill_exclusivity(agents):
    errs, seen = [], {}
    for slug in sorted(agents):
        fm, _ = agents[slug]
        for s in fm.get("skills") or []:
            if s in SYSTEM_SKILLS:
                continue
            if s in seen:
                errs.append("role skill '%s' is owned by both '%s' and '%s'" % (s, seen[s], slug))
            else:
                seen[s] = slug
    return errs


def check_orphans(root, agents):
    errs = []
    referenced = set()
    for fm, _ in agents.values():
        referenced.update(fm.get("skills") or [])
    sdir = root / "skills"
    if not sdir.is_dir():
        return errs
    for d in sorted(sdir.iterdir()):
        if d.is_dir() and d.name not in referenced:
            errs.append("skills/%s: orphan — not listed by any agent" % d.name)
    return errs


def check_teams(root):
    errs = []
    tdir = root / "teams"
    if not tdir.is_dir():
        return errs
    for d in sorted(tdir.iterdir()):
        if not (d.is_dir() and (d / "TEAM.md").exists()):
            continue
        fm, _ = parse_frontmatter(d / "TEAM.md")
        for f in ("name", "description", "slug"):
            if not fm.get(f):
                errs.append("teams/%s: missing '%s'" % (d.name, f))
        # 'manager' must be declared, but null is a legitimate value: a board has
        # no manager — the founder chairs it, and the founder is not an agent.
        # Requiring truthiness here forced teams/board to name the very agent its
        # reviewer exists to attack. Absent and null are different claims: absent
        # is an omission, null is a decision.
        if "manager" not in fm:
            errs.append("teams/%s: missing 'manager' (use 'manager: null' for a "
                        "manager-less team)" % d.name)
        if fm.get("slug") and fm["slug"] != d.name:
            errs.append("teams/%s: slug '%s' does not match directory" % (d.name, fm["slug"]))
        for p in [fm.get("manager")] + list(fm.get("includes") or []):
            if p and not (d / p).exists():
                errs.append("teams/%s: path '%s' does not resolve" % (d.name, p))
    return errs


def check_tasks(root, agents):
    errs = []
    files = sorted(root.glob("tasks/*/TASK.md")) + sorted(root.glob("projects/*/tasks/*/TASK.md"))
    for tfile in files:
        fm, _ = parse_frontmatter(tfile)
        rel = tfile.relative_to(root)
        if not fm.get("name"):
            errs.append("%s: missing 'name'" % rel)
        a = fm.get("assignee")
        if a not in agents:
            errs.append("%s: assignee '%s' is not a real agent" % (rel, a))
            continue
        skill = (fm.get("metadata") or {}).get("skill")
        if not skill:
            errs.append("%s: metadata.skill is required" % rel)
        elif skill not in (agents[a][0].get("skills") or []):
            errs.append("%s: skill '%s' is not in agent '%s' skills[]" % (rel, skill, a))
    return errs


def check_ownership(root, agents):
    errs = []
    p = root / "references" / "ownership.yaml"
    if not p.exists():
        return ["references/ownership.yaml: missing"]
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    seen = {}
    for agent, files in (data.get("owns") or {}).items():
        if agent not in agents:
            errs.append("ownership.yaml: '%s' is not a real agent" % agent)
        for f in files or []:
            if f in seen:
                errs.append("ownership.yaml: '%s' is owned by both '%s' and '%s'" % (f, seen[f], agent))
            else:
                seen[f] = agent
    for f in data.get("workspace_files") or []:
        if f not in seen:
            errs.append("ownership.yaml: workspace file '%s' has no owner" % f)
    return errs


def _ownership_by_path(root):
    p = root / "references" / "ownership.yaml"
    if not p.exists():
        return {}
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    by_path = {}
    for agent, files in (data.get("owns") or {}).items():
        for f in files or []:
            by_path[f] = agent
    return by_path


def check_skill_writes(root, agents):
    """A skill's declared output must be owned by the agent holding the skill.

    Catches the class of bug where an agent runs a skill whose output file
    belongs to someone else — invisible to every other check, because
    agent->skill and file->owner can both be valid while skill->file is not.
    """
    errs = []
    sdir = root / "skills"
    if not sdir.is_dir():
        return errs
    own_path = _ownership_by_path(root)
    holder = {}
    for slug in sorted(agents):
        fm, _ = agents[slug]
        for s in fm.get("skills") or []:
            if s not in SYSTEM_SKILLS:
                holder[s] = slug
    for d in sorted(sdir.iterdir()):
        if not (d.is_dir() and (d / "SKILL.md").exists()):
            continue
        if d.name in SYSTEM_SKILLS:
            continue
        fm, _ = parse_frontmatter(d / "SKILL.md")
        writes = (fm.get("metadata") or {}).get("writes") or []
        if isinstance(writes, str):
            writes = [writes]
        agent = holder.get(d.name)
        if agent is None:
            continue  # orphan skill — check_orphans reports it
        for w in writes:
            if w not in own_path:
                errs.append("skills/%s: writes '%s', which no agent owns in ownership.yaml"
                            % (d.name, w))
            elif own_path[w] != agent:
                errs.append("skills/%s: held by '%s' but writes '%s', owned by '%s'"
                            % (d.name, agent, w, own_path[w]))
    return errs


def check_sections(root, agents):
    """Every workspace path a skill writes must declare its section contract.

    `owns:` says who may write a file; `sections:` says what is inside it. Both
    halves are load-bearing. Without the second, `founder-os-init` scaffolds a
    bare heading, every skill invents its own spelling for the section it was
    told to replace, and nothing catches it — `founder-os-doctor` checks that
    files exist, so section rot is undetectable by design.

    Two directions, because a map can drift on either side:
      - a skill writes a path with no declared sections -> the contract is missing
      - sections are declared for a path no agent owns   -> the contract is stale
    """
    errs = []
    p = root / "references" / "ownership.yaml"
    if not p.exists():
        return errs  # check_ownership reports the missing map
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    sections = data.get("sections") or {}
    own_path = _ownership_by_path(root)

    for path in sorted(sections):
        if path not in own_path:
            errs.append("ownership.yaml: sections declared for '%s', which no "
                        "agent owns" % path)
        if not sections[path]:
            errs.append("ownership.yaml: sections for '%s' is empty" % path)

    sdir = root / "skills"
    if not sdir.is_dir():
        return errs
    for d in sorted(sdir.iterdir()):
        if not (d.is_dir() and (d / "SKILL.md").exists()):
            continue
        fm, _ = parse_frontmatter(d / "SKILL.md")
        writes = (fm.get("metadata") or {}).get("writes") or []
        if isinstance(writes, str):
            writes = [writes]
        for w in writes:
            if w in own_path and w not in sections:
                errs.append("skills/%s: writes '%s', which declares no sections "
                            "in ownership.yaml" % (d.name, w))
    return errs


AGENT_HEADINGS = ["## What triggers you", "## What you do",
                  "## What you produce", "## Who you hand off to"]


def check_agent_headings(root, agents):
    """Agent bodies keep the mandated four headings, in order.

    Twelve agents are only legible if every one answers the same four questions
    in the same order — a reader who has to hunt for "who do I hand off to"
    stops handing off. This was review-only until a reviewer pointed out that
    nothing would catch a regression. `## Refusals` and anything else may follow
    the four; they may not interleave.
    """
    errs = []
    for slug in sorted(agents):
        _, body = agents[slug]
        found = [(body.index(h), h) for h in AGENT_HEADINGS if h in body]
        missing = [h for h in AGENT_HEADINGS if h not in body]
        for h in missing:
            errs.append("agents/%s: missing mandated heading '%s'" % (slug, h))
        order = [h for _, h in sorted(found)]
        expected = [h for h in AGENT_HEADINGS if h in body]
        if order != expected:
            errs.append("agents/%s: headings out of order — got %s, expected %s"
                        % (slug, order, expected))
    return errs


def check_beliefs(root, agents):
    """Every role skill states >=3 principles, before the steps that use them.

    The validator cannot judge whether a belief is any good — the bar ("at least
    3 principles a competent generic advisor would NOT say") is a judgement call
    no regex reaches. It can enforce that the section exists, is populated, and
    sits before `## Steps`, which is the difference between a contract and an
    aspiration. System skills are exempt: they are mechanical procedure, and a
    refusal rule does not get to have opinions about itself.
    """
    errs = []
    sdir = root / "skills"
    if not sdir.is_dir():
        return errs
    for d in sorted(sdir.iterdir()):
        if not (d.is_dir() and (d / "SKILL.md").exists()):
            continue
        if d.name in SYSTEM_SKILLS:
            continue
        _, body = parse_frontmatter(d / "SKILL.md")
        if "## Beliefs" not in body:
            errs.append("skills/%s: missing '## Beliefs' — every role skill states at "
                        "least 3 principles a generic advisor would not say" % d.name)
            continue
        b_at = body.index("## Beliefs")
        if "## Steps" in body and b_at > body.index("## Steps"):
            errs.append("skills/%s: '## Beliefs' must come before '## Steps' — the agent "
                        "reads what it believes before what to do" % d.name)
        section = body[b_at + len("## Beliefs"):]
        nxt = re.search(r"\n## ", section)
        if nxt:
            section = section[:nxt.start()]
        bullets = [ln for ln in section.split("\n") if ln.strip().startswith("- ")]
        if len(bullets) < 3:
            errs.append("skills/%s: '## Beliefs' has %d bullet(s); the bar is 3"
                        % (d.name, len(bullets)))
    return errs


def check_routines(root, agents):
    """Every recurring task must have a real, firing trigger.

    The Paperclip importer parses TASK.md `schedule.recurrence` as
    `legacyRecurrence` and hard-errors on weekly/monthly/yearly interval > 1,
    returning trigger:null — the cadence silently does not exist. Our own
    quarterly-planning (frequency: monthly, interval: 3) shipped that way and
    nothing caught it, because a package that "validates" is not a package that
    imports. This check is the difference.
    """
    errs = []
    tasks = {}
    for tfile in (sorted(root.glob("tasks/*/TASK.md"))
                  + sorted(root.glob("projects/*/tasks/*/TASK.md"))):
        fm, _ = parse_frontmatter(tfile)
        rel = tfile.relative_to(root)
        if "schedule" in fm:
            errs.append("%s: uses legacy 'schedule:' — the importer treats this as "
                        "legacyRecurrence and hard-errors on interval > 1. Use "
                        "'recurring: true' + .paperclip.yaml routines.<slug>.triggers." % rel)
        if fm.get("recurring"):
            tasks[tfile.parent.name] = rel

    p = root / ".paperclip.yaml"
    data = (yaml.safe_load(p.read_text(encoding="utf-8")) or {}) if p.exists() else {}
    routines = data.get("routines") or {}

    for slug in sorted(tasks):
        r = routines.get(slug)
        if not r:
            errs.append("%s: recurring task has no .paperclip.yaml routines.%s entry — "
                        "it will never fire" % (tasks[slug], slug))
            continue
        if r.get("catchUpPolicy") not in CATCH_UP_POLICIES:
            errs.append("routines.%s: catchUpPolicy must be set to one of %s — the runtime "
                        "default (skip_missed) silently drops missed runs"
                        % (slug, sorted(CATCH_UP_POLICIES)))
        cc = r.get("concurrencyPolicy")
        if cc is not None and cc not in CONCURRENCY_POLICIES:
            errs.append("routines.%s: concurrencyPolicy '%s' is not one of %s"
                        % (slug, cc, sorted(CONCURRENCY_POLICIES)))
        scheduled = [t for t in (r.get("triggers") or []) if t.get("kind") == "schedule"]
        if not scheduled:
            errs.append("routines.%s: no trigger of kind 'schedule'" % slug)
        for t in scheduled:
            cron = t.get("cronExpression")
            if not cron or len(str(cron).split()) != 5:
                errs.append("routines.%s: cronExpression '%s' is not a 5-field expression"
                            % (slug, cron))
            if not t.get("timezone"):
                errs.append("routines.%s: schedule trigger needs a timezone" % slug)

    for slug in sorted(routines):
        if slug not in tasks:
            errs.append("routines.%s: no recurring task with that slug" % slug)
    return errs


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "founder-os")
    if not root.is_dir():
        print("FAIL: package root '%s' not found" % root)
        return 1
    agents = load_agents(root)
    errs = (check_company(root) + check_agents(root, agents)
            + check_role_skill_exclusivity(agents) + check_orphans(root, agents)
            + check_teams(root) + check_tasks(root, agents)
            + check_ownership(root, agents) + check_skill_writes(root, agents)
            + check_routines(root, agents) + check_beliefs(root, agents)
            + check_agent_headings(root, agents)
            + check_sections(root, agents))
    for e in errs:
        print("FAIL: %s" % e)
    print("\n%d agent(s), %d error(s)" % (len(agents), len(errs)))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
