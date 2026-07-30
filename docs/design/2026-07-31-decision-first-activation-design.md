# Founder OS decision-first activation design

**Status:** Approved design

**Date:** 2026-07-31

**Scope:** Product positioning, landing-page information architecture, first-run
activation, workflow feedback, and early-use ergonomics

## Summary

Founder OS should present and deliver one continuous promise:

> In less than fifteen minutes, turn one real business situation into a useful,
> source-linked decision that is saved locally and can return in a later
> cadence.

The package already contains the proof needed to support that promise: a local
Markdown workspace, one owner per file, a state gateway, a resumable first run,
a daily brief, scheduled cadences, a fictional contract-shaped workspace, and
bounded roles. The design does not replace those mechanisms. It makes their
relationship visible and gives the user a consistent receipt after they run.

The primary user is a solo service-business founder who already uses Claude
Code or Codex, owns both sales and delivery, and has decisions scattered across
chat, notes, and memory. Multi-business founders remain supported, but they are
a secondary audience in the acquisition path.

This positioning is a hypothesis derived from the current product and Studio
North example. The repository contains no customer-interview evidence or
activation analytics that would make it a finding. It must be tested with real
target users before being treated as proven.

## Problem

The current landing page demonstrates many strong product properties, but it
gives them similar visual weight: the daily brief, pain points, company memory,
the Studio North workspace, installation, weekly rhythm, 52 workflows, 13
roles, multi-business support, state ownership, guardrails, fit, requirements,
and FAQ.

The user can inspect the output and the files, but the dominant path does not
show one complete interaction:

1. what the founder said;
2. which state was read;
3. why one role and workflow owned the decision;
4. what was decided;
5. where the result was saved;
6. when that decision will return.

The onboarding flow has the inverse problem. Its state and persistence
contracts are strong, but the user experiences four groups of questions and
an activation condition before seeing a concise account of why each input was
needed and how the result relates to the problem that brought them to the
plugin.

The result is a product that proves many parts of its architecture before it
makes its simplest working loop unmistakable.

## Goals

- Make the target user, problem, result, and product boundary understandable
  within the first screen of the landing page.
- Show one complete, contract-accurate decision loop before presenting the
  catalogue of roles and workflows.
- Preserve the current state-first activation contract and fifteen-minute hard
  stop.
- End activation with a user-facing receipt that is emitted only after the
  persisted first brief has been re-read and validated.
- Let users describe situations in natural language without learning 52
  command names.
- Make every completed workflow explain its decision, evidence, persistence,
  missing state, return point, and required human action.
- Reduce capture friction without turning `inbox.md` into a second queue.
- Improve recovery messages without weakening fail-closed writes, ownership,
  or workspace isolation.

## Non-goals

- A CRM, accounting system, task manager, shared team dashboard, or life OS.
- Autonomous email, posting, payment, signing, cancellation, or any other
  outbound action.
- Automatic integrations with inbox, calendar, CRM, bank, or accounting data.
- A second state store for onboarding progress, workflow receipts, or first-week
  guidance.
- A universal confidence percentage for AI output.
- Moving multi-business support out of the product. It moves lower in the
  acquisition hierarchy only.
- Replacing the 13-role ownership model or the local state gateway.
- Adding product telemetry.

## Considered approaches

### Documentation-only simplification

Reorder the landing page, show one loop, and make the full catalogue secondary.
This is fast and low risk, but it improves comprehension without changing the
post-install experience.

### Activation-only improvement

Improve `/founder-os-init`, checkpoints, and the activation receipt without
changing the landing page. This improves time to value, but users still install
without a clear model of what will happen.

### One decision-first path across the product

Use the same promise and decision loop on the landing page, during onboarding,
in activation, and after recurring workflows. This is the selected approach.
It makes the marketing claim observable in the product while preserving the
existing state and safety contracts.

## Product positioning

### Primary user

A founder of an operating solo service business who:

- uses Claude Code or Codex already;
- owns sales, delivery, money, and prioritisation personally;
- has live clients, revenue, prospects, or concrete commitments;
- repeatedly reconstructs company context from chat, notes, and memory;
- wants decision discipline and continuity without hiring an executive team.

### Secondary user

