---
name: scope-guard
description: Rule on whether an ask is inside scope by checking it against the proposal's exclusions — run the moment a client asks for something that was not quoted
metadata:
  writes:
    - clients/
---

# Scope Guard

Scope creep does not arrive as a demand. It arrives as a friendly Slack message
with the word "quick" in it, and the founder says yes because saying no would be
awkward for eleven seconds. This skill makes the eleven seconds cheaper than the
hours.

## When to use

The moment an ask lands that was not in the proposal — "while you're in there",
"one small tweak", "could you also just". Also at every renewal, to count what
was absorbed last time and price it.

## Inputs

Read first, in order — house rule 1:

- `pipeline.md` — the proposal `proposal-draft` wrote for this client. **Its
  exclusions list is your baseline.** Everything else in the document is
  commentary.
- `offer.md` — the offer boundary: what this company sells at all
- `clients/<client>.md` — what has already been absorbed on this engagement, and
  the running count

If the proposal has no exclusions list, stop. That is the finding, and it is
worth more than the ruling: this engagement has no boundary, so every ask from
here to renewal is a negotiation against the founder's mood on the day. Hand to
the **Pipeline Coach** — `proposal-draft` owns that gap.

## Steps

1. **Check the exclusions first.** If the ask is named there, it is out, and the
   conversation is short because the client already signed the sentence that
   says so. This is the entire reason exclusions exist.
2. **Then check the deliverables.** Named there → it is in. Do the work, log the
   hours, no ruling needed.
3. **Handle the gap, which is where the real problem lives.** In neither list
   means the proposal was silent, and **silence defaults to the client's reading,
   not the founder's.** Do not pretend it was excluded — that argument loses, and
   loses the relationship with it. Say it is undecided, price it, and get it
   decided this week. It will not get cheaper at week six with the deadline
   visible.
4. **Price the creep in hours, then in what those hours cost.** "About six
   hours" is not a price. "Six hours, which is Thursday, which moves the Acme
   milestone to the following week" is a price. Get the trade explicitly
   accepted or explicitly declined. The founder absorbing it silently — that is
   the failure this skill exists to prevent, and it costs nothing at the moment
   it happens, which is why it happens.
5. **Count it.** Log every absorbed ask with hours in `clients/<client>.md`. The
   count is the whole value here. One favour is goodwill and the founder is right
   that it buys something. The fourth is an unbilled project the client does not
   know they are receiving, which means it buys nothing at all — you cannot be
   thanked for a gift nobody noticed.
6. **Apply the thresholds:**
   - **3+ absorbed asks on one engagement → stop ruling on scope.** This is a
     repricing conversation now. Hand to the **CFO** for the effective rate
     first, so the founder walks in with a number instead of a grievance.
   - **the same exclusion breached across 3 different clients** → this is not
     three difficult clients. It is a broken offer boundary. Hand to the
     **Positioning Advisor**; `offer.md` is wrong and it is not your file.

## Output

Append to `clients/<client>.md` under `## Scope`:

    ### YYYY-MM-DD — <the ask, in the client's own words>
    Ruling: <excluded | included | undecided — proposal was silent>
    Hours: <n>
    Trade: <what moves, and by how long, if we absorb it>
    Outcome: <billed | absorbed (#<n> this engagement) | declined>

## Guardrails

Do not rule from memory of the deal. If the proposal is not in `pipeline.md`,
you have no baseline, and you say that instead of adjudicating from vibes. An
invented boundary is worse than an admitted absence.

Do not decide whether to absorb it. That is the founder's call, and sometimes six
free hours buy a renewal they can see and you cannot. Your job is that the price
is on the table when they decide — not that they decide your way.

Never edit `offer.md` or `pipeline.md` to make a scope ruling stick. Hand off to
the owner and say what you need changed.
