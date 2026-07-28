#!/usr/bin/env python3
"""Keep Founder OS role subagents on the capability-bound state gateway.

Claude identifies a role directly with ``agent_type``. Codex supplies a
``turn_id`` that ``record-agent.py`` maps to the same role. Once a role is
known, direct filesystem, shell, web, and non-Founder-OS MCP access is denied.
The seven local gateway calls are recognized explicitly; a subagent may not
open its own role session, and every role-bound call must carry a live
capability whose role agrees with a native role identity.

The hook remains defense in depth, not a security sandbox. Malformed hook input
and calls without a subagent identity stay out of the founder's way. A known
role, however, fails closed at the tool boundary described above.

Python 3.9, stdlib + optional PyYAML for the retained ownership helpers.
"""
import hashlib
import json
import math
import os
import re
import stat
import sys
import time

_YAML_UNSET = object()
yaml = _YAML_UNSET

ROLE_NAMES = frozenset({
    "board-member", "brand-editor", "cfo", "chief-of-staff",
    "delivery-lead", "focus-coach", "network-manager", "ops-engineer",
    "pipeline-coach", "portfolio-manager", "positioning-advisor",
    "skills-mentor", "strategist",
})
GENERIC_AGENT_TYPES = frozenset({"default", "general-purpose"})
GATEWAY_TOOLS = frozenset({
    "resolve_workspace", "open_role_session", "list_state", "read_state",
    "read_reference", "write_owned_state", "close_role_session",
})
OUTBOUND_TOOLS = frozenset({"Bash", "WebFetch", "WebSearch"})
DIRECT_FILE_TOOLS = frozenset({
    "Read", "Write", "Edit", "NotebookEdit", "Glob", "Grep", "apply_patch",
})
MCP_TOOL = re.compile(r"^mcp__")
SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")
SESSION_FIELDS = frozenset({
    "capability_hash", "workspace_id", "role", "correlation_id", "workflow",
    "expires_at", "status",
})

# The founder's local overlay (references/extensibility.md). `_local/` is the
# directory; the file below it is the additive half of the ownership map.
LOCAL_DIR = "_local/"
LOCAL_MAP = "_local/ownership.yaml"

# One overlay read per root per process. A hook process handles one invocation,
# so this is per-invocation caching — the same property PERF-002 pinned for
# workspace_roots, for the same reason: a multi-path apply_patch must not
# re-read the same file once per path.
_LOCAL_CACHE = {}


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


def _yaml_load(yaml_module, text):
    """Use LibYAML's C loader when installed, otherwise SafeLoader."""
    loader = getattr(yaml_module, "CSafeLoader", yaml_module.SafeLoader)
    return yaml_module.load(text, Loader=loader) or {}


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


def _owns_from_text(text, source):
    """Return the `owns:` mapping from ownership YAML text, or None.

    One parser for both maps. The packaged map and the founder's overlay have
    the same shape by contract, and giving the overlay its own reader is how
    the two quietly stop agreeing about what a map is.
    """
    yaml_module = _get_yaml()
    if yaml_module is not None:
        try:
            data = _yaml_load(yaml_module, text)
        except yaml_module.YAMLError as e:
            log("%s is not valid YAML (%s)" % (source, e))
            return None
        owns = data.get("owns") if isinstance(data, dict) else None
        if not isinstance(owns, dict):
            log("%s has no usable 'owns:' map" % source)
            return None
        return owns
    owns = _parse_owns_without_yaml(text)
    if owns is None:
        log("PyYAML missing and %s is not in the shape the fallback parser "
            "understands" % source)
    return owns


def _by_path(owns):
    """Flatten {agent: [path]} to {path: agent}, dropping unusable entries."""
    out = {}
    for agent, files in owns.items():
        if not isinstance(agent, str) or not agent.strip():
            continue
        for f in files or []:
            if isinstance(f, str) and f.strip():
                out[f.strip()] = agent.strip()
    return out


def local_ownership(root):
    """Return {entry: owner} from `<root>/_local/ownership.yaml`, or {}.

    The founder's additive overlay (references/extensibility.md). Everything
    here fails to an empty map rather than to a deny: an overlay we cannot read
    costs the founder coverage of their own local files, which is not what a
    false deny costs.

    Read per root on purpose. Business A's overlay is not business B's map.
    """
    if root in _LOCAL_CACHE:
        return _LOCAL_CACHE[root]
    result = {}
    path = os.path.join(root, *LOCAL_MAP.split("/"))
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as e:
            log("could not read overlay %s (%s) — ignoring it" % (path, e))
            text = None
        if text is not None:
            owns = _owns_from_text(text, path)
            if owns is None:
                log("overlay %s is unusable — ignoring it" % path)
            else:
                result = _by_path(owns)
    _LOCAL_CACHE[root] = result
    return result


