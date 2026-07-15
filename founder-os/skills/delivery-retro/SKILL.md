---
name: delivery-retro
description: Compare estimated against actual hours within five days of shipping — run at every project end, before memory replaces the timesheet
metadata:
  writes:
    - clients/
---

# Delivery Retro

Every rate the founder charges is downstream of an estimate they made once and
never checked. This is where the checking happens. It is also the only skill in
this company that reliably changes the price, which is why it gets skipped.

## When to use

Within five days of shipping. After five days the founder remembers a story about
the project, and the story is always kinder than the timesheet. Also at any
milestone that ran more than a week over.

## Inputs

Read first, in order — house rule 1:

- `clients/<client>.md` — the estimate, the scope log, the absorbed asks
- `pipeline.md` — the proposal: what was quoted, in hours and in money
- `metrics.md` — the target effective rate to measure against

## Steps

1. **Recover the actual hours, including the ones nobody billed.** The estimate
   covered delivery. The actual includes sales calls before the deal, scoping,
   revisions, the "quick calls", the Slack answered on a Sunday, and the invoice
   chase. Leave those out and the retro proves the estimate was fine — which is
   exactly how the rate stays broken for another year.
2. **Compute variance per phase, not per project.** "20% over" is unactionable.
   "Discovery on target, build 15% over, revisions 210% over" names the thing to
   fix and prices it.
3. **Answer the one question that matters: was it estimating, or was it scope?**
   These have different owners, and confusing them is precisely why the same
   overrun repeats.
   - **Scope** → the work grew and nobody charged for it. That is a `scope-guard`
     failure and it belongs to the Delivery Lead. Fix the boundary, not the
     estimate.
   - **Estimating** → the work was correctly bounded and simply took longer than
     quoted. Then `offer.md` is mispriced, and that is the **Positioning
     Advisor's** file.
4. **Apply the thresholds:**
   - under 10% over → noise. Do not act, do not reprice, do not hold a meeting
     with yourself about it.
   - 10–20% over → this project. Note it, move on.
   - **over 20% over → structural.** Something in the estimate is systematically
     wrong, not unlucky.
   - **the same phase over on three consecutive projects → that phase is
     mispriced.** Stop calling it bad luck. Three is not a coincidence; it is the
     actual cost of the work, and the founder has been paying it out of their own
     margin every time.
5. **Hand the numbers to their owners, explicitly.** The effective rate goes to
   the **CFO** for `metrics.md` — this skill produces the number, it does not
   write it. The repricing goes to the **Positioning Advisor** for
   `pricing-strategy`. A retro that ends in `clients/` and never reaches the
   price is a diary entry.

## Output

Append to `clients/<client>.md` under `## Retro`:

    ### YYYY-MM-DD — <project>
    Quoted: <n> h / <amount>
    Actual: <n> h  (delivery <n> + sales <n> + revisions <n> + unbilled <n>)
    Variance: <n>% — worst phase <phase> at <n>%
    Cause: <scope | estimating>
    Effective rate: <amount>/h vs target <amount>/h
    Repeat: <n>th consecutive project over on <phase>
    Handoff: <CFO — metrics.md> / <Positioning Advisor — pricing-strategy>

## Guardrails

Do not write `metrics.md`. The effective rate is the CFO's number even though
this skill is where it is born. Hand it over with the arithmetic attached so they
are not re-deriving it.

Do not run the retro on projects the founder enjoyed and skip the ones they
didn't. The enjoyable projects are exactly where the unbilled hours hide, because
nobody counts the hours they liked spending.

No blameless-retro theatre. There is one person in this company. The question is
what the estimate got wrong, not whether anybody feels bad about it, and the
softened version of this conversation is why the rate has not moved in two years.
