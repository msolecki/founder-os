# Founder OS dual-host decision system design

**Date:** 2026-07-22  
**Status:** Approved after host-parity clarification  
**Baseline:** 13 roles, 50 workflows, 10 cadences (`skill-forge` included)  
**Target:** 13 roles, 52 workflows, 10 cadences

## Problem

Founder OS has specialist workflows, but no reliable situation-first front door,
no durable evidence chain for a hard cross-domain decision, and no single Trust
Center. Its host story is also asymmetric in two places:

- Claude Code can load `agents/*.md`; the documented Codex plugin surface
  discovers the shared skills but does not package those role files as native
  Codex agents.
- The local-overlay `/skill-forge` currently installs user skills only under
  `~/.claude/skills/`, so a founder-created workflow is not available in Codex.

## Required host contract

Claude Code and Codex must expose the same:

- workflow names and trigger conditions;
- questions, routing decisions, evidence rules and recommendations;
- output schemas and workspace writes;
- ownership, no-outbound, no-money and regulated-advice guardrails;
- packaged and founder-created local workflows.

Host-specific files are adapters only. Business logic lives once in
`skills/<name>/SKILL.md` (or the local overlay equivalent). Claude Code may
select it through an agent definition; Codex may discover it through
`agents/openai.yaml`; neither path gets a separate decision procedure.

## Situation-first routing

Add `/situation-review`, owned by the Chief of Staff and available through both
host adapters. It runs `context-load`, reuses facts already supplied, and asks
only missing questions, one at a time, with a hard cap of four:

1. What decision must be made?
2. What real options exist?
3. Why now?
4. What happens if nothing changes?

It returns exactly:

```text
Decision: <one sentence>
Business: <resolved slug or single-business workspace>
Owner: <one Founder OS role>
Run: /<one workflow>
Why this route: <one evidence-based sentence>
Missing state: <none or the exact file/observation still required>
```

It writes nothing and does not answer the specialist's question. A material,
hard-to-reverse choice spanning at least two decision domains routes to
`/strategic-evaluation`. A pile of obligations routes to `/triage`.

## Strategic evaluation

Add `/strategic-evaluation`, owned by the Chief of Staff. It writes only to a
new `evaluations/` directory owned by that role. The workspace map pins these
member-file sections:

```text
## Decision
## Scope
## Observations
## Interpretations
## Options
## Recommendation
## Challenge
## Open questions
## Evidence appendix
```

The workflow:

1. Writes the decision, real options, why-now and cost of no change.
2. Names one decision owner and two or three relevant read-only perspectives.
3. Uses separate read-only passes where supported, otherwise attributed
   sequential passes, and records which mode was used.
4. Records observations as `O1`, `O2`, ... with source path and date.
5. Records interpretations as `I1`, `I2`, ... citing observations.
6. Compares options against interpretation IDs.
7. Produces one owner-named recommendation and one Board Member challenge.
8. Writes `evaluations/YYYY-MM-DD-<slug>.md`; an existing path gets `-2`,
   `-3`, ... and is never overwritten.

It must never call sequential passes independent. Unknowns remain unknown. The
report status is `evaluation — founder has not decided`. If the founder decides,
`/decision-log` creates the canonical decision and links the evaluation from
`## Context`; it does not copy the recommendation as the founder's reason.

## Local-overlay parity

`/skill-forge` remains one shared workflow. A forged source directory contains:

```text
$FOUNDER_OS_HOME/_local/skills/local-<slug>/
  SKILL.md
  agents/openai.yaml
```

After explicit consent it installs the same directory to both user scopes:

```text
~/.claude/skills/founder-os-local-<business>-<slug>/
~/.codex/skills/founder-os-local-<business>-<slug>/
```

The Codex adapter names `$local-<slug>` in `default_prompt`. The doctor reports
drift when either installed copy is absent or differs from the overlay source.
A local role file remains ownership/organizational metadata; all executable
behavior required on both hosts stays in the local `SKILL.md`.

No installation happens without naming both destinations and receiving an
explicit yes. No plugin, marketplace, authentication or global config file is
rewritten by this flow.

## Trust Center

Add `docs/trust.md` as the canonical user-facing boundary summary and link it
from the landing page, getting started, enforcement guide and Codex manifest.
It must state:

- canonical business state is local Markdown, but prompts/context/tool results
  sent to a model host follow that host's data settings;
- Founder OS has no cloud service, telemetry or automatic calendar/CRM/email/
  bank synchronization;
- workflows draft but never send, publish, pay, sign or cancel;
- bundled hooks require user review/trust where the host asks for it;
- hooks and ownership are operational guardrails, not a security sandbox;
- unknown and main-thread writes deliberately fail open;
- cron is local and runs only while the machine/service is available;
- Codex plugins use cached installed copies and need update/reinstall plus a new
  conversation to load changes;
- uninstall leaves the founder's workspace intact;
- both hosts expose the same workflow/state/guardrail contract even though
  their discovery adapters differ;
- public issues must contain no secret or private business state.

## Codex hardening

- Every canonical `SKILL.md` must have valid `agents/openai.yaml` with
  `display_name`, `short_description`, and a `default_prompt` naming the same
  `$skill`.
- The Codex manifest says 52 workflows, 13 decision roles and 10 cadences; it
  must not claim the role files are native Codex agents.
- Starter prompts cover situation routing, strategic evaluation and daily brief.
- Manifest homepage/repository/website/trust URLs are absolute HTTPS URLs.
- Hook command objects gain visible status messages; their matchers, Python
  behavior and deliberate fail-open posture do not change.
- Technical docs state that both hosts execute the same `SKILL.md` core.

## Non-goals

- No new role, cadence, cloud service, telemetry or external integration.
- No unsupported `.codex/agents/*.toml` packaging.
- No host-specific decision logic or output schema.
- No authentication/middleware change.
- No change to the ownership guard's fail-open decision.
- No automatic outbound action or global installation without consent.

## Acceptance

1. One ambiguous situation yields exactly one owner and one workflow, with no
   write.
2. One hard cross-domain decision yields a durable, dated `O# → I# → option →
   recommendation → challenge` report and no automatic decision.
3. The same canonical workflow instructions, output and write contract serve
   Claude Code and Codex.
4. All 52 packaged workflows have valid Codex discovery metadata.
5. A local forged workflow installs and is doctor-checked on both hosts.
6. Trust documentation names the model boundary, hook trust, fail-open limit,
   local scheduler, cache/update behavior and uninstall behavior.
7. Landing catalogue contains 52 unique workflows and 10 cadence badges.
8. Package validator, Python tests, Node behavior tests, installed-copy smoke,
   plugin validation and isolated Codex CLI installation pass.

## Official Codex basis

- Plugin structure and cached installed copies:
  <https://developers.openai.com/codex/plugins/build>
- Shared skill discovery and `agents/openai.yaml`:
  <https://developers.openai.com/codex/skills>
- Hooks and their trust/payload contract:
  <https://developers.openai.com/codex/hooks>
- Native project/user subagents, which are not a documented plugin component:
  <https://developers.openai.com/codex/agent-configuration/subagents>

The official manual helper and Docs MCP were unavailable in this managed
environment. The audit used official OpenAI web documentation plus verified
current-session behavior: this Codex installation discovers user skills under
`~/.codex/skills/`.