A founder running several businesses who needs isolated operating state per
business and one narrow cross-business allocation decision. This use case is
important after the core product is understood, but it should not compete with
the primary promise in the first navigation and first screen.

### Anti-ICP

- A pre-idea user with no operating business state who expects the plugin to
  invent a company.
- A team seeking a shared CRM, project-management dashboard, or collaboration
  layer.
- A user seeking an autonomous business operator.
- A user seeking tax, legal, medical, or investment advice.
- A user unwilling to maintain any explicit local business state.

### Job to be done

When a recurring or unclear situation appears in the business, use current
state to assign it to the right decision owner, reach a bounded conclusion,
save the result in the canonical workspace, and bring it back when it becomes
relevant again.

### Product promise

In less than fifteen minutes, produce the first useful daily decision with a
source, an explicit trade, and a durable local record. Founder OS promises
decision quality and continuity, not a business outcome.

## Landing-page experience

### Information architecture

The landing page should follow this order:

1. target user and outcome;
2. one complete decision loop;
3. five recognisable entry situations;
4. proof in the Studio North workspace;
5. the first fifteen minutes;
6. the operating rhythm;
7. ownership and trust;
8. fit and requirements;
9. installation;
10. expandable reference material for roles, workflows, and multi-business.

The first navigation should link to the decision loop, live sample, first run,
trust, and install. Multi-business and the full workflow count move out of the
primary navigation.

### Hero

The first screen must answer four questions without scrolling:

- **Who:** solo service founders using Claude Code or Codex.
- **Problem:** company decisions disappear into chats and disconnected notes.
- **Result:** one source-linked decision saved to local state.
- **Time:** a valid first brief in less than fifteen minutes.

The primary call to action is `See one decision move through the system`. The
installation call to action is secondary until the mechanism has been shown.
The current proof strip—local Markdown, no automatic sending, explicit
ownership, and no hidden actions—remains visible.

### Canonical landing scenario

The landing uses the existing Studio North state and this founder input:

> I need to finish the Acme proposal, follow up with Northwind, and redesign
> the website. What actually matters today?

The page then shows the contract-accurate loop:

1. **Input:** one unclear priority question.
2. **State:** `goals.md`, `queue.md`, `week.md`, and the dated next actions in
   `pipeline.md`.
3. **Owner:** Chief of Staff running `/daily-brief`.
4. **Decision:** finish `q-0720a`, serving `B1`; do not start the website
   redesign; surface the overdue Northwind follow-up as rotting.
5. **Persistence:** update the Chief of Staff-owned daily review and queue.
6. **Return:** the queue survives the session and the Friday weekly review
   scores what happened.

This scenario extends the presentation of the current example; it does not
change the fictional business facts.

### Situational entry points

Before the full catalogue, show five cards:

| Situation | Owner | Workflow | Persisted result |
|---|---|---|---|
| I do not know what matters today | Chief of Staff | `/daily-brief` | `reviews/daily/`, `queue.md` |
| I do not know whether I can take a new client | Delivery Lead | `/capacity-check` | `clients/_capacity.md` |
| A deal has stopped moving | Pipeline Coach | `/pipeline-review` | `pipeline.md` |
| A client request may be outside scope | Delivery Lead | `/scope-guard` | `clients/` |
| I do not know which work makes money | CFO | `/profitability-analysis` | `metrics.md` |

Each card shows the real decision, owner, workflow, and state destination. The
complete catalogue remains available as a collapsed reference and search tool.

### Existing content to retain

- The Studio North workspace browser, reframed as proof of the preceding loop.
- The first-brief demo and source links.
- The week rhythm.
- The fit and anti-fit section.
- Requirements, dual-host installation, Trust Center, and explicit product
  boundaries.

The 13-role list, 52-workflow catalogue, detailed multi-business section, and
architecture explanation remain accessible but no longer interrupt the main
activation story.

## First-run activation

### Invariants that do not change

- Stage 0 remains read-only and must succeed before any question or mutation.
- The resolved workspace tuple remains frozen for the run.
- Existing populated state remains byte-for-byte preserved.
- Business, customer, quarter, and money remain the four required state groups.
- Unknown values stay unknown.
- Owner agents persist their own outputs through separate role sessions.
- Activation exists only after the first daily brief passes the existing
  validity invariant in the resolved workspace.
- The interview still stops at fifteen minutes.

