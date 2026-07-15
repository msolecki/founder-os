---
name: proposal-draft
description: Draft a proposal with scope, price, exclusions and an expiry date — run when a qualified deal is ready to close, never before capacity-check, and never with an empty exclusions list
metadata:
  writes:
    - pipeline.md
---

# Proposal Draft

Four things make a proposal: scope, price, exclusions, expiry. Founders write
the first two beautifully and skip the last two, and then spend the project
paying for it.

**The exclusions are the point.** They are not fine print and they are not
defensiveness — they are the scope baseline that `scope-guard` (Delivery Lead)
enforces in week five when the client asks for "one small thing". An exclusion
that is not written in this document does not exist. "We both understood that
wasn't included" has never once worked, on anyone, in the history of
professional services.

## When to use

When a deal is qualified — amount named, decision-maker identified, trigger
real — and the next action is to propose. Not before `capacity-check`.

## Inputs

Read first, in order — house rule 1:

- `pipeline.md` — this deal: what they asked for, in their words, on the call
- `offer.md` — the offer, the `### Not included` list, the price, and the floor.
  You copy from this file; you do not invent a number in it.
- `clients/` — **the most important input**. Every scope overrun that actually
  happened, and every hour delivered and never billed. This is where the real
  exclusions live.
- Delivery Lead's `capacity-check` — the start date. You do not know what is
  free, and guessing commits the founder to work they cannot deliver.

## Steps

1. **State their problem in their words, first.** Quote the call. A proposal
   that opens with the founder's methodology is a brochure, and the buyer is
   checking whether you understood them before they check anything else.
2. **Write "done means" as an observable condition.** Copy it from `offer.md`.
   If this proposal cannot say what is true when it ends, it cannot end.
3. **List deliverables as nouns.** What lands in the buyer's hands.
4. **Build the exclusions from the record.** Start with `### Not included` in
   `offer.md`, then add what `clients/` says actually leaked on the last three
   engagements. Exclusions written from imagination miss the real ones, because
   the real ones are the things the founder considered "just part of it" until
   they ate a fortnight.
5. **Apply the exclusion tests. Both of them.**
   - **The plausibility test:** every exclusion must be something this buyer
     might genuinely expect to be included. "We don't do your taxes" is
     decoration and it makes the list look like paranoia rather than clarity.
   - **The cost test:** every exclusion must be something that, if requested
     mid-project and quietly absorbed, would cost more than a day. Under a day,
     leave it out — you are cluttering the document that has to be read.

   **Minimum three exclusions that pass both.** Fewer than three means you have
   not read `clients/`, because no three engagements in history leaked less
   than three ways.
6. **Give every exclusion a consequence.** What happens if it is requested
   anyway: a change order at a stated rate, or a separate engagement. An
   exclusion without a consequence is a complaint written in advance — it tells
   the client you'd rather not, which they will read as "he'd rather not, but
   he will".
7. **Set the expiry.** 14 days. A proposal with no expiry is a free option the
   buyer holds indefinitely, and it is the single reason deals sit for six weeks
   and then reopen at a worse price. Say what changes after the date — the
   price, the start date, or both. Then honour it; an expiry the founder
   silently extends has taught the buyer that the founder's words are decorative.
8. **State payment shape.** Deposit before start, stages after. The deposit is
   not about cash flow — it is the first evidence that this buyer can actually
   execute a decision internally.
9. **Ask the question the founder avoids: what did the last project cost in
   unbilled hours — and is that thing excluded here?** If it is not, this
   proposal is a plan to donate the same fortnight twice.

## Named failure modes

- **The proposal as brochure.** Pages of methodology, credentials and process
  diagrams, with the scope on page seven. It is written to reassure the founder,
  not to be signed.
- **The silent exclusion.** The founder knows something isn't included, decides
  the client "obviously understands", and doesn't write it. This is the origin
  of most scope disputes and every one of them was preventable here.

## Output

The proposal document goes to the founder to send. This skill does not send.

Its structure, in order:

    1. Your problem — in their words, quoted from the call
    2. Done means — <the observable condition>
    3. Included — <deliverables, as nouns>
    4. Not included — <exclusion> → if requested: <change order at <rate> | separate engagement>
    5. Price — <amount from offer.md>, <deposit>, <stages>
    6. Dates — start <from capacity-check>, delivery <date>
    7. This proposal expires YYYY-MM-DD. After that: <what changes>

Record it in `pipeline.md` under `## Live`:

    ### <Prospect> — proposal sent YYYY-MM-DD
    Scope: <one line> | Price: <amount> (offer.md YYYY-MM-DD) | Expires: YYYY-MM-DD
    Exclusions — verbatim, the baseline scope-guard rules against:
    - <exclusion, in the words the client will read> → if requested: <change order at <rate> | separate engagement>
    - <exclusion> → if requested: <...>
    - <exclusion> → if requested: <...>
    Start date confirmed with Delivery Lead: <yes | NO — do not send>
    Next action: <what the founder does> — YYYY-MM-DD

**Write the exclusions out in full. Never a count.** This block is the handoff:
when the deal closes, `pipeline-review` carries these lines into `## Won`, where
the **Delivery Lead** rules against them for the life of the engagement. A count
is worse than nothing — `scope-guard` cannot check whether an ask is named in the
integer 3, but the integer tells it a baseline exists, so it never triggers the
one escape hatch it has and rules from vibes instead. Write these lines so they
can be enforced in week five by someone who was not on the call and has only this
file.

## Guardrails

**Refuse to produce a proposal with an empty exclusions list.** Not a warning —
a refusal. It is the one output of this skill that cannot be added later, and a
founder who is told to "add exclusions if you like" never does.

Never negotiate on price inside the proposal. The concession ladder in
`offer.md` is scope, not price. If the founder wants a discount, that is the
**CFO's** call and it goes in `decisions/` with what it repriced.

Never promise a start date without `capacity-check`. Never quote a price not in
`offer.md`.

No contract terms — liability, indemnity, IP assignment, termination,
jurisdiction. Scope and price are commercial and yours; what is *owed* when
things go wrong is a lawyer's. Name the clause that concerns you, say a lawyer
should read it, log it in `decisions/`. See `guardrails`.