def merged_ownership(by_path, root):
    """The packaged map plus whatever the overlay is allowed to add.

    Additive only, and a collision is a finding rather than a precedence
    contest: the packaged entry stays, the local entry is dropped with a log
    line, and founder-os-doctor reports it against the overlay. An overlay that
    could reassign `metrics.md` would silently take the month's close away from
    the CFO in one founder's workspace, and nothing upstream would ever see it.
    """
    local = local_ownership(root) if root else {}
    if not local:
        return by_path
    packaged = {entry.casefold() for entry in by_path}
    merged = dict(by_path)
    for entry, agent in local.items():
        if entry.casefold() in packaged:
            log("overlay claims '%s', which the packaged map already owns "
                "(%s) — ignoring the overlay entry"
                % (entry, by_path.get(entry, "a packaged agent")))
            continue
        merged[entry] = agent
    return merged


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
        owns = _owns_from_text(text, path)
        if owns is None:
            return None
        return _by_path(owns) or None

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
            data = _yaml_load(yaml_module, text)
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
    """Workspace-relative POSIX path for `file_path`, or None if it's outside."""
    return resolve_in_workspace(file_path, hook_cwd, roots)[1]


def resolve_in_workspace(file_path, hook_cwd, roots=None):
    """`(root, relative_path)` for `file_path`, or `(None, None)` if outside.

    Both sides get realpath'd (which collapses `..` and follows symlinks) and
    also compared literally, so a symlink pointing *into* the workspace is still
    caught and a `..` walk can't spoof a slot. If neither resolution lands inside
    a candidate root, the file is not ours and the caller allows.

    The matched root is returned because the overlay is per workspace: which
    root a write landed in decides which `_local/ownership.yaml` may speak for
    it, and a merged map assembled from the wrong workspace is a worse map than
    none.
    """
    if not os.path.isabs(file_path):
        # Codex apply_patch uses workspace-relative paths. Its hook payload
        # carries the session cwd, so resolve against that explicit value.
        if not isinstance(hook_cwd, str) or not os.path.isabs(hook_cwd):
            return (None, None)
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
                return (root, target[len(prefix):].replace(os.sep, "/"))
    return (None, None)


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


def _deny_tool(agent_type, tool_name, reason):
    deny(
        "Founder OS role boundary: `%s` may not use `%s`. %s\n\n"
        "Role subagents read and write business state only through the local "
        "`founder-os-state` gateway. Return control to the main thread if a "
        "different capability is required." % (agent_type, tool_name, reason)
    )


def _gateway_tool_name(tool_name):
    """Return a known local action, ``""`` for an unknown local action, else None."""
    if not isinstance(tool_name, str) or not MCP_TOOL.match(tool_name):
        return None
    parts = tool_name.split("__")
    if len(parts) != 3:
        return None
    server = parts[1].replace("-", "_")
    if server != "founder_os_state":
        return None
    action = parts[2]
    return action if action in GATEWAY_TOOLS else ""


def _valid_text(value):
    return isinstance(value, str) and bool(value.strip()) and "\x00" not in value


def _read_small_regular_json(path):
    """Read one bounded plugin-data record without following its final link."""
    if not hasattr(os, "O_NOFOLLOW"):
        return None
    descriptor = None
    try:
        flags = os.O_RDONLY | os.O_NOFOLLOW
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        descriptor = os.open(path, flags)
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size > 16 * 1024:
            return None
        with os.fdopen(descriptor, encoding="utf-8") as handle:
            descriptor = None
            return json.load(handle)
    except (OSError, ValueError, TypeError, UnicodeError):
        return None
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass


def _session_role(tool_input):
    """Resolve a live capability to its persisted role without exposing it."""
    if not isinstance(tool_input, dict):
        return None
    capability = tool_input.get("capability")
    if not _valid_text(capability) or len(capability) > 512:
        return None
    data_root = os.environ.get("PLUGIN_DATA") or os.environ.get("CLAUDE_PLUGIN_DATA")
    if not data_root:
        return None
    try:
        encoded_capability = capability.encode("utf-8")
    except UnicodeEncodeError:
        return None
    capability_hash = hashlib.sha256(encoded_capability).hexdigest()
    path = os.path.join(data_root, "state-gateway", capability_hash + ".json")
    record = _read_small_regular_json(path)
    if not isinstance(record, dict) or set(record) != SESSION_FIELDS:
        return None
    if record.get("capability_hash") != capability_hash:
        return None
    if record.get("status") != "open":
        return None
    if not _valid_text(record.get("workspace_id")):
        return None
    if not _valid_text(record.get("correlation_id")):
        return None
    role = record.get("role")
    if role not in ROLE_NAMES:
        return None
    workflow = record.get("workflow")
    if workflow is not None and not _valid_text(workflow):
        return None
    expires_at = record.get("expires_at")
    try:
        now = time.time()
    except Exception:  # noqa: BLE001 - capability uncertainty must deny
        return None
    if (
        isinstance(expires_at, bool)
        or not isinstance(expires_at, (int, float))
        or not math.isfinite(float(expires_at))
        or now >= float(expires_at)
    ):
        return None
    return role


