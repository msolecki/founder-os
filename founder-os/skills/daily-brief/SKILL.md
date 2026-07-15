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
- `clients/<client>.md` `## Health` — the latest `Verdict:` line on each active
  engagement. `at-risk` or `failing` is rotting; `healthy` is not. That is
  `client-health`'s vocabulary and those are the only three words it writes.
- `reviews/daily/` — yesterday's brief: what did they commit to?

## Steps

1. **Check yesterday's commitment.** Did it happen? If it didn't and it's the
   third day running, that is the brief — say so, and stop pretending the
   problem is today's plan.
2. **Name one thing.** Exactly one, and tie it to a bet in `goals.md`. If
   nothing on today's list ties to a bet, that is the finding.
3. **Name what's rotting — at most three, ranked by days.** An overdue pipeline
   action, a client whose `Verdict:` is `at-risk` or `failing`, an invoice past
   terms. One line each with the number of days attached, no editorializing.

   **Ranked by age, not by anxiety.** The loudest item is rarely the oldest, and
   the oldest is the one that is actually rotting — the founder already knows
   about the thing they are worried about, which is precisely why it is not the
   finding.

   **Above three, stop listing and hand the pile to `triage`.** Three is a
   warning; six is wallpaper. A brief carrying six warnings is the to-do list
   this skill exists not to produce: the founder reads two, feels behind, and
   opens email — which is the exact morning this cadence was built to prevent.
   More than three things rotting at once is not a briefing problem, it is an
   unsorted pile, and the **Chief of Staff** has a skill for that.
4. **Say what today costs.** If the founder does the one thing, what doesn't
   happen? Make the trade explicit — a plan with no cost is a wish.

## Output

Append to `reviews/daily/YYYY-MM-DD.md`:

    # YYYY-MM-DD
    ## The one thing
    <what, and which bet it serves>
    ## Rotting
    - <item> — <n> days          (oldest first, 3 maximum)
    - <item> — <n> days
    <"+<n> more — handed to triage", if there were more than three>
    ## The trade
    <what doesn't happen today>

## Guardrails

Do not produce a to-do list. The founder has one, and it is the problem. One
thing, one trade, what's rotting. Nothing else.

Do not motivate. If the founder is three days behind, say so flatly and move on.
