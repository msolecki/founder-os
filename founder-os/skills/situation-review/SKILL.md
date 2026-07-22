---
name: situation-review
description: Route one unclear business situation to exactly one Founder OS owner and workflow — use when the founder describes what is happening, asks what to do next, or does not know which role to ask
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
6. Return the routing record and stop.

## Output

    Decision: <one sentence>
    Business: <resolved slug or single-business workspace>
    Owner: <one Founder OS role>
    Run: /<one workflow>
    Why this route: <one evidence-based sentence>
    Missing state: <none or the exact file/observation still required>

## Guardrails

Write no file. Do not answer the specialist's question. Never return several
possible owners "to consider." Never use this for tax, legal, medical or
investment advice; route to a qualified professional.