### Activation intent

After preflight and before the first required group, ask:

> What made you install Founder OS today?

The answer is optional. If supplied, persist it in the Chief of Staff-owned
installation decision under `## Context`, labelled as the founder's stated
activation reason with the current date. It is evidence of the founder's
intent, not evidence that the underlying business claim is true. It does not
enter `queue.md`, alter the first bet, or select the first daily commitment by
itself.

On resume, preserve a supplied activation reason and do not ask again. An
omitted reason does not block activation.

### Progress presentation

Each required group shows:

- its position out of four;
- an estimated duration;
- the decision the state will support;
- the fact that `UNKNOWN` is acceptable.

Example:

> Customer 2/4 · about two minutes · helps distinguish a good-fit opportunity
> from another distraction. Unknown evidence stays unknown.

After each valid owner checkpoint, present one human-readable line naming the
owner, persisted file, and any truthful gap. Do not expose capabilities,
correlation identifiers, hashes, or internal session transitions in the normal
success path.

### Activation receipt

After Stage 6 has persisted and revalidated the first brief, replace the
implementation-heavy success summary with this user-facing structure:

- **You came with:** the activation reason, or `not supplied`.
- **Your first decision:** the one thing and its trade.
- **Based on:** the source files and dates used by the first brief.
- **Saved to:** the exact daily-review path.
- **Founder OS will remember:** the live queue item, bet link, and explicit
  missing inputs.
- **Recommended next move:** exactly one workflow derived from current state.

The existing full list of files and their owners remains available in a
collapsed technical detail or documentation link. The normal receipt leads
with user value.

### Return to the activation reason

Activation completes before any attempt to solve the initial situation. After
the receipt, the Chief of Staff may run `/situation-review` on the supplied
activation reason and show the selected owner, workflow, required state, and
expected persistence. The specialist workflow runs only after the founder
chooses to continue.

If the fifteen-minute hard stop has been reached, do not open another role
session. Show one copyable `/situation-review` command carrying the reason and
end successfully.

## Situation Review as the front door

The package already defines `/situation-review` as the entry point for one
unclear situation. Product surfaces should treat it that way:

- the Codex and Claude discovery copy leads with describing a situation;
- the landing page and getting-started guide show natural-language examples;
- the post-activation receipt recommends it when the next decision is unclear;
- the 52-workflow catalogue is reference material, not required knowledge.

The strict six-field delegation request remains internal and unchanged. The
founder sees the reduced decision sentence, selected owner, reason, missing
state, expected state destination, and a continue/stop choice. The main thread
continues to validate and execute the handoff; the routing role does not answer
the specialist's question.

## Workflow receipt

### User-facing contract

After each successfully completed workflow, show:

- **Decision:** the verdict or result.
- **Evidence:** workspace paths and source dates used for the conclusion.
- **Changed:** paths whose expected persistence was re-read and validated.
- **Gaps:** missing or stale state that constrained the answer.
- **Returns:** the cadence or date that will revisit the decision, or `none`.
- **Your move:** exactly one human action, or `none`.

For a read-only workflow, `Changed` is `none`. For a workflow that drafts an
outbound body, `Your move` may say that the founder must review and send it;
the receipt never claims it was sent.

### Orchestration contract

The role result must give the main thread structured inputs for the receipt:
the decision, evidence paths and dates, gaps, return point, required human
action, and expected persistence. This is separate from a delegation request,
whose existing exact six-field shape does not change.

The main thread renders the user-facing receipt only after the persistence gate
has re-read and verified every expected path. The re-read path list, not the
role's claim, populates `Changed`. A failed or uncertain persistence check
produces an error receipt and never a success receipt.

The receipt is conversational output. It creates no workspace file and no
second history.

### Freshness vocabulary

Use three explicit states:

- `current` only when a workflow already defines a freshness threshold and the
  source is inside it;
- `stale` only when a named workflow or doctor threshold has been crossed;
- `unknown` when a required value is absent.

When no threshold exists, show the source date without assigning `current` or
`stale`. Do not invent one global freshness period and do not calculate an AI
confidence percentage.

## Quick capture

Add `/capture` as a Chief of Staff role skill with `metadata.writes` containing
only `inbox.md`.

Example:

```text
/capture Call Anna about the Acme scope
```

