---
name: weekly-review
description: Score the week's commitments against what actually happened and name the pattern across weeks — run Friday afternoon, before the week is remembered kindly
metadata:
  writes:
    - reviews/weekly/
---

# Weekly Review

The founder already knows how their week went. What they cannot see is the
fourth consecutive week it went that way, because they only ever look at one
week at a time. This skill exists to look at four.

## When to use

End of the working week, before the weekend rewrites it. Triggered
automatically by `tasks/weekly-review`.

Also whenever the founder says "this week was unusual" for the third time.

## Inputs

Read first, in order — house rule 1:

- `goals.md` — the quarter's bets, so a week can be scored against something
- `reviews/daily/` — the last five briefs: five committed "one things"
- `reviews/weekly/` — the last four weeks: this is where the pattern lives

## Steps

1. **Score the five, binary.** Each daily "one thing": done or not done.
   "Progressed", "mostly", and "started" are not done. A week's honest score is
   a number out of five, and the number is usually lower than the feeling.
2. **Apply the hit-rate rule.** Below 3/5 for two consecutive weeks, the
   problem is not the week — it is that the one thing is being chosen wrong.
   Say which: too big for a day, or not actually the founder's to do. Do not
   accept a third week of the same diagnosis.
3. **Count the one things per bet.** Which bet in `goals.md` got the most days
   this week, and which got zero? A bet with zero days for three weeks running
   is dead and nobody has said the word. Name it, and hand to the
   **Strategist** for `kill-or-continue`. You do not kill it; you refuse to let
   it stay unmentioned.
4. **Read the last four reviews for the repeated reason.** If "client work took
   over" appears three times, it is not a reason, it is the operating model.
   State it as the operating model and let the founder decide whether they want
   it. This is the finding the week itself can never produce.
5. **Commit one thing for next week.** Week-scale, tied to a bet, with a
   Friday-observable result. Not three.

## Output

Append to `reviews/weekly/YYYY-Www.md`:

    # YYYY-Www
    ## Committed vs done
    <N>/5 — <one line per miss, no reasons attached>
    ## Days per bet
    - <bet>: <N> days
    ## The pattern
    <what the last four weeks say, not what this week says>
    ## Next week
    <one commitment, and how Friday will know>

## Guardrails

Do not write a diary of the week's events. The founder was there. Everything
here is cross-week or it is filler.

Do not accept a reason. Reasons are what the founder brings; the count is what
you bring. If a reason is real it will show up three weeks running, and then it
stops being a reason and becomes step 4.

Do not average. "A mixed week" is not an output — 2/5 is.
