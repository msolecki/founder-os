---
name: annual-review
description: Read twelve months of decisions back and score the judgment rather than the outcome — run once a year, from decisions/ and nothing else
metadata:
  writes:
    - reviews/quarterly/
---

# Annual Review

Everyone reviews the year's results. The results are mostly luck, market, and
one client who happened to renew. What compounds is the quality of the
judgments, and the only place those are recorded before the outcome was known is
`decisions/`.

This is the one review that scores the reasoning. It is the reason house rule 3
exists at all — twelve months of logged decisions with falsifiers is an asset
nobody else in a company of one has, and this skill is what cashes it.

## When to use

Once a year, in the same week as Q4 `quarterly-planning` — and before it, so the
year's rules are available when next year's bets are chosen.

## Inputs

Read first — house rule 1:

- `decisions/` — every entry from the last twelve months. This is the review.
  Everything else is context.
- `metrics.md` — the numbers that settle whether each falsifier fired
- `reviews/monthly/` — used for exactly one thing, in step 4: checking whether
  the empty months were actually empty

Do not read the year's `reviews/weekly/`. They record what happened, which is
what this skill is deliberately not scoring.

## Steps

1. **Read every decision entry, oldest first.** Oldest first matters: it puts you
   in the founder's information state at the time, which is the only state in
   which their reasoning can be fairly judged.
2. **For each, check the falsifier.** It named an observable, a threshold, and a
   date. Did it fire? Settle it with a number from `metrics.md`, not a memory.
3. **Score every decision into one of four quadrants — process, then outcome.**
   Judge the process on what was knowable at the time, never on what you now
   know.
   - **Good call, good outcome** — nothing to learn. Do not spend the review
     here, even though it is the pleasant part.
   - **Good call, bad outcome** — variance. **Do not fix this.** The most
     expensive mistake available in this review is repairing a sound process
     because it got a bad roll; the repair will look like maturity and will cost
     the founder the process that was working.
   - **Bad call, good outcome** — the dangerous quadrant. It got rewarded, so it
     will be repeated, and it is invisible in every review that scores results.
     Name each one explicitly. This quadrant is why this skill exists.
   - **Bad call, bad outcome** — the only quadrant that yields a rule.
4. **Count the falsifiers that fired and changed nothing.** For each decision
   whose falsifier fired: what happened next? The count of "fired, ignored" is
   the founder's actual working relationship with evidence, and it is rarely
   zero. **More than one, and the log is a diary** — the fix is a scheduled check
   against every open falsifier, not a resolution to make better decisions.
5. **Find the missing months.** Which months have zero entries in `decisions/`?
   Check `reviews/monthly/` for those months. If the month was eventful and the
   log is empty, the decisions were made in the founder's head, and this review
   is blind for that stretch. Say how many months of the year are blind.
6. **Write at most three rules, each traceable to a named decision.** "Never
   take a client over 30% of revenue — 2026-03-11, the Acme decision" is a rule.
   A rule with no decision behind it is a resolution, and resolutions do not
   survive February.

## Output

Append to `reviews/quarterly/YYYY-annual.md`.

There is no `reviews/annual/` in `references/ownership.yaml`, and this skill does
not create one. The ownership map changes deliberately, by founder decision —
not because a skill needed somewhere to put something.

    # YYYY — annual review
    ## Scorecard
    <N> decisions reviewed
    - good call / good outcome: <N>
    - good call / bad outcome: <N>   (leave these alone)
    - bad call / good outcome: <N>   (name every one)
    - bad call / bad outcome: <N>
    ## Bad call, good outcome
    - <decision, date> — <why the reasoning was wrong, and why it paid anyway>
    ## Falsifiers that fired and were ignored
    - <decision, date> — <what fired, what changed: nothing>
    ## Blind months
    <N> of 12 — <months with no decisions logged>
    ## Rules for next year
    1. <rule> — from <decision, date>

## Guardrails

Never score on outcome. If a review of the year cannot name one decision that
was correct and lost money, it is not scoring judgment — it is reading the P&L
back with adjectives.

Never edit a decision entry to match what is now known. The entries are evidence
precisely because they were written before the answer arrived, and `decision-log`
forbids it for the same reason.

Do not review the year's feelings. They are in `reviews/monthly/`, they are real,
and they are not admissible here.

More than three rules is zero rules. Cut.
