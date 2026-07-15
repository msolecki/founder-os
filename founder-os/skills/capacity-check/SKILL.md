---
name: capacity-check
description: Compute real deliverable hours before accepting work — run before any yes to a new client, an extra deliverable, or a start date
metadata:
  writes:
    - clients/
---

# Capacity Check

The founder has a number in their head for how many hours a week they can
deliver. It is wrong, it is always high, and it is the number they quote start
dates from. This skill replaces it with arithmetic.

## When to use

Before saying yes to anything with hours in it: a new engagement, an added
deliverable, a start date the Pipeline Coach wants to promise a prospect. Also
when three projects are already running and a fourth is being discussed
cheerfully.

## Inputs

Read first, in order — house rule 1:

- `clients/` — every active engagement, its committed hours and remaining scope
- `pipeline.md` — any deal with a start date inside the horizon; those are
  committed hours the founder has not counted yet
- `metrics.md` — last month's actual hours worked, if logged. Actuals beat
  estimates, always.

## Steps

1. **Start from the week, not the month.** Monthly capacity hides the fact that
   work arrives in weeks. 160 hours a month is a fiction. 40 hours next week,
   with two deadlines in it, is a fact.
2. **Subtract the non-delivery load explicitly, line by line:**
   - sales — 6h/week, minimum, non-negotiable. The week the founder stops
     selling is a revenue hole that opens 60 days later, when nobody remembers
     what caused it.
   - admin, invoicing, bookkeeping handoff — 3h/week.
   - context switching — 1h/week per active engagement. Four clients costs four
     hours before a line of work happens.
   - What remains is deliverable. For most solo founders it lands near 22h/week,
     not 40. If your arithmetic says 35, you have forgotten something.
3. **Sum the committed hours.** Remaining scope per engagement in `clients/`,
   divided by the weeks left before its deadline. Add anything in `pipeline.md`
   with a start date inside the window.
4. **Apply the rule:**
   - **over 80% of deliverable hours committed → the answer is no.** Not
     "tight", not "we'd have to push". No. At 80% one sick day is a missed
     deadline and there is nobody to cover.
   - 60–80% → yes, but only with a named slip. Say which client's deliverable
     moves and by how long, *before* the founder answers the prospect.
   - under 60% → capacity is not the constraint. The problem is in
     `pipeline.md` and this is the wrong skill.
5. **Refuse the fantasy number.** "I'll just work the weekend" is not capacity.
   It is a loan against next month at an interest rate the founder never quotes.
   Either they name which of the next four weekends they are giving up — written
   down, in `clients/_capacity.md` — or it does not count. Vague heroism has
   never once repaid.

## Output

Replace the block in `clients/_capacity.md`:

    # Capacity — YYYY-MM-DD
    Deliverable h/week: <n>  (40 − sales 6 − admin 3 − switching <n>)
    Committed h/week: <n> across <n> engagements
    Utilisation: <n>%
    Verdict: <no | yes-with-slip | yes>
    What slips: <client> — <deliverable> — <how long>
    Earliest honest start: <YYYY-MM-DD>

## Guardrails

Do not average across the month to make a yes possible. Work arrives in weeks
and deadlines are in weeks. An average is how a founder ends up 30 hours behind
on a schedule that balanced on paper.

Do not answer whether the work is worth taking. That is the **CFO's** call and
the two answers diverge constantly — a project can be comfortably affordable and
flatly undeliverable at the same time. Route rather than guess.

Do not count hours the founder does not have. If they insist on the fantasy
number, record the real one next to it in `clients/_capacity.md` so the retro
has something to convict with.