The skill accepts one nonblank logical line of at most 2048 UTF-8 bytes. It
rejects NUL and newline characters rather than silently splitting one capture
into several items. It appends one Markdown list item under `## Inbox`; the
founder's bytes after the list marker remain unchanged. Prefixing the item with
`- ` prevents input such as `## Urgent` from creating a new document heading.
The skill adds no ID, date, priority, owner, classification, bet, or inferred
wording. The response is:

> Captured in `inbox.md`. The next `/daily-brief` or `/triage` will decide what
> it becomes.

The gateway write is re-read before confirmation. Capture failure leaves the
original inbox unchanged and must not claim success. The daily brief and triage
remain the only drains.

Adding this skill increases the public workflow count by one. Generated command
documentation, manifests, landing copy, public counts, and validators must move
together in the same package change.

## First-week guidance

First-week guidance is derived from existing state plus the current activation
flow and appears only in the workflow receipt's `Your move` field. It creates
no progress file.

The rule order is:

1. no valid first brief: resume `/founder-os-init`;
2. the current flow has just completed activation: show one `/capture` example;
3. on later runs, no current pipeline review: recommend `/pipeline-review` before the next
   Thursday cadence;
4. no weekly review: name the next Friday `/weekly-review`;
5. otherwise, derive the next step from the workflow result or show `none`.

Only one next action is shown. The complete first-five-actions list remains in
the documentation and is not repeated after every run.

## Error experience

The stable gateway codes remain the machine contract. The main thread adds a
human-facing wrapper with five facts:

1. whether any write occurred;
2. whether the original file is preserved;
3. the canonical owner or unresolved context;
4. what the system will do next;
5. whether the founder must act.

Required mappings include:

| Code | User-facing action |
|---|---|
| `WORKSPACE_UNRESOLVED` | Ask which business is active; perform no read or write. |
| `ROLE_SESSION_INVALID` | Stop the role run and return control to the main thread. |
| `PATH_OUTSIDE_WORKSPACE` | Refuse the path and name the resolved workspace boundary. |
| `ROLE_NOT_OWNER` | Name the canonical owner and request one bounded handoff. |
| `INVALID_DOCUMENT_STRUCTURE` | Preserve the file, name the structural mismatch, and route to the owner or doctor. |
| `STALE_WRITE` | Re-read, reconcile deliberately, and retry once. |
| `STATE_IO_ERROR` | Preserve the original file, stop, and surface the concrete recovery step. |

Raw codes may appear as technical detail, but the first line must describe the
user impact. No error message may imply that a failed write was persisted.

## Components and ownership

| Component | Responsibility |
|---|---|
| `docs/index.html` and extracted landing controllers | Decision-loop presentation, situational entry points, progressive disclosure, and accessible behaviour. |
| Root README and operator documentation | Carry the same primary user, promise, first-run path, and product boundaries. |
| Studio North example | Remain the canonical fictional evidence behind the landing scenario. |
| `/founder-os-init` | Collect optional activation intent, present progress, preserve checkpoints, and emit the activation receipt after validation. |
| `references/orchestration.md` | Define structured workflow-result inputs and the post-persistence user receipt. |
| `/situation-review` | Remain the single routing front door and exact bounded delegation producer. |
| `/capture` | Append raw founder input to Chief of Staff-owned `inbox.md`. |
| State gateway | Remain the authoritative owner, structure, workspace, version, and atomic-write boundary. |
| Validators and tests | Prevent documentation, host, skill-count, ownership, receipt, and activation contracts from drifting. |

No component gains outbound tools. No file changes owner. No receipt or
first-week state is persisted.

## Data flows

### Recurring decision

```text
founder situation
  -> context-load resolves one workspace
  -> situation-review chooses one owner and workflow
  -> main thread validates the bounded handoff
  -> role reads only required state through its capability
  -> role proposes owner-safe persistence
  -> gateway validates ownership, structure, and file version
  -> main thread re-reads expected persistence
  -> user-facing workflow receipt
  -> later cadence reads the same canonical state
```

### Capture

```text
founder text
  -> /capture under Chief of Staff capability
  -> verbatim append under inbox.md / ## Inbox
  -> persistence re-read
  -> capture confirmation
  -> daily-brief or triage drains and decides
```

### Failed write

