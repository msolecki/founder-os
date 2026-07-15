---
name: profitability-analysis
description: Rank every client by effective hourly rate to find where the margin dies — run quarterly, before any renewal, and before agreeing to more of the same work
metadata:
  writes:
    - metrics.md
---

# Profitability Analysis

Aggregate profitability is a lie of averages, and it exists to be reassuring.
This skill breaks it apart per client, and the finding is reliably unwelcome:
**the client the founder likes most is usually the worst-paying one.** Rank by
effective rate, not by how the calls feel.

## When to use

Quarterly. Before every renewal. Before agreeing to more of the same kind of work
— "we should do more of these" is a claim about margin, and it is almost always
made from a memory of the mood rather than the timesheet.

## Inputs

Read first, in order — house rule 1:

- `metrics.md` — collected revenue per client, the target rate
- `clients/` — every hour logged per engagement, including the absorbed scope
  `scope-guard` counted and the unbilled hours `delivery-retro` recovered
- `offer.md` — what this work was supposed to be priced at
- `ingestion-gate` — the ranking is arithmetic and needs no gate, but its
  denominator is not. An hour logged as it happened is first-hand; an hour the
  founder reconstructs at quarter end is a recollection, and the gate's own rule
  is that derived claims inherit their weakest input. An effective rate computed
  from remembered hours is a remembered rate however many decimals it has.

## Beliefs

- **Margin dies between the work, not in the work.** The delivery hours land
  roughly where they were estimated. It is the waiting, the re-briefing, the
  chasing and the fourth re-reading of a thread that empty the rate — none of
  which appear in the deliverable, and all of which belong in the denominator.
- **An underpriced client is not a client, it is a template.** The founder quotes
  the next similar project from what they charged this one, so a bad rate
  propagates to every engagement that resembles it. This quarter's margin is the
  small part of the cost.
- **Revenue per client is a vanity ranking, and the founder's memory uses it
  instead of this one.** The biggest logo is usually mid-table on rate and gets
  defended anyway, because losing it would be visible to everyone the founder
  knows. Losing margin is visible to nobody — which is precisely why margin is
  what gets lost.
- **Efficiency is the wrong lever and it is the first one founders reach for.**
  A client at 55% of target is not fixed by faster work: the same client served
  twice as fast still costs more to serve than they pay, and the founder now has
  less time in which to notice.

## Steps

1. **Build the denominator honestly. This is the entire skill.** Hours per client
   include delivery, the sales hours spent winning them, scoping, revisions,
   absorbed scope, the quick calls, and admin on their account. Amortise the sales
   hours across the engagement's life. A client won in one call and a client won
   over eleven hours of pursuit are not the same client at the same price, and
   only one of them is worth repeating.
2. **Effective rate per client = collected revenue ÷ all-in hours.** Collected,
   not invoiced. An unpaid client has an effective rate of zero, and the ranking
   should say so rather than flattering them with an invoice number.
3. **Rank, worst first. Never aggregate.** The average conceals precisely the
   client you are hunting. Publish the ordered list.
4. **Cross the ranking against the founder's affection.** Ask them to name their
   favourite client *before* you show the table. The correlation is inverse often
   enough to be a diagnostic, and there is a mechanism behind it, not a
   coincidence: pleasant clients receive more free hours, because refusing a
   pleasant person costs more than refusing an unpleasant one. The founder is
   buying a nice relationship with unbilled time. That may be a perfectly good
   purchase — it should be a conscious one, with the price written down.
5. **Find the hours-to-revenue asymmetry.** Per client: % of total hours against
   % of total revenue. **Any client eating over 25% of hours for under 15% of
   revenue is not a margin problem, it is *the* margin problem.** Fixing that one
   client is worth more than every efficiency the founder is currently
   contemplating, combined.
6. **Apply the rule:**
   - **under 60% of target rate → fix or fire within 60 days.** Fix means reprice
     at renewal or cut the absorbed scope. Nothing else counts as a fix — "be more
     efficient" is not a fix, it is the same client and a more tired founder.
   - 60–90% of target → reprice at renewal. No drama, no meeting.
   - **bottom of the table for two consecutive quarters after a fix attempt** →
     hand to `rate-raise` for the arithmetic, then to the **Chief of Staff** to
     log the decision. A fix that has failed twice is not a fix, it is a habit.

## Output

Replace the `## Profitability — YYYY-Qn` block in `metrics.md`:

    ## Profitability — YYYY-Qn  (before tax; see Guardrails)
    | client | collected | all-in h | hours from | eff. rate | % of target | % hours | % revenue |
    |---|---|---|---|---|---|---|---|
    | <worst first> | | | <logged \| reconstructed YYYY-MM-DD> | | | | |
    Target rate: <amount>/h
    Below 60% of target: <clients>
    Asymmetry flag: <client> — <n>% of hours for <n>% of revenue
    Founder's stated favourite: <client> — ranked <n> of <n>
      (per the founder, asked before the table, YYYY-MM-DD)
    Action: <fix | fire | reprice> — <client> — by <YYYY-MM-DD>

Two slots, and neither is decoration. **`hours from` is the stamp that matters**,
because step 1 says the denominator is the entire skill and the denominator is
the one column that can be fiction. `logged` means the hours were recorded while
the work happened. `reconstructed` means the founder counted backwards at quarter
end, and a reconstructed denominator is systematically too small — nobody
remembers the fourth re-reading of a thread, which is exactly the time the
Beliefs above say kills the margin. So a `reconstructed` row's effective rate is
an upper bound and reads as one, and the fix is not a stamp, it is logging next
quarter.

`Founder's stated favourite` is stamped `asked before the table` because that
ordering is the whole diagnostic in step 4. Asked afterwards it is worthless —
they have seen the ranking — and six weeks later nothing but the stamp
distinguishes the two.

## Guardrails

**No tax advice. No legal advice.** Not deductions, not entity structure, not
VAT, not cross-border invoicing, not depreciation, not what is claimable. Not
"in general terms", not "I'm not an accountant, but". The founder's jurisdiction
and structure are not in `metrics.md` and are not guessable, and a confident
wrong answer here costs real money. Profit before tax is the only profit this
skill computes, and the output says so on its own line — a per-client margin that
silently implies an after-tax number is worse than no number.

Nor legal. Whether a client can be dropped mid-contract, what notice is owed,
what the termination clause actually permits: a lawyer reads that, not you. Name
the clause that concerns you, say a lawyer should read it, and log the concern in
`decisions/`.

Do not print an aggregate margin as a summary line. Somebody will quote it, and
the entire finding dies the moment they do.

Firing a client is the founder's decision. You produce the ranking and its
consequence; the **Chief of Staff** logs whatever they choose.
