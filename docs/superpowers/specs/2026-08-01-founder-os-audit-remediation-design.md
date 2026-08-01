# Founder OS Audit Remediation Design

**Date:** 2026-08-01  
**Status:** Approved design  
**Scope:** Repair every finding from the repository, integration, workflow,
security, durability, documentation, and host-compatibility audit.

## Goals

The repaired package must:

1. keep every business workspace isolated while giving the portfolio manager a
   narrow, explicit way to read the inputs it owns across businesses;
2. reject role, workflow, and workspace combinations that the package's agent
   definitions do not authorize;
3. implement the MCP and JSON-RPC lifecycle expected by current Claude Code and
   Codex hosts;
4. run scheduled workflows unattended on either supported host without losing
   permissions, paths, sibling schedules, or missed laptop runs;
5. keep state writes durable and runtime bookkeeping bounded;
6. replace the 100-path listing failure with deterministic pagination; and
7. prove the repaired flows through behavioral and integration tests rather
   than source-text assertions alone.

No new third-party runtime dependency will be introduced. Python 3.9 remains
the minimum interpreter. The existing staged deletion of
`docs/design/2026-07-31-decision-first-activation-design.md` is outside this
work and must remain untouched.

## Rejected Approaches

### Patch the current shell snippets and optional arguments in place

This is the smallest diff, but it keeps policy distributed between prose,
shell quoting, gateway branches, and agent frontmatter. It would fix individual
symptoms while leaving the same integration boundaries able to drift again.

### Replace the local runtime with a framework, database, and general YAML parser

That could centralize more behavior, but it would add installation and
compatibility risk to a local-first plugin. None of the findings requires a
database or a new dependency.

## Architecture

The implementation keeps the existing gateway capability model and adds one
purpose-built eighth tool for portfolio inputs. The main boundaries become:

- `WorkspaceResolver`: registry parsing, root disjointness, workspace kind, and
  bounded lookup of registered business roots;
- `RoleSessionStore`: role/workflow membership, workspace-kind compatibility,
  capability lifetime, retention, and operation-journal rotation;
- `Gateway`: capability enforcement and the only cross-workspace read surface;
- `ProtocolServer`: JSON-RPC validation and MCP lifecycle state;
- `SafeStateIO`: bounded reads, paginated discovery, and durable atomic writes;
- `cadence_manager.py`: deterministic host command generation and safe,
  idempotent scheduler updates; and
- package validators and integration tests: executable contracts shared by
  Claude Code and Codex.

## Workspace Types and Registry Integrity

`WorkspaceBinding` gains a `workspace_kind` value with exactly three states:

- `single-business`: no registry is present;
- `business`: a named registry business; and
- `portfolio`: the registry's portfolio workspace.

`resolve_workspace` returns this value alongside the existing fields. Registry
validation resolves every business and portfolio root and rejects any pair
that is equal or where either root is an ancestor of the other. It validates
active and paused entries alike so a paused business cannot alias another
workspace.

The resolver exposes a bounded business lookup only to gateway code. It reloads
and revalidates the registry, confirms that the calling binding is still the
registered portfolio root, then resolves one explicit registered business
slug. No path supplied by a model participates in this lookup.

## Role, Workflow, and Workspace Authorization

`RoleSessionStore` parses the small YAML frontmatter subset already emitted by
the package's thirteen `agents/*.md` files. For every role it builds the set of
listed workflows. Opening a session fails closed when:

- the role is unknown;
- a workflow is absent or not listed for that role;
- a non-portfolio role targets a portfolio workspace;
- `portfolio-manager` targets anything other than a portfolio workspace; or
- the workflow is `portfolio-review` outside a portfolio-manager session.

Standalone maintenance skills do not become role workflows merely because a
directory exists. Universal skills remain available only when they are listed
in that role's frontmatter. Existing capability expiry and opaque-token rules
remain unchanged.

The gateway passes the resolved `workspace_kind` into session opening. It also
asks the resolver to revalidate the binding against the current registry on
every call. A registry appearing, disappearing, or changing a bound root
invalidates existing capabilities instead of silently changing their
authority.

## Portfolio Read Boundary

The new tool is `read_portfolio_inputs`. Its input is:

```json
{
  "capability": "opaque capability",
  "business_slug": "registered-slug"
}
```

It is usable only by `portfolio-manager`, only with workflow
`portfolio-review`, and only from a portfolio binding. The gateway resolves an
active business slug through the validated registry and extracts exactly
`goals.md` `## Bets`, plus `metrics.md` `## Close` and `## Runway`. The response
contains the slug, each fixed heading and body, the source file digest, and a
fixed-reference `missing` list for absent files or sections. Missing inputs are
therefore reportable evidence gaps rather than authority-expanding retries.
Callers cannot provide paths, headings, patterns, or roots.

