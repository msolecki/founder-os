# Founder OS — Documentation

Founder OS is for a solo service founder using
[Claude Code](https://code.claude.com/docs) or
[Codex](https://developers.openai.com/codex/plugins/build). Describe one
situation or run `/situation-review`; it routes a source-linked decision into a
local Markdown workspace. Behind that first path are **13 agents, 52 skills, 10
optional cadences**, one owner per file, an authoritative local state gateway,
and multi-business support when the core loop is already understood.

It does not run the company for you. It gives your decisions persistent state,
an owner, and a review rhythm.

This directory is the **complete documentation set**. It is written for two
readers: the **operator** running the package on their own business, and the
**maintainer** developing against it. Where a fact has a single source of truth
in the package itself, these pages point at it rather than copy it — a second
copy of a map goes stale silently, which is the exact failure the package is
built to prevent.

## Start here

| If you want to… | Read |
|---|---|
| Install and run it for the first time | [`getting-started.md`](getting-started.md) |
| Understand the idea before the mechanics | [`concepts.md`](concepts.md) |
| See how the machine actually works | [`architecture.md`](architecture.md) |
| Know which agent owns which decision | [`agents.md`](agents.md) |
| Find the right command | [`commands.md`](commands.md) |
| Understand data boundaries and host parity | [`trust.md`](trust.md) |

## Operating it

- **[`concepts.md`](concepts.md)** — the mental model (founder as CEO, an org of
  agents, one decision each, shared Markdown state) and a glossary.
- **[`workspace-state.md`](workspace-state.md)** — every workspace file, its
  owner, its pinned sections, and how work moves through them. Includes the
  guided tour of the `studio-north` example.
- **[`commands.md`](commands.md)** — all 52 skills grouped by the agent that
  runs them, the system commands, and the cadence schedule.
- **[`cadences.md`](cadences.md)** — how `setup-cadences` turns workflows into
  real cron jobs, and why there is no cloud scheduler.
- **[`multi-business.md`](multi-business.md)** — running more than one company of
  one from one machine.
- **[`house-rules.md`](house-rules.md)** — the seven rules every agent obeys,
  explained for the person relying on them.
- **[`data-integrity.md`](data-integrity.md)** — how outside claims are tiered
  before they enter a file, how entities are linked, and how the package learns
  your voice.
- **[`troubleshooting.md`](troubleshooting.md)** — `founder-os-doctor`, stable
  gateway failures, host-hook boundaries, and the questions people actually ask.

## Building on it

- **[`architecture.md`](architecture.md)** — plugin layout, the shared
  seven-tool state gateway, sibling orchestration, generated files, and
  dual-host adapters.
- **[`enforcement.md`](enforcement.md)** — the ownership map, authoritative
  gateway, host-hook defense, build validator, and security-boundary limits.
- **[`development.md`](development.md)** — how to add a skill or an agent, every
  check the validator runs, the test suite, CI, and versioning.

## Canonical sources (the maps these docs describe)

These live in the package and are the source of truth. When a doc and one of
these disagree, the file wins.

| Source | What it is |
|---|---|
| [`founder-os/CLAUDE.md`](../founder-os/CLAUDE.md) | The guidance loaded into every session. |
| [`founder-os/README.md`](../founder-os/README.md) | Product philosophy and what the package refuses to do. |
| [`founder-os/COMMANDS.md`](../founder-os/COMMANDS.md) | The generated command catalogue (never hand-edited). |
| [`founder-os/references/house-rules.md`](../founder-os/references/house-rules.md) | The seven house rules, in full. |
| [`founder-os/references/ownership.yaml`](../founder-os/references/ownership.yaml) | Who owns each file and what sections live in it. |
| [`founder-os/references/multi-business.md`](../founder-os/references/multi-business.md) | The multi-business procedure. |
| [`founder-os/references/ingestion-gate.md`](../founder-os/references/ingestion-gate.md) | The claim-tiering procedure. |
| [`founder-os/references/linking.md`](../founder-os/references/linking.md) | The `[[slug]]` linking rule. |
| [`founder-os/references/skill-template.md`](../founder-os/references/skill-template.md) | The shape every skill follows. |
| [`examples/studio-north/`](../examples/studio-north/) | A fictional, contract-shaped workspace. |
