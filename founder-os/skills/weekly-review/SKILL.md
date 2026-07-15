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
by cron if the founder ran `/setup-cadences`; otherwise `/weekly-review`, by hand.

Also whenever the founder says "this week was unusual" for the third time.

## Inputs

Read first, in order — house rule 1:

- `goals.md` — the quarter's bets, so a week can be scored against something
- `reviews/daily/` — the last five briefs: five committed "one things", each with
  the id of the queue item it became
- `queue.md` — all five sections. `## Done` is the week's score with no memory
  involved; the other four are what you are about to sweep.
- `reviews/weekly/` — the last four weeks: this is where the pattern lives

## Beliefs

- A single week is noise. Nothing observed once is a pattern, and everything the
  founder wants to discuss on a Friday happened once. The unit of judgment here
  is four weeks, and the founder has never looked at four.
- Reasons are true and useless. "Client work took over" is accurate every time it
  is said — which is exactly what makes it worthless as an explanation and
  decisive as a count. The third occurrence is not a reason with a pattern behind
  it; it is the pattern, and the reason was always the cover.
- A 2/5 week with a good reason and a 2/5 week with no reason are the same week.
  The founder will spend the review arguing about which one this was. The number
  does not read prose, and neither should you.
- An unusual week is a week. Four unusual weeks are the schedule — and nobody
  imposed it, the founder accepted it one Tuesday at a time, which is also the
  only way it can be changed.

## Steps

1. **Score the five, binary, from `## Done`.** Take each daily brief's id and look
   for it in `queue.md` `## Done`. There or not there — that is the whole method,
   and it is why the queue exists: "progressed", "mostly", and "started" are not
   states this file has, so the argument the founder wants to have on a Friday
   afternoon has nowhere to happen. An id still sitting in `## Doing` on Friday is
   a miss, and it is a miss with a start date attached.

   A week's honest score is a number out of five, and the number is usually lower
   than the feeling.
2. **Apply the hit-rate rule.** Below 3/5 for two consecutive weeks, the
   problem is not the week — it is that the one thing is being chosen wrong.
   Say which: too big for a day, or not actually the founder's to do. Do not
   accept a third week of the same diagnosis.
3. **Count the one things per bet, from the `bet:` field on each `## Done`
   item.** Which bet in `goals.md` got the most days this week, and which got
   zero? A bet with zero days for three weeks running
   is dead and nobody has said the word. Name it, and hand to the
   **Strategist** for `kill-or-continue`. You do not kill it; you refuse to let
   it stay unmentioned.
4. **Read the last four reviews for the repeated reason.** If "client work took
   over" appears three times, it is not a reason, it is the operating model.
   State it as the operating model and let the founder decide whether they want
   it. This is the finding the week itself can never produce.
5. **Sweep the queue. This is the only place the reaper runs.** Run `queue` and
   walk its clocks: 21 days in `## Queued` is a drop, 14 days in `## Blocked` is a
   drop or a promoted blocker, 5 working days in `## Doing` is an item that was
   always a project. Do not carry a reap into next week. A reaper that can be
   postponed is postponed every week for a quarter, and at the end of that quarter
   the founder has two hundred items, a file they avoid opening, and a low-grade
   guilt they will start attributing to themselves rather than to the file.

   Report the counts, not the items — the items are in `## Dropped` with their
   reasons, where anybody who wants them can read them.

   **Five or more drops in one sweep is a step 4 finding, not a good week's
   pruning.** The reaper is working; the intake isn't. The founder is accepting
   obligations they were never going to meet, at a rate of one a day, and the
   queue is now just the place where that gets measured. Say it as the operating
   model and let them decide whether they want it.
6. **Commit one thing for next week, and put it in the queue.** Week-scale, tied
   to a bet, with a Friday-observable result. Not three. Run `queue`: it goes to
   `## Queued` with an id, which means it has 21 days to live, which means if this
   commitment is still unstarted on the third Friday from now the queue will kill
   it and you will not have to have the conversation — the file will have had it
   for you.

## Output

Append to `reviews/weekly/YYYY-Www.md`:

    # YYYY-Www
    ## Committed vs done
    <N>/5 — <one line per miss, no reasons attached>
    Queue: doing <n>/3 | queued <n>/15 | blocked <n> | aged out this sweep <n> | bet:none <n>/<n>
    ## Days per bet
    - <bet>: <N> days
    ## The pattern
    <what the last four weeks say, not what this week says>
    ## Next week
    [q-MMDDx] <one commitment, and how Friday will know>

## Guardrails

Do not write a diary of the week's events. The founder was there. Everything
here is cross-week or it is filler.

Do not accept a reason. Reasons are what the founder brings; the count is what
you bring. If a reason is real it will show up three weeks running, and then it
stops being a reason and becomes step 4.

Do not average. "A mixed week" is not an output — 2/5 is.

**Do not rescue an item from the reaper because dropping it feels harsh on a
Friday.** The founder may re-raise anything, and re-raising is not free: it is a
new item, a new id, a fresh 21 days, and an out-loud claim that they are starting
it inside those three weeks. If they will not say that, it stays in `## Dropped`,
where it is at least honest. And when the same thing is re-raised after ageing out
for the third time — visible in `## Dropped`, which keeps 90 days — it is not a
priority, it is a guilt, and `triage`'s three-strike rule applies: permanent, in
writing, and it does not come back.
