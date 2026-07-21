---
name: founder-os-init
description: Run first-install onboarding — interview the founder, scaffold the workspace, and hand each answer to the agent that owns it
---

# Founder OS Init

This is the one resumable path from an installed package to a useful first
daily brief. It runs as the Chief of Staff. It orchestrates the owner agents;
it does not borrow their files or call a scaffold an activation.

Activation exists only when a valid brief has been persisted at
`reviews/daily/YYYY-MM-DD.md` in the workspace resolved at preflight. Until
then the workspace is incomplete and the next `/founder-os-init` continues it.

## When to use

Run immediately after install, after moving `FOUNDER_OS_HOME`, or to resume an
interrupted first run. Do not use it to refresh an activated workspace; that is
`/founder-os-doctor`.

Start with Stage 0. Do not ask whether the founder is ready and do not mutate a
workspace before preflight succeeds.

## Inputs

- `references/ownership.yaml` — the only source for scaffold paths, headings
  and owners.
- `references/multi-business.md` and `~/.founder-os/businesses.yaml`, when the
  registry exists.
- `$FOUNDER_OS_HOME`, default `./founder-os/`.
- the canonical Founder OS context injected into this session;
- existing workspace files and `reviews/daily/`, read before any question.

## Stage 0 — Preflight

Stage 0 is read-only. Finish every check before the first workspace write:

1. Confirm the plugin manifest, `CLAUDE.md`, `references/house-rules.md`,
   `references/ownership.yaml`, `references/multi-business.md` and every
   downstream skill named below exist in the installed package.
2. Before normal target resolution, read an **explicit resume tuple** from the
   invocation when one was supplied. It is complete only when it names the
   exact recorded `FOUNDER_OS_HOME`, business slug and resolved workspace path;
   a partial tuple stops instead of being guessed.
3. Resolve the target using the resume-resolution table below. Treat the
   resulting path, `FOUNDER_OS_HOME` and business slug as one frozen
   **resolved workspace** tuple for the entire run.
4. Validate the registry without rewriting it. A second-business request
   follows `references/multi-business.md`; an ambiguous or invalid slug stops.
5. Check from filesystem metadata that the target or its nearest existing
   parent is writable. Do not create a probe file.
6. Confirm the canonical context is present and carries `CLAUDE.md`, the house
   rules, ownership map and resolved workspace.
7. Apply the **daily-review validity invariant**: in this resolved workspace,
   a candidate `reviews/daily/YYYY-MM-DD.md` is valid only when it contains the
   headings declared for `reviews/daily/` by `references/ownership.yaml`, with
   a non-empty `## The one thing` and `## The trade`. Stage 6 uses this exact
   invariant again; there is no weaker activation check.
8. If the selected workspace's `decisions/*-founder-os-installed.md` already
   carries a target checkpoint, compare its `FOUNDER_OS_HOME`, business slug
   and resolved path with the selected tuple. Any mismatch outside the
   confirmed-relocation case stops before a read or write outside the selected
   workspace.
9. Read the target's `charter.md`, owned outputs and `reviews/daily/`, then
   classify exactly one activation state:

### Resume resolution

| Invocation state | Selection rule | Action |
|---|---|---|
| `no explicit resume tuple` | Use the registry and current `FOUNDER_OS_HOME` for normal resolution. | Select a new, incomplete or activated workspace by the ordinary rules. |
| `changed active slug` | The complete explicit resume tuple selects the recorded workspace; ignore the registry's active slug. | Validate the checkpoint at that exact path before reading activation state. |
| `changed home` | The complete explicit resume tuple selects the recorded workspace; ignore the current `FOUNDER_OS_HOME`. | Continue at the recorded path if it exists; otherwise require confirmed relocation. |
| `confirmed relocation` | Require the exact old tuple, exact new tuple and founder confirmation that the workspace moved. | Select the new path, validate that its checkpoint carries the old tuple, and update the target checkpoint to the new tuple only after every read-only preflight check succeeds. |

Never scan sibling workspaces to find a checkpoint. Never infer relocation
from a copied directory or a mismatch. The explicit tuple makes the old target
discoverable; confirmed relocation is the only rebinding procedure.

| State | Evidence | Action |
|---|---|---|
| `new` | No populated Founder OS state and no valid daily review. | Scaffold missing paths, then start Stage 1. |
| `incomplete` | No valid daily review, but one or more owned outputs already contain state. | Preserve every populated section byte-for-byte and resume from the first missing stage. |
| `activated` | A valid `reviews/daily/YYYY-MM-DD.md` exists in the resolved workspace. | Stop and route to `/founder-os-doctor`; never re-run onboarding over live state. |

Any failed preflight check stops before mutation. Report the failed check, why
it matters and the exact repair or resume command. Never silently choose a
different business.

For a `new` workspace, scaffold every `workspace_files:` entry using the H1 and
ordered empty headings from `sections:`. Create directories as directories.
For a new second active business, scaffold the portfolio workspace from
`portfolio_files:` as `multi-business.md` requires. Scaffolding is lifecycle:
outside Chief of Staff-owned paths, never put content below those headings.

