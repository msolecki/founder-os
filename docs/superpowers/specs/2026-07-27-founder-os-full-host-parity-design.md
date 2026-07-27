# Founder OS full Claude Code and Codex parity design

**Date:** 2026-07-27
**Status:** Approved design; written-spec review pending
**Target release:** 2.5.0 before its first Git tag
**Scope:** Runtime parity, agent orchestration, state integrity, audit fixes,
documentation, and the public static site

## Problem

Founder OS currently describes one product for Claude Code and Codex, but the
runtime contract is not executable on both hosts.

- Founder OS subagents need to read business state before advising and write
  only files owned by their role.
- Claude Code agents can receive native file tools, while the current Codex
  subagent surface reads local files through shell execution.
- Founder OS denies subagents `Bash` because it is outbound-capable, so a Codex
  role cannot read the Markdown state it needs.
- Manager agents are instructed to spawn other agents. Claude Code subagents
  cannot spawn subagents, so onboarding and cross-domain decisions stop at the
  first nested handoff.
- The existing installed-copy smoke injects `agent_type` directly and does not
  exercise the real Codex `SubagentStart` bookkeeping path.

The audit also found independent release blockers and reliability defects: a
missing `trust.html`, silent SessionStart context loss, focus left in a hidden
website panel, unsafe YAML-shape assumptions, stale public counts and versions,
and an unreliable clipboard fallback.

The product is not release-ready while those defects remain.

## Product decision

Founder OS will provide full behavioral parity across Claude Code and Codex.
All thirteen roles remain real agents. A specialist reads the state and writes
its own files directly; the main thread does not write on the specialist's
behalf.

Host-specific files are adapters only. The following stay identical across
hosts:

- workflow and role instructions;
- business-state inputs;
- routing and decision rules;
- ownership and document-structure enforcement;
- persisted outputs and error codes;
- no-outbound, no-money, and regulated-advice boundaries.

The implementation must not depend solely on Codex discovering Claude-style
`agents/*.md` as named plugin agents. That behavior is available in the current
environment but is not part of the documented Codex plugin package structure.

## Architecture

### 1. One local state gateway

The plugin will bundle a dependency-light Python stdio MCP server named
`founder-os-state`. It is a local process, not a remote service. It makes no
network requests, has no authentication integration, and sends no telemetry.

The server owns all Founder OS agent access to business-state files. Both hosts
use the same Python implementation and the same ownership data.

Claude Code loads a plugin-root `.mcp.json`. Codex loads a host-specific MCP
configuration referenced by `mcpServers` in `.codex-plugin/plugin.json`. The
two configuration files differ only in host path variables and point to the
same server entry point.

The implementation uses the MCP initialization, `tools/list`, and `tools/call`
contracts over stdio. Protocol responses go to stdout. Diagnostics go to
stderr so they cannot corrupt JSON-RPC framing.

### 2. Gateway tools

#### `resolve_workspace`

Input:

- optional business slug;
- host project directory as context, not as an authority to select an arbitrary
  filesystem path.

Behavior:

- applies the existing `FOUNDER_OS_HOME` default and multi-business registry
  rules;
- resolves one canonical workspace;
- returns an opaque workspace identifier, business slug, and display path;
- stores the canonical resolved path server-side;
- refuses ambiguous multi-business requests.

The returned identifier, not a caller-supplied absolute path, is used by every
later state operation.

#### `open_role_session`

Input:

- resolved workspace identifier;
- one of the thirteen packaged roles;
- orchestration correlation identifier.

Behavior:

- may be called only from the main orchestration thread;
- creates a cryptographically random, short-lived capability;
- binds it to one role, one workspace, and one orchestration run;
- persists only a hash and metadata under the plugin data directory;
- returns the capability once for delivery to the role agent.

The host hook denies subagents an attempt to open or elevate a role session.
Hooks remain an operational control rather than a security sandbox.

#### `list_state`

Input:

- role-session capability;
- a bounded relative pattern under the resolved workspace.

Behavior:

- lists regular Markdown files only;
- rejects absolute paths, `..`, NUL bytes, and unsupported glob constructs;
- never follows a symlink outside the workspace;
- caps result count and response size.

All roles may read all business-state files.

#### `read_state`

Input:

- role-session capability;
- one or more relative paths returned by the state map or `list_state`.

Behavior:

