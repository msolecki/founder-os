---
# promptscript-generated: 2026-08-14T09:55:27.938Z | source: .promptscript/project.prs | target: claude
name: strategic-evaluation
description: Evaluate one material, hard-to-reverse or cross-domain decision through dated evidence, owned perspectives, a recommendation and a Board challenge — run before the founder decides
metadata:
  writes:
    - evaluations/
references:
  - agents/openai.yaml
---

# Strategic Evaluation

This workflow convenes a small, attributable decision review before the founder
commits. It writes analysis, never the decision itself.

## When to use

Run when the founder explicitly requests an evaluation, or when a decision is
material, hard to reverse, or spans at least two decision domains.

## Inputs

Run `context-load` first. Require the decision sentence, real options, why now,
cost of no change, and dated workspace state. Invite at most two additional
domain files per perspective, read-only.

## Shared sibling request

Every role transition returns one request to the main thread with exactly
`role`, `workflow`, `workspace_id`, `correlation_id`, `handoff`, and
`expected_persistence`. It carries one bounded handoff of at most 4096 UTF-8
bytes. The main thread passes each carried answer unchanged and executes the
request; no role executes another role. Native and generic execution use the
byte-identical packaged role under `references/orchestration.md`.

## Beliefs

- More perspectives do not make a decision rigorous; a visible evidence chain does.
- An observation without source and date is an opinion wearing a label.
- The person assembling an evaluation does not acquire the right to make the founder's decision.
- Sequential role passes are useful, but calling them independent would be fabricated evidence about the process.

## Sibling checkpoint protocol

1. **Chief of Staff routing.** The Chief of Staff reduces the request to one
   decision, chooses the decision owner and two or three perspective roles, and
   returns their delegation requests to the main thread. The main thread opens
   a fresh role session, passes one capability and the original bounded handoff,
   then closes the routing session before any perspective starts.
2. **Perspective siblings.** The main thread opens two or three separate,
   attributed, read-only sibling sessions. Each receives the same original
   decision scope, never a prior or another perspective result or answer, and
   returns `expected_persistence: []`. The main thread records the attributed
   carried answer unchanged and calls `close_role_session` before opening the
   next perspective. Sequential host execution stays labelled attributed
   sequential passes, never independent.
3. **Board Member challenge.** After all attributed perspectives return, the
   main thread opens a fresh Board Member session with the original scope and
   the labelled perspective bundle. The Board Member returns a read-only
   challenge with `expected_persistence: []`; the main thread closes the session
   before the final pass.
4. **Chief of Staff persistence.** The main thread opens a new Chief of Staff
   session for `/strategic-evaluation`. Only that owner composes and writes
   `evaluations/YYYY-MM-DD-<decision-slug>.md`. The main thread re-reads the
   persisted `evaluations/` checkpoint and calls `close_role_session` before
   advancing to any `/decision-log` request.

The controller does not author or write any specialist answer and does not
decide business content. It validates envelopes, keeps attribution, opens and
closes sessions, and enforces the persistence gate.

## Steps

1. Record the decision, options, why now and cost of no change.
2. Run Chief of Staff routing, then select two or three relevant read-only perspectives through the sibling checkpoint protocol.
3. Run separate read-only sibling passes where supported; otherwise run attributed sequential sibling passes. Record `Perspective mode` and never call sequential passes independent.
4. Record observations as `O1`, `O2`, ... with source path and date.
5. Record interpretations as `I1`, `I2`, ... citing observation identifiers.
6. Compare every option, including do-nothing when real, against interpretation identifiers.
7. Name one recommendation and decision owner, then return the Board Member request to the main thread for one challenge verdict.
8. Open the final Chief of Staff persistence pass and write `evaluations/YYYY-MM-DD-<decision-slug>.md`; if it exists, use `-2`, `-3`, ... and never overwrite.
9. Stop. If the founder decides, hand the evaluation to `/decision-log`; do not infer or log the decision.

## Output

```markdown
# <decision>

Date: YYYY-MM-DD
Business: <slug>
Decision owner: <role>
Perspective mode: separate read-only passes | attributed sequential passes
Status: evaluation — founder has not decided

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

Every observation carries source and date. Every interpretation cites `O#`.
Options cite `I#`; the recommendation cites its supporting interpretations.
Unknowns remain under `## Open questions`.

## Guardrails

Write only the evaluation directory. Never overwrite an evaluation, implement
its recommendation, send anything, spend money, or modify another owner's
files. Never call sequential passes independent. A founder decision belongs in
`/decision-log`, whose `## Context` links this evaluation without copying its
recommendation as the founder's reason.
