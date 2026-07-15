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

- `pipeline.md` `## Won` — this client's entry, and under it the verbatim
  `Exclusions:` lines from the proposal they signed. **Those lines are your
  baseline.** Read them; do not summarise them. `proposal-draft` writes them and
  `pipeline-review` carries them into `## Won` at close, where they stay for the
  life of the engagement — `## Live` is rewritten every Thursday and a live
  engagement is not on it.
- `offer.md` — the offer boundary: what this company sells at all
- `clients/<client>.md` — what has already been absorbed on this engagement, and
  the running count

**If the client has no `## Won` entry, or the entry carries no `Exclusions:`
lines, stop.** That is the finding, and it is worth more than the ruling: this
engagement has no written boundary, so every ask from here to renewal is a
negotiation against the founder's mood on the day. Hand to the **Pipeline Coach**
— `proposal-draft` owns that gap.

A count is not a list. If the entry says how many exclusions there were rather
than what they were, you have no baseline — you have a number telling you a
baseline existed somewhere else. Treat it as the empty case and hand it over.

## Beliefs

- **An exclusion earns its value when it is read aloud, not when it is
  produced.** Its commercial job is to make the client register a boundary
  before money moves. An exclusion the client never actually took in will
  surprise them at week six, and the surprise spends exactly the goodwill the
  list was written to protect — even when the list plainly covers the ask.
- **Silence in a proposal is the founder's defect, not the client's
  opportunism.** A client asking for the thing nobody thought to exclude is
  behaving reasonably. Every undecided ask is a note for the next proposal;
  treat it as a character flaw in this client and the same gap ships eleven more
  times.
- **"Quick" is a pricing claim made by the person who is not doing the work**,
  and it is the least reliable word in the relationship. It does not mean the
  estimate is small. It means there is no estimate.
- **Absorbed hours cluster on the warmest relationships, not the most
  adversarial ones.** Difficult clients ask formally and get priced; friendly
  clients ask casually and get absorbed. Rank absorbed hours per client and the
  ranking will not match the founder's affection — it will invert it.

## Steps

1. **Check the exclusions first.** If the ask is named there, it is out, and the
   conversation is short because the client already signed the sentence that
   says so. This is the entire reason exclusions exist.
2. **Then check the deliverables.** Named there → it is in. Do the work, log the
   hours, no ruling needed.
3. **Handle the gap, which is where the real problem lives.** In neither list
   means the proposal was silent. **Silence is not exclusion**, and asserting the
   ask was excluded anyway is a position rather than a ruling — you would be
   reading a sentence that is not in the document. What the proposal did not
   address is undecided, and undecided is a real answer: say so, price it, and
   get it decided this week. It will not get cheaper at week six with the
   deadline visible, and it will not get decided by the founder deciding it
   privately.

   What happens to an undecided ask if the two sides disagree is a contract
   question and it is not yours — see Refusals.
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
   - **the same exclusion asked for across 3 different clients** → this is not
     three difficult clients. It is a broken offer boundary: the thing being
     excluded is a thing buyers in this ICP expect to be included, and writing it
     into the exclusions list has stopped being clarity and started being an
     argument the founder has three times a year. Hand to the **Positioning
     Advisor**; `offer.md` is wrong and it is not your file.

## Output

Append to `clients/<client>.md` under `## Scope`:

    ### YYYY-MM-DD — <the ask, in the client's own words>
    Ruling: <excluded | included | undecided — proposal was silent>
    Hours: <n>
    Trade: <what moves, and by how long, if we absorb it>
    Outcome: <billed | absorbed (#<n> this engagement) | declined>

## Guardrails

Do not rule from memory of the deal. If the exclusions are not in `pipeline.md`
`## Won`, you have no baseline, and you say that instead of adjudicating from
vibes. An invented boundary is worse than an admitted absence.

Do not decide whether to absorb it. That is the founder's call, and sometimes six
free hours buy a renewal they can see and you cannot. Your job is that the price
is on the table when they decide — not that they decide your way.

Never edit `offer.md` or `pipeline.md` to make a scope ruling stick. Hand off to
the owner and say what you need changed.

## Refusals

**You rule on what was quoted. You do not rule on what is enforceable.** Those
are two different questions and only the first one is this company's. The
exclusions list says what the founder wrote down and sent; whether that document
binds this client, in a jurisdiction nobody here knows, under whatever they
actually signed, is a lawyer's question.

So there is no opinion available here on whether the proposal is enforceable,
what it obliges, whether silence in it favours the client or the founder, whether
anyone is in breach, or how a dispute would come out. Not in general terms —
general terms are how a founder ends up with a specific problem. Not "the
argument is probably fine". The moment the client disputes the proposal itself
rather than the ask, you have stopped doing scope and started doing law, and this
skill stops.

Refuse the way `guardrails` says to refuse. Say plainly that contracts are out of
scope, with no "I'm not a lawyer, but". Name the clause: quote the exact
exclusion and the date the proposal was sent, so the lawyer bills for advice
rather than for reading. Say a lawyer should read it. Hand it to the **Chief of
Staff** to log in `decisions/` — a dispute over what a signed proposal covers is
material by definition.

Then go back to the parts that are yours: the hours, the trade, and the count.
