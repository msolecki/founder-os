---
name: offer-design
description: Turn what the founder does into an outcome with an explicit boundary — run when work is quoted in hours, when every project is bespoke, or when a prospect can't repeat the offer to a colleague
metadata:
  writes:
    - offer.md
---

# Offer Design

"40 hours of consulting" is a body for rent, and a body is priced against every
other body. An offer is an outcome with a boundary: what the buyer gets, when it
is done, and what is explicitly not in it. The boundary is not fine print — it
is the part that makes the price defensible and gives the **Delivery Lead**
something to enforce six weeks later.

This skill also produces the positioning statement. The statement is an output,
not an exercise; a sentence with nothing decided behind it is a slogan.

## When to use

After `icp-definition` and before `pricing-strategy`. Also when the founder
describes what they do differently every time they're asked, when the
description contains the word "and" three times, or when scope keeps leaking on
delivery — an offer with no boundary cannot leak, because it had no shape.

## Inputs

Read first, in order — house rule 1:

- `offer.md` — the `## ICP` section. If it is empty, stop and run
  `icp-definition`. An offer for nobody is a menu.
- `clients/` — what was actually delivered, and where the hours went that
  nobody paid for. Your exclusions are hiding in there.
- `pipeline.md` — what prospects asked for, and what they didn't understand
- `metrics.md` — which engagement shape made money

## Beliefs

- Nobody has ever bought competence. The buyer purchases a specific state of the
  world they cannot reach alone; the founder's twelve years make that credible,
  they do not make it valuable, and an offer built on the twelve years is
  selling the evidence instead of the claim.
- "We work bespoke" is almost never a service philosophy. It is a decision
  nobody made. Bespoke is the most expensive thing a company of one can sell —
  every proposal is a fresh invention — and the customisation the buyer actually
  valued was about a tenth of it.
- The offer the founder finds boring is usually the one worth selling.
  Interesting work is interesting because it is rare, and rare means there is no
  repeatable shape underneath it. Boredom measures how well-defined the thing
  has become, not what it is worth.

## Steps

1. **Name the deliverable as a noun the buyer already wanted.** "A migration
   plan you can hand a contractor." "A hiring scorecard." If the deliverable can
   only be described as a verb — advising, helping, supporting — the buyer must
   do the work of imagining the outcome, and they will not do that work. They
   will say "this is interesting" and leave.
2. **Define done as an observable condition.** Not a date, not a feeling: the
   thing that is true when the engagement ends. If nobody can state it, the
   engagement cannot end, and an engagement that cannot end is a retainer that
   nobody agreed to.
3. **Ask what the buyer does the day after delivery.** If neither of you can
   answer, the outcome is not real and you have designed a document.
4. **Draw the boundary from the record, not from imagination.** Go to `clients/`
   and list the work that was done and never billed. Those are your exclusions.
   Imagined exclusions miss the real ones every time, because the real ones are
   things the founder considered "just part of it" until it ate a fortnight.
5. **Name the real alternative.** It is almost never another consultant. It is
   do-nothing, a junior hire, or a tool with a free tier. An offer positioned
   against a competitor the buyer was never considering answers a question
   nobody asked.
6. **Make "why us" falsifiable.** "We care about quality" is not a reason — it
   is a claim every competitor makes and no buyer checks. "I have run this
   migration eleven times and can name the three ways it fails" is falsifiable,
   specific, and only this founder can say it.
7. **Run the colleague test.** Can a prospect repeat the offer accurately to
   someone who wasn't on the call? If the offer needs the founder in the room to
   make sense, it is not an offer — it is a conversation, and it does not
   scale past the founder's calendar or survive a referral.

## Named failure modes

- **The résumé.** A list of things the founder can do, offered as an offer. It
  puts the assembly work on the buyer and reads as availability, not capability.
- **The offer built around one live deal.** Designing the offer to fit the
  prospect currently in `pipeline.md` produces a bespoke project wearing an
  offer costume — it will fit exactly one buyer, and you already had them.

## Output

Write to `offer.md`, replacing the `## Offer` section entirely:

    ## Offer
    Updated: YYYY-MM-DD

    ### Positioning statement
    For <ICP> facing <trigger>, <offer name> delivers <outcome> in <duration>.
    Unlike <the real alternative>, <the falsifiable reason it's us>.

    ### What the buyer gets
    - <deliverable, a noun>

    ### Done means
    <the observable condition that ends the engagement>

    ### Not included
    - <exclusion> — if requested: <change order | separate engagement>

    ### Why us
    - <claim> — evidence: <the specific thing that happened>

    ### Colleague test
    Passed YYYY-MM-DD — <who repeated it back, and what they got wrong>

The `### Not included` list is the scope baseline. `proposal-draft` copies from
it and `scope-guard` (Delivery Lead) enforces it. An exclusion that is not
written here cannot be defended later, and "we both understood that wasn't
included" has never once worked.

Changing what the company sells is material. Log it via `decision-log`.

## Guardrails

Never design an offer without an ICP in `offer.md`. Never widen the offer to
capture a prospect who doesn't fit the ICP — that is repositioning by accident,
under deal pressure, which is the worst available condition for the decision.

Do not set the price here. That is `pricing-strategy`, and a price invented
while you are still admiring the offer is a price set on enthusiasm.

Do not describe contract terms — liability, IP assignment, warranty. Naming what
is *delivered* is yours; what is *owed* is a lawyer's. See `guardrails`.

If the honest finding is that the current rate cannot support this offer, hand
to the **CFO** for `rate-raise`. You decide what the offer is; they decide
whether the book survives the change.
