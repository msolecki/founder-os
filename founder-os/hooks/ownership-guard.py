#!/usr/bin/env python3
"""Keep Founder OS role subagents on the capability-bound state gateway.

Claude identifies a role directly with ``agent_type`` — as the bare name or
host-namespaced (``founder-os:cfo``). Codex supplies a ``turn_id`` that
``record-agent.py`` maps to the same role. Once a *role* is known, direct
filesystem, shell, web, and non-Founder-OS MCP access is denied. The eight
local gateway calls are recognized explicitly — under the packaged name
(``mcp__founder-os-state__*``) and the host-wrapped one
(``mcp__plugin_founder-os_founder-os-state__*``); a subagent may not open its
own role session, and every role-bound call must carry a live capability whose
role agrees with a native role identity.

A subagent that is *not* one of the thirteen roles — a reviewer, an Explore
pass, another plugin's agent — is not governed by the gateway lockdown. It is
bound by three checks: no write under ``_local/``, no write under a path the
map lists in ``derived_files:``, and no write to a file the ownership map gives
someone else. Everything else it does is between it and the normal permission
system.

Those three bind **tools that name a path** — ``Write``, ``Edit``,
``NotebookEdit``, ``apply_patch``. They do not inspect a shell command, so a
non-role subagent holding ``Bash`` can write anything its own permissions allow,
and this hook will not be what stops it. That is the deliberate trade: the
alternative, denying every unrecognized subagent every tool, locked reviewers
and Explore passes out of unrelated repositories machine-wide. Read the three
checks as protection against an honest agent editing the wrong file, not as a
boundary around a hostile one. A *role* is different — it holds no shell at all.

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
    "read_reference", "read_portfolio_inputs", "write_owned_state",
    "close_role_session",
})
OUTBOUND_TOOLS = frozenset({"Bash", "WebFetch", "WebSearch"})
# A role does not spawn subagents. One-level orchestration is the packaged
# contract (`check_one_level_orchestration`) and no role's frontmatter lists
# these, but the guard denies them anyway: a role that can spawn a subagent
# escapes its own lockdown through the child, which is bound by far less.
NESTED_AGENT_TOOLS = frozenset({"Task", "Agent"})
DIRECT_FILE_TOOLS = frozenset({
    "Read", "Write", "Edit", "NotebookEdit", "Glob", "Grep", "apply_patch",
})
# The tools `_tool_paths` can read a target path out of, in the order a deny
# names them. Narrower than DIRECT_FILE_TOOLS, which is about a role touching
# the filesystem at all: this is the set every ownership and derived deny is
# actually speaking about. A path-naming tool missing from here — MultiEdit on
# a host that ships it — hands the guard no path and is allowed, which is why
# the derived deny names these four rather than claiming "a file tool".
PATH_NAMING_TOOLS = ("Write", "Edit", "NotebookEdit", "apply_patch")
MCP_TOOL = re.compile(r"^mcp__")
SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")
# Agent identities may carry a host namespace — `founder-os:cfo` on Claude
# Code. turn_id keeps SAFE_ID: it becomes a filename and never holds a colon.
SAFE_AGENT = re.compile(r"^[A-Za-z0-9._:-]+$")
# This plugin's name, which is also the namespace the host prefixes onto its
# subagent identities. Pinned to `founder-os` by `check_plugin`.
PLUGIN_NAMESPACE = "founder-os"
GATEWAY_SERVER = "founder_os_state"
# The gateway server as each host registers it, normalized: the packaged name,
# and Claude Code's `mcp__plugin_<plugin>_<server>__<action>` wrapping. Both
# halves of the wrapped form are validator-pinned (`check_plugin`,
# `check_host_adapters`). This is an exact allowlist on purpose — see
# `_gateway_tool_name`.
GATEWAY_SERVERS = frozenset({
    GATEWAY_SERVER,
    "plugin_%s_%s" % (PLUGIN_NAMESPACE.replace("-", "_"), GATEWAY_SERVER),
})
ROLE_BY_FOLDED = {name.casefold(): name for name in ROLE_NAMES}
SESSION_FIELDS = frozenset({
    "capability_hash", "workspace_id", "workspace_kind", "role",
    "correlation_id", "workflow", "expires_at", "status",
})
AGENT_MAPPING_TTL_SECONDS = 24 * 60 * 60
MAIN_AGENT_TYPE = "__founder_os_main__"

# The founder's local overlay (references/extensibility.md). `_local/` is the
# directory; the file below it is the additive half of the ownership map.
LOCAL_DIR = "_local/"
LOCAL_MAP = "_local/ownership.yaml"

# One overlay read per root per process. A hook process handles one invocation,
# so this is per-invocation caching — the same property PERF-002 pinned for
# workspace_roots, for the same reason: a multi-path apply_patch must not
# re-read the same file once per path.
_LOCAL_CACHE = {}
# The packaged map, keyed by the plugin root the search started from, under the
# same discipline: `owns:` and `derived_files:` are two readers of one document.
_PACKAGED_CACHE = {}


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


def _flow_entries(first, lines):
    """A `derived_files: [a, b]` flow sequence as a tuple, or ().

    PyYAML accepts flow style and the packaged map does not use it, so a
    fallback that read block style only would enforce less than the PyYAML path
    on the very same document — the divergence `_parse_derived_without_yaml`
    exists to prevent. `lines` is the shared iterator so a sequence written
    across several lines is read whole; a tag (`!!seq [...]`) is dropped
    because it says nothing about the shape.
    """
    value = first.strip()
    if value.startswith("!"):
        value = value.split(None, 1)[1].strip() if " " in value else ""
    if not value.startswith("["):
        return ()
    while "]" not in value:
        nxt = next(lines, None)
        if nxt is None:
            return ()  # unterminated — a shape we don't understand
        value += " " + nxt.strip()
    items, buf, quote = [], [], None
    for char in value[1:value.index("]")]:
        if quote:
            if char == quote:
                quote = None
            else:
                buf.append(char)
        elif char in "'\"":
            quote = char
        elif char == ",":
            items.append("".join(buf).strip())
            buf = []
        else:
            buf.append(char)
    if quote:
        return ()
    items.append("".join(buf).strip())
    if any(set("[]{}") & set(item) for item in items):
        return ()  # nested or mapping — PyYAML would hand us no strings here
    return tuple(item for item in items if item)


def _parse_derived_without_yaml(text):
    """Minimal parser for the top-level `derived_files:` sequence, or ().

    Exists for the same reason `_parse_owns_without_yaml` does: without it, a
    machine whose python3 lacks PyYAML would keep the ownership deny and
    silently lose the derived one, which is the worst of the two states — a
    guard that enforces most of its map is harder to notice than one that
    enforces none of it.

    Returns () for anything it does not recognize, including the key being
    absent. That is an allow, and an allow is what a parser that is guessing
    should produce.
    """
    entries, in_block = [], False
    lines = iter(text.split("\n"))
    for raw in lines:
        line = raw.split("#", 1)[0].rstrip() if not raw.lstrip().startswith("#") else ""
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if indent == 0:
            if in_block:
                # A block sequence may sit at column 0 under its own key.
                if line.startswith("- "):
                    entries.append(line[2:].strip().strip("'\""))
                    continue
                break  # next top-level key ends the block
            key, sep, value = line.partition(":")
            if not sep or key.strip() != "derived_files":
                continue
            if value.strip():
                return _flow_entries(value, lines)
            in_block = True
            continue
        if not in_block:
            continue
        body = line.strip()
        if not body.startswith("- "):
            return ()  # a shape we don't understand — don't pretend we do
        entries.append(body[2:].strip().strip("'\""))
    return tuple(entry for entry in entries if entry)


def _derived_from_text(text, source):
    """Return the `derived_files:` entries from ownership YAML text, or ().

    One-way fail-open, deliberately unlike `_owns_from_text`: that one
    distinguishes "no map" from "empty map" because a broken map must not be
    read as "nobody owns anything". Here there is nothing to protect by
    guessing — an entry this function does not return is a path the guard
    treats as ordinary, which is exactly what it did before the key existed.
    """
    yaml_module = _get_yaml()
    if yaml_module is None:
        return _parse_derived_without_yaml(text)
    try:
        data = _yaml_load(yaml_module, text)
    except yaml_module.YAMLError as e:
        log("%s is not valid YAML (%s)" % (source, e))
        return ()
    entries = data.get("derived_files") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return ()
    return tuple(entry.strip().strip("'\"") for entry in entries
                 if isinstance(entry, str) and entry.strip())


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


def _read_packaged_map():
    """`(path, text)` for the plugin's ownership.yaml, or `(None, None)`.

    Two readers now want the same document — `owns:` and `derived_files:` — and
    the one thing they must never disagree about is *which* document they read.
    Memoised for that reason first and the saved stat second: without the cache
    the two searches are independent, so a map edited between them would hand
    one reader an owner list the other's derived list never saw. Per invocation,
    the same discipline `_LOCAL_CACHE` holds for the overlay (PERF-002).
    """
    env_root = os.environ.get("PLUGIN_ROOT") or os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env_root in _PACKAGED_CACHE:
        return _PACKAGED_CACHE[env_root]
    roots = []
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
        _PACKAGED_CACHE[env_root] = (path, text)
        return path, text

    log("ownership.yaml not found (looked in: %s)" % ", ".join(roots))
    _PACKAGED_CACHE[env_root] = (None, None)
    return None, None


def load_ownership():
    """Return {entry: owner} from the plugin's ownership.yaml, or None.

    None means "I could not read my own map" and every caller turns that into an
    allow.
    """
    path, text = _read_packaged_map()
    if text is None:
        return None
    owns = _owns_from_text(text, path)
    if owns is None:
        return None
    return _by_path(owns) or None


def load_derived():
    """Return the `derived_files:` entries from the packaged map, or ().

    Never None: an absent key, an unreadable map and a shape we don't recognize
    all mean "this guard knows of no derived directory", which is an allow, not
    a deny. The key is optional by contract — a map written before the dashboard
    existed has none — so a missing one cannot be an error.

    Reading the key is independent of `owns:`, and so is enforcing it. The only
    caller, `check_ownership`, still allows and exits when `load_ownership`
    returns None — an unreadable map is not evidence that a write is wrong —
    but it runs the derived check first, so a document that keeps
    `derived_files:` and loses `owns:` denies the rendered tree with the
    ownership deny off rather than neither. `check_local_map` does sit behind
    that bail, deliberately: it governs the founder's own overlay, where the
    fail-open posture costs a stale map and not a fabricated number. Pinned by
    tests/test_ownership_guard.py::TestDerivedFilesAreNotWritable::
    test_an_unusable_owns_key_does_not_switch_the_derived_deny_off.
    """
    path, text = _read_packaged_map()
    if text is None:
        return ()
    return _derived_from_text(text, path)


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


def _derived_entry(rel, derived):
    """The `derived_files:` entry covering a workspace-relative path, or None.

    Matched by path *segment*, never by string prefix: `_dashboard/` covers
    `_dashboard` and everything under `_dashboard/`, and covers neither
    `_dashboard_secrets.md` nor `_dashboardish/x.md`. A prefix test would deny
    both of those, and a deny the founder cannot explain from the map is how a
    guard stops being read as a map.

    The trailing slash is stripped rather than required, because an entry that
    lost it is a typo in the map and the safe reading of a typo in a deny list
    is the broader one. Casefolded to agree with `owner_of` — a map dodged by a
    shift key is not a map.

    `rel` arrives from `resolve_in_workspace`, which has already realpath'd and
    normalized it, so there is no `..` left here to walk out of the directory.
    """
    rel_cmp = rel.casefold()
    for entry in derived:
        entry_cmp = entry.casefold().rstrip("/")
        if not entry_cmp:
            continue
        if rel_cmp == entry_cmp or rel_cmp.startswith(entry_cmp + "/"):
            return entry
    return None


def _deny_tool(agent_type, tool_name, reason):
    deny(
        "Founder OS role boundary: `%s` may not use `%s`. %s\n\n"
        "Role subagents read and write business state only through the local "
        "`founder-os-state` gateway. Return control to the main thread if a "
        "different capability is required." % (agent_type, tool_name, reason)
    )


def _role_of(agent_type):
    """Bare role name for one of *this plugin's* role identities, or None.

    Claude Code identifies plugin subagents as ``<plugin>:<agent>``; Codex and
    the packaged fixtures use the bare name.

    Only this plugin's namespace counts. `cfo`, `strategist` and `board-member`
    are ordinary agent names, so a second installed plugin shipping one arrives
    as ``<their-plugin>:cfo`` — that is their agent, and it must not inherit the
    founder's CFO authority at the gateway. It is a stranger, handled as one.

    The bare segment is matched casefolded because `owner_of` is casefolded and
    the filesystem may be too: without this, ``founder-os:CFO`` would be "not a
    role" to the lockdown and the CFO to the ownership map at the same time.
    Role-ness decides whether the lockdown applies at all, so a near miss has
    to resolve toward the restricted reading, not away from it.
    """
    if not isinstance(agent_type, str):
        return None
    namespace, separator, bare = agent_type.rpartition(":")
    if separator and namespace.casefold() != PLUGIN_NAMESPACE:
        return None
    return ROLE_BY_FOLDED.get(bare.casefold())


def _gateway_tool_name(tool_name):
    """Return a known local action, ``""`` for an unknown local action, else None.

    Hosts register the same server under different outer names: the packaged
    shape is ``mcp__founder-os-state__<action>``, and Claude Code wraps plugin
    servers as ``mcp__plugin_founder-os_founder-os-state__<action>``. Both
    normalized names are in `GATEWAY_SERVERS` and nothing else is.

    The allowlist is exact rather than a suffix test. Matching
    ``*_founder_os_state`` reads as conservative — "treat a lookalike as ours
    and capability-check it" — but it inverts the decision it is guarding:
    an unrecognized server's baseline is *denied*, so adopting it turns a deny
    into an allow, and for the six capability-bound actions it hands the
    founder's live capability token to whatever named itself that way.
    ``mcp__evil-founder-os-state__write_owned_state`` matched, and so did
    ``mcp__x__founder-os-state__read_state``, because ``_`` is also the tail of
    ``__``. An unknown wrapper must deny.
    """
    if not isinstance(tool_name, str) or not MCP_TOOL.match(tool_name):
        return None
    head, _, action = tool_name.rpartition("__")
    server = head[len("mcp__"):].replace("-", "_")
    if server not in GATEWAY_SERVERS:
        return None
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
    if record.get("workspace_kind") not in {
        "single-business", "business", "portfolio"
    }:
        return None
    if not _valid_text(record.get("correlation_id")):
        return None
    role = record.get("role")
    if role not in ROLE_NAMES:
        return None
    workflow = record.get("workflow")
    if not _valid_text(workflow):
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


def check_gateway(agent_type, role, tool_name, tool_input):
    """Authorize only the capability-consistent local gateway surface.

    ``role`` is the normalized bare role name (`_role_of`), or None when the
    caller is not one of the thirteen roles.
    """
    action = _gateway_tool_name(tool_name)
    if action is None:
        _deny_tool(agent_type, tool_name, "Other MCP servers are not allowed.")
    if not action:
        _deny_tool(agent_type, tool_name, "That gateway action is not part of the contract.")
    if action == "open_role_session":
        _deny_tool(agent_type, tool_name, "A subagent cannot elevate itself or mint a session.")
    if action == "resolve_workspace":
        return

    session_role = _session_role(tool_input)
    if session_role is None:
        _deny_tool(agent_type, tool_name, "A live role capability is required.")
    if role is not None and session_role != role:
        _deny_tool(agent_type, tool_name, "The capability belongs to a different role.")
    if role is None and agent_type not in GENERIC_AGENT_TYPES:
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
    """Return paths touched by a Codex apply_patch payload.

    Case-insensitive: a header the regex does not recognize yields no paths,
    and no paths means `check_ownership` returns without an opinion. Matching
    the verb's exact case made `*** update File: _local/ownership.yaml` an
    allow and `*** Update File: …` a deny.
    """
    if not isinstance(command, str):
        return []
    paths = []
    marker = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", re.I)
    move = re.compile(r"^\*\*\* Move to: (.+)$", re.I)
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
    if tool_name in PATH_NAMING_TOOLS:
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


def _path_naming_tools():
    """`PATH_NAMING_TOOLS` as the prose of a deny, so the two cannot drift."""
    names = ["`%s`" % name for name in PATH_NAMING_TOOLS]
    return "%s or %s" % (", ".join(names[:-1]), names[-1])


def _workspace_rels(file_path, hook_cwd, roots):
    """Every workspace-relative name `file_path` has, the resolved one first.

    `resolve_in_workspace` answers with the first of its two resolutions that
    lands inside a root, and that is the realpath. Right for ownership — the
    map governs the real file, and an owner reached through a symlink is still
    that owner — and not enough for `derived_files:`, which is not a claim
    about a file but about a *location*: `_dashboard/` is where the renderer
    writes. A `_dashboard/` symlinked at a sibling directory inside the same
    workspace resolved to the sibling's name, and the derived deny then judged
    a name the write never used. Both names are checked, so neither spelling of
    the same write is the one that gets through.
    """
    rels = []
    _, resolved = resolve_in_workspace(file_path, hook_cwd, roots)
    if resolved is not None:
        rels.append(resolved)
    if not os.path.isabs(file_path):
        if not isinstance(hook_cwd, str) or not os.path.isabs(hook_cwd):
            return rels
        file_path = os.path.join(hook_cwd, file_path)
    literal = os.path.normpath(os.path.abspath(file_path))
    for root in roots:
        if literal == root:
            continue
        prefix = root.rstrip(os.sep) + os.sep
        if literal.startswith(prefix):
            rel = literal[len(prefix):].replace(os.sep, "/")
            if rel not in rels:
                rels.append(rel)
            break
    return rels


def check_derived(agent_type, rel, derived):
    """No agent writes a generated file — including one nobody owns.

    `derived_files:` names output, not state, and is excluded from every
    ownership join on purpose. That exclusion is exactly why the unowned-path
    allow below would otherwise wave it through: nobody owns it, so there is no
    owner to steal from. That reasoning is right for a founder's scratch note
    and wrong here. A derived file is what the dashboard renders *from*, so an
    agent that can write one can put a number on the page that no workspace
    file ever contained — `evidence over vibes` failing silently, which is the
    one failure mode the key was added to prevent.

    So this deny does not consult ownership and cannot be granted by adding an
    entry — the same shape as `check_local_map`, for the same reason: a rule
    that a map edit can switch off is advice. No map edit switches it off:
    `check_ownership` runs this check on both sides of the `owns:` bail, so a
    document that keeps `derived_files:` and loses `owns:` still denies here.

    The thirteen roles never reach here; they are denied every direct file tool
    earlier, in `main`. This closes the branch that governs everyone else.

    It closes it exactly as far as the hook can see, which is a path a tool
    names — under either of its names, since `_workspace_rels` hands over the
    symlinked spelling as well as the resolved one. A shell command names no
    path at all and is outside this rule by design (module docstring), which is
    why the deny text names the tools it reads rather than claiming the
    absolute. `check_local_map` still judges the resolved name only.
    """
    entry = _derived_entry(rel, derived)
    if entry is None:
        return
    deny(
        "`%s` is generated, not authored. `%s` is a derived path "
        "(references/ownership.yaml, `derived_files:`) and no agent writes it "
        "with %s — including `%s`.\n\n"
        "Nothing under `%s` is evidence: it is rendered from the workspace "
        "files that own the numbers, and it is owned by nobody so that it can "
        "never be cited back as state. This deny does not depend on ownership "
        "and cannot be granted by adding an entry to the map.\n\n"
        "If something here is wrong, the fix is in the file it was rendered "
        "from — change that, and render again.\n\n"
        "(The founder can always make this edit themselves — this rule is "
        "about agents.)" % (rel, entry, _path_naming_tools(), agent_type, entry)
    )


def check_ownership(agent_type, tool_name, tool_input, hook_cwd):
    paths = _tool_paths(tool_name, tool_input)
    if not paths:
        return
    derived = load_derived()
    roots = workspace_roots(hook_cwd)
    by_path = load_ownership()
    if by_path is None:
        # `derived_files:` has its own reader, and an `owns:` block this guard
        # cannot parse says nothing about it. Everything else here still fails
        # open — an unreadable map is not evidence that a write is wrong — but
        # it is not evidence that a write into the rendered tree is right
        # either, and that is the one write whose damage is a number on the
        # page with no workspace file behind it.
        for file_path in paths:
            for rel in _workspace_rels(file_path, hook_cwd, roots):
                check_derived(agent_type, rel, derived)
        allow("no ownership map — the guard is off, not strict")
    for file_path in paths:
        root, rel = resolve_in_workspace(file_path, hook_cwd, roots)
        if rel is None:
            log("allow: %s is outside the workspace" % file_path)
            continue
        check_local_map(agent_type, rel)
        for derived_rel in _workspace_rels(file_path, hook_cwd, roots):
            check_derived(agent_type, derived_rel, derived)
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
    if isinstance(direct, str) and SAFE_AGENT.fullmatch(direct):
        return direct
    turn_id = data.get("turn_id")
    if not isinstance(turn_id, str) or not SAFE_ID.fullmatch(turn_id):
        return None
    data_root = os.environ.get("PLUGIN_DATA") or os.environ.get("CLAUDE_PLUGIN_DATA")
    if not data_root:
        return None
    path = os.path.join(data_root, "agent-types", turn_id + ".json")
    payload = _read_small_regular_json(path)
    if not isinstance(payload, dict) or set(payload) != {
        "agent_type", "recorded_at"
    }:
        return None
    recorded_at = payload.get("recorded_at")
    try:
        now = time.time()
    except Exception:
        return None
    if (
        isinstance(recorded_at, bool)
        or not isinstance(recorded_at, (int, float))
        or not math.isfinite(float(recorded_at))
        or not math.isfinite(float(now))
        or float(recorded_at) > float(now) + 300
        or float(now) - float(recorded_at) >= AGENT_MAPPING_TTL_SECONDS
    ):
        return None
    resolved = payload.get("agent_type")
    return resolved if isinstance(resolved, str) and SAFE_AGENT.fullmatch(resolved) else None


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
    if data.get("agent_type") == MAIN_AGENT_TYPE:
        _deny_tool(
            "unresolved role",
            tool_name if isinstance(tool_name, str) else "<invalid tool name>",
            "The main-thread identity is reserved for a recorded Codex turn.",
        )
    for identity_field, pattern in (("agent_type", SAFE_AGENT),
                                    ("turn_id", SAFE_ID)):
        if identity_field in data:
            identity_value = data.get(identity_field)
            if not isinstance(identity_value, str) or not pattern.fullmatch(
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
    if agent_type == MAIN_AGENT_TYPE:
        allow("recorded Codex main thread — the founder is the CEO")
    if not agent_type:
        turn_id = data.get("turn_id")
        if isinstance(turn_id, str) and SAFE_ID.fullmatch(turn_id):
            _deny_tool(
                "unresolved Codex role",
                tool_name if isinstance(tool_name, str) else "<invalid tool name>",
                "The turn identity mapping is missing or invalid.",
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

    role = _role_of(agent_type)
    if role is None:
        # Not one of the thirteen decision roles: a reviewer, an Explore pass,
        # another plugin's agent. The gateway lockdown is not for them — only
        # the overlay and the ownership map are.
        if MCP_TOOL.match(tool_name):
            if _gateway_tool_name(tool_name) is not None:
                check_gateway(agent_type, None, tool_name, tool_input)
            allow("foreign MCP is not this guard's business")
        check_ownership(agent_type, tool_name, tool_input, data.get("cwd"))
        allow()

    if MCP_TOOL.match(tool_name):
        check_gateway(agent_type, role, tool_name, tool_input)
        allow()
    if tool_name in NESTED_AGENT_TOOLS:
        _deny_tool(
            agent_type,
            tool_name,
            "A role does not spawn subagents; the child would be bound by "
            "less than the role is.",
        )
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
