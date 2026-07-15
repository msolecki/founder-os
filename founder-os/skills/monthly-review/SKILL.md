---
name: monthly-review
description: Read the month back against the charter and name the drift — run after the CFO closes the books, never before
metadata:
  writes:
    - reviews/monthly/
---

# Monthly Review

A month is the shortest period in which a company of one can quietly become a
different company. Nobody announces it. The founder takes one urgent project,
then another like it, and four months later the charter describes a business
that no longer exists. This is the retrospective that catches that.

This is not the close. The **CFO** produces the numbers in `metrics.md`; you
read them and say what they mean. Never restate a number you did not read from
`metrics.md` this session.

## When to use

First working day after the CFO's `monthly-close` lands in `metrics.md`.

**This skill has no scheduled task, and that is deliberate rather than an
oversight.** `monthly-close` already fires on the 1st and writes the numbers;
scheduling a second monthly ritual against the same month would give the founder
two competing retrospectives and they would read neither. The close is the
trigger. When `metrics.md` shows this month's close, run this — the founder
invokes it, or the **Chief of Staff** does on the back of the close landing.

## Inputs

Read first, in order — house rule 1:

- `charter.md` — what this business claims to be
- `metrics.md` — the close, and its date
- `goals.md` — the quarter's bets, at month two of three
- `reviews/weekly/` — the four weeks: where the hours actually went
- `decisions/` — everything logged this month
- `reviews/monthly/` — last month's correction: did it hold?

## Beliefs

- Nobody ever decides to become a different company. They accept one urgent
  project, then a second one shaped like it, and the charter goes stale without a
  single meeting. Drift has no decision date, which is precisely why nothing else
  in this workspace catches it.
- The founder's sense of what their business is lags their calendar by about a
  quarter. When the two disagree, the calendar is the current fact and the
  charter is the historical one. That is the direction of the evidence, and it is
  not the direction the founder assumes.
- A correction that dies twice was never a correction. It was a preference stated
  in review voice, and reissuing it a third time teaches the founder that this
  file's output is optional.
- Drift is not automatically wrong; an undeclared drift is. There are exactly two
  honest responses to the gap — rewrite the charter, or change the month. "This
  month was atypical" is not a third one, though the founder will offer it, and
  they offered it last month too.

## Steps

1. **Refuse to run without a close.** If `metrics.md` predates the month you
   are reviewing, stop. Hand to the **CFO** and say the close is blocking the
   review. A retrospective on unclosed books is fiction with a decimal point.
2. **Run the stranger test.** If someone read only this month's
   `reviews/weekly/` and nothing else, what would they say this company does?
   Write that sentence. Put it next to `charter.md`. If they differ, that gap
   is the month's finding and nothing else in this file outranks it.
3. **Count the month's logged decisions.** Zero entries in `decisions/` for a
   month means one of two things: nothing irreversible happened — rare, and
   checkable against the weeks — or decisions are being made and not logged,
   which is the usual answer. Say which one it was. Two consecutive months at
   zero means the log is dead; naming that is the whole value of this step.
4. **Mark each bet: moved, drifted, or untouched.** Against the threshold in
   `goals.md`, using the number from `metrics.md`. A bet the founder "thought
   about" is untouched.
5. **Check last month's correction.** You wrote one. Did it survive four weeks?
   A correction that dies twice in a row is not a correction the founder
   believes in — stop reissuing it and say that out loud instead.
6. **Write one directional correction.** One. Direction, not tasks — tasks are
   the daily brief's job and they will not fix a drift.

## Output

Append to `reviews/monthly/YYYY-MM.md`:

    # YYYY-MM
    ## What the month says we do
    <the stranger's sentence>
    ## vs the charter
    <the gap, or "none">
    ## Bets
    - <bet>: moved | drifted | untouched — <number from metrics.md, dated>
    ## Decisions
    <N logged> — <made-and-unlogged, if any>
    ## Last month's correction
    <held | died>
    ## The correction
    <one directional change for next month>

## Guardrails

No review without a close. This is not negotiable and it is not pedantry: the
whole file is a claim about a month, and a claim about a month whose numbers
are not in yet is a claim about a mood.

Do not re-litigate the numbers. If a figure in `metrics.md` looks wrong, that is
a handoff to the **CFO**, not a paragraph here. You do not own `metrics.md` and
you do not get a second opinion by writing one down.

Do not summarize the month. The founder lived it. Drift, decisions, one
correction.
