---
name: energy-audit
description: Read the calendar record for when the founder's output is good and when it isn't — run monthly, once the ledger has enough weeks to mean something
metadata:
  writes:
    - week.md
---

# Energy Audit

Energy is calendar shape, not willpower: what the founder does, when, and in
what order. The workspace has been recording which blocks got finished and at
what hour for weeks now, and that record answers a question the founder cannot
answer from memory — **which hours actually produce work, and which sequence
destroys them.** The output is two lines in `week.md` that `week-plan` uses on
Monday to place deep work. That is the whole point of this skill.

## When to use

Monthly, or when the pattern in `calendar-audit` is that the blocks were there
and the work still did not happen. That is not a scheduling failure — the hours
were booked — so the question moves to which hours they were.

## Inputs

Read first, in order — house rule 1:

- `week.md` — the `## Ledger` and the `## Audit`. This is the record: planned
  against actual, week after week. It is the only evidence you have.
- `reviews/daily/` — the one thing committed each day, and whether it happened.
  Cross this against the hour it was blocked for.
- `clients/` — delivery hours, to see which weeks mixed sales and delivery.
- `metrics.md` — output that shipped, so "good week" means something checkable.

## Steps

1. **Check you have enough weeks. Four is the floor.** Under four weeks of
   ledger, stop and say so. Three data points will produce a confident,
   invented pattern, and the founder will schedule a quarter around it.
2. **Find the productive hours.** For every deep work block in the ledger, tag
   the start hour and whether it completed. Rank hours by completion rate. Two
   or three hours will separate; if none do, say none do — a flat result is a
   finding, not a failure to look hard enough.
3. **Price the sequence.** Compare days that mixed sales and delivery against
   days that did one thing. Four hours of context-switching between sales and
   delivery produces two hours of work. Say that in hours from the ledger, not
   as a metaphor — the metaphor is not checkable and the hours are.
4. **Count the days off.** From the ledger, plainly: how many in the period.
   State the count. Do not interpret it — read `## Guardrails` before you write
   the sentence after the number.
5. **Write the shape, not the theory.** Two lines: the hours that finish work,
   and the sequence that kills them. No chronotypes, no energy model, no
   metaphors about tanks or batteries. `week-plan` needs an hour range it can
   put a block in.

## Output

Replace the `## Shape` section of `week.md`. Change nothing else — `week-plan`
owns `## Blocks`, `calendar-audit` owns `## Audit`.

    ## Shape
    Deep hours <hh:mm–hh:mm> · Sequence to avoid <what> (from energy-audit YYYY-MM-DD)
    Evidence: <n> weeks of ledger · completion <n>% in those hours vs <n>% outside
    Recorded: <n> days off in <n> weeks

If the evidence does not separate, write that instead of a number:
`Deep hours undetermined — <n> weeks show no difference`. A confident wrong hour
range is worse than an honest gap, because `week-plan` will build on it.

## Guardrails

**You do not give medical advice.** Verbatim from the `guardrails` skill, which
every agent in this company carries:

> No advice on sleep, burnout, stimulants, mood, or exhaustion beyond what the
> workspace factually records. You may say "you have logged six weeks without a
> day off." You may not diagnose it and you may not prescribe.
>
> **Instead:** name the observation, say it belongs in a conversation with a
> doctor, return to the calendar.

This applies to everything this skill touches, because a founder asking why
their output dropped is asking a question that has both a calendar answer and a
medical one, and only one of them is yours. State what the workspace records —
the days off, the hours, the completion rate. Then stop. Do not explain the
number, do not recommend rest, sleep, a break, a supplement, or a change of
habits, and do not name a cause. Naming a cause is diagnosis.

Refuse the way `guardrails` says to refuse: plainly, no "I'm not a doctor, but",
no answer "in general terms". Name the observation, name the doctor, hand back
the specific number to bring, return to the calendar.

Do not invent an energy model. You have a ledger of blocks and completions.
Everything beyond that is a story, and this company does not ship stories as
findings — house rule 2.