- resolves every path beneath the bound workspace;
- refuses directories, special files, and escaping symlinks;
- returns UTF-8 content, modification metadata, and SHA-256;
- caps the number of files, per-file size, and total response size;
- returns missing state explicitly rather than inventing an empty document.

#### `read_reference`

Input:

- role-session capability;
- a relative packaged-reference path.

Behavior:

- reads only an explicit allowlist: canonical guidance, ownership data, house
  rules, and reference files used by the active workflow;
- never reads plugin data, credentials, host configuration, or arbitrary files
  beside the plugin;
- applies the same UTF-8 and response-size limits as `read_state`.

#### `write_owned_state`

Input:

- role-session capability;
- one relative destination;
- complete UTF-8 document content;
- expected SHA-256 for an existing file, or an explicit create-only marker.

Behavior:

1. Resolve the capability, role, workspace, and destination.
2. Reject paths outside the workspace and all writes below `_local/`.
3. Resolve member-file ownership from the canonical `ownership.yaml` rules.
4. Require the bound role to own the destination.
5. Validate required document headings for the matched ownership entry.
6. Compare the current hash with `expected_sha256`.
7. Write a temporary file in the destination directory, flush it, and replace
   the destination atomically.
8. Return the new hash and operation metadata.

The tool exposes no delete, rename, shell, network, send, payment, publication,
or subscription action. Updates are full-document replacements after a read;
the initial version does not implement a patch language.

#### `close_role_session`

Invalidates the capability and records only the final status. Expired and
closed capabilities cannot be reused.

### 3. Ownership and identity

The gateway is the authoritative write boundary for Founder OS agents. It
fails closed for every write uncertainty.

The host hook remains defense in depth:

- it resolves Claude `agent_type` directly;
- it resolves Codex `turn_id` through the `SubagentStart` mapping;
- it allows only the known local Founder OS gateway tools;
- it treats other MCP tools as outbound-capable and denies them to subagents;
- it denies subagents from opening role sessions;
- it checks that a known native role agrees with the capability-bound role;
- it keeps direct `Write`, `Edit`, `apply_patch`, and arbitrary `Bash` denied
  for Founder OS role agents.

The capability allows the documented generic-agent fallback to preserve role
identity when a host does not expose the packaged role as a named native agent.
The fallback receives exactly one role file, one active workflow, one bounded
handoff, and one role capability.

### 4. One-level orchestration

Subagents never spawn other subagents. The main thread is the technical
orchestrator on both hosts.

The main thread may:

- invoke the Chief of Staff to decide routing;
- open a role session requested by that routing decision;
- invoke a named native role when available;
- otherwise invoke a generic subagent with the unchanged packaged role
  instructions;
- pass bounded carried answers and prior role results;
- wait, validate the persisted result, and close the role session;
- invoke the next sibling agent required by the workflow.

The main thread may not:

- make a business recommendation itself;
- alter a role result before persistence;
- write a specialist-owned file;
- claim success from a verbal result without re-reading persisted state;
- create a role not present in the packaged ownership and agent maps.

The Chief of Staff and manager roles return a structured delegation request
instead of invoking `Agent(...)` themselves. The main thread executes the
request without changing the decision.

All existing `Agent(...)` edges are removed from subagent tool allowlists and
from claims that a subagent directly summons another agent. The validator
rejects any future nested-agent edge.

### 5. Orchestration examples

First-run onboarding becomes:

1. Main thread conducts the bounded interview under `founder-os-init`.
2. Chief of Staff persists its owned charter and queue state through the
   gateway and returns the first delegation request.
3. Main thread invokes Positioning Advisor, which reads state and writes
   `offer.md` through its own session.
4. Main thread invokes Strategist, which writes `goals.md` and the quarterly
   review through its own session.
5. Main thread invokes CFO for revenue review and runway in order, reusing the
   CFO role but validating each independently persisted block.
6. Main thread invokes Chief of Staff for the first daily brief.

Strategic evaluation becomes:

1. Chief of Staff selects the decision owner and two or three perspectives.
2. Main thread invokes each perspective as a read-only sibling role.
3. Main thread invokes Board Member with the attributed options and evidence.
4. Main thread invokes Chief of Staff with all attributed results.
5. Chief of Staff writes the final evaluation through its own gateway session.

No perspective is described as independent when it received another
perspective's output.

## Error contract