Ordinary `read_state`, `list_state`, and writes remain confined to the binding
that created their capability. `portfolio.md` therefore remains writable only
inside the portfolio workspace, while business goals and metrics are readable
without granting general cross-workspace access.

## MCP and JSON-RPC Lifecycle

`ProtocolServer` becomes a per-connection state machine:

```text
new -> initialize response sent -> initialized notification received -> ready
```

Every message must contain `jsonrpc: "2.0"`, a string method, and—when it is a
request—a valid string or finite numeric ID that is not a boolean or null.
Malformed requests receive `-32600`; malformed parameters receive `-32602`;
unknown methods receive `-32601`; malformed JSON remains `-32700`.

`initialize` validates `protocolVersion`, `capabilities`, and `clientInfo` with
non-empty `name` and `version`. The server supports `2025-11-25` and the
compatibility version `2025-06-18`, returns the requested version when
supported, and otherwise returns its newest supported version as required by
MCP negotiation. Duplicate initialization fails closed.

`ping` returns an empty result object throughout the connection lifecycle.
Before readiness, all methods other than `initialize`, `ping`, and the expected
`notifications/initialized` are rejected as not initialized. Notifications
never receive a response when they are valid notifications; structurally
invalid messages receive an Invalid Request response with a null ID.

## Paginated State Discovery

`list_state` adds optional `limit` and `cursor` fields. `limit` defaults to 100
and is restricted to 1–100. Results remain lexically sorted and return:

```json
{
  "paths": ["..."],
  "next_cursor": "opaque-or-null"
}
```

The cursor encodes the last returned relative path, a digest of the pattern,
and a format version. It does not carry authority; the capability and workspace
binding are checked on every page. Reusing it with another pattern or passing
an invalid cursor fails with `STATE_IO_ERROR`. Lexically ordered traversal
retains at most `limit + 1` eligible page records to determine whether another
page exists, and all existing byte and path-safety limits still apply.

`SafeStateIO.list_markdown` remains as an internal compatibility wrapper for
callers that require a complete bounded list. The gateway uses the new page
method, eliminating the product-level failure when a workspace contains more
than 100 matching Markdown files.

## Durable Writes and Bounded Runtime Data

Every atomic replace follows this order:

1. write the temporary file;
2. flush and `fsync` the file;
3. validate the precondition again;
4. `os.replace` within the already-open trusted parent directory; and
5. `fsync` that parent directory before reporting success.

The rule applies to workspace state, capability records, hook mappings,
journal rotation, and cadence manifests. A directory-sync failure is surfaced
as the component's existing fail-closed I/O error.

Session records gain explicit close/expiry timestamps. Closed and expired
records are retained for seven days, then pruned in bounded batches during
session lifecycle operations. Abandoned open records older than expiry plus
the same retention window are also removed. Hook turn-to-agent mappings are
pruned after 24 hours in bounded batches.

`operations.jsonl` rotates under an exclusive local lock at 5 MiB and keeps
three archives. Rotation and pruning reject symlinks and non-regular files and
sync the containing directory. Current writes continue to be append-only and
synced before success.

## Cadence Generation and Installation

A new standard-library script, `founder-os/scripts/cadence_manager.py`, owns
machine-readable cadence construction. It has separate preview and apply
phases:

- preview resolves the host binary, workspace, work directory, log directory,
  scheduler, slug, and date; emits the exact cron block or user-service files;
  and records a manifest checksum;
- snapshot saves the current user scheduler state under `~/.founder-os/` and
  returns its checksum and exact backup path;
- apply requires the preview manifest and snapshot, re-reads scheduler state,
  aborts if it changed, replaces only the exact selected fences/services, and
  installs the already-previewed artifacts; and
- removal supports one exact slug or all Founder OS entries without prefix
  matching sibling slugs.

The script invokes scheduler binaries with argument arrays and never through an
interpolated shell. Cron command fields use POSIX `shlex.quote`, so whitespace,
quotes, dollar signs, and metacharacters in paths remain literal. Fence parsing
uses exact marker identities, not GNU/BSD-dependent regular-expression word
boundaries. A registry migration removes only the legacy single-business fence
and replaces it with the selected business fence.

The supported scheduler policy stays decision-based:

- sleeping macOS machines use per-cadence LaunchAgents;
- always-on machines may use user crontab;
- sleeping Linux machines use persistent user systemd timers when requested.

All host changes still require the existing single explicit founder
confirmation after preview and backup disclosure. No scheduler file is written
to `FOUNDER_OS_HOME`.

## Host Commands and Permissions

Preview selects one installed host explicitly. If both are installed, the
founder chooses; if neither is installed, setup stops.

Claude Code commands use the namespaced slash workflow and explicitly allow
the packaged state MCP tools in unattended mode. The command uses
`--permission-mode dontAsk`, a narrowly scoped `--allowedTools` MCP pattern,
and `--max-turns 50`. Unlisted command, web, filesystem, and external MCP tools
remain denied.

