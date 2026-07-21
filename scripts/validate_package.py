#!/usr/bin/env python3
"""Validate the Founder OS Claude Code plugin.

v2 — retargeted from the paperclipai/agentcompanies format to Claude Code
native. The checks that survived are the ones that were never about paperclip:
one owner per file, one decision per agent, beliefs, guardrails. The ones that
died with the old runtime (COMPANY.md, TEAM.md, .paperclip.yaml routines) are
gone rather than kept "just in case" — a second map goes stale silently.
"""
import json
import re
import sys
from pathlib import Path

import yaml

SYSTEM_SKILLS = {"founder-os-init", "founder-os-doctor", "context-load",
                 "guardrails", "state-integrity", "ingestion-gate",
                 "setup-cadences"}
UNIVERSAL_SKILLS = {"guardrails", "state-integrity", "ingestion-gate"}

# Skills the founder runs directly; they belong to no agent by design.
STANDALONE_SKILLS = {"setup-cadences"}

# House Rule 0, enforced at the tool layer rather than requested in prose.
# An agent with Bash can curl. An agent with WebFetch can POST. An agent with
# an MCP mail tool can send. The rule says agents draft and the founder sends,
# so no agent gets a tool that can reach the outside world — the capability
# existing is the thing the rule is about.
OUTBOUND_TOOLS = {"Bash", "WebFetch", "WebSearch", "NotebookEdit", "Task"}
ALLOWED_AGENT_TOOLS = {"Read", "Write", "Edit", "Glob", "Grep", "Skill", "Agent"}

AGENT_HEADINGS = ["## What triggers you", "## What you do",
                  "## What you produce", "## Who you hand off to"]


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
    for p in sorted(adir.glob("*.md")):
        agents[p.stem] = parse_frontmatter(p)
    return agents


def _tool_names(tools):
    """Split a `tools:` value into bare names. `Agent(a, b)` -> `Agent`."""
    if not tools:
        return []
    if isinstance(tools, list):
        raw = tools
    else:
        raw = re.split(r",\s*(?![^()]*\))", str(tools))
    return [re.sub(r"\(.*\)", "", t).strip() for t in raw if t and t.strip()]


def _agent_targets(tools):
    m = re.search(r"Agent\(([^)]*)\)", str(tools or ""))
    return [t.strip() for t in m.group(1).split(",") if t.strip()] if m else []


def check_plugin(root, agents):
    errs = []
    p = root / ".claude-plugin" / "plugin.json"
    if not p.exists():
        return [".claude-plugin/plugin.json: missing"]
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [".claude-plugin/plugin.json: invalid JSON (%s)" % e]
    if not d.get("name"):
        errs.append("plugin.json: 'name' is the one required field and it is missing")
    if d.get("name") and d["name"] != "founder-os":
        errs.append("plugin.json: name must be 'founder-os'")
    return errs


def check_agents(root, agents):
    errs = []
    for slug in sorted(agents):
        fm, _ = agents[slug]
        for f in ("name", "description", "skills"):
            if not fm.get(f):
                errs.append("agents/%s.md: missing '%s'" % (slug, f))
        if fm.get("name") and fm["name"] != slug:
            errs.append("agents/%s.md: name '%s' does not match the filename"
                        % (slug, fm["name"]))
        for s in fm.get("skills") or []:
            if not (root / "skills" / s / "SKILL.md").exists():
                errs.append("agents/%s.md: skill '%s' has no skills/%s/SKILL.md"
                            % (slug, s, s))
        for req in sorted(UNIVERSAL_SKILLS):
            if req not in (fm.get("skills") or []):
                errs.append("agents/%s.md: must list universal skill '%s'" % (slug, req))
    return errs


