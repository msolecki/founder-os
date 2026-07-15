---
name: calendar-audit
description: Diff where the week actually went against where it was planned — run every Friday, and whenever the founder claims they have no time
metadata:
  writes:
    - week.md
---

# Calendar Audit

The founder worked all week and the quarter did not move. Both facts are true
and the reason is in the calendar. This skill puts Monday's plan next to the
week that actually happened and reads the difference out loud. **The gap is the
finding** — not the plan, not the excuse for the gap.

## When to use

Friday afternoon, before the week is forgotten. Also whenever the founder says
they have no time, which is a claim you can check, and usually the claim is
"no time for the bet" while the hours went somewhere specific and nameable.

## Inputs

Read first, in order — house rule 1:

- `week.md` — Monday's `## Blocks`. This is the baseline. Without it there is
  no audit.
- The founder's calendar for the week that just happened — what is actually in
  there, including what was added after Monday.
- `clients/` — delivery hours logged, to tell overrun from drift.
- `week.md` `## Ledger` — the same gap in prior weeks. One week is an anecdote.

## Steps

1. **No plan, no audit.** If `week.md` has no `## Blocks` for this week, stop.
   Do not reconstruct the week from the founder's memory — they will remember it
   generously and inaccurately, and an audit against a flattering memory is
   worse than none. Say so, run `week-plan` Monday, audit next Friday.
2. **Account for every hour.** Assign each actual hour to a planned block or to
   `unplanned`. Do not round in the founder's favour. Unplanned hours get a
   second column: whose priority was that?
3. **Diff per bet.** Planned hours against actual hours, bet by bet. **A bet
   that received under 50% of its planned hours two weeks running is not being
   executed** — that is a finding for the **Strategist**, not a nudge for the
   founder.
4. **Name the largest unplanned consumer, in hours per quarter.** Multiply the
   week by 13. "The standing sync costs 26 hours a quarter" is the only sentence
   that has ever deleted a recurring meeting; "that sync feels unnecessary" has
   deleted none.
5. **Check the recurring meetings against their reason.** For each, name the
   project or relationship that created it. If that project ended, the meeting
   is a ghost — propose deleting it, with the quarterly hours attached.
6. **Refuse the weird week defence.** The founder will say this week was
   unusual. Check the ledger. If the last three weeks were also unusual, the
   week is not unusual — the plan is. Say that, once, without elaborating.
7. **Route the cause.** Delivery overran → **Delivery Lead**. Too much was
   agreed to → **Chief of Staff**. The quarter does not fit the calendar at all
   → **Strategist**. The founder was slow at the work rather than short of hours
   → **Skills Mentor**. Naming the cause is the audit; fixing it is not yours.

## Output

Fill the `## Audit` section of `week.md` — the file `week-plan` wrote on Monday.
Change nothing else in that file; `week-plan` rewrites it and carries the ledger
forward.

    ## Audit
    Planned <h> / actual <h> · unplanned <h> (<n>% of the week)
    | bet | planned | actual | gap |
    |-----|---------|--------|-----|
    | <bet> | <h> | <h> | <±h> |
    Largest unplanned: <what> — <h> this week, <h>/quarter
    Ghost meetings: <name> — created by <project, ended YYYY-MM>, <h>/quarter
    Pattern: <the same gap, N weeks running> | none yet (<N> weeks of ledger)
    Route: <agent> — <the one-line reason>

## Guardrails

Do not propose a new system. The founder does not need a different calendar
tool; they need to know that 40% of last week was unplanned and where it went.

Do not soften the gap into a lesson. It is arithmetic. State it and stop.

Do not re-plan the week here — `week-plan` does that on Monday, with this audit
as an input. An audit that ends in a new plan is a plan nobody audited.

Do not write `goals.md`, `clients/`, or `metrics.md`. Hand off and say so.