def check_gateway(agent_type, tool_name, tool_input):
    """Authorize only the capability-consistent local gateway surface."""
    action = _gateway_tool_name(tool_name)
    if action is None:
        _deny_tool(agent_type, tool_name, "Other MCP servers are not allowed.")
    if not action:
        _deny_tool(agent_type, tool_name, "That gateway action is not part of the contract.")
    if action == "open_role_session":
        _deny_tool(agent_type, tool_name, "A subagent cannot elevate itself or mint a session.")
    if action == "resolve_workspace":
        return

    role = _session_role(tool_input)
    if role is None:
        _deny_tool(agent_type, tool_name, "A live role capability is required.")
    if agent_type in ROLE_NAMES and role != agent_type:
        _deny_tool(agent_type, tool_name, "The capability belongs to a different role.")
    if agent_type not in ROLE_NAMES and agent_type not in GENERIC_AGENT_TYPES:
        _deny_tool(agent_type, tool_name, "The subagent identity is not an approved role fallback.")


def check_outbound(agent_type, tool_name):
    """Retained public helper for focused unit tests."""
    if tool_name in OUTBOUND_TOOLS:
        _deny_tool(
            agent_type,
            tool_name,
            "House rule 0 says agents draft and the founder sends.",
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


def check_local_map(agent_type, rel):
    """No subagent edits the map that governs it. references/extensibility.md.

    Stricter than "one owner per file" on purpose, and the only place in this
    file that is. `_local/` is founder-authored by definition — `skill-forge`
    runs on the main thread, and no packaged agent has ever had a reason to
    write there — so this costs honest work nothing and closes the one move
    that would make every other check advisory.
    """
    if not rel.casefold().startswith(LOCAL_DIR):
        return
    deny(
        "`%s` is the founder's local overlay, and no agent writes it — "
        "including this one.\n\n"
        "`_local/` holds the map that decides what `%s` is allowed to write "
        "(references/extensibility.md). An agent that can edit that map does "
        "not have one, so this deny does not depend on ownership and cannot be "
        "granted by adding an entry.\n\n"
        "If a local file, skill or agent needs to exist or change, that is "
        "`/skill-forge` with the founder in the room, not an edit to make on "
        "the way past." % (rel, agent_type)
    )


def check_ownership(agent_type, tool_name, tool_input, hook_cwd):
    paths = _tool_paths(tool_name, tool_input)
    if not paths:
        return
    by_path = load_ownership()
    if by_path is None:
        allow("no ownership map — the guard is off, not strict")
    roots = workspace_roots(hook_cwd)
    for file_path in paths:
        root, rel = resolve_in_workspace(file_path, hook_cwd, roots)
        if rel is None:
            log("allow: %s is outside the workspace" % file_path)
            continue
        check_local_map(agent_type, rel)
        owner = owner_of(rel, merged_ownership(by_path, root))
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
    if isinstance(direct, str) and SAFE_ID.fullmatch(direct):
        return direct
    turn_id = data.get("turn_id")
    if not isinstance(turn_id, str) or not SAFE_ID.fullmatch(turn_id):
        return None
    data_root = os.environ.get("PLUGIN_DATA") or os.environ.get("CLAUDE_PLUGIN_DATA")
    if not data_root:
        return None
    path = os.path.join(data_root, "agent-types", turn_id + ".json")
    payload = _read_small_regular_json(path)
    if not isinstance(payload, dict) or set(payload) != {"agent_type"}:
        return None
    resolved = payload.get("agent_type")
    return resolved if isinstance(resolved, str) and SAFE_ID.fullmatch(resolved) else None


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

    tool_name = data.get("tool_name") or ""
    for identity_field in ("agent_type", "turn_id"):
        if identity_field in data:
            identity_value = data.get(identity_field)
            if not isinstance(identity_value, str) or not SAFE_ID.fullmatch(
                identity_value
            ):
                _deny_tool(
                    "unresolved role",
                    (
                        tool_name
                        if isinstance(tool_name, str)
                        else "<invalid tool name>"
                    ),
                    "A present subagent identity marker is invalid.",
                )
    agent_type = agent_type_for(data)
    if not agent_type:
        turn_id = data.get("turn_id")
        if isinstance(turn_id, str) and SAFE_ID.fullmatch(turn_id):
            _deny_tool(
                "unresolved Codex role",
                tool_name if isinstance(tool_name, str) else "<invalid tool name>",
                "The SubagentStart identity mapping is missing or invalid.",
            )
        allow("main thread — the founder is the CEO")

    if not isinstance(tool_name, str):
        _deny_tool(
            agent_type,
            "<invalid tool name>",
            "A role tool invocation must name one concrete tool.",
        )
    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}

    if MCP_TOOL.match(tool_name):
        check_gateway(agent_type, tool_name, tool_input)
        allow()
    if tool_name in OUTBOUND_TOOLS:
        check_outbound(agent_type, tool_name)
    if tool_name in DIRECT_FILE_TOOLS:
        _deny_tool(
            agent_type,
            tool_name,
            "Direct local file access bypasses capability and ownership checks.",
        )
    allow()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        # Malformed hook/runtime input must not block the founder's main thread.
        log("unexpected error, allowing (%s)" % e)
        sys.exit(0)
