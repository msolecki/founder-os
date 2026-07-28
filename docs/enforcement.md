# Ownership and enforcement

"Every file has exactly one owner" and "no agent sends" are not promises left
to prose. They are enforced by a canonical map, the local state gateway, host
hooks, and a build validator. The gateway is the authoritative write boundary.
Hooks are defense in depth and explicitly not a security sandbox.

## The four layers

| Layer | File | When | Catches |
|---|---|---|---|
| Canonical map | `references/ownership.yaml` | Every build and write | Who owns each path and which `##` sections that document may contain. |
| Local gateway | `mcp/founder_os_state.py` | Every role state call | Unsafe paths, invalid/expired capability, wrong owner, stale content, invalid structure, and I/O failure. |
| Host hooks | `hooks/*.py` | Session/subagent start and role tool calls | Missing context, Claude/Codex identity mapping, direct file/outbound access, self-elevation, and capability-role mismatch. |
| Build validator | `scripts/validate_package.py` | CI / before merge | Incoherent manifests, adapters, roles, tools, sibling orchestration, skills, ownership, sections, beliefs, hooks, and public counts. |

The validator proves the package is internally coherent. The gateway enforces
the actual read or write against the workspace and session that were resolved
for this run. The host hook prevents a known role from bypassing that gateway
through a direct file, shell, web, or unrelated MCP tool.

## The authoritative state gateway

Both Claude Code and Codex start the same local stdio process named
`founder-os-state`. It exposes exactly seven actions:

- `resolve_workspace`
- `open_role_session`
- `list_state`
- `read_state`
- `read_reference`
- `write_owned_state`
- `close_role_session`

The main thread resolves one workspace and opens a short-lived role capability.
That capability is bound to the resolved workspace, role, workflow, and
orchestration correlation id. A specialist uses it directly; the main thread
does not write the specialist's file on its behalf.

`write_owned_state` fails closed before mutation when any authority is unknown.
It rejects paths outside the workspace and everything under `_local/`, resolves
the canonical owner, validates the document's required headings, and requires
either create-only state or the SHA-256 observed by the preceding read. It then
writes and fsyncs a temporary file beside the target and atomically replaces
the destination. The journal stores only metadata and hashes, never business
content, prompts, or the raw capability.

Failures use one stable code and one recovery action:

| Code | Meaning |
|---|---|
| `WORKSPACE_UNRESOLVED` | No unique business workspace; ask, then make no read or write. |
| `ROLE_SESSION_INVALID` | Capability missing, expired, closed, forged, or mismatched; return to the main thread. |
| `PATH_OUTSIDE_WORKSPACE` | Path or symlink escaped the bounded root; refuse without guessing another path. |
| `ROLE_NOT_OWNER` | The role does not own the target; hand off to the canonical owner. |
| `STALE_WRITE` | The file changed since read; re-read, reconcile, then retry once. |
| `INVALID_DOCUMENT_STRUCTURE` | Required headings or lifecycle shape are absent; correct the proposed document first. |
| `STATE_IO_ERROR` | A bounded filesystem operation failed; preserve the original and surface the error. |

## What the host guard does

`ownership-guard.py` runs for direct file tools, `Bash`, web tools, and all MCP
tools. Claude supplies `agent_type`; Codex supplies a `turn_id` recorded by
`record-agent.py` at `SubagentStart`.

For a known packaged role or approved generic fallback, the guard:

1. denies `Read`, `Write`, `Edit`, `NotebookEdit`, `Glob`, `Grep`, and
   `apply_patch` so role state cannot bypass the gateway;
2. denies shell, web, and every non-Founder-OS MCP tool under house rule 0;
3. permits only the seven known local gateway actions;
4. denies `open_role_session` to subagents so they cannot mint or elevate their
   own authority; and
5. requires a live capability and, for a named native role, requires the
   capability-bound role to match that identity.

Malformed hook input or a call with no resolvable subagent identity stays out
of the founder's main-thread permission flow. That narrow fail-open behavior is
not role state authority: a known role with an invalid capability, unknown MCP
action, or direct file tool is denied. The gateway remains fail closed
regardless of what the hook can observe.

## What this is not

Hooks are operational policy, **not a security boundary**. Matchers observe host
tool calls; they do not contain an adversarial process. The system therefore
does not rely on the hook alone:

- role frontmatter exposes only the bounded gateway tool surface;
- the host guard rejects direct and outbound tools if an allowlist is loosened;
- the gateway independently binds every state call to a live role capability;
- the ownership and section map is revalidated at the actual write boundary.

There is no shell proxy, arbitrary filesystem browser, delete tool, remote MCP
service, network request, authentication integration, or telemetry in the
gateway. The hook's existence does not make arbitrary local execution safe.

## Sibling orchestration

Subagents never spawn subagents. A manager returns a structured delegation
request containing the role, workflow, workspace id, correlation id, bounded
handoff, and expected persistence. The main thread opens the requested role
session and invokes that role as a sibling.

Where a host exposes the packaged role natively, it may select that role.
Otherwise the generic-agent fallback receives exactly one unchanged role file,
one active workflow, one bounded handoff, and one role capability. The input
bytes and ownership boundary are the same, so host discovery does not change
the business behavior.

## Multi-business and overlays

`resolve_workspace` applies the registry rules before state opens. Every later
gateway action uses the opaque workspace id and server-side canonical path,
never a caller-supplied absolute path. Two active businesses without a unique
selection fail with `WORKSPACE_UNRESOLVED`; the system does not guess.

The packaged ownership map remains authoritative. A business-local
`_local/ownership.yaml` may add paths but cannot reassign packaged paths, and no
role capability may write anywhere under `_local/`. `/skill-forge` runs with
the founder on the main thread because an agent that can edit the map governing
it does not have a meaningful boundary.
