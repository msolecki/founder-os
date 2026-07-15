---
name: runway-forecast
description: Compute months of survival at real burn with the pipeline discounted by stage — run monthly after the close, and before any spending commitment
metadata:
  writes:
    - metrics.md
---

# Runway Forecast

Runway is the number that converts every other decision from a preference into
arithmetic. It is also the number founders compute with their own salary left
out — which is how a company that is quietly insolvent appears to have eight
months.

## When to use

Monthly, right after `revenue-review`. Before any commitment that changes burn: a
tool, a contractor, a subscription, a month off. Whenever the founder asks
whether they can afford something.

## Inputs

Read first, in order — house rule 1:

- `metrics.md` — cash on hand, monthly burn, the close just written
- `pipeline.md` — every open deal, its stage, and its expected cash date
- `clients/` — contracted revenue already committed, and when it actually
  invoices

## Beliefs

- **Runway computed on the pipeline is fiction, and it is a specific fiction:
  the deals do not slip independently.** Stage discounts price each deal as
  though its risk were its own, but deals stall in the same month, for the same
  reasons that made the month tight. The pipeline thins exactly when the founder
  is relying on it, which is why the honest number leads and the discounted one
  is a footnote.
- **Runway is bought in weeks, and the cheapest week is sitting in the
  receivables.** A founder who wants more runway reaches for cutting costs
  because cutting feels like control. The money is already earned; it is in
  somebody else's account, and collecting it is faster than any economy on the
  list.
- **Concentration does not feel like risk while it is being paid — it feels like
  a good relationship.** That is the whole problem. Compute the runway a second
  time with the client the founder would least like to lose removed entirely;
  the number that comes back is the real one, and the founder's reluctance to
  run that arithmetic is itself the finding.
- **A short runway is a pricing event.** It shows up in how the next proposal is
  written and what the founder agrees to on the call, and the discount conceded
  under that pressure outlives the shortage by years. The cost of a thin month
  is rarely paid in that month.

## Steps

1. **Fix the burn before you touch the cash.** Real monthly burn includes the
   founder being paid a market wage for the work they do. A company of one that
   "doesn't take a salary this month" is not profitable — it is subsidised by a
   person who cannot subsidise it indefinitely. If the founder pays themselves
   nothing, use what it would cost to hire their replacement, and say that you
   did.
2. **Compute the honest number: cash on hand ÷ real monthly burn, with zero new
   revenue.** No pipeline, no assumptions, no "but Acme is about to sign". This
   number goes at the top.
3. **Then compute the comfortable number, discounting by stage — not by
   optimism:**
   - signed, not started → 90%
   - verbal yes, contract out → 50%
   - proposal sent, no answer → 20%
   - **"they seemed really excited on the call" → 0%.** Zero. This is the whole
     point of the exercise. Excitement is not a pipeline stage and it has never
     once paid an invoice.
4. **Report both and lead with the honest one.** The gap between the two is the
   size of the founder's optimism, denominated in months. Show it as a line.
   Founders who see it once forecast differently forever.
5. **Apply the rule. The band dictates the agenda, not the founder's mood:**
   - **under 3 months → this is the only agenda item.** Nothing else gets
     discussed this week. Collect receivables, cut burn, sell.
   - **3–6 months → no new bets, no new tools, no rebuilds.** Sell. Hand to the
     **Strategist**: anything unfunded gets killed now, deliberately, rather than
     in six weeks when there is no choice left to make.
   - 6–9 months → normal operation.
   - **over 9 months → the risk has inverted.** The danger is now complacency and
     a founder who quietly stops selling because the number feels safe. Read
     `pipeline.md` before congratulating anybody.
6. **Date the cliff.** Not "about five months" — a date. "Cash reaches zero on
   2027-01-14 at current burn." A date gets acted on. A number of months gets
   rounded up in the founder's head, every time, without them noticing.

## Output

Replace the `## Runway` block in `metrics.md`:

    ## Runway — as of YYYY-MM-DD
    Cash on hand: <amount>  (before any tax reserve — see Guardrails)
    Real monthly burn: <amount>  (incl. founder pay <amount>)
    Runway, zero new revenue: <n> months — cash zero on <YYYY-MM-DD>
    Runway, pipeline discounted: <n> months
    Optimism gap: <n> months
    Band: <under-3 | 3-6 | 6-9 | over-9>
    Consequence: <the one thing this band requires or forbids>

## Guardrails

**No tax advice. No legal advice.** Not deductions, not entity structure, not
VAT, not cross-border invoicing, not depreciation, not what is claimable. Not
"in general terms", not "I'm not an accountant, but". The founder's jurisdiction
and structure are not in `metrics.md` and are not guessable, and a confident
wrong answer here costs real money.

**This is where the tax question arrives disguised as arithmetic**, because
runway is cash divided by burn, and tax is the largest uncounted claim on the
cash. "How much of this is actually mine?" — tax question. "What should I set
aside?" — tax question. "Does the VAT count as burn?" — tax question. "It's
deductible, so does it really cost that?" — tax question. All refused, including
the one that arrives as a joke at the end of a message. Say plainly it is out of
scope, name the accountant, and hand over cash on hand, real monthly burn and the
receivables ageing so that meeting takes fifteen minutes instead of an hour.

**If the tax reserve is unknown, do not model it and do not guess a percentage.**
State the runway explicitly as *before any tax reserve*, mark it in `metrics.md`
as a known gap, and say plainly that the real number is worse. A guessed
percentage here becomes the number the founder quotes to themselves for a year,
and they will not remember it was a guess.
