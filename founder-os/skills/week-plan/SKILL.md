---
name: week-plan
description: Turn this quarter's bets into blocks with dates — run every Monday before the week fills itself
metadata:
  writes:
    - week.md
---

# Week Plan

A bet lives in `goals.md` and costs nothing there. It costs something the moment
it has hours attached to a day, which is the only moment it becomes real. This
skill does the arithmetic the founder is avoiding: what the quarter requires
against what the week actually contains.

## When to use

Monday morning, before the first meeting. Triggered automatically by
`tasks/week-plan`. Also whenever the founder says the week "got away from them"
— that week had no plan to get away from.

## Inputs

Read first, in order — house rule 1:

- `goals.md` — the bets. This is the input, not a draft you may edit.
- `clients/` — delivery hours already sold. These are not negotiable this week.
- `week.md` — last week's `## Ledger` and `## Shape`, and last week's `## Audit`
  if `calendar-audit` ran. You are about to overwrite this file: carry both
  forward before you do.
- `metrics.md` — the effective rate, for costing the trade.
- The founder's calendar — what is already booked by other people.

## Steps

1. **Do the arithmetic first, and say it first.** Available hours minus
   committed delivery hours equals free hours. Total the bets' required hours.
   If required > free, the plan is fiction and everything below it is theatre —
   report the shortfall in hours and hand to the **Strategist**. You do not fix
   this by shrinking a bet; bet sizing is theirs.
2. **Book what is already sold.** Delivery hours from `clients/` go in before
   anything else. A week plan that treats sold work as flexible is a plan to
   miss a client deadline and call it a surprise.
3. **Give every bet a block, or name it unfunded.** Walk `goals.md` bet by bet.
   **If a bet gets no block this week, it isn't a bet** — it goes under
   `## Unfunded` with the hours it needed, and if it is still unfunded next
   Monday, it is the Strategist's problem, not a scheduling one.
4. **Put deep work at the hours in `## Shape`.** `energy-audit` recorded when
   the founder actually finishes things. Use those hours. If `## Shape` is
   empty, use 09:00–12:00 as a placeholder and say it is a guess — house rule 2.
5. **Check block size.** Anything under 90 minutes is not a deep work block, it
   is a context switch with a name on it. Merge it or cut it.
6. **Stop at 85% of free hours.** A week planned to 100% has no room for the
   first thing that slips, and the thing that slips is never the client call —
   it is the bet. Above 85%, delete a block; do not shrink all of them.
7. **Name the trade.** What does not happen this week because of this plan?
   A plan with no cost is a wish, and the founder will discover the cost anyway
   — on Thursday, from someone else.

## Output

Rewrite `week.md` entirely. Carry `## Shape` and `## Ledger` forward unchanged,
and prepend one ledger line for the week just ended (from its `## Audit`).
Keep 12 weeks of ledger; drop the oldest. Leave `## Audit` empty — Friday fills it.

    # Week of YYYY-MM-DD
    ## Arithmetic
    Available <h> · Committed delivery <h> · Free <h> · Planned <h> (<n>% of free)
    ## Shape
    Deep hours <hh:mm–hh:mm> · Sequence to avoid <what> (from energy-audit YYYY-MM-DD)
    ## Blocks
    | day | hours | block | serves |
    |-----|-------|-------|--------|
    | Mon | 09:00–11:30 | <what> | <bet from goals.md> |
    ## Unfunded
    - <bet> — needs <h>, got 0
    ## The trade
    <what does not happen this week>
    ## Audit
    ## Ledger
    - YYYY-MM-DD: planned <h> / actual <h> · <bet> <planned>→<actual> · largest unplanned <what> <h> · days off <n>

Every row under `## Blocks` names a bet in the `serves` column. A block that
serves nothing is admin — either it is delivery, or it should not be in the
week.

## Guardrails

Do not re-rank the bets. The **Chief of Staff** ranks priorities and the
**Strategist** picks bets; you take that ranking as given. A Focus Coach who
reorders priorities is a second, worse Chief of Staff.

Do not write `goals.md`. If the week proves the quarter undeliverable, that is a
finding you report to the **Strategist** — reporting it is your job, deciding
what to drop is theirs.

Do not plan a week that requires the founder to be a different person: no 6am
starts they have never once done, no Saturday recovery block. The ledger says
what they actually do.

Do not produce a to-do list. Blocks with days and hours, or nothing.
