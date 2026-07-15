#!/usr/bin/env python3
"""Validate the Founder OS agentcompanies/v1 package."""
import re
import sys
from pathlib import Path

import yaml

SYSTEM_SKILLS = {"founder-os-init", "founder-os-doctor", "context-load",
                 "guardrails", "state-integrity"}
UNIVERSAL_SKILLS = {"guardrails", "state-integrity"}
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
        for f in ("name", "description", "slug", "manager"):
            if not fm.get(f):
                errs.append("teams/%s: missing '%s'" % (d.name, f))
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


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "founder-os")
    if not root.is_dir():
        print("FAIL: package root '%s' not found" % root)
        return 1
    agents = load_agents(root)
    errs = (check_company(root) + check_agents(root, agents)
            + check_role_skill_exclusivity(agents) + check_orphans(root, agents)
            + check_teams(root) + check_tasks(root, agents)
            + check_ownership(root, agents) + check_skill_writes(root, agents))
    for e in errs:
        print("FAIL: %s" % e)
    print("\n%d agent(s), %d error(s)" % (len(agents), len(errs)))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
