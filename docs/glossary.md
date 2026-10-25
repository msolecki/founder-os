---
title: "Glossary"
status: current
owner: Mateusz Solecki
last-verified: 2026-10-25
---

# Glossary

The terms a new reader meets, one or two lines each, with the page that
explains them. The ideas behind them are in [`concepts.md`](concepts.md).

| Term | Meaning |
|---|---|
| Agent, role | One of the role definitions in `founder-os/agents/`. Each owns one decision, a set of skills and, for most, a set of workspace files. See [`agents.md`](agents.md). |
| Owner | The one agent allowed to write a workspace file. Everyone reads; only the owner writes. See [`workspace-state.md`](workspace-state.md). |
| Ownership map | `founder-os/references/ownership.yaml`: who owns each file (`owns:`), the expected inventory (`workspace_files:`) and the headings each file may hold (`sections:`). It is the only map. See [`enforcement.md`](enforcement.md). |
| Skill, workflow | A procedure in `founder-os/skills/<name>/SKILL.md`, run as `/founder-os:<name>`. A *role skill* belongs to one agent, a *system skill* is cross-cutting, a *standalone skill* is run by the founder directly. See [`commands.md`](commands.md). |
| Workspace | The directory of Markdown state, `FOUNDER_OS_HOME` (default `./founder-os/`), one per business. It is the whole data boundary. See [`workspace-state.md`](workspace-state.md). |
| Main thread | The founder's own conversation. It invokes roles as siblings and re-reads what they wrote; it never writes a role's file for it. See [`architecture.md`](architecture.md). |
| State gateway | The local `founder-os-state` MCP server, the authoritative write boundary: bounded reads, owner-checked atomic writes that fail closed. See [`architecture.md`](architecture.md). |
| Role capability, role session | The short-lived grant the main thread opens for one role, workspace, workflow and run; every gateway read and write a role makes carries it. See [`enforcement.md`](enforcement.md). |
| Guard, hook | `founder-os/hooks/ownership-guard.py`, the `PreToolUse` hook: defense in depth that keeps roles on the gateway. See [`enforcement.md`](enforcement.md). |
| Fail closed | The gateway's write posture: an unknown workspace, role session, path, owner, structure or file version produces a stable denial and no change. See [`enforcement.md`](enforcement.md). |
| House rules | The seven rules every agent obeys; rule 0 is *never outbound, never money*. See [`house-rules.md`](house-rules.md). |
| Bet | A quarterly commitment in `goals.md` under `## Bets`, owned by the Strategist, with a threshold, a judgment date and a downside cap. See [`workspace-state.md`](workspace-state.md). |
| Brief | The daily decision `daily-brief` writes to `reviews/daily/`: one commitment from the queue, the work traded away, and the files behind it. See [`getting-started.md`](getting-started.md). |
| Queue | `queue.md`, what is outstanding. Cadences propose into it; only the Chief of Staff writes it. `## Doing` holds at most three items. See [`workspace-state.md`](workspace-state.md). |
| Inbox | `inbox.md`, the founder's door: one section, no fields, drained to zero by `triage` and `daily-brief`. See [`workspace-state.md`](workspace-state.md). |
| Capture | The `capture` workflow: puts one unstructured thought in `inbox.md` without classifying it. See [`commands.md`](commands.md). |
| Situation review | The `situation-review` workflow: routes one unclear situation to exactly one owner and workflow. The usual first step. See [`getting-started.md`](getting-started.md). |
| Cadence | A workflow `setup-cadences` can schedule on the founder's machine (cron, launchd or user systemd). Every cadence also runs by hand. See [`cadences.md`](cadences.md). |
| Receipt | What every finished workflow shows: decision, evidence, changed paths, gaps, return point and one human action. See [`architecture.md`](architecture.md). |
| Draft, `## Sent` | A body in `drafts/` the founder is about to send; `## Sent` records only what the founder reports they sent. See [`workspace-state.md`](workspace-state.md). |
| Decision record | A file in a workspace's `decisions/` folder for an irreversible decision, with the rejected option and what would reverse it. Not the project log in [`decisions.md`](decisions.md). See [`workspace-state.md`](workspace-state.md). |
| Provenance | The inline stamp on a claim that came from outside, e.g. `(per Anna, buyer at Acme, call, 12 May)`. See [`data-integrity.md`](data-integrity.md). |
| Tier | The FACT / VALIDATE / DISREGARD label on every claim entering a file. See [`data-integrity.md`](data-integrity.md). |
| `[[slug]]` | An entity link: a reference to an entity another file also names, instead of a retyped name. See [`data-integrity.md`](data-integrity.md). |
| Derived file | A generated path listed under `derived_files:` in the ownership map (today `_dashboard/`). It has no owner and no subagent may write it. See [`dashboard.md`](dashboard.md). |
| Local overlay | `$FOUNDER_OS_HOME/_local/`: files, skills or agents one business adds. It can add and never reassign or remove. See [`architecture.md`](architecture.md). |
| Doctor | `/founder-os-doctor`, the health check against a real workspace: missing files, section drift, stale metrics and more. See [`troubleshooting.md`](troubleshooting.md). |
| Portfolio, registry | Multi-business machinery: `~/.founder-os/businesses.yaml` names the businesses, and a portfolio workspace holds `portfolio.md`. See [`multi-business.md`](multi-business.md). |
