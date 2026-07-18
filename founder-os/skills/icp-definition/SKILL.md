---
name: icp-definition
description: Narrow who this company serves until the definition excludes real, nameable people — run before any pipeline or content work, and whenever the founder describes their buyer in adjectives
metadata:
  writes:
    - offer.md
---

# ICP Definition

An ICP that excludes nobody is a mailing list. The founder already knows they
serve "businesses that need help" — that sentence has never disqualified a
single bad-fit call, which is the only job an ICP has.

## When to use

Before `offer-design`, always — an offer for nobody in particular is a service
menu. Also when the founder describes their buyer with adjectives ("ambitious",
"values quality", "gets it"), when every project is bespoke, or when a prospect
says "this is interesting" and vanishes. Run when `/founder-os-init` hands off
here — it is the first stop after the charter.

## Inputs

Read first, in order — house rule 1:

- `clients/` — everyone who actually paid. This is the ICP; the rest is
  hypothesis. Note per client: margin, days-to-payment, scope overrun.
- `offer.md` — the current ICP, if any, and when it was last touched
- `pipeline.md` — who is currently in play, and who has been in play too long
- `metrics.md` — effective rate per engagement, if the CFO has it
- `ingestion-gate` — its third named failure mode is *the ICP from one flattering
  call*, and it names this file. An attribute out of `clients/` is first-hand and
  needs no gate; an attribute out of something a prospect said on a call is the
  gate's job, and the answer is almost always that it does not enter.

## Beliefs

- Being wrong about the ICP costs less than being vague about it. A narrow
  definition that turns out wrong is discovered within a quarter and corrected;
  a broad one is never wrong and never right, and it survives for years
  precisely because nothing can falsify it.
- An ICP is a set of situations, not a set of people. The same buyer is in it in
  March and out of it in June, and nothing about them changed except what broke.
- Two thirds of revenue from one segment is not concentration risk to be
  diversified away. It is the answer, arrived at by accident — and the founder
  is about to spend a year escaping it.
- Until it costs a live, payable deal, it is not a definition, it is a
  paragraph. The founder finds out the ICP is real on the day they say no to
  money they could have taken.

## Steps

1. **Rank the paid clients by three numbers, not by feeling.** Margin,
   days-to-payment, hours over scope. The founder's favourite client and their
   most profitable client are frequently different people, and only one of them
   is the ICP.
2. **Ask the question they are avoiding: which client would you not take
   again — and what did you know about them before you signed?** The answer is
   the ICP, stated as an exclusion. Founders cannot describe their buyer in the
   abstract and can always describe them by example.
3. **Extract attributes that are checkable before the first call ends.** "Has
   two to five engineers and no product manager" is checkable. "Values quality"
   is not — nobody self-identifies as valuing garbage, so it disqualifies
   nobody. Every attribute you keep must survive this test or it comes out.
4. **Name the trigger.** Not who they are — what just happened to them. Buyers
   do not purchase because they match a firmographic; they purchase because
   something broke, someone left, or a date is coming. An ICP without a trigger
   explains the audience but not the timing, and timing is the sale.
5. **Test the exclusion.** The founder names three real companies, by name, that
   fit and would take a call — and one that clearly does not. If they cannot
   name three, the ICP is abstract. If they cannot name the one that doesn't
   fit, the ICP is a mailing list and you have not finished.
6. **Check it against the book.** Your ICP must exclude at least one client you
   have actually invoiced. A definition that retroactively welcomes everyone who
   ever paid has described the past, not chosen a future.
7. **Write it, with the evidence attached.** Every attribute cites the client it
   came from. An ICP with no client behind it is a market opinion, and this
   company does not trade in those.

## Named failure modes

- **The demographic.** "B2B SaaS, 10-50 people, Series A" predicts nothing. Two
  companies matching it perfectly buy differently because one just lost their
  lead engineer and the other didn't. Firmographics are how you find them, not
  why they buy.
- **The wish.** An ICP written from who the founder wants to work with rather
  than who paid on time. It always describes larger, more prestigious clients
  than the book contains, and it is always adjectives.

## Output

Write to `offer.md`, replacing the `## ICP` section entirely:

    ## ICP
    Updated: YYYY-MM-DD

    ### Who
    <one sentence, no "and">

    ### Trigger
    <what just happened to them that makes this urgent now>
    (per <person, role at client>, <channel>, YYYY-MM-DD)

    ### Attributes — all checkable before the first call ends
    - <attribute> — I check it by: <the observable> — from: <client, who paid>

    ### Not this
    - <named exclusion> — because: <what it cost last time, from clients/>

    ### Evidence
    - <client> — fits/doesn't — margin <n>, paid in <n>d, <n>h over scope
    - Fits, by name: <company>, <company>, <company>
    - Clearly doesn't: <company>

Two provenance slots, and they are different. **Attributes cite a client, not a
speaker** — step 7 already says every attribute names the client it came from,
and that client is in `clients/` with invoices behind them, which is first-hand
and outranks anything anyone said. An attribute whose `from:` is a prospect
rather than a payer has failed the gate and the Guardrails below, and the fix is
deletion, not a stamp.

**The trigger is the one thing here that can only come from a mouth.** Nothing in
`clients/` records what broke the week before they called; a person told the
founder that, once, on a date. So it is stamped. Unstamped, a trigger from a
2024 client reads as a description of today's market — and every outreach,
proposal and post downstream quotes `## ICP` as though it were current. The stamp
is what makes it possible to notice the trigger expired.

Narrowing the ICP is material and irreversible in practice — it changes what
gets sold, published, and pursued for a quarter. Log it via `decision-log`
(Chief of Staff), including what would change your mind.

## Guardrails

Never write an ICP from market knowledge, category convention, or what similar
companies target. It comes from `clients/`. If you find yourself producing a
segment you have never invoiced, you are guessing with confidence, which is the
one thing house rule 2 exists to stop.

If `clients/` is empty, say so and label the output a **hypothesis with a test
date** — not a finding. A pre-revenue ICP is a bet, and dressing it as evidence
poisons every downstream decision that quotes it.

Do not write `pipeline.md` or `content.md`. If the new ICP disqualifies live
deals, that is the Pipeline Coach's call to make, and you hand them the list.

Before any repositioning that abandons an existing client base, hand to the
**Board Member** first. That decision deserves a hostile reader, not agreement.