def check_agent_tools(root, agents):
    """No agent may hold a tool that can reach the outside world."""
    errs = []
    for slug in sorted(agents):
        fm, _ = agents[slug]
        if not fm.get("tools"):
            errs.append("agents/%s.md: 'tools' must be an explicit allowlist — "
                        "omitting it inherits every tool, including Bash, and an "
                        "agent with Bash can send" % slug)
            continue
        for t in _tool_names(fm["tools"]):
            if t in OUTBOUND_TOOLS:
                errs.append("agents/%s.md: tool '%s' can reach the outside world — "
                            "house rule 0 says agents draft and the founder sends"
                            % (slug, t))
            elif t not in ALLOWED_AGENT_TOOLS:
                errs.append("agents/%s.md: unknown tool '%s'" % (slug, t))
    return errs


def check_agent_graph(root, agents):
    """Every Agent(...) target is a real agent; nobody can summon themselves."""
    errs = []
    for slug in sorted(agents):
        fm, _ = agents[slug]
        for target in _agent_targets(fm.get("tools")):
            if target not in agents:
                errs.append("agents/%s.md: Agent(%s) is not a real agent" % (slug, target))
            elif target == slug:
                errs.append("agents/%s.md: may not summon itself" % slug)
    return errs


def check_role_skill_exclusivity(root, agents):
    errs, seen = [], {}
    for slug in sorted(agents):
        fm, _ = agents[slug]
        for s in fm.get("skills") or []:
            if s in SYSTEM_SKILLS:
                continue
            if s in seen:
                errs.append("role skill '%s' is held by both '%s' and '%s'"
                            % (s, seen[s], slug))
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
        if not d.is_dir():
            continue
        if d.name in referenced or d.name in STANDALONE_SKILLS:
            continue
        errs.append("skills/%s: held by no agent and not declared standalone" % d.name)
    return errs


def check_agent_headings(root, agents):
    errs = []
    for slug in sorted(agents):
        _, body = agents[slug]
        for h in AGENT_HEADINGS:
            if h not in body:
                errs.append("agents/%s.md: missing mandated heading '%s'" % (slug, h))
        found = sorted((body.index(h), h) for h in AGENT_HEADINGS if h in body)
        order = [h for _, h in found]
        expected = [h for h in AGENT_HEADINGS if h in body]
        if order != expected:
            errs.append("agents/%s.md: headings out of order" % slug)
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
                errs.append("ownership.yaml: '%s' is owned by both '%s' and '%s'"
                            % (f, seen[f], agent))
            else:
                seen[f] = agent
    for f in data.get("workspace_files") or []:
        if f not in seen:
            errs.append("ownership.yaml: workspace file '%s' has no owner" % f)
    for f in data.get("portfolio_files") or []:
        if f not in seen:
            errs.append("ownership.yaml: portfolio file '%s' has no owner" % f)
    return errs


def check_workspace_files_complete(root, agents):
    """Every owned path is also a scaffolded path.

    check_ownership walks workspace_files: -> owns: and catches a workspace file
    nobody owns. This is the other direction, and it catches the quieter bug: a
    path in owns: that never made it into workspace_files: is owned, writable and
    green — and founder-os-init scaffolds from workspace_files:, so the directory
    its owner was promised is never created. The agent writes into a path that
    does not exist, on a founder's machine, months later.
    """
    errs = []
    p = root / "references" / "ownership.yaml"
    if not p.exists():
        return errs
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    declared = set(data.get("workspace_files") or [])
    # portfolio_files: is the second scaffold promise — the portfolio workspace,
    # scaffolded by founder-os-init when the registry gains a second business.
    # A path in either list has a scaffolder; a path in neither has none.
    declared |= set(data.get("portfolio_files") or [])
    for agent, files in (data.get("owns") or {}).items():
        for f in files or []:
            if f not in declared:
                errs.append("ownership.yaml: '%s' is owned by '%s' but is not in "
                            "workspace_files: or portfolio_files: — "
                            "founder-os-init will never scaffold it" % (f, agent))
    return errs


