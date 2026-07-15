---
name: rate-raise
description: Decide whether the rate rises, by how much, and hand over the script — run when profitability-analysis says the rate is below target, not when the founder feels brave
metadata:
  writes:
    - metrics.md
---

# Rate Raise

Every founder intends to raise their rates. The intention was never the obstacle.
The obstacle is a fear with no number attached — *how many clients leave?* — and
this skill puts the number on it. The number is usually startling enough to make
the raise happen the same week.

## When to use

When `profitability-analysis` shows the effective rate below target for two
consecutive quarters. When the win rate is too high. At the renewal of any client
in the bottom quartile. **Not when the founder feels brave** — bravery is not a
trigger, and it evaporates somewhere between deciding and sending.

## Inputs

Read first, in order — house rule 1:

- `metrics.md` — the per-client effective-rate table from
  `profitability-analysis`, the target rate, collected revenue
- `clients/` — the `delivery-retro` variances: where the estimate broke, and why
- `pipeline.md` — the win rate on proposals sent in the last two quarters
- `offer.md` — what the **Positioning Advisor** says the offer is worth

## Steps

1. **Decide whether, from triggers rather than feelings:**
   - effective rate below target two quarters running → raise.
   - **win rate above 70% → raise.** This one gets argued with, so be direct: a
     founder winning nearly everything they quote is not good at sales, they are
     cheap. **A 100% win rate is a pricing failure wearing the costume of a
     triumph.** The correct win rate is uncomfortable.
   - `delivery-retro` shows the same phase over on three projects → the work costs
     more than the price. Raise. This one is not optional; the founder has been
     funding the gap personally.
2. **Decide how much — and do not do 15%.** A 15% raise costs the founder the
   exact same conversation, the same anxiety and the same risk as 30%, and buys
   half as much. If the conversation is happening at all, have it properly. Start
   from the target rate in `metrics.md`, not from the current rate plus a polite
   increment.
3. **Do the arithmetic that actually makes it happen — churn tolerance:**

       tolerable churn = raise ÷ (1 + raise)

   At +30%: 0.30 ÷ 1.30 = **23% of the book can leave before the founder is worse
   off than today** — and that ignores the hours freed by their leaving, so the
   true tolerance is higher still. Then say it in clients, not percentages:

   > *"Of your nine clients, two can walk and you are still ahead. And the two
   > most likely to walk are the two at the bottom of the effective-rate table —
   > the ones currently costing you money to keep."*

   That sentence is the product of this skill. Everything else is scaffolding.
4. **Sequence it so the risk is real but small:**
   - **new prospects get the new rate immediately.** No conversation exists, no
     relationship is at stake. This is free, and the founder has been postponing
     free.
   - existing clients at renewal, 60 days' written notice.
   - **never mid-project.** Repricing work in flight turns a scope disagreement
     into a dispute, and the CFO does not do disputes.
5. **Hand over the script. One line, no justification:**

       From <date> my rate for <work> is <new rate>. Everything currently in
       flight finishes at the current rate. I'd like to keep working together
       and I'm happy to talk through timing.

   **Do not explain.** An explanation is an offer to have your reasons evaluated,
   and every reason is a door: costs have gone up (then they can come down), the
   work is worth more (says who), demand is high (prove it). The rate is the rate.
   The founder will want to add a paragraph of apology — that paragraph is what
   loses the client, not the number.
6. **Predict the leavers before sending, so silence isn't misread as disaster.**
   Most clients say nothing and pay. Some ask for a phased increase, which is a
   yes with a calendar attached. A few leave, and they cluster at the bottom of
   the ranking. Write down who you predict will go *before* the emails go out,
   then check. It is the cheapest calibration test the founder will ever run on
   their own judgment.
7. **Log it.** A rate change is irreversible in practice — you cannot un-tell a
   client. Hand to the **Chief of Staff** for `decisions/`: what was decided, why,
   and what would change our mind.

## Output

Replace the `## Rate` block in `metrics.md`:

    ## Rate — decided YYYY-MM-DD
    Current: <amount>/h   Effective: <amount>/h   Target: <amount>/h
    Trigger: <2 quarters below target | win rate <n>% | retro variance on <phase>>
    New rate: <amount>/h  (+<n>%)
    Tolerable churn: <n>% of book = <n> of <n> clients
    Predicted leavers: <clients>  (ranked <n>, <n> on effective rate)
    Sequence: new clients from <date>; existing at renewal, 60 days' notice
    Handed to: Chief of Staff for decisions/

## Guardrails

**No tax advice. No legal advice.** Not deductions, not entity structure, not
VAT, not cross-border invoicing, not depreciation, not what is claimable. Not
"in general terms", not "I'm not an accountant, but". The founder's jurisdiction
and structure are not in `metrics.md` and are not guessable, and a confident
wrong answer here costs real money.

**This skill is the single most likely place in the company for a tax question to
arrive**, because a rate raise is a change in income and the founder is halfway to
asking before they notice they have. "Does this push me into a higher band?" —
tax. "Better as salary or dividend?" — tax. "Should I incorporate before this
lands?" — tax and legal at once. "Will VAT registration bite at the new rate?" —
tax. Every one is refused, flatly, including the version that arrives as a joke in
the last line of a message. Say it is out of scope, name the accountant, and hand
over the current rate, the new rate and the projected annual delta from
`metrics.md` so the meeting takes fifteen minutes.

Legal, likewise. Whether the contract permits a mid-term increase, what notice the
agreement requires, whether a client can hold the founder to the old rate: a
lawyer reads the contract. Name the clause, say a lawyer should read it, log the
concern in `decisions/`. Reviewing it "just for the obvious stuff" is exactly the
failure mode — the obvious stuff is not what hurts.

Do not decide what the offer is worth. That is the **Positioning Advisor** and
`pricing-strategy`. You decide whether the business survives at the current rate,
and what the raise does to the book.

Never soften the script to make the founder comfortable. A comfortable script has
a reason in it, and a reason is a negotiation.
