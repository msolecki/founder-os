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
from pathlib import Path, PurePosixPath

import yaml

from _package import (SYSTEM_SKILLS, STANDALONE_SKILLS, UNIVERSAL_SKILLS,
                      parse_frontmatter)

# House Rule 0, enforced at the tool layer rather than requested in prose.
# An agent with Bash can curl. An agent with WebFetch can POST. An agent with
# an MCP mail tool can send. The rule says agents draft and the founder sends,
# so no agent gets a tool that can reach the outside world — the capability
# existing is the thing the rule is about.
OUTBOUND_TOOLS = {"Bash", "WebFetch", "WebSearch", "NotebookEdit", "Task"}
ROLE_GATEWAY_TOOLS = {
    "mcp__founder-os-state__resolve_workspace",
    "mcp__founder-os-state__list_state",
    "mcp__founder-os-state__read_state",
    "mcp__founder-os-state__read_reference",
    "mcp__founder-os-state__write_owned_state",
    "mcp__founder-os-state__close_role_session",
}
ALLOWED_AGENT_TOOLS = ROLE_GATEWAY_TOOLS

AGENT_HEADINGS = ["## What triggers you", "## What you do",
                  "## What you produce", "## Who you hand off to"]


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
    names = []
    for value in raw:
        if not isinstance(value, str):
            names.append("<invalid-tool-type:%s>" % type(value).__name__)
            continue
        token = value.strip()
        if not token:
            continue
        if re.fullmatch(r"Agent\([^)]*\)", token):
            token = "Agent"
        names.append(token)
    return names


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
    codex_path = root / ".codex-plugin" / "plugin.json"
    if codex_path.exists():
        try:
            codex = json.loads(codex_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            return errs + [".codex-plugin/plugin.json: invalid JSON (%s)" % e]
        for field in ("name", "version", "description"):
            if d.get(field) != codex.get(field):
                errs.append("plugin manifests: %s differs between Claude and Codex" % field)
    return errs


def check_host_adapters(root, agents):
    """Validate Claude and Codex point at the same packaged stdio gateway."""
    errs = []
    claude_path = root / ".mcp.json"
    codex_path = root / ".codex-plugin" / "plugin.json"
    claude_expected = {
        "mcpServers": {
            "founder-os-state": {
                "command": "python3",
                "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/founder_os_state.py"],
            },
        },
    }
    codex_expected = {
        "founder-os-state": {
            "command": "python3",
            "args": ["${CODEX_PLUGIN_ROOT}/mcp/founder_os_state.py"],
        },
    }

    if not claude_path.is_file():
        errs.append(".mcp.json: missing Claude founder-os-state adapter")
    else:
        try:
            claude = json.loads(claude_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errs.append(".mcp.json: invalid JSON (%s)" % exc)
        else:
            if claude != claude_expected:
                errs.append(
                    ".mcp.json: founder-os-state must use python3 and "
                    "${CLAUDE_PLUGIN_ROOT}/mcp/founder_os_state.py"
                )

    if not codex_path.is_file():
        errs.append(".codex-plugin/plugin.json: missing Codex adapter manifest")
    else:
        try:
            codex = json.loads(codex_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errs.append(".codex-plugin/plugin.json: invalid JSON (%s)" % exc)
        else:
            if codex.get("mcpServers") != codex_expected:
                errs.append(
                    ".codex-plugin/plugin.json: mcpServers must inline "
                    "founder-os-state via ${CODEX_PLUGIN_ROOT}/mcp/"
                    "founder_os_state.py"
                )

    entry = root / "mcp" / "founder_os_state.py"
    if not entry.is_file():
        errs.append("mcp/founder_os_state.py: missing shared gateway entry")
    else:
        try:
            compile(entry.read_text(encoding="utf-8"), str(entry), "exec")
        except (OSError, SyntaxError) as exc:
            errs.append("mcp/founder_os_state.py: does not compile (%s)" % exc)
    return errs


def check_codex_skill_interfaces(root, agents):
    """Prove every shared workflow has a Codex discovery adapter."""
    errs = []
    for skill_path in sorted((root / "skills").glob("*/SKILL.md")):
        slug = skill_path.parent.name
        interface_path = skill_path.parent / "agents" / "openai.yaml"
        if not interface_path.exists():
            errs.append(
                "skills/%s: missing agents/openai.yaml for Codex" % slug
            )
            continue
        try:
            data = yaml.safe_load(
                interface_path.read_text(encoding="utf-8")
            ) or {}
        except yaml.YAMLError as exc:
            errs.append(
                "skills/%s/agents/openai.yaml: invalid YAML (%s)"
                % (slug, exc)
            )
            continue
        interface = data.get("interface") if isinstance(data, dict) else None
        if not isinstance(interface, dict):
            errs.append(
                "skills/%s/agents/openai.yaml: missing interface" % slug
            )
            continue
        for field in (
            "display_name",
            "short_description",
            "default_prompt",
        ):
            value = interface.get(field)
            if not isinstance(value, str) or not value.strip():
                errs.append(
                    "skills/%s/agents/openai.yaml: missing %s"
                    % (slug, field)
                )
        prompt = interface.get("default_prompt", "")
        prompt_names_skill = (
            isinstance(prompt, str)
            and prompt.strip()
            and ("$" + slug) in prompt
        )
        if isinstance(prompt, str) and prompt.strip() and not prompt_names_skill:
            errs.append(
                "skills/%s/agents/openai.yaml: default_prompt must name $%s"
                % (slug, slug)
            )
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


def check_one_level_orchestration(root, agents):
    """Require sibling roles with one gateway contract and no nested edges."""
    errs = []
    for slug in sorted(agents):
        fm, body = agents[slug]
        declared = fm.get("tools")
        names = set(_tool_names(declared))
        if _agent_targets(declared or "") or "Agent" in names:
            errs.append(
                "agents/%s.md: one-level execution forbids Agent(...)" % slug
            )
        for tool in sorted(ROLE_GATEWAY_TOOLS - names):
            errs.append(
                "agents/%s.md: one-level gateway contract is missing %s"
                % (slug, tool)
            )
        for tool in sorted(names - ROLE_GATEWAY_TOOLS):
            errs.append(
                "agents/%s.md: one-level execution forbids tool %s"
                % (slug, tool)
            )

        lower = body.lower()
        required = (
            "## state and handoff contract",
            "main thread",
            "capability",
            "only state you own",
            "never spawn or invoke another role",
            "expected_persistence",
        )
        absent = [phrase for phrase in required if phrase not in lower]
        if absent:
            errs.append(
                "agents/%s.md: shared state contract is missing %s"
                % (slug, ", ".join(absent))
            )

        active_orchestration = lower.replace(
            "never spawn or invoke another role", ""
        ).replace(
            "do not execute the request or invoke its role", ""
        )
        if re.search(
                r"\b(?:spawn|spawns|summon|summons|invoke|invokes|"
                r"dispatch|dispatches)\b",
                active_orchestration):
            errs.append(
                "agents/%s.md: nested-spawn instructions are forbidden" % slug
            )

        if slug in {
                "chief-of-staff", "delivery-lead", "focus-coach",
                "positioning-advisor"}:
            marker = "## delegation request"
            if marker not in lower:
                errs.append(
                    "agents/%s.md: manager is missing '## Delegation request'"
                    % slug
                )
            else:
                section = lower.split(marker, 1)[1]
                fields = {
                    "role", "workflow", "workspace_id", "correlation_id",
                    "handoff", "expected_persistence",
                }
                missing_fields = [
                    field for field in sorted(fields)
                    if "`%s`" % field not in section
                ]
                if missing_fields:
                    errs.append(
                        "agents/%s.md: delegation request is missing %s"
                        % (slug, ", ".join(missing_fields))
                    )
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
    """Validate matcher coverage and compile both identity-boundary hooks.

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

    for tool in (
        "Read", "Write", "Edit", "NotebookEdit", "Glob", "Grep",
        "Bash", "WebFetch", "WebSearch", "apply_patch", "mcp__x",
    ):
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
    recorder = root / "hooks" / "record-agent.py"
    if not recorder.exists():
        errs.append("hooks/record-agent.py: missing")
    else:
        try:
            compile(recorder.read_text(encoding="utf-8"), str(recorder), "exec")
        except SyntaxError as e:
            errs.append("hooks/record-agent.py: does not compile (%s)" % e)
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

    docs = [root / "docs" / "README.md", root / "docs" / "getting-started.md",
            root / "docs" / "index.html", root / ".codex-plugin" / "plugin.json"]
    patterns = {
        "Agents": r"(\d+)\s+(?:specialized\s+business\s+roles|decision-owning executive agents|agents)",
        "Skills": r"(\d+)\s+(?:skills|workflows)",
        "Cadences": r"(\d+)\s+(?:optional\s+)?(?:operating\s+)?cadences",
    }
    for path in docs:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for label, pattern in patterns.items():
            values = [int(value) for value in re.findall(pattern, text, re.I)]
            if values and any(value != actual.get(label) for value in values):
                errs.append("%s: %s count drifts from package value %d" %
                            (path.relative_to(root), label.lower(), actual.get(label, 0)))
    return errs


CHECKS = [check_plugin, check_host_adapters, check_codex_skill_interfaces, check_agents,
          check_agent_tools, check_one_level_orchestration,
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


def _agent_parts(record):
    if isinstance(record, (tuple, list)) and len(record) == 2:
        return record[0], record[1]
    return record, ""


def _agent_skills(record):
    frontmatter, _ = _agent_parts(record)
    value = frontmatter.get("skills", []) if isinstance(frontmatter, dict) else []
    if isinstance(value, str):
        return {part.strip() for part in value.split(",") if part.strip()}
    return {part for part in value if isinstance(part, str)} if isinstance(value, list) else set()


def _workflow_writes(package_root, workflow):
    """Return declared workflow writes, or None when its contract is invalid."""
    path = package_root / "skills" / workflow / "SKILL.md"
    try:
        frontmatter, _ = parse_frontmatter(path)
    except (OSError, ValueError, yaml.YAMLError):
        return None
    if "metadata" not in frontmatter:
        return []
    metadata = frontmatter.get("metadata")
    if not isinstance(metadata, dict):
        return None
    if "writes" not in metadata:
        return []
    writes = metadata.get("writes")
    if isinstance(writes, str):
        writes = [writes]
    if (not isinstance(writes, list)
            or any(not _nonblank(value) for value in writes)):
        return None
    return writes


def _nonblank(value):
    return isinstance(value, str) and bool(value.strip()) and "\x00" not in value


def _safe_state_path(value):
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path if path.as_posix() == value else None


def _owner_for(ownership, path):
    matches = []
    for prefix, owner in ownership.items():
        raw_prefix = str(prefix)
        prefix_path = PurePosixPath(raw_prefix)
        parts = prefix_path.parts
        is_owned = (
            path == prefix_path
            if not raw_prefix.endswith("/")
            else len(path.parts) > len(parts)
            and path.parts[:len(parts)] == parts
        )
        if is_owned:
            matches.append((len(parts), owner))
    return max(matches)[1] if matches else None


def delegation_request_errors(package_root, agents, request,
                              current_workspace_id, current_correlation_id):
    fields = {"role", "workflow", "workspace_id", "correlation_id", "handoff", "expected_persistence"}
    if not isinstance(request, dict):
        return ["delegation request must contain exactly six fields"]
    errors = []
    actual = set(request)
    if actual != fields:
        errors.append("delegation request must contain exactly role, workflow, workspace_id, correlation_id, handoff, expected_persistence; missing=%s extra=%s" % (sorted(fields - actual), sorted(actual - fields)))
    role, workflow = request.get("role"), request.get("workflow")
    workflow_writes = None
    if not _nonblank(role) or role not in agents:
        errors.append("unknown delegation role %r" % role)
    elif (not _nonblank(workflow)
          or workflow in SYSTEM_SKILLS
          or workflow not in _agent_skills(agents[role])):
        errors.append("workflow %r is not held by role %s" % (workflow, role))
    else:
        workflow_writes = _workflow_writes(package_root, workflow)
        if workflow_writes is None:
            errors.append("workflow %s has no valid persistence contract" % workflow)
    for field in ("workspace_id", "correlation_id"):
        if not _nonblank(request.get(field)):
            errors.append("%s must be a nonblank NUL-free string" % field)
    if not _nonblank(current_workspace_id):
        errors.append("current workspace_id must be a trusted nonblank string")
    elif request.get("workspace_id") != current_workspace_id:
        errors.append("workspace_id must match the resolved workspace")
    if not _nonblank(current_correlation_id):
        errors.append("current correlation_id must be a trusted nonblank string")
    elif request.get("correlation_id") != current_correlation_id:
        errors.append("correlation_id must match the active main-thread flow")
    handoff = request.get("handoff")
    if not _nonblank(handoff):
        errors.append("handoff must be a nonblank NUL-free string")
    else:
        try:
            size = len(handoff.encode("utf-8"))
        except UnicodeEncodeError:
            size = 4097
        if size > 4096:
            errors.append("handoff exceeds 4096 UTF-8 bytes")
    paths = request.get("expected_persistence")
    if not isinstance(paths, list):
        errors.append("expected_persistence must be a list")
        return errors
    if len(paths) > 16:
        errors.append("expected_persistence exceeds 16 paths")
    if workflow_writes and not paths:
        errors.append(
            "expected_persistence may be empty only for a read-only workflow"
        )
    strings = [path for path in paths if isinstance(path, str)]
    if len(strings) != len(paths) or len(strings) != len(set(strings)):
        errors.append("expected_persistence must contain unique path strings")
    ownership = _ownership_by_path(package_root)
    for value in paths:
        path = _safe_state_path(value)
        if path is None:
            errors.append("unsafe expected_persistence path %r" % value)
        elif _owner_for(ownership, path) != role:
            errors.append("expected_persistence path %s is not owned by %s" % (value, role))
    return errors


def execution_envelope_errors(package_root, agents, native, fallback):
    fields = {"role", "role_file", "role_instructions", "workflow", "handoff", "capability"}
    errors = []
    for label, envelope in (("native", native), ("fallback", fallback)):
        if not isinstance(envelope, dict) or set(envelope) != fields:
            errors.append("%s envelope must contain exactly six fields" % label)
            continue
        role = envelope.get("role")
        role_is_valid = _nonblank(role) and role in agents
        if not role_is_valid:
            errors.append("%s envelope has unknown role" % label)
        elif (not _nonblank(envelope.get("workflow"))
              or envelope.get("workflow") in SYSTEM_SKILLS
              or envelope.get("workflow") not in _agent_skills(agents[role])):
            errors.append("%s envelope workflow is not held by role" % label)
        expected_role_file = "agents/%s.md" % role if role_is_valid else None
        if envelope.get("role_file") != expected_role_file:
            errors.append("%s envelope uses the wrong role file" % label)
        if not isinstance(envelope.get("role_instructions"), bytes):
            errors.append("%s role_instructions must be bytes" % label)
        handoff = envelope.get("handoff")
        if not _nonblank(handoff) or not _nonblank(envelope.get("capability")):
            errors.append("%s envelope requires one handoff and one capability" % label)
        else:
            try:
                handoff_size = len(handoff.encode("utf-8"))
            except UnicodeEncodeError:
                errors.append("%s envelope handoff must be valid UTF-8" % label)
            else:
                if handoff_size > 4096:
                    errors.append(
                        "%s envelope handoff exceeds 4096 UTF-8 bytes" % label
                    )
    if isinstance(native, dict) and isinstance(fallback, dict):
        if native.get("role_file") != fallback.get("role_file"):
            errors.append("native and fallback must use the same role path")
        if native.get("role_instructions") != fallback.get("role_instructions"):
            errors.append("native and fallback role instructions must be byte-identical")
        for field in ("role", "workflow", "handoff", "capability"):
            if native.get(field) != fallback.get(field):
                errors.append("native and fallback must carry the same %s" % field)
        role = native.get("role")
        role_file = native.get("role_file")
        instructions = native.get("role_instructions")
        expected_role_file = (
            "agents/%s.md" % role
            if _nonblank(role) and role in agents
            else None
        )
        if (role_file == expected_role_file
                and isinstance(instructions, bytes)):
            try:
                source = (package_root / "agents" / (role + ".md")).read_bytes()
            except OSError:
                errors.append("cannot read role file %s" % role_file)
            else:
                if source != instructions:
                    errors.append("role instructions must be byte-identical to %s" % role_file)
    return errors


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
