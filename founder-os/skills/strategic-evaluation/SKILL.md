---
name: strategic-evaluation
description: Evaluate one material, hard-to-reverse or cross-domain decision through dated evidence, owned perspectives, a recommendation and a Board challenge — run before the founder decides
metadata:
  writes:
    - evaluations/
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

## Beliefs

- More perspectives do not make a decision rigorous; a visible evidence chain does.
- An observation without source and date is an opinion wearing a label.
- The person assembling an evaluation does not acquire the right to make the founder's decision.
- Sequential role passes are useful, but calling them independent would be fabricated evidence about the process.

## Steps

1. Record the decision, options, why now and cost of no change.
2. Name one decision owner and select two or three relevant read-only perspectives.
3. Use separate read-only passes where supported; otherwise use attributed sequential passes. Record `Perspective mode` and never call sequential passes independent.
4. Record observations as `O1`, `O2`, ... with source path and date.
5. Record interpretations as `I1`, `I2`, ... citing observation identifiers.
6. Compare every option, including do-nothing when real, against interpretation identifiers.
7. Name one recommendation and decision owner, then ask the Board Member for one challenge verdict.
8. Write `evaluations/YYYY-MM-DD-<decision-slug>.md`; if it exists, use `-2`, `-3`, ... and never overwrite.
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
