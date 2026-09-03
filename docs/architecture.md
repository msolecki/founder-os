# Architecture

How the machine works end to end. If [`concepts.md`](concepts.md) is the idea,
this is the wiring.

## The package is a plugin

Founder OS ships as a Claude Code plugin (and a Codex plugin — see
[Dual-host](#dual-host-claude-code--codex)). It is installed from this
repository, which is **both the plugin marketplace and the source repo**:

```
/plugin marketplace add msolecki/founder-os
/plugin install founder-os@founder-os
/founder-os:founder-os-init
```

Codex uses `codex plugin marketplace add`, `codex plugin add`, and
`$founder-os:founder-os-init`; see [`getting-started.md`](getting-started.md).

There is no server, no account, and no subscription of its own. It runs inside
your existing Claude Code or Codex environment; host plans and usage stay
separate.

## Activation path

The first-run architecture is outcome-first. One host-specific
`founder-os-init` invocation orchestrates the complete path and the same skill
resumes it after a failure:

```text
empty folder
  → read-only preflight
  → four question groups (business, customer, quarter, money)
  → sibling owner sessions persist offer.md, goals.md, metrics.md, queue.md
  → minimum-state validation
  → /daily-brief
  → reviews/daily/YYYY-MM-DD.md
  → Activation complete
```

The daily review is the activation record. There is no hidden completion flag:
validation and persistence resolve the same workspace, existing populated
sections are never overwritten, and a partial run resumes from the first
missing owned output. An already activated workspace routes to
`/founder-os-doctor` instead of being re-scaffolded.

A valid `reviews/daily/YYYY-MM-DD.md` has all four required headings from
`ownership.yaml`: `## The one thing`, `## Rotting`, `## The trade`, and
`## Triage`, with non-empty `## The one thing` and `## The trade`. An empty,
malformed, or wrong-path file never reaches `Activation complete`.

Workspace files stay on your machine. Prompts and context sent through Claude
Code or Codex remain subject to that environment's data-handling terms; local
Markdown state is not a claim that the host operates offline.

## Workflow results and receipts

Every role returns structured `decision`, `evidence`, `gaps`, `return_point`,
`human_action`, and `expected_persistence` inputs. That result is separate from
the unchanged six-field delegation request. The main thread re-reads every
expected path before it renders:

- **Decision:** the verdict or result.
- **Evidence:** workspace paths and source dates used.
- **Changed:** only paths re-read and verified after the role returned.
- **Gaps:** missing or stale state that constrained the answer, or `none`.
- **Returns:** the cadence or date that revisits the decision, or `none`.
- **Your move:** exactly one human action, or `none`.

A read-only workflow reports **Changed:** `none`. Failed or uncertain
persistence produces an error receipt and never a success receipt. Receipts are
conversation output and create no second workspace history.

Freshness uses only `current`, `stale`, and `unknown`. `current` and `stale`
require a named workflow or doctor threshold; `unknown` means a required value
is absent. With no threshold, the receipt shows the source date without a
freshness state. There is no global freshness period or AI confidence score.

Gateway failures retain their seven stable codes and add five user-facing
facts, in order: whether a write occurred; whether the original file is
preserved; the canonical owner or unresolved context; what the system will do
next; and whether the founder must act.

| Code | Recovery |
|---|---|
| `WORKSPACE_UNRESOLVED` | Ask which business is active; make no read or write. |
| `ROLE_SESSION_INVALID` | Stop the role and return control to the main thread. |
| `PATH_OUTSIDE_WORKSPACE` | Refuse the path and name the workspace boundary. |
| `ROLE_NOT_OWNER` | Name the canonical owner and request one bounded handoff. |
| `INVALID_DOCUMENT_STRUCTURE` | Preserve the file, name the mismatch, and route to the owner or doctor. |
| `STALE_WRITE` | Re-read, reconcile deliberately, and retry once. |
| `STATE_IO_ERROR` | Preserve the original, stop, and show the concrete recovery step. |

## Repository layout

```
founder os/                     ← repo root (marketplace + source)
├── founder-os/                 ← the plugin itself
│   ├── .claude-plugin/plugin.json   ← Claude Code manifest (name, version)
│   ├── .mcp.json                    ← Claude local state-gateway adapter
│   ├── .codex-plugin/plugin.json    ← Codex manifest
│   ├── CLAUDE.md               ← guidance injected into every session
│   ├── COMMANDS.md             ← GENERATED catalogue (do not hand-edit)
│   ├── README.md               ← product philosophy
│   ├── agents/*.md             ← 13 agents (role definitions)
│   ├── skills/<name>/SKILL.md  ← 57 shared skills (workflows)
│   │   └── <name>/agents/openai.yaml  ← Codex presentation adapter
│   ├── hooks/                  ← session-context.py, record-agent.py,
│   │                             ownership-guard.py, hooks.json
│   ├── mcp/                    ← eight-tool local state gateway
│   ├── scripts/cadence_manager.py ← safe local scheduler manager
│   ├── scripts/dashboard/      ← the `/dashboard` renderer (package)
│   ├── references/             ← house-rules, ownership.yaml, thresholds.yaml,
│   │                             linking, orchestration, multi-business,
│   │                             skill-template
│   └── images/                 ← org chart, etc.
├── scripts/
│   ├── validate_package.py     ← build-time validator (the bar for structure)
│   ├── generate_commands.py    ← regenerates COMMANDS.md from the package
│   ├── smoke_installed_copy.py ← copied-package lifecycle
│   └── check_local_links.py    ← tracked local targets and anchors
├── tests/                      ← unittest + behavior tests
├── examples/studio-north/      ← a fictional, contract-shaped workspace
├── docs/                       ← this documentation set
└── .github/workflows/ci.yml    ← runs validator, --check, and tests
```

## The three moving parts

### Agents — role definitions

Each `agents/<slug>.md` is a Markdown file with YAML frontmatter and a body.

- **Frontmatter**: `name` (must equal the filename), `description` (the routing
  blurb), `skills:` (the skills this agent may run), and `tools:` (an explicit
  allowlist).
- **`tools:`** contains six common role-callable gateway actions: workspace
  resolution, bounded state/reference reads, owner-checked writes, and session
  close. `portfolio-manager` alone adds `read_portfolio_inputs`; no role can
  mint its own session. No direct file, shell, web, external MCP, or
  nested-agent tool appears in a role allowlist.
- **Body**: four mandated headings in order — `## What triggers you`,
  `## What you do`, `## What you produce`, `## Who you hand off to`. The
  validator enforces their presence and order.

Agents are invoked, not always-on. A slash command runs the skill; the skill's
owning agent is the role that acts. A manager returns a bounded delegation
request to the main thread, which opens a new sibling role session, waits for
its persisted result, and validates that result before advancing. Subagents
never spawn subagents. See [`agents.md`](agents.md) for the full org chart.

### Skills — workflows

Each `skills/<name>/SKILL.md` is one workflow, invoked as
`/founder-os:<name>` in Claude Code or `$founder-os:<name>` in Codex. Its shape is
fixed by [`references/skill-template.md`](../founder-os/references/skill-template.md):

- **Frontmatter**: `name`, `description` (starts with a verb, says when to use
  it), and `metadata.writes` — every workspace path the skill writes, spelled
  exactly as it appears in `ownership.yaml`.
- **Body**: `# Title`, `## When to use`, `## Inputs`, `## Beliefs`, `## Steps`,
  `## Output`, `## Guardrails`. One optional heading is sanctioned:
  `## Named failure modes`.
- **`## Beliefs`** is required on every role skill and machine-checked: at least
  three principles *a competent generic advisor would not say*, placed before
  `## Steps`. This is what stops the agent giving Wikipedia advice the moment the
  founder steps off the script. The count and placement are enforced by the
  validator; whether the beliefs are actually contestable is what human review
  is for.

Three kinds of skill:

- **Role skills** — belong to exactly one agent (listed in its `skills:`), and
  their `metadata.writes` must be owned by that same agent.
- **System skills** — `founder-os-init`, `founder-os-doctor`, `context-load`,
  `guardrails`, `state-integrity`, `ingestion-gate`. Cross-cutting; they write no
  workspace file of their own (init scaffolds the whole workspace regardless of
  owner). Every agent lists the three *universal* ones: `guardrails`,
  `state-integrity`, `ingestion-gate`.
- **Standalone skills** — `setup-cadences` and `skill-forge`. The founder runs
  them directly because they modify host schedule state or the founder-owned
  local overlay; neither operation belongs to a role subagent.

### Hooks — the runtime layer

`hooks/hooks.json` wires three Python hooks:

| Event | Hook | What it does |
|---|---|---|
| `SessionStart` (startup/resume/clear/compact) | `session-context.py` | Injects `founder-os/CLAUDE.md` into the session as additional context. This is how the house rules and state map are present in every session. |
| `UserPromptSubmit` and `SubagentStart` | `record-agent.py` | Records `turn_id → agent_type` for Codex (Claude includes `agent_type` directly; Codex identifies later tool calls by `turn_id`). Lets one guard enforce both hosts. The same script is registered under both events and each registration passes `--event`, because a payload field that stops arriving would record nothing for the main turn — and the guard denies every call on a turn it cannot resolve. |
| `PreToolUse` on direct file, shell, web, and MCP tools | `ownership-guard.py` | Denies known roles direct file/outbound/unknown-MCP access, denies self-elevation, and checks gateway capabilities against native role identity. |

The gateway and guard are covered in full in
[`enforcement.md`](enforcement.md). The gateway is the authoritative state
boundary and role writes fail closed. The hook is **operational defense in
depth, not a security boundary**: malformed hook traffic stays out of the
founder's way, but a known role is denied direct access or invalid capability
use.

## Session start: what happens

1. `session-context.py` fires and injects `CLAUDE.md` — the founder-as-CEO
   framing, where state lives, the never-outbound/never-money rules, and "ask the
   chief-of-staff when you don't know who to ask."
2. When a workflow runs, `context-load` (house-rule-1 check) loads `charter.md`,
   `goals.md`, and `metrics.md` with their dates stamped, and — on a
   multi-business install — resolves *which business* the session means before
   opening any file, stamping the slug into the context line.
3. The main thread resolves the workspace and opens a short-lived role
   capability. The relevant sibling agent reads through `founder-os-state` and
   writes only its owned paths; the controller re-reads persisted state before
   closing the session or invoking the next sibling.

## The eight-tool state gateway

`founder-os-state` is a local Python stdio MCP process shared by both hosts. It
makes no network request and exposes no shell or arbitrary filesystem browser.

- `resolve_workspace` applies the single/multi-business rules and returns an
  opaque workspace identifier.
- `open_role_session` binds a short-lived role capability to one workspace,
  role, workflow, and orchestration correlation id.
- `list_state`, `read_state`, and `read_reference` provide bounded UTF-8 reads
  below the resolved workspace or from an explicit package-reference allowlist.
- `read_portfolio_inputs` is portfolio-only and returns exactly `goals.md`
  `## Bets` plus `metrics.md` `## Close` and `## Runway` for one active business.
- `write_owned_state` checks the capability, canonical owner, required heading
  order, and expected SHA-256 before atomic replacement and metadata-only
  journaling.
- `close_role_session` invalidates the capability; closed and expired values
  cannot be reused.

Write uncertainty fails closed with one of seven stable domain error codes.
The main thread may orchestrate and mint a capability, but it does not author a
specialist-owned result.

## Generated, not hand-maintained

Two files are derived from the package so they cannot drift:

- **`founder-os/COMMANDS.md`** — generated by `scripts/generate_commands.py` from
  the skills' frontmatter, the agents' `skills[]`, and the cadence table in
  `setup-cadences`. CI runs it with `--check` and fails when the committed file
  differs. A hand edit here is a second map, and second maps go stale silently.
- The **README "What's inside" counts** (Agents / Skills / Cadences) are checked
  against the actual package by `check_readme_counts` in the validator. A count
  that drifts is a build failure, not a review finding.

## Extension: the local overlay

The packaged map is complete for the files the package ships, and no founder
runs a company in general. `$FOUNDER_OS_HOME/_local/` is where a business adds
what it needs without forking — a file, a workflow, and if it genuinely earns
one, an agent. Contract:
[`founder-os/references/extensibility.md`](https://github.com/msolecki/founder-os/blob/main/founder-os/references/extensibility.md).

```
$FOUNDER_OS_HOME/_local/
  ownership.yaml        ← additive only: adds paths, never reassigns one
  skills/local-<slug>/SKILL.md
  agents/<slug>.md
```

Four properties hold it together, and each exists because the alternative fails
quietly:

1. **Additive by construction.** `merged_ownership()` in the guard adds a local
   entry only when the packaged map does not already own that path; a collision
   is dropped, logged, and reported by the doctor. An overlay able to reassign
   `metrics.md` would take the month's close away from the CFO in one
   workspace, with nothing upstream ever seeing it.
2. **Per workspace.** The overlay is read for the root a write actually landed
   in, so on a multi-business install one business's extension never speaks for
   another's files.
3. **Not agent-writable.** The guard denies every subagent any write under
   `_local/`. An agent that can edit the map governing it does not have a map.
4. **Validated late, by the doctor.** `scripts/validate_package.py` runs in this
   repository's CI and will never see a stranger's `_local/`, so the six overlay
   checks live in `founder-os-doctor` and run weeks later on real state. That is
   worse than build-time validation and it is the only option; the skill says so
   rather than implying the overlay was vetted.

`/skill-forge` is the way in, and it is standalone for the same reason
`setup-cadences` is: running it as a subagent is denied by construction, since
its first write is `_local/` and its last is outside the workspace entirely.
Its commonest correct outcome is a refusal naming the packaged agent that
already owns the decision.

**What the overlay does not do:** constrain main-thread writes. The guard is
scoped to subagents, so an installed local skill invoked as `/local-foo` is not
checked against the merged map — the identical property every packaged skill
has, stated in the docs rather than implied away.

## Dual-host: Claude Code + Codex

The same package runs under Claude Code and Codex:

- **Claude Code** reads `.claude-plugin/plugin.json`, `agents/*.md`, and
  `skills/*/SKILL.md`; `.mcp.json` points at the shared gateway with
  `${CLAUDE_PLUGIN_ROOT}`.
- **Codex** reads `.codex-plugin/plugin.json` (which points `skills` at
  `./skills/`) and, per skill, `skills/<name>/agents/openai.yaml` — a small
  interface file (`display_name`, `short_description`, `default_prompt`). Its
  inline `mcpServers` entry reaches the same gateway as `./mcp/founder_os_state.py`
  with `"cwd": "."`, resolved from the plugin root the host launches it in.
  `${CODEX_PLUGIN_ROOT}` is not expanded there, and an unexpanded path is a
  gateway that never starts.
- The `SessionStart` and guard hooks are written to handle both: Claude supplies
  `agent_type` on tool calls directly; Codex identifies every call by `turn_id`
  and `record-agent.py` holds the mapping — the `--event user-prompt`
  registration records the main turn, `--event subagent-start` records a
  subagent's role. A Codex turn with no mapping is denied rather than treated as
  the founder. `AGENTS.md` at the repo root
  points Codex at `founder-os/CLAUDE.md` as the canonical guidance.
- The main thread prefers a named native role where the host exposes it. The
  portable generic-agent fallback receives the byte-identical packaged role
  file, one active workflow, one bounded handoff, and the same role capability;
  Codex parity does not depend on undocumented `agents/*.md` discovery.

## Versioning

The version lives in `founder-os/.claude-plugin/plugin.json` (and mirrored in
`.codex-plugin/plugin.json`); the [`CHANGELOG.md`](../CHANGELOG.md) tracks it.
Current candidate: **2.8.0** (decision-first activation and workflow receipts,
with full Claude Code and Codex parity). Releases follow SemVer against the plugin
manifest. See [`development.md`](development.md) for the release checklist.