def check_skill_writes(root, agents):
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
        if not (d.is_dir() and (d / "SKILL.md").exists()) or d.name in SYSTEM_SKILLS:
            continue
        fm, _ = parse_frontmatter(d / "SKILL.md")
        writes = (fm.get("metadata") or {}).get("writes") or []
        if isinstance(writes, str):
            writes = [writes]
        agent = holder.get(d.name)
        if agent is None:
            continue
        for w in writes:
            if w not in own_path:
                errs.append("skills/%s: writes '%s', which no agent owns" % (d.name, w))
            elif own_path[w] != agent:
                errs.append("skills/%s: held by '%s' but writes '%s', owned by '%s'"
                            % (d.name, agent, w, own_path[w]))
    return errs


def check_sections(root, agents):
    errs = []
    p = root / "references" / "ownership.yaml"
    if not p.exists():
        return errs
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    sections = data.get("sections") or {}
    own_path = _ownership_by_path(root)
    for path in sections:
        if path not in own_path:
            errs.append("ownership.yaml: sections declares '%s', which no agent owns" % path)
    sdir = root / "skills"
    if not sdir.is_dir():
        return errs
    for d in sorted(sdir.iterdir()):
        if not (d.is_dir() and (d / "SKILL.md").exists()) or d.name in SYSTEM_SKILLS:
            continue
        fm, _ = parse_frontmatter(d / "SKILL.md")
        writes = (fm.get("metadata") or {}).get("writes") or []
        if isinstance(writes, str):
            writes = [writes]
        for w in writes:
            if w not in sections:
                errs.append("skills/%s: writes '%s' but ownership.yaml declares no "
                            "sections for it" % (d.name, w))
    return errs


def check_beliefs(root, agents):
    """Every role skill states >=3 principles, before the steps that use them.

    The bar ("at least 3 principles a competent generic advisor would NOT say")
    is a judgement call no regex reaches. This enforces presence, count and
    placement — the difference between a contract and an aspiration.
    """
    errs = []
    sdir = root / "skills"
    if not sdir.is_dir():
        return errs
    for d in sorted(sdir.iterdir()):
        if not (d.is_dir() and (d / "SKILL.md").exists()) or d.name in SYSTEM_SKILLS:
            continue
        _, body = parse_frontmatter(d / "SKILL.md")
        if "## Beliefs" not in body:
            errs.append("skills/%s: missing '## Beliefs'" % d.name)
            continue
        b_at = body.index("## Beliefs")
        if "## Steps" in body and b_at > body.index("## Steps"):
            errs.append("skills/%s: '## Beliefs' must come before '## Steps'" % d.name)
        section = body[b_at + len("## Beliefs"):]
        nxt = re.search(r"\n## ", section)
        if nxt:
            section = section[:nxt.start()]
        bullets = [ln for ln in section.split("\n") if ln.strip().startswith("- ")]
        if len(bullets) < 3:
            errs.append("skills/%s: '## Beliefs' has %d bullet(s); the bar is 3"
                        % (d.name, len(bullets)))
    return errs


def check_hooks(root, agents):
    """The write-time layer is one JSON file and one script; prove both load.

    A typo in the matcher or a syntax error in the guard ships silently today:
    every other check validates prose and map, and the one layer that acts at
    runtime is the one layer nothing exercises at build time. Coverage is
    checked by matching each tool name against the matcher patterns (regex
    fullmatch), not by substring search — "Edit" is a substring of
    "NotebookEdit", so a substring check would pass a matcher that silently
    dropped "Edit".
    """
    errs = []
    hj = root / "hooks" / "hooks.json"
    if not hj.exists():
        return ["hooks/hooks.json: missing — the write-time layer is gone"]
    try:
        data = json.loads(hj.read_text(encoding="utf-8"))
    except ValueError as e:
        return ["hooks/hooks.json: not valid JSON (%s)" % e]
    patterns = [h.get("matcher", "")
                for h in (data.get("hooks") or {}).get("PreToolUse", [])]

    def covered(tool_name):
        for pat in list(patterns):
            if not pat:
                continue
            try:
                if re.fullmatch(pat, tool_name):
                    return True
            except re.error:
                errs.append("hooks/hooks.json: matcher %r is not a valid "
                            "regex" % pat)
                patterns.remove(pat)
        return False

    for tool in ("Write", "Edit", "NotebookEdit", "Bash", "WebFetch", "apply_patch", "mcp__x"):
        if not covered(tool):
            if tool == "mcp__x":
                errs.append("hooks/hooks.json: PreToolUse matcher does not "
                            "cover mcp__ tools")
            else:
                errs.append("hooks/hooks.json: PreToolUse matcher does not "
                            "cover '%s'" % tool)
    guard = root / "hooks" / "ownership-guard.py"
    if not guard.exists():
        errs.append("hooks/ownership-guard.py: missing")
    else:
        try:
            compile(guard.read_text(encoding="utf-8"), str(guard), "exec")
        except SyntaxError as e:
            errs.append("hooks/ownership-guard.py: does not compile (%s)" % e)
    return errs