Codex commands use the dollar-prefixed skill name and the documented
non-interactive surface: `codex -a never exec --sandbox workspace-write`, an
explicit working directory, and an ephemeral session. The workspace sandbox
permits only the local state writes required by the cadence. The configured
Founder OS plugin and MCP boundary remain authoritative.

Before installation, the manager validates the chosen binary and every flag it
will use. The smoke command runs with a cron-equivalent minimal environment and
the exact quoted invocation from the preview.

External contracts:

- Codex non-interactive mode:
  <https://developers.openai.com/codex/noninteractive>
- Codex CLI command reference:
  <https://developers.openai.com/codex/cli/reference>
- Claude Code headless mode:
  <https://code.claude.com/docs/en/headless>
- Claude Code MCP permissions:
  <https://code.claude.com/docs/en/agent-sdk/mcp>
- MCP lifecycle:
  <https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle>
- JSON-RPC 2.0:
  <https://www.jsonrpc.org/specification>

## Documentation and Package Consistency

Human documentation separates Claude Code and Codex invocation syntax and no
longer tells Codex users to enter slash commands. Scheduling documentation
describes the actual host choice, laptop catch-up behavior, permissions,
backup, logs, smoke test, and removal path.

The documented workflow count becomes 53 everywhere it is intentionally
stated. Package validation checks those canonical count statements or replaces
them with generated values where practical, preventing another silent drift.
References to the public MCP surface change from seven to eight tools, and only
the portfolio-manager agent receives the new tool in its host declaration.

## Error Handling

The implementation preserves the package's stable domain error codes:

- workspace type, registry collision, or root mismatch ->
  `WORKSPACE_UNRESOLVED`;
- role/workflow/workspace mismatch or expired capability ->
  `ROLE_SESSION_INVALID`;
- unsafe paths, malformed cursors, durability failure, journal failure, or
  scheduler state races -> the component's fail-closed I/O error;
- unauthorized file ownership -> `ROLE_NOT_OWNER`; and
- stale content preconditions -> `STALE_WRITE`.

Protocol validation errors stay at the JSON-RPC layer and do not expose
internal paths or exception messages. Scheduler application stops before
mutation on malformed fences, stale snapshots, unsupported flags, or a failed
backup.

## Test Strategy

Every behavioral change follows red-green-refactor. Tests exercise artifacts
and effects rather than merely searching prose.

### Workspace and portfolio integration

- reject duplicate, symlink-equivalent, parent, and child registry roots;
- reject portfolio-manager sessions in business and single-business roots;
- reject other roles in portfolio roots;
- reject workflows absent from the role frontmatter;
- return only the three fixed sections through `read_portfolio_inputs` and
  report fixed missing inputs without returning the rest of either file;
- refuse arbitrary paths, paused or unregistered slugs, and use of that tool by
  any other session; and
- verify `portfolio.md` can be written only in the portfolio root.

### Protocol and pagination

- cover invalid JSON-RPC versions and IDs, malformed initialize parameters,
  duplicate initialize, pre-initialize tools, initialized notification order,
  both supported protocol versions, fallback negotiation, ping, notifications,
  unknown tools, and a complete ready-state tool call;
- create more than 100 Markdown files and traverse every page without gaps or
  duplicates; and
- reject malformed cursors and invalid limits while preserving path and byte
  bounds.

### Durability and retention

- prove parent-directory `fsync` happens after replace and that its failure is
  surfaced;
- prune only records older than their retention windows;
- retain fresh closed/expired records and current hook mappings;
- rotate the journal at the threshold, keep exactly three archives, and retain
  complete JSONL events; and
- reject symlink and non-regular bookkeeping targets.

### Cadences and hosts

- render and execute a harmless smoke command from paths containing spaces,
  quotes, dollar signs, and shell metacharacters;
- install the same cron preview twice and obtain byte-identical output;
- preserve unrelated crontab bytes and sibling business fences;
- migrate only the legacy fence; reject malformed or concurrently changed
  scheduler state;
- generate distinct Claude and Codex invocations with their required
  permission/sandbox flags and skill syntax;
- parse generated LaunchAgent and systemd artifacts; and
- run installed-package host probes against the generated tool catalogue and
  command surfaces.

### Final verification

The completion gate runs, at minimum:

```text
python3 scripts/validate_package.py founder-os
python3 -m unittest discover -s tests -v
node --test tests/*.behavior.test.js
python3 scripts/generate_commands.py founder-os --check
```

It also runs local-link checks, installed smoke tests, Claude/Codex host probes,
and the available official plugin validators. A clean result must coexist with
the user's pre-existing staged deletion unchanged.

## Acceptance Criteria

All twelve audit findings are closed only when their reproductions have become
passing regression tests, both hosts have executable documented flows, the
package validator reports zero errors, the complete Python and JavaScript test
suites pass, and no unrelated working-tree change appears in the remediation
diff.
