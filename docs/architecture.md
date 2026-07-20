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
/founder-os-init
```

There is no server, no account, and no subscription of its own. It runs inside
your existing Claude Code environment; your Claude plan and usage stay separate.

## Repository layout

```
founder os/                     ← repo root (marketplace + source)
├── founder-os/                 ← the plugin itself
│   ├── .claude-plugin/plugin.json   ← Claude Code manifest (name, version)
│   ├── .codex-plugin/plugin.json    ← Codex manifest
│   ├── CLAUDE.md               ← guidance injected into every session
│   ├── COMMANDS.md             ← GENERATED catalogue (do not hand-edit)
│   ├── README.md               ← product philosophy
│   ├── agents/*.md             ← 13 agents (role definitions)
│   ├── skills/<name>/SKILL.md  ← 49 skills (workflows)
│   │   └── <name>/agents/openai.yaml  ← Codex per-skill interface
│   ├── hooks/                  ← session-context.py, record-agent.py,
│   │                             ownership-guard.py, hooks.json
│   ├── references/             ← house-rules, ownership.yaml, linking,
│   │                             multi-business, ingestion-gate, skill-template
│   └── images/                 ← org chart, etc.
├── scripts/
│   ├── validate_package.py     ← build-time validator (the bar for structure)
│   └── generate_commands.py    ← regenerates COMMANDS.md from the package
├── tests/                      ← unittest + behavior tests
├── examples/studio-north/      ← a fictional, contract-shaped workspace
├── docs/                       ← this documentation set
├── site/                       ← the sales landing page
└── .github/workflows/ci.yml    ← runs validator, --check, and tests
```

## The three moving parts

### Agents — role definitions

Each `agents/<slug>.md` is a Markdown file with YAML frontmatter and a body.

- **Frontmatter**: `name` (must equal the filename), `description` (the routing
  blurb), `skills:` (the skills this agent may run), and `tools:` (an explicit
  allowlist).
- **`tools:`** is the real safety boundary. It may contain only
  `Read, Write, Edit, Glob, Grep` and — for managers — `Agent(...)` naming the
  reports they may summon. Nothing that can reach the outside world. The
  board-member holds only `Read, Glob, Grep`: it advises, it does not even write.
- **Body**: four mandated headings in order — `## What triggers you`,
  `## What you do`, `## What you produce`, `## Who you hand off to`. The
  validator enforces their presence and order.

Agents are invoked, not always-on. A slash command runs the skill; the skill's
owning agent is the role that acts. Managers can summon their reports via the
`Agent(...)` edges; nobody can summon sideways. See [`agents.md`](agents.md) for
the full org chart.

### Skills — workflows

Each `skills/<name>/SKILL.md` is one workflow, invoked as `/<name>`. Its shape is
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
- **Standalone skills** — `setup-cadences`. Run by the founder directly; it edits
  the crontab, which no agent may do, so it belongs to no agent by design.

### Hooks — the runtime layer

`hooks/hooks.json` wires three Python hooks:

| Event | Hook | What it does |
|---|---|---|
| `SessionStart` (startup/resume/clear/compact) | `session-context.py` | Injects `founder-os/CLAUDE.md` into the session as additional context. This is how the house rules and state map are present in every session. |
| `SubagentStart` | `record-agent.py` | Records `turn_id → agent_type` for Codex (Claude includes `agent_type` directly; Codex identifies later tool calls by `turn_id`). Lets one guard enforce both hosts. |
| `PreToolUse` on `Write\|Edit\|NotebookEdit\|apply_patch\|Bash\|WebFetch\|mcp__*` | `ownership-guard.py` | The write-time enforcement of ownership (house rule 4) and the outbound ban (house rule 0). |

The guard is covered in full in [`enforcement.md`](enforcement.md). The key fact:
it is **operational policy, not a security boundary**, it is scoped to
*subagents* (the founder as CEO is always allowed), and it **fails open** — any
unknown results in allow.

## Session start: what happens

1. `session-context.py` fires and injects `CLAUDE.md` — the founder-as-CEO
   framing, where state lives, the never-outbound/never-money rules, and "ask the
   chief-of-staff when you don't know who to ask."
2. When a workflow runs, `context-load` (house-rule-1 check) loads `charter.md`,
   `goals.md`, and `metrics.md` with their dates stamped, and — on a
   multi-business install — resolves *which business* the session means before
   opening any file, stamping the slug into the context line.
3. The relevant agent acts, reading the files it needs and writing only the ones
   it owns. Any write is checked by the guard.

## Generated, not hand-maintained

Two files are derived from the package so they cannot drift:

- **`founder-os/COMMANDS.md`** — generated by `scripts/generate_commands.py` from
  the skills' frontmatter, the agents' `skills[]`, and the cadence table in
  `setup-cadences`. CI runs it with `--check` and fails when the committed file
  differs. A hand edit here is a second map, and second maps go stale silently.
- The **README "What's inside" counts** (Agents / Skills / Cadences) are checked
  against the actual package by `check_readme_counts` in the validator. A count
  that drifts is a build failure, not a review finding.

## Dual-host: Claude Code + Codex

The same package runs under Claude Code and Codex:

- **Claude Code** reads `.claude-plugin/plugin.json`, `agents/*.md`, and
  `skills/*/SKILL.md`.
- **Codex** reads `.codex-plugin/plugin.json` (which points `skills` at
  `./skills/`) and, per skill, `skills/<name>/agents/openai.yaml` — a small
  interface file (`display_name`, `short_description`, `default_prompt`).
- The `SessionStart` and guard hooks are written to handle both: Claude supplies
  `agent_type` on tool calls directly; Codex supplies `turn_id`, resolved through
  the `record-agent.py` mapping. `AGENTS.md` at the repo root points Codex at
  `founder-os/CLAUDE.md` as the canonical guidance.

## Versioning

The version lives in `founder-os/.claude-plugin/plugin.json` (and mirrored in
`.codex-plugin/plugin.json`); the [`CHANGELOG.md`](../CHANGELOG.md) tracks it.
Current: **2.3.0** (multi-business). Releases follow SemVer against the plugin
manifest. See [`development.md`](development.md) for the release checklist.