def check_readme_counts(root, agents):
    """README's counts must match the package, or the README is a second map.

    The package's own philosophy (stated in ownership.yaml's comment block) is
    that a hardcoded count of a growing set goes stale silently — the last one
    said "ten" and stayed at ten. The README table (Agents/Skills/Cadences) is
    exactly such a count, and until now it was the one map nothing checked:
    v2.2 shipped with founder-os-init still saying "eight cadences" a full
    version after the ninth landed. This check makes the drift a build failure
    instead of a review finding.

    A package without a README (the test fixtures) is skipped: the README is
    the storefront, not the structure, and its absence is a packaging question
    rather than a coherence one. Same for the cadence row when setup-cadences
    is absent.
    """
    errs = []
    readme = root / "README.md"
    if not readme.exists():
        return errs
    text = readme.read_text(encoding="utf-8")

    def table_count(label):
        m = re.search(r"^\|\s*%s\s*\|\s*(\d+)\s*\|" % label, text,
                      re.M | re.I)
        return int(m.group(1)) if m else None

    actual = {
        "Agents": len(agents),
        "Skills": len(list((root / "skills").glob("*/SKILL.md"))),
    }
    cadences = root / "skills" / "setup-cadences" / "SKILL.md"
    if cadences.exists():
        rows = re.findall(r"^\|\s*`/[a-z0-9-]+`\s*\|[^|]*\|\s*`[^`]+`\s*\|\s*$",
                          cadences.read_text(encoding="utf-8"), re.M)
        actual["Cadences"] = len(rows)
    for label, real in actual.items():
        claimed = table_count(label)
        if claimed is None:
            errs.append("README.md: 'What's inside' table has no '%s' row" % label)
        elif claimed != real:
            errs.append("README.md: claims %d %s, the package has %d — a count "
                        "that drifts is a second map" % (claimed, label.lower(), real))
    return errs


CHECKS = [check_plugin, check_agents, check_agent_tools, check_agent_graph,
          check_role_skill_exclusivity, check_orphans, check_agent_headings,
          check_ownership, check_workspace_files_complete, check_skill_writes,
          check_sections, check_beliefs, check_hooks, check_readme_counts]


def run_checks(root):
    """Load agents and run every check, containing per-file parse failures.

    One malformed SKILL.md used to kill the whole run with a traceback — the
    difference between "FAIL: skills/x: missing YAML frontmatter" and a
    stack trace is whether the author reads the other forty findings.
    """
    try:
        agents = load_agents(root)
    except (ValueError, yaml.YAMLError) as e:
        return {}, [str(e)]
    errs = []
    for fn in CHECKS:
        try:
            errs += fn(root, agents)
        except (ValueError, yaml.YAMLError) as e:
            errs.append("%s (check '%s' aborted at first bad file)"
                        % (e, fn.__name__))
    return agents, errs


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "founder-os")
    if not root.is_dir():
        print("FAIL: plugin root '%s' not found" % root)
        return 1
    agents, errs = run_checks(root)
    for e in errs:
        print("FAIL: %s" % e)
    print("\n%d agent(s), %d skill(s), %d error(s)"
          % (len(agents), len(list((root / "skills").glob("*/SKILL.md"))), len(errs)))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
