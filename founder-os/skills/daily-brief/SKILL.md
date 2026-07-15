---
name: daily-brief
description: Open the day with the one thing that matters — run every weekday morning before the founder picks their own work
metadata:
  writes:
    - reviews/daily/
---

# Daily Brief

The founder's inbox will happily fill the day with other people's priorities.
This is the fifteen minutes that decides whether today moved the quarter.

## When to use

Weekday mornings, before opening email. Triggered automatically by
`tasks/daily-brief`.

## Inputs

Read first, in order — house rule 1:

- `goals.md` — what this quarter is actually for
- `pipeline.md` — anything with a next action dated today or overdue
- `clients/` — any client marked at-risk
- `reviews/daily/` — yesterday's brief: what did they commit to?

## Steps

1. **Check yesterday's commitment.** Did it happen? If it didn't and it's the
   third day running, that is the brief — say so, and stop pretending the
   problem is today's plan.
2. **Name one thing.** Exactly one, and tie it to a bet in `goals.md`. If
   nothing on today's list ties to a bet, that is the finding.
3. **Name what's rotting.** Overdue pipeline actions, an at-risk client, an
   unpaid invoice. One line each, no editorializing.
4. **Say what today costs.** If the founder does the one thing, what doesn't
   happen? Make the trade explicit — a plan with no cost is a wish.

## Output

Append to `reviews/daily/YYYY-MM-DD.md`:

    # YYYY-MM-DD
    ## The one thing
    <what, and which bet it serves>
    ## Rotting
    - <item> (<how long>)
    ## The trade
    <what doesn't happen today>

## Guardrails

Do not produce a to-do list. The founder has one, and it is the problem. One
thing, one trade, what's rotting. Nothing else.

Do not motivate. If the founder is three days behind, say so flatly and move on.
