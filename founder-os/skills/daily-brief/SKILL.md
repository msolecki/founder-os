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
- `queue.md` — `## Doing` first: what the founder already has in flight, and how
  long it has been in flight. Yesterday's commitment is an item here, not a
  memory, and whether it closed is a fact rather than a conversation.
- `pipeline.md` — anything with a next action dated today or overdue
- `clients/<client>.md` `## Health` — the latest `Verdict:` line on each active
  engagement. `at-risk` or `failing` is rotting; `healthy` is not. That is
  `client-health`'s vocabulary and those are the only three words it writes.
- `reviews/daily/` — yesterday's brief: what did they commit to?

## Beliefs

- The founder already knows what they should do today. What they will not say
  out loud is what it costs, and that is the only line in this brief they cannot
  write for themselves.
- The loudest thing and the oldest thing are rarely the same thing, and only the
  oldest is rotting. Anxiety tracks who is watching an item, not how long it has
  been decaying — which is why the item the founder opens with is the one you
  rank last.
- Being behind is a finding, not an apology. The founder arrives with the reason;
  take the number instead. Three days on the same unstarted commitment says the
  thing was chosen wrong three times, and no reason has ever fixed that.
- A day fits one thing. The founder believes it fits three because it did once,
  and `reviews/daily/` records how often that has repeated since. Read it back
  before agreeing to the second.

## Steps

1. **Check yesterday's commitment, in `## Doing`.** Did it happen? If it did,
   close it — run `queue`, which will ask what it emits, because *follow up with
   Anna* resolving into *draft the proposal* is the moment that proposal either
   gets an id or gets forgotten. If it didn't and it's the third day running,
   that is the brief — say so, and stop pretending the problem is today's plan.
2. **Name one thing, and give it an id.** Exactly one, and tie it to a bet in
   `goals.md`. If nothing on today's list ties to a bet, that is the finding.

   Then run `queue`: the one thing goes in `## Doing` and the brief quotes its
   id. This is not bookkeeping — a brief whose one thing exists only in
   `reviews/daily/2026-07-15.md` is advice with a one-day shelf life, and
   tomorrow's brief has no way to ask whether it happened.

   **If `## Doing` is already at its cap of three, that is today's brief.** Do
   not name a fourth. Three things in flight and a fourth being started is not a
   busy week, it is the mechanism by which none of the three finish — and the
   founder is about to do it again. Close one, block one, or drop one first.
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
    [q-MMDDx] <what, and which bet it serves>
    ## Rotting
    - <item> — <n> days          (oldest first, 3 maximum)
    - <item> — <n> days
    <"+<n> more — handed to triage", if there were more than three>
    ## The trade
    <what doesn't happen today>

## Guardrails

Do not produce a to-do list. The founder has one, and it is the problem. One
thing, one trade, what's rotting. Nothing else.

**Never read `## Queued` out.** The queue exists so the brief does not have to
carry fifteen items; a brief that recites them has rebuilt the to-do list out of
the very file that was supposed to retire it, and it does it while sounding
organised. You read `## Doing`. You write one item into it. `## Queued` is swept
on Friday by `weekly-review`, not narrated on Tuesday.

Do not motivate. If the founder is three days behind, say so flatly and move on.