For an `incomplete` workspace, create only missing stubs or missing declared
headings. Never replace, normalize, reorder or rephrase existing content.

## Stage 1/4 — Business

Display `Onboarding 1/4 — Business`.

Ask for the founder's timezone in IANA form, the business in one sentence
without “and”, and the five-year north star. Explain that timezone records the
founder's stated zone; it does not schedule cron.

Write only missing answers to `charter.md` under `## Timezone`, `## Business`
and `## North star`. On resume, treat a populated section as completed and do
not ask for or rewrite it. The Chief of Staff owns this file.

- **Target checkpoint:** persist `decisions/YYYY-MM-DD-founder-os-installed.md` with the exact `FOUNDER_OS_HOME`, business slug and resolved workspace path before Stage 2; this owner-written decision record binds later resume runs without creating hidden state.

## Stage 2/4 — Customer

Display `Onboarding 2/4 — Customer`.

Ask for two clients or companies the founder would take again, one they would
not take again, and the observable difference. Carry the answer in this
session for `/icp-definition`; do not write it to `offer.md` yourself.

If any part is unknown, carry the known examples and label the missing evidence
as unknown. Do not turn a preference into customer evidence.

- **Stage checkpoint:** immediately invoke `/icp-definition` through the owner allowlist and require its successful persisted `offer.md` result in the resolved workspace before Stage 3; until that write validates, Stage 2 is incomplete rather than an accepted answer held only in memory.

## Stage 3/4 — Quarter

Display `Onboarding 3/4 — Quarter`.

Ask what result must be true in 90 days, the numeric failure threshold, and the
hours and cash available to pursue it. Carry the answer for
`/quarterly-planning`; do not write it to `goals.md` yourself.

A missing capacity or cash cap stays unknown. The first bet may be thin, but it
may not be unsized while pretending to be complete.

- **Stage checkpoint:** immediately invoke `/quarterly-planning` through the owner allowlist and require a successful persisted `goals.md` whose `## Bets` contains `Activation status: ready`, exactly one `### Bet`, and non-empty `Proposed:`, `Outcome:`, `Cost:` and `Kill if:` lines before Stage 4; `Activation status: blocked` is resumable persisted state but must halt at Stage 3 rather than advance or re-ask completed interview answers.

## Stage 4/4 — Money

Display `Onboarding 4/4 — Money`.

Ask for cash on hand, revenue collected over the last three months, and real
monthly burn including founder pay. Collected is not booked. Carry these values
to `/revenue-review` and `/runway-forecast`; do not write `metrics.md` yourself.

Unknown values stay unknown. Do not estimate cash, infer receivables, discount
pipeline into cash, or omit founder pay to make runway look longer.

- **Stage checkpoint:** immediately invoke `/revenue-review` and then `/runway-forecast` through the owner allowlist, requiring each successful independently persisted `metrics.md` result in the resolved workspace before Stage 5.
- **Revenue checkpoint:** invoke `/revenue-review` and require a successful persisted `## Close — YYYY-MM` contract in `metrics.md` with heading matcher: `^## Close — \d{4}-\d{2}$` and `Close type: activation-baseline` before `/runway-forecast`; on resume, do not repeat a valid activation close.
- **Runway checkpoint:** invoke `/runway-forecast` after the revenue checkpoint and require a successful persisted `## Runway` contract in `metrics.md` with heading matcher: `^## Runway — as of \d{4}-\d{2}-\d{2}$` before Stage 5; without that distinct dated block, Stage 4 remains incomplete.

The interview has a hard stop at fifteen minutes. Anything still unanswered
moves to `queue.md`: unknown cash on hand goes in `## Doing`; every other
missing fact goes in `## Queued`. Each item gets an id, a date, `bet: none`,
the owner who can settle it and the missing evidence. There are no `TODO`
lines. The quarter's cash capacity is a bet constraint, not this blocker.

## Stage 5 — Owner-safe delegation

The Chief of Staff writes only `charter.md`, `queue.md`, `decisions/`,
`reviews/daily/`, `reviews/weekly/`, `reviews/monthly/` and `inbox.md`; it
scaffolds other paths as empty lifecycle stubs and delegates all content to the
owner declared by `references/ownership.yaml`.

Use the Chief of Staff's explicit agent allowlist. Pass each carried answer,
the resolved workspace tuple and the fact that this is a bounded first run.
Wait for each owner result before continuing.

| Skill | Holder | Declared writes | Required first-run result |
|---|---|---|---|
| `/icp-definition` | `positioning-advisor` | `offer.md` | Evidence-backed ICP or a dated hypothesis with missing validation queued. |
| `/quarterly-planning` | `strategist` | `goals.md`, `reviews/quarterly/` | One sized partial-quarter bet with a numeric outcome, kill condition and first move. |
| `/revenue-review` | `cfo` | `metrics.md` | Only supplied or computable close values; every unavailable input stays explicit. |
| `/runway-forecast` | `cfo` | `metrics.md` | Real cash and burn arithmetic, or an explicit gap and owned queue item. |

