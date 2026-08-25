#!/usr/bin/env python3
"""Validate the Founder OS Claude Code plugin.

v2 — retargeted from the paperclipai/agentcompanies format to Claude Code
native. The checks that survived are the ones that were never about paperclip:
one owner per file, one decision per agent, beliefs, guardrails. The ones that
died with the old runtime (COMPANY.md, TEAM.md, .paperclip.yaml routines) are
gone rather than kept "just in case" — a second map goes stale silently.
"""
import ast
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
    "mcp__plugin_founder-os_founder-os-state__resolve_workspace",
    "mcp__plugin_founder-os_founder-os-state__list_state",
    "mcp__plugin_founder-os_founder-os-state__read_state",
    "mcp__plugin_founder-os_founder-os-state__read_reference",
    "mcp__plugin_founder-os_founder-os-state__write_owned_state",
    "mcp__plugin_founder-os_founder-os-state__close_role_session",
}
PORTFOLIO_READ_TOOL = (
    "mcp__plugin_founder-os_founder-os-state__read_portfolio_inputs"
)
ALLOWED_AGENT_TOOLS = ROLE_GATEWAY_TOOLS | {PORTFOLIO_READ_TOOL}
PUBLIC_GATEWAY_TOOLS = {
    "resolve_workspace",
    "open_role_session",
    "list_state",
    "read_state",
    "read_reference",
    "read_portfolio_inputs",
    "write_owned_state",
    "close_role_session",
}

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
    if isinstance(tools, str):
        raw = re.split(r",\s*(?![^()]*\))", tools)
    elif isinstance(tools, list) and all(
            isinstance(value, str) for value in tools):
        raw = tools
    else:
        raise ValueError("tools must be a string or a list of strings")
    names = []
    for value in raw:
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
            "args": ["./mcp/founder_os_state.py"],
            "cwd": ".",
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
                    "founder-os-state via ./mcp/founder_os_state.py with "
                    "cwd '.'"
                )

    entry = root / "mcp" / "founder_os_state.py"
    if not entry.is_file():
        errs.append("mcp/founder_os_state.py: missing shared gateway entry")
    else:
        try:
            compile(entry.read_text(encoding="utf-8"), str(entry), "exec")
        except (OSError, SyntaxError) as exc:
            errs.append("mcp/founder_os_state.py: does not compile (%s)" % exc)

    gateway_path = root / "mcp" / "gateway.py"
    if gateway_path.is_file():
        try:
            tree = ast.parse(
                gateway_path.read_text(encoding="utf-8"),
                filename=str(gateway_path),
            )
            schemas = None
            for node in ast.walk(tree):
                if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                    continue
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if any(
                    isinstance(target, ast.Name)
                    and target.id == "_TOOL_SCHEMAS"
                    for target in targets
                ):
                    schemas = ast.literal_eval(node.value)
                    break
            if not isinstance(schemas, (tuple, list)):
                raise ValueError("_TOOL_SCHEMAS is not a literal sequence")
            names = [
                schema.get("name") if isinstance(schema, dict) else None
                for schema in schemas
            ]
        except (OSError, SyntaxError, TypeError, ValueError) as exc:
            errs.append(
                "mcp/gateway.py: public gateway catalogue is unreadable (%s)"
                % exc
            )
        else:
            if len(names) != len(PUBLIC_GATEWAY_TOOLS) or set(names) != PUBLIC_GATEWAY_TOOLS:
                missing = sorted(PUBLIC_GATEWAY_TOOLS - set(names))
                unexpected = sorted(set(names) - PUBLIC_GATEWAY_TOOLS, key=str)
                errs.append(
                    "mcp/gateway.py: public gateway tools must be exactly eight; "
                    "missing=%s unexpected=%s"
                    % (missing, unexpected)
                )
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
        expected_tools = set(ROLE_GATEWAY_TOOLS)
        if slug == "portfolio-manager":
            expected_tools.add(PORTFOLIO_READ_TOOL)
        for tool in sorted(expected_tools - names):
            errs.append(
                "agents/%s.md: one-level gateway contract is missing %s"
                % (slug, tool)
            )
        for tool in sorted(names - expected_tools):
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

        result_required = (
            "workflow result",
            "`decision`",
            "`evidence`",
            "`gaps`",
            "`return_point`",
            "`human_action`",
            "`expected_persistence`",
        )
        missing_result = [
            phrase for phrase in result_required if phrase not in lower
        ]
        if missing_result:
            errs.append(
                "agents/%s.md: shared workflow result contract is missing %s"
                % (slug, ", ".join(missing_result))
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


def _ownership_string_list(value, label):
    if (not isinstance(value, list)
            or any(not isinstance(item, str) for item in value)):
        raise ValueError(
            "ownership.yaml: %s must be a list of strings" % label
        )
    return list(value)


def load_ownership_schema(root):
    """Load and type-check the one ownership/section schema."""
    p = root / "references" / "ownership.yaml"
    if not p.exists():
        return None
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("ownership.yaml: root must be a mapping")

    owns = data.get("owns", {})
    if not isinstance(owns, dict):
        raise ValueError("ownership.yaml: owns must be a mapping")
    normalized_owns = {}
    for agent, paths in owns.items():
        if not isinstance(agent, str):
            raise ValueError("ownership.yaml: owns keys must be strings")
        normalized_owns[agent] = _ownership_string_list(
            paths, "owns.%s" % agent
        )

    sections = data.get("sections", {})
    if not isinstance(sections, dict):
        raise ValueError("ownership.yaml: sections must be a mapping")
    normalized_sections = {}
    for path, headings in sections.items():
        if not isinstance(path, str):
            raise ValueError("ownership.yaml: sections keys must be strings")
        normalized_sections[path] = _ownership_string_list(
            headings, "sections.%s" % path
        )

    return {
        "workspace_files": _ownership_string_list(
            data.get("workspace_files", []), "workspace_files"
        ),
        "portfolio_files": _ownership_string_list(
            data.get("portfolio_files", []), "portfolio_files"
        ),
        "derived_files": _ownership_string_list(
            data.get("derived_files", []), "derived_files"
        ),
        "owns": normalized_owns,
        "sections": normalized_sections,
    }


def _ownership_by_path_from_schema(data):
    by_path = {}
    for agent, files in data["owns"].items():
        for f in files:
            by_path[f] = agent
    return by_path


def _ownership_by_path(root):
    data = load_ownership_schema(root)
    return _ownership_by_path_from_schema(data) if data is not None else {}


def check_ownership(root, agents):
    errs = []
    p = root / "references" / "ownership.yaml"
    if not p.exists():
        return ["references/ownership.yaml: missing"]
    data = load_ownership_schema(root)
    seen = {}
    for agent, files in data["owns"].items():
        if agent not in agents:
            errs.append("ownership.yaml: '%s' is not a real agent" % agent)
        for f in files:
            if f in seen:
                errs.append("ownership.yaml: '%s' is owned by both '%s' and '%s'"
                            % (f, seen[f], agent))
            else:
                seen[f] = agent
    for f in data["workspace_files"]:
        if f not in seen:
            errs.append("ownership.yaml: workspace file '%s' has no owner" % f)
    for f in data["portfolio_files"]:
        if f not in seen:
            errs.append("ownership.yaml: portfolio file '%s' has no owner" % f)
    derived = set(data["derived_files"])
    for f in sorted(derived & set(seen)):
        errs.append("ownership.yaml: '%s' is declared derived and also owned" % f)
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
    data = load_ownership_schema(root)
    declared = set(data["workspace_files"])
    # portfolio_files: is the second scaffold promise — the portfolio workspace,
    # scaffolded by founder-os-init when the registry gains a second business.
    # A path in either list has a scaffolder; a path in neither has none.
    declared |= set(data["portfolio_files"])
    for agent, files in data["owns"].items():
        for f in files:
            if f not in declared:
                errs.append("ownership.yaml: '%s' is owned by '%s' but is not in "
                            "workspace_files: or portfolio_files: — "
                            "founder-os-init will never scaffold it" % (f, agent))
    return errs


def check_derived_files(root, agents):
    """Derived paths stay out of every ownership join.

    `derived_files:` exists so the dashboard can write inside the workspace
    without becoming state. That only holds while nothing owns the path, nothing
    declares its sections, and no skill claims to write it — the three joins that
    would quietly turn a generated file into evidence.
    """
    errs = []
    p = root / "references" / "ownership.yaml"
    if not p.exists():
        return errs
    data = load_ownership_schema(root)
    derived = set(data["derived_files"])
    if not derived:
        return errs
    for agent, files in data["owns"].items():
        for f in files:
            if f in derived:
                errs.append("ownership.yaml: '%s' is derived but owned by '%s'"
                            % (f, agent))
    for f in data["sections"]:
        if f in derived:
            errs.append("ownership.yaml: '%s' is derived but declares sections" % f)
    sdir = root / "skills"
    if sdir.is_dir():
        for d in sorted(sdir.iterdir()):
            if not (d.is_dir() and (d / "SKILL.md").exists()):
                continue
            fm, _ = parse_frontmatter(d / "SKILL.md")
            writes = (fm.get("metadata") or {}).get("writes") or []
            if isinstance(writes, str):
                writes = [writes]
            for w in writes:
                if w in derived:
                    errs.append("skills/%s: declares a write to the derived path "
                                "'%s'" % (d.name, w))
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
    data = load_ownership_schema(root)
    sections = data["sections"]
    own_path = _ownership_by_path_from_schema(data)
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


def check_capture_contract(root, agents):
    """Keep the one-line inbox door narrow when capture is part of the package."""
    capture_path = root / "skills" / "capture" / "SKILL.md"
    capture_expected = (
        (root / "skills" / "founder-os-init" / "SKILL.md").exists()
        or capture_path.exists()
        or any(
            "capture" in ((frontmatter.get("skills") or []))
            for frontmatter, _ in agents.values()
        )
    )
    if not capture_expected:
        return []
    if not capture_path.exists():
        return ["skills/capture: missing required quick-capture workflow"]

    errs = []
    frontmatter, body = parse_frontmatter(capture_path)
    if frontmatter.get("name") != "capture":
        errs.append("skills/capture: name must be 'capture'")
    if frontmatter.get("metadata") != {"writes": ["inbox.md"]}:
        errs.append(
            "skills/capture: metadata.writes must contain only inbox.md"
        )

    holders = sorted(
        slug for slug, (agent_frontmatter, _) in agents.items()
        if "capture" in (agent_frontmatter.get("skills") or [])
    )
    if holders != ["chief-of-staff"]:
        errs.append(
            "skills/capture: must be held only by chief-of-staff, found %s"
            % (", ".join(holders) if holders else "none")
        )

    required = (
        "one nonblank logical line",
        "2048 utf-8 bytes",
        "reject nul, newline, and carriage return",
        "do not trim or normalize",
        "do not split",
        "founder's accepted bytes unchanged",
        "prefix `- `",
        "write_owned_state",
        "observed sha-256",
        "expected hash",
        "after a successful write, re-read the full file",
        "exact appended list item",
        "original inbox unchanged",
        "post-write re-read fails, persistence is uncertain",
        "omit the success receipt",
        "only `/daily-brief` and `/triage` drain",
        "captured in `inbox.md`. the next `/daily-brief` or `/triage` will "
        "decide what it becomes.",
    )
    normalized = " ".join(body.lower().split())
    missing = [phrase for phrase in required if phrase not in normalized]
    if missing:
        errs.append(
            "skills/capture: quick-capture contract is missing %s"
            % ", ".join(missing)
        )
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
    hooks = data.get("hooks") or {}
    patterns = [h.get("matcher", "")
                for h in hooks.get("PreToolUse", [])]

    def recorders(event):
        return [
            hook.get("command", "")
            for group in hooks.get(event, [])
            for hook in group.get("hooks", [])
            if isinstance(hook, dict) and hook.get("type") == "command"
            and "record-agent.py" in hook.get("command", "")
        ]

    # One script under two events, and both registrations have to exist. Which
    # one fired is the host's knowledge, and a payload that stops carrying
    # `hook_event_name` records nothing — after which the guard denies every
    # Codex tool call on the unrecorded turn. The existence half was checked for
    # the main turn only, so deleting the whole SubagentStart block validated
    # clean while every subagent turn went unmapped.
    for event, flag, denied in (
        ("UserPromptSubmit", "--event user-prompt", "the founder's main turn"),
        ("SubagentStart", "--event subagent-start", "every subagent turn"),
    ):
        registrations = recorders(event)
        if not registrations:
            errs.append(
                "hooks/hooks.json: %s must record its turn via "
                "record-agent.py — without it the guard denies %s under Codex"
                % (event, denied)
            )
        for command in registrations:
            if flag not in command:
                errs.append(
                    "hooks/hooks.json: the %s registration of record-agent.py "
                    "must pass %s" % (event, flag)
                )

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


# Published counts are written both ways — `56 workflows` in a table, "fifty-six
# workflows" in a sentence — and only the digits were ever checked. So the three
# pages that spell it out drifted through a release that moved the number, two
# lines under a paragraph telling the reader that a count which drifts is a
# second map.
NUMBER_WORDS = {
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20,
}
for _tens, _tens_value in (("thirty", 30), ("forty", 40), ("fifty", 50),
                           ("sixty", 60), ("seventy", 70), ("eighty", 80),
                           ("ninety", 90)):
    NUMBER_WORDS[_tens] = _tens_value
    for _unit, _unit_value in (("one", 1), ("two", 2), ("three", 3),
                               ("four", 4), ("five", 5), ("six", 6),
                               ("seven", 7), ("eight", 8), ("nine", 9)):
        NUMBER_WORDS["%s-%s" % (_tens, _unit)] = _tens_value + _unit_value


def _as_number(value):
    """A published count, however it was written."""
    text = str(value).strip().casefold()
    if text.isdigit():
        return int(text)
    return NUMBER_WORDS.get(text)


# Scanned for version literals nobody registered. A file here may hold the
# version only at a site `bump_version.py` declares.
VERSION_SCANNED = (
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "docs/getting-started.md",
    "docs/development.md",
    "docs/trust.md",
    "docs/trust.html",
    "founder-os/README.md",
    "founder-os/CLAUDE.md",
    ".github/ISSUE_TEMPLATE/report.yml",
    ".github/ISSUE_TEMPLATE/idea.yml",
)


def check_version_sites(root, agents):
    """Every place the version is written must be one `bump_version.py` knows.

    A release moves one number through eleven files. The list of eleven lived in
    a prose checklist, which is a hand-kept list of places — the same shape as
    every count this package refuses to hand-keep. So the list lives in
    `scripts/bump_version.py`, this reads it, and a twelfth site added without
    telling that script fails the build instead of shipping a package that
    disagrees with itself about which version it is.

    Skipped whole when the repository is absent, which is every test fixture:
    the release sites are a property of this repo, not of a package layout.
    """
    errs = []
    repo = root.parent
    bump = repo / "scripts" / "bump_version.py"
    manifest = root / ".claude-plugin" / "plugin.json"
    if not (bump.exists() and manifest.exists()):
        return errs
    try:
        version = json.loads(manifest.read_text(encoding="utf-8"))["version"]
    except (ValueError, KeyError):
        return [".claude-plugin/plugin.json: no readable version"]

    namespace = {"__file__": str(bump)}
    try:
        exec(compile(bump.read_text(encoding="utf-8"), str(bump), "exec"),
             namespace)
    except Exception as error:  # noqa: BLE001 - a broken script is the finding
        return ["scripts/bump_version.py: does not import (%s)" % error]
    sites = namespace.get("SITES") or ()
    records = namespace.get("RECORDS") or ()

    declared = {}
    for relative, pattern, description in sites:
        path = repo / relative
        if not path.exists():
            errs.append("scripts/bump_version.py: names %s, which does not "
                        "exist" % relative)
            continue
        text = path.read_text(encoding="utf-8")
        found = re.findall(pattern, text)
        if len(found) != 1:
            errs.append("%s: %s matched %d times, not once — bump_version.py "
                        "would rewrite the wrong thing" % (relative,
                                                           description,
                                                           len(found)))
            continue
        if found[0][1] != version:
            errs.append("%s: %s says %s, the package is %s"
                        % (relative, description, found[0][1], version))
        declared[relative] = declared.get(relative, 0) + 1

    # A record is a version that must *not* move: it names a release that
    # already shipped. Counted as accounted-for, never rewritten.
    for relative, pattern, description in records:
        path = repo / relative
        if not path.exists():
            errs.append("scripts/bump_version.py: records %s in %s, which does "
                        "not exist" % (description, relative))
            continue
        # Only a record holding *this* version consumes an allowance. One that
        # names an older release is invisible to the scan below anyway, and
        # counting it would license an unregistered literal beside it.
        declared[relative] = declared.get(relative, 0) + sum(
            1 for found in re.findall(pattern,
                                      path.read_text(encoding="utf-8"))
            if (found if isinstance(found, str) else found[0]) == version
        )

    # The other half: a version literal in a scanned file that no site claims.
    # CHANGELOG.md is exempt — its older headings are a record of versions that
    # were, and rewriting those is the failure this whole check descends from.
    for relative in sorted({site[0] for site in sites} | set(VERSION_SCANNED)):
        path = repo / relative
        if not path.exists():
            continue
        literals = len(re.findall(
            r"(?<![\d.])%s(?![\d.])" % re.escape(version),
            path.read_text(encoding="utf-8"),
        ))
        if literals > declared.get(relative, 0):
            errs.append(
                "%s: writes %s %d time(s) and bump_version.py knows %d of "
                "them — a version it does not rewrite ships stale"
                % (relative, version, literals, declared.get(relative, 0))
            )
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

    # The site lives at the repository root, not inside the package. These were
    # written as `root / "docs" / ...` and `founder-os/docs/` has never existed,
    # so the loop below skipped every one of them and the whole docs half of
    # this check was dead — which is how docs/index.html kept saying "nine
    # cadences" through two releases that added one.
    #
    # index.html is deliberately not in this list: its catalogue carries a per-
    # category "9 workflows" on every group heading, which these patterns cannot
    # tell from a package count. tests/test_docs_workflows.py and the feature
    # ledger's derived count are what hold that page.
    site = root.parent / "docs"
    docs = [site / "README.md", site / "getting-started.md",
            site / "commands.md", site / "cadences.md",
            site / "troubleshooting.md", site / "og-image.svg",
            site / "concepts.md", site / "agents.md",
            root / "README.md", root / "CLAUDE.md", root / "COMMANDS.md",
            root / "references" / "extensibility.md",
            root / "skills" / "skill-forge" / "SKILL.md",
            root.parent / ".github" / "ISSUE_TEMPLATE" / "idea.yml",
            root / ".codex-plugin" / "plugin.json"]
    counted = r"(\d+|%s)" % "|".join(sorted(NUMBER_WORDS, key=len, reverse=True))
    patterns = {
        "Agents": counted + r"\s+(?:specialized\s+business\s+roles|decision-owning executive agents|agents)",
        "Skills": counted + r"\s+(?:skills|workflows)",
        "Cadences": counted + r"\s+(?:optional\s+)?(?:operating\s+)?cadences",
    }
    for path in docs:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for label, pattern in patterns.items():
            values = [_as_number(value)
                      for value in re.findall(pattern, text, re.I)]
            drifted = [value for value in values if value != actual.get(label)]
            if drifted:
                errs.append(
                    "%s: says %s %s, the package has %d — a count that drifts "
                    "is a second map"
                    % (path.relative_to(root.parent),
                       ", ".join(str(value) for value in sorted(set(drifted))),
                       label.lower(), actual.get(label, 0))
                )
    return errs


def _schedule_table_rows(text):
    """Commands listed in a page's schedule tables, and only those.

    Identified by a `When` column, because both pages carry other tables of
    commands and matching any row that starts with a command let a workflow
    absent from the schedule pass on the strength of its role-table row.
    """
    rows = set()
    in_schedule = False
    for line in text.splitlines():
        if not line.startswith("|"):
            in_schedule = False
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if "When" in cells:
            in_schedule = True
            continue
        if not in_schedule:
            continue
        match = re.fullmatch(r"`/?([a-z0-9-]+)`", cells[0])
        if match:
            rows.add(match.group(1))
    return rows


def check_docs_parity(root, agents):
    """The reference pages must name what the package actually ships.

    A count is the cheap half of this and `check_readme_counts` has it. The
    expensive half is membership: `docs/commands.md` lost three workflows and
    `docs/agents.md` lost two skills and two owned paths across two releases,
    while every count on both pages stayed correct. Sets, not numbers — and no
    per-role parsing, because the Board Member owns "*nothing.*" and its Owns
    line carries a `Read, Glob, Grep` in backticks.

    Skipped whole when the site is absent, which is every test fixture: the
    pages are the storefront, not the structure.
    """
    errs = []
    site = root.parent / "docs"
    commands = site / "commands.md"
    agents_page = site / "agents.md"
    cadence_source = root / "skills" / "setup-cadences" / "SKILL.md"
    if not (commands.exists() and agents_page.exists()
            and cadence_source.exists()):
        return errs

    cadences = set(re.findall(
        r"^\|\s*`/([a-z0-9-]+)`\s*\|[^|]*\|\s*`[^`]+`\s*\|\s*$",
        cadence_source.read_text(encoding="utf-8"), re.M))
    for page in (commands, site / "cadences.md"):
        if not page.exists():
            continue
        rows = _schedule_table_rows(page.read_text(encoding="utf-8"))
        for missing in sorted(cadences - rows):
            errs.append("docs/%s: schedule table omits the cadence '%s'"
                        % (page.name, missing))

    listed = set(re.findall(r"`/([a-z0-9-]+)`",
                            commands.read_text(encoding="utf-8")))
    packaged = {path.parent.name for path in (root / "skills").glob("*/SKILL.md")}
    for missing in sorted(packaged - listed):
        errs.append("docs/commands.md: no row for the '%s' workflow" % missing)
    for extra in sorted(listed - packaged):
        errs.append("docs/commands.md: '%s' is not a packaged workflow" % extra)

    named = set(re.findall(r"`([A-Za-z0-9_./-]+)`",
                           agents_page.read_text(encoding="utf-8")))
    for agent, record in sorted(agents.items()):
        for skill in sorted(_agent_skills(record)):
            if skill not in UNIVERSAL_SKILLS and skill not in named:
                errs.append("docs/agents.md: %s lists no '%s' skill"
                            % (agent, skill))
    schema = load_ownership_schema(root)
    for owner, owned in sorted((schema or {}).get("owns", {}).items()):
        for owned_path in owned:
            if owned_path not in named:
                errs.append("docs/agents.md: %s is not shown owning '%s'"
                            % (owner, owned_path))
    return errs


CHECKS = [check_plugin, check_host_adapters, check_codex_skill_interfaces, check_agents,
          check_agent_tools, check_one_level_orchestration,
          check_role_skill_exclusivity, check_orphans, check_agent_headings,
          check_ownership, check_derived_files, check_workspace_files_complete,
          check_skill_writes,
          check_sections, check_capture_contract, check_beliefs, check_hooks,
          check_readme_counts, check_docs_parity,
          check_version_sites]


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