```text
role proposal
  -> gateway denial or stale version
  -> no success receipt
  -> human-facing impact and recovery
  -> one safe handoff or one deliberate retry
```

## Delivery sequence

### Release A: show the mechanism

- Reorder the landing information architecture.
- Add the canonical decision loop and five situational entry points.
- Reframe the Studio North browser as proof.
- Move multi-business and complete catalogues lower.
- Align README and getting-started documentation.
- Change no package behaviour.

### Release B: improve first value

- Add optional activation intent after preflight.
- Add purpose, timing, and `UNKNOWN` guidance to each onboarding group.
- Add human-readable owner checkpoints.
- Add the validated activation receipt.
- Route back to activation intent after success without running a specialist
  automatically.

### Release C: improve recurring ergonomics

- Add the structured workflow-result and receipt contract.
- Add explicit freshness and gap presentation.
- Add stable-code user messages.
- Add `/capture` and update the package-wide workflow count.
- Add first-week single-next-action guidance.

Each release must be independently usable and reversible. Release A can ship as
documentation without a package version change. Releases B and C change package
behaviour and require the repository's normal versioning and changelog process.

## Validation

Every package-changing release must pass:

```text
python3 scripts/validate_package.py founder-os
python3 scripts/generate_commands.py founder-os --check
python3 -m unittest discover -s tests
node --test tests/*.behavior.test.js
python3 scripts/check_local_links.py
python3 scripts/smoke_installed_copy.py
```

Release-specific automated checks must prove:

- the landing exposes the full decision loop, keeps all fragment targets valid,
  and does not place multi-business in primary navigation;
- decision-loop and situational controls work with keyboard and screen readers;
- onboarding preserves Stage 0, the four owner stages, the fifteen-minute hard
  stop, resume tuples, byte-for-byte populated state, and the first-brief
  validity invariant;
- activation intent is optional, labelled as founder-stated context, preserved
  on resume, and never enters `queue.md` automatically;
- no success receipt renders before expected persistence is re-read;
- receipt `Changed` paths come from verified persistence, not role prose;
- read-only workflows render `Changed: none`;
- delegation requests retain their exact six-field shape;
- `/capture` is held by Chief of Staff, declares only `inbox.md`, writes only
  under `## Inbox`, rejects multiline and NUL input, preserves the accepted
  text after a safe list marker, and confirms only after re-read;
- every stable gateway error maps to a user impact and recovery action;
- Claude Code native roles, Codex roles, and generic fallback carry the same
  receipt and error contracts.

## Usability validation and success criteria

Because Founder OS has no telemetry, these are evaluated through moderated
tests and voluntary local evidence, not silent product reporting.

Run the same scripted test with at least five target users before Release A and
again against the complete Release C candidate before it is merged:

1. Show the first landing screen for thirty seconds.
2. Ask who the product is for, what it does, and what persists.
3. Give the user an unclear business situation and ask them to start without a
   command list.
4. Run first activation from `/founder-os-init` to a valid first brief.
5. Ask the user to identify the decision, evidence, saved path, next return
   point, and required human action.

The release target is:

- at least four of five users correctly identify the primary user, durable
  decision, and local-state boundary after thirty seconds;
- at least four of five start the scenario through natural language or
  `/situation-review` without browsing the full catalogue;
- at least four of five reach a valid first brief within fifteen minutes,
  measured from invoking `/founder-os-init` and excluding host installation;
- all successful participants can point to the saved brief and explain its
  trade;
- no participant interprets a draft as sent or a failed write as persisted;
- at least three of five voluntary first-week testers produce both a daily
  brief and a weekly review without maintainer intervention.

The existing shareable doctor report may support voluntary debugging, but it
does not carry founder-authored content, customer names, amounts, absolute
paths, or telemetry.

## Design constraints

- The founder remains CEO; roles advise and persist bounded state.
- Nothing sends, pays, signs, cancels, or publishes.
- Every business claim is sourced or explicitly identified as unknown or a
  hypothesis.
- Every workspace file keeps one canonical owner.
- Draft bodies and sent records remain distinct.
- All writes fail closed through the state gateway.
- Multi-business resolution occurs before opening business state.
- User-facing simplicity may hide orchestration mechanics, but it may not hide
  what was read, written, refused, or left unknown.