The Stage 2–4 checkpoints invoke these rows in table order. Stage 5 reconciles
their persisted results; it does not wait until now to make the first call. The
two CFO skills share one owner and one file, so `/runway-forecast` reads the
first-run close that `/revenue-review` just wrote. Treat a dated `## Close —
YYYY-MM` with `Close type: activation-baseline` and a dated `## Runway` matching
the Stage 4 expressions as independent completion markers. After each result,
re-read and validate its own block from the same resolved workspace. Do not
accept a verbal “done” as persisted state and do not re-run a valid completed
owner output.

The Chief of Staff may write missing-data queue items and update the target
checkpoint because it owns those paths. The decision record uses the four
headings declared for `decisions/`, records the timezone, resolved workspace
and unknown inputs, and labels itself `none — install record` under
`## Rejected` and `## Supersedes`.

## Stage 6 — First brief

Use the same resolved workspace tuple — the same `FOUNDER_OS_HOME`, business
slug and resolved workspace path fixed in Stage 0 — for validation, invocation
and persistence.

Use the **daily-review validity invariant** from Stage 0 and its headings from
`references/ownership.yaml`; do not substitute a file-exists check.

- **Minimum-state validation:** in the same resolved workspace, validate non-empty charter identity plus owner-persisted `offer.md`, `queue.md`, a `goals.md` `## Bets` with `Activation status: ready` and its complete committed `### Bet`, a `metrics.md` `## Close — YYYY-MM` block with `Close type: activation-baseline`, and a separate dated `## Runway` block matching Stage 4; truthful financial unknowns are valid, but a blocked quarter or fabricated completeness is not.
- **Daily-brief invocation:** invoke `/daily-brief` as the Chief of Staff against that same resolved workspace.
- **Persisted completion:** require a successful persisted write to `reviews/daily/YYYY-MM-DD.md` in that same resolved workspace and validate its declared daily-review headings before continuing.

Minimum state is not “every field known.” It is enough truthful state for the
brief to choose exactly one first move or the blocking cash unknown. Missing
historical items do not become rotting work merely because this is day one.

## Stage 7 — Activation receipt

- **Activation receipt:** print `Activation complete` only after the successful persisted write from Stage 6 has been validated and only when no unresolved activation-stage blocker remains.

Re-resolve nothing here. This is the same resolved workspace: the same
`FOUNDER_OS_HOME`, business slug and path tuple validated in Stage 6. Include:

- the one thing selected for today;
- the persisted `reviews/daily/YYYY-MM-DD.md` path;
- every file written and its owner;
- honest gaps added to `queue.md`;
- the first five actions: run `/daily-brief`, write a thought to `inbox.md`,
  run `/pipeline-review`, run `/weekly-review`, and ask the Chief of Staff where
  to route an uncategorized decision.

Name `/setup-cadences` as optional post-activation setup. Do not run it. Do not
send telemetry, feedback, messages or any other outbound event.

## Resume and failure

Resume state comes only from the persisted outputs in the resolved workspace;
there is no hidden progress file or second state tracker.

### Failure

On a failed preflight, delegation, validation, invocation or write, halt before
Stage 7. Print the completed stages, the missing stage and the concrete failed
condition. Print a copyable `/founder-os-init resume` command carrying the
explicit resume tuple: the exact `FOUNDER_OS_HOME`, business slug and resolved
workspace path from the target checkpoint. Omit the success receipt. A caught
failure in one owner stage must not erase another owner's successful output.

### Resume

- **Preservation:** keep and preserve every populated section byte-for-byte and create only missing stubs or declared headings before continuing from the first missing stage.

On the next run, use the explicit resume tuple — exact `FOUNDER_OS_HOME`,
business slug and resolved workspace path — to select the checkpoint before
consulting current defaults. Derive completed stages from valid owned outputs
and compare the tuple to the target checkpoint before continuing. A moved
workspace requires the confirmed relocation procedure from Stage 0; never
silently rebind it. Do not re-scaffold destructively, re-ask completed stages
or copy a carried answer into a file owned by someone else. An activated
classification still routes to the doctor instead of resuming.

## Output

- One resolved business workspace, never a guessed cross-business path.
- Existing populated state preserved exactly.
- Owner-persisted charter, ICP/hypothesis, first bet, financial baseline/runway
  or explicit gaps, queue items and first daily brief.
- A local activation receipt shown only after the brief validates.

## Guardrails

Never overwrite populated state. Never invent a fact or write content into a
file owned by another agent. Read `references/ownership.yaml` at runtime; the
table above describes orchestration, not a replacement owner map.

Never send, publish, pay, invoice, sign, cancel or install anything. No tax,
legal or medical advice belongs in onboarding. Route those questions according
to `guardrails` and continue only with the in-scope business facts.