The gateway returns stable machine-readable codes plus a concise human action.

| Code | Meaning | Required response |
|---|---|---|
| `WORKSPACE_UNRESOLVED` | No unique business workspace | Ask for the business; make no read or write |
| `ROLE_SESSION_INVALID` | Missing, expired, closed, or mismatched capability | Stop and return control to the main thread |
| `PATH_OUTSIDE_WORKSPACE` | Path or symlink escapes the allowed root | Refuse without retrying a modified path guess |
| `ROLE_NOT_OWNER` | Role does not own the target | Name the canonical owner and request a handoff |
| `STALE_WRITE` | Current file hash differs from the read version | Re-read, reconcile deliberately, then retry once |
| `INVALID_DOCUMENT_STRUCTURE` | Required headings or lifecycle shape are absent | Correct the proposed document before retrying |
| `STATE_IO_ERROR` | Filesystem operation failed | Preserve the original file and surface the error |

Unknown role, malformed ownership data, missing ownership, invalid capability,
unreadable destination, and failed structure validation always deny a write.
There is no best-effort persistence.

State writes are atomic. A failed write leaves the prior destination intact and
removes its temporary file when possible.

The operation journal stores timestamp, correlation identifier, role,
workspace identifier, relative path, operation, result code, and before/after
hashes. It never stores business content or prompts.

## Session context behavior

`SessionStart` must never report an empty success when canonical guidance could
not be read or decoded.

- Valid guidance produces the existing additional context.
- Missing, unreadable, or invalid UTF-8 guidance produces a model-visible
  warning and a matching stderr diagnostic.
- The warning names the installed plugin path and tells the model not to give
  Founder OS advice until context is restored.
- The hook does not crash the host session.

## Remaining audit fixes

### Validator hardening

All frontmatter and ownership readers validate container types before calling
mapping or string methods. Invalid YAML shapes become collected validator
errors, never uncaught `AttributeError` tracebacks.

Tests cover mapping, list, scalar, null, mixed tool entries, scalar `owns`, and
non-list owned-path collections.

### Trust Center

`docs/trust.html` becomes a real deployable page at the URL used by the Codex
manifest and landing page. `docs/trust.md` remains the concise source text.
A test compares their required claims so they cannot drift silently.

The local-link checker resolves every tracked Markdown and HTML target and
fails on missing files or anchors.

### Website behavior

When in-panel navigation hides the current workspace panel, focus moves to the
new panel heading. Direct initial-page rendering does not steal focus.

Clipboard fallback:

- treats a false `execCommand("copy")` result as failure;
- restores focus;
- removes the temporary element in `finally`;
- announces success only after a confirmed copy;
- provides a truthful manual-copy message on failure.

Node behavior tests exercise keyboard navigation, focus transfer, successful
clipboard fallback, false fallback, exception cleanup, and focus restoration.

### Documentation and release metadata

Public counts, workflow totals, validator-check totals, architecture version,
doctor samples, troubleshooting copy, and release tests are synchronized with
the package source of truth.

The 2.5.0 release test checks the 2.5.0 changelog section and current full-host
contract. Historical release text remains historical and is not rewritten.

`docs/superpowers/plans/` and `docs/superpowers/specs/` stop being ignored so
the repository's required planning system can actually be committed. Existing
user-owned staged changes are preserved.

## Testing strategy

Implementation follows test-driven development. Each behavior begins with a
failing contract test.

### Gateway unit and protocol tests

- stdio MCP initialize, notification handling, `tools/list`, and `tools/call`;
- diagnostics never written to protocol stdout;
- single- and multi-business resolution;
- opaque workspace IDs cannot be forged into arbitrary paths;
- traversal, absolute paths, NUL bytes, special files, and escaping symlinks;
- role-session creation, expiry, close, wrong workspace, and wrong role;
- all ownership entry types, including directory member files;
- required section validation;
- create-only and hash-guarded replacement;
- stale-write refusal;
- atomic-write failure preserving the prior file;
- operation journal contains metadata but not content.

### Hook and orchestration tests

- Claude `agent_type` and Codex `SubagentStart`/`turn_id` round trips;
- gateway reads allowed for valid role sessions;
- role-session elevation denied to subagents;
- CFO write to `metrics.md` succeeds;
- Strategist write to `metrics.md` returns `ROLE_NOT_OWNER`;
- all external MCP, WebFetch, and arbitrary Bash remain denied;
- direct subagent file tools remain denied;
- no packaged role contains a nested `Agent(...)` edge;
- native-role and generic-role execution use the same role instructions;
- onboarding and strategic-evaluation sibling sequences persist every required
  checkpoint before advancing.

