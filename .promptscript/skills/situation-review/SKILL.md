---
name: situation-review
description: Route one unclear business situation to exactly one Founder OS owner and workflow — use when the founder describes what is happening, asks what to do next, or does not know which role to ask
references:
  - agents/openai.yaml
---

# Situation Review

This is the front door for one unclear situation. It routes the decision; it
does not answer the specialist's question or create another pile.

## When to use

Use when the founder describes one situation without naming a workflow or owner.
Use `triage` for a pile of obligations.

## Inputs

Run `context-load` first. Reuse facts already supplied by the founder and read
only the state needed to identify the decision domain.

## Shared sibling request

Return one request to the main thread with exactly `role`, `workflow`,
`workspace_id`, `correlation_id`, `handoff`, and `expected_persistence`. It
carries one bounded handoff of at most 4096 UTF-8 bytes. The main thread passes
the carried answer unchanged and executes the request; this workflow does not.
Native and generic execution use the byte-identical packaged role under
`references/orchestration.md`.

## Beliefs

- Routing is a decision, not a polite preface to generic advice.
- One situation with two owners is two decisions; split it before routing.
- Missing state is an output. A confident route without the file that settles it is invented certainty.
- A hard-to-reverse cross-domain choice is not a routing edge case; it is a strategic evaluation.

## Steps

1. Resolve the business through `context-load`.
2. Ask only missing questions, one at a time, with a hard cap of four: What decision must be made? What real options exist? Why now? What happens if nothing changes?
3. Reduce the situation to one decision sentence.
4. Select exactly one owner and one workflow from the Chief of Staff routing table.
5. If it is material, hard to reverse, and crosses two or more decision domains, route to `/strategic-evaluation`.
6. Return the exact shared sibling request and stop. Do not execute it. The main
   thread validates the resolved workspace, correlation, target owner,
   workflow, bounded handoff and expected persistence, then presents the
   user-facing preview below before deciding whether to open the target.

## Output

- `role`: Owner: <one Founder OS role>
- `workflow`: Run: /<one workflow>
- `workspace_id`: <the already resolved workspace identifier>
- `correlation_id`: <the active main-thread flow identifier>
- `handoff`: <the decision, why this route, and missing state as one carried answer>
- `expected_persistence`: <safe paths declared by the selected workflow, or [] when read-only>

Return no extra field and no specialist answer. The main thread executes the
request only after validation and founder consent; this routing workflow ends
here.

## User-facing preview

The main thread reduces the validated internal request to one preview with:

- the decision sentence;
- the selected owner;
- the reason for this route;
- any missing state;
- the expected state destination derived from `expected_persistence`;
- exactly `Continue` and `Stop`.

Only after the founder chooses `Continue` does the main thread open the target
sibling and execute the selected workflow. `Stop` ends with no specialist run.
The routing role does not answer the specialist's question, and the preview
does not claim any persistence occurred.

## Guardrails

Write no file. Do not answer the specialist's question. Never return several
possible owners "to consider." Never use this for tax, legal, medical or
investment advice; route to a qualified professional.
