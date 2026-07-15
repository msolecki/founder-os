---
name: pricing-strategy
description: Price the offer against the buyer's outcome and their real alternative, and name the founder's walk-away floor in writing before any negotiation starts
metadata:
  writes:
    - offer.md
---

# Pricing Strategy

Hours are what the work costs the founder. They are not what the outcome is
worth to the buyer, and the buyer has never once asked to see the timesheet.

The output of this skill that matters most is not the price. It is the **floor**
— the number below which the answer is no — written down before a prospect is
in the room. A floor invented during a negotiation is not a floor, it is a mood,
and it always moves in the same direction.

## When to use

After `offer-design`. Also before any proposal at a new number, when the founder
is about to discount to win a deal, and when they have not lost a deal on price
in six months.

## Inputs

Read first, in order — house rule 1:

- `metrics.md` — monthly burn *including the founder's own pay*, cash, and the
  effective rate on delivered work. Note the date; apply the `context-load`
  staleness rule and say the date out loud.
- `offer.md` — the offer, the outcome, and the real alternative
- `clients/` — hours actually spent per engagement, including the unbilled ones
- `pipeline.md` — what prospects have flinched at, and what they didn't

## Beliefs

- Price is a claim about the buyer, not about the work. It changes who shows up
  long before it changes what anyone receives — which is why a rate rise arrives
  as a different clientele rather than as a better margin on the same one.
- Losing on price is cheap. Winning on price is what costs the quarter: a deal
  won on the number arrives with a client who bought a number, and they will
  manage the engagement like someone who bought a number.
- The founder's price is not low because they undervalue their work. It is low
  because a low price is an effective way of not being rejected, and it is
  working. That is why encouragement has never once moved it, and a floor
  written down before the room does.

## Steps

1. **Compute the effective rate on the last three delivered engagements.** Fee
   divided by hours actually spent, unbilled hours included. This is the only
   pricing fact you have; everything else is judgement.
2. **Check whether this is a pricing problem at all.** If the effective rate is
   below target but the list price is not, the leak is scope, not price. Raising
   the price on an engagement that runs 38 hours over just raises the size of
   the thing being overrun. Hand to the **Delivery Lead** — `scope-guard` —
   before touching the number.
3. **Set the floor from the numbers, not the nerve.** Monthly burn (with founder
   pay) divided by realistically billable days per month gives a day the
   business cannot sell below. Then ask the question the founder is avoiding:
   **at what number would you rather have the free week?** That is the floor.
   Write it in `offer.md` where a future, more desperate version of the founder
   will read it.
4. **Anchor on the buyer's alternative and the cost of not acting.** What does
   the outcome pay them — in avoided hires, avoided downtime, a date they hit?
   Estimate it within an order of magnitude and label the estimate. If you
   cannot estimate it at all, you are pricing on hours by default, whatever the
   invoice says.
5. **Apply the flinch rule.** If fewer than one in five qualified prospects
   flinches at the price, the price is too low — you are not being chosen, you
   are being defaulted to. Losing on price occasionally is the evidence the
   price is real.
6. **Build a concession ladder made of scope, never price.** If you must move,
   remove a deliverable. Each rung: what comes out, what the new number is.
7. **Say what the discount teaches.** A 20% discount to win one deal does not
   cost 20% of one deal. It sets the reference price for that client's renewal,
   their referral, and the next three prospects who talk to them. Name that
   cost out loud before the founder decides.

## Named failure modes

- **The comfort price.** Set at the number the founder can say without their
  voice changing. It tracks their confidence, not the buyer's value, and it goes
  up only after a good week.
- **The rescue discount.** Cutting price to save a deal that should have been
  disqualified. It converts a qualification failure into a delivery problem at a
  worse rate.

## Output

Write to `offer.md`, replacing the `## Pricing` section entirely:

    ## Pricing
    Updated: YYYY-MM-DD

    ### Price
    <offer> — <amount> <currency> — <fixed | retainer | deposit + stages>

    ### Floor
    <amount> — below this the answer is no.
    Derived: burn <n>/mo ÷ <n> billable days (metrics.md YYYY-MM-DD)
    Founder's stated walk-away: <amount>

    ### Priced against
    Buyer's real alternative: <the actual one>
    Their cost of not acting: <estimate> [VALIDATE] (per <speaker>, <channel>, <date>
      — validate: <what would settle it>, <owner>, by <date>)

    ### Concession ladder — scope, not price
    1. Remove <deliverable> → <amount>
    2. Remove <deliverable> → <amount>
    Floor reached at rung <n>. Below that: no.

    ### Evidence
    Effective rate, last 3 engagements: <n> vs target <n> (metrics.md YYYY-MM-DD)
    Flinch rate: <n> of last <n> qualified prospects

A price change is material. Log it via `decision-log` — what changed, why, and
what would send it back.

## Guardrails

No pricing without `metrics.md`. If it is more than 30 days old, label every
downstream claim a guess out loud (house rule 2); past 60 days, hand to the
**CFO** for a close first. Pricing against nine-week-old numbers is fiction with
a decimal point.

Never quote a discount. The concession is scope. If the founder overrides you,
that is their right — write what the discount repriced, and move on.

Raising the price on the **existing book** is not yours. That is the CFO's
`rate-raise`: you set what the offer costs, they run the raise against live
clients and the cash consequences of the ones who leave.

No tax, VAT, entity, or cross-border invoicing advice — the price and what is
owed on it are different questions, and the second one is an accountant's. Name
the number to bring them. See `guardrails`.