### Installed-host tests

The installed-copy smoke starts the bundled MCP server from a copied plugin,
uses the real configuration paths, exercises session context, role bookkeeping,
read, authorized write, wrong-owner denial, stale-write denial, and structural
validation.

When the local CLIs are available, release verification also runs:

- Claude plugin and marketplace validation;
- Codex plugin discovery from an isolated local marketplace/install;
- one Claude role I/O probe;
- one Codex role I/O probe;
- native and fallback orchestration probes where the host exposes both.

An unavailable host probe is a release blocker, not a silent skip, for a release
claiming that host.

### Full repository verification

- `python3 scripts/validate_package.py founder-os`
- `python3 scripts/generate_commands.py founder-os --check`
- `python3 scripts/smoke_installed_copy.py`
- `python3 -m unittest discover -s tests -v`
- `node --test tests/*.behavior.test.js`
- `claude plugin validate .`
- `claude plugin validate founder-os`
- Codex installed-plugin discovery and role probes
- local Markdown/HTML link and anchor check
- `git diff --check`

The repository has no npm package, lint script, or build target. No dependency
installation is introduced by this design.

## Acceptance criteria

1. All thirteen roles can read the resolved Founder OS state on Claude Code and
   Codex without shell access.
2. Every role can persist only destinations it owns, through the same gateway
   implementation on both hosts.
3. CFO can update `metrics.md`; Strategist receives `ROLE_NOT_OWNER` for the
   same destination.
4. A concurrent modification produces `STALE_WRITE` and preserves both the
   current file and the rejected proposed content in memory only.
5. No subagent spawns another subagent.
6. Onboarding completes through Chief of Staff, Positioning Advisor,
   Strategist, and CFO with persisted checkpoint validation.
7. Strategic evaluation uses attributed sibling perspectives and a final
   Chief of Staff write.
8. Named native roles and the generic fallback execute the same packaged role
   instructions and ownership contract.
9. Session context loss is visible and prevents unsupported Founder OS advice.
10. Invalid YAML shapes produce validator findings rather than tracebacks.
11. The public Trust Center URL resolves to a real tracked HTML page.
12. Website panel navigation and clipboard fallback meet the documented focus
    and success-announcement contracts.
13. Documentation counts, versions, and release assertions match source.
14. Every command in the full repository verification matrix passes.

## Non-goals

- No remote MCP service, cloud database, authentication system, telemetry, or
  external integration.
- No outbound action, payment, publishing, signing, invoicing, or subscription
  cancellation.
- No arbitrary filesystem browser or shell proxy.
- No deletion tool in the initial gateway.
- No host-specific business logic or duplicate role instructions.
- No automatic plugin publication, Git tag, push, or release.
- No change to founder authority in the main thread outside a role workflow.

## Rollout

The work lands in independently deployable stages:

1. Gateway protocol and state-integrity core behind tests.
2. Host configuration and hook integration.
3. One-level orchestration and role migration.
4. Installed-copy and host parity probes.
5. Independent audit defects: SessionStart, validator, Trust Center, website,
   and documentation.
6. Full verification and release-readiness review.

The package version remains 2.5.0 because no 2.5.0 Git tag or public release
exists. Tagging and publishing require a separate explicit request.

## Official host basis

- OpenAI plugin packaging documents bundled `.mcp.json` servers, the
  `mcpServers` manifest field, plugin-scoped approval policy, hooks, and
  installed-copy behavior:
  <https://developers.openai.com/plugins/build/plugins>
- Claude Code documents plugin-provided local stdio MCP servers and
  `${CLAUDE_PLUGIN_ROOT}` path resolution:
  <https://code.claude.com/docs/en/mcp>
- Claude Code documents that subagents cannot spawn other subagents:
  <https://code.claude.com/docs/en/sub-agents>
- MCP defines stdio transport and the `tools/list` / `tools/call` contracts:
  <https://modelcontextprotocol.io/specification/2025-06-18/basic/transports>
  and
  <https://modelcontextprotocol.io/specification/2025-06-18/server/tools>
