---
name: ingestion-gate
description: Tier every claim arriving from outside the workspace — fact, validate, or disregard — before it enters a canonical file, and stamp its speaker and date inline in the line that carries it
---

# Ingestion Gate

Every agent in this company carries this skill. It is house rule 5 — *tier what
comes in, and stamp where it came from* — turned from a preference into a check
that runs before the write.

`state-integrity` asks whether you are allowed to write this file. This asks
whether what you are about to put in it is true. Different questions, and
passing the first says nothing about the second: the CFO owns `metrics.md`
outright, which makes the CFO the only agent in the company able to write a
fiction into the file every other agent quotes.

That is the whole failure mode. A claim arrives soft and conversational — "they
said they'd pay by the 30th" — gets written once as a number, and by the third
agent to read the file it is evidence. House rule 2 demands evidence over vibes.
Without a gate on the way in, house rule 2 is a laundering machine: it does not
stop the vibe, it requires the vibe to be written down first, after which it
outranks anybody's memory of where it came from.

## When to use

Before writing any claim that did not come from the workspace. A call, an email,
a Slack thread, a prospect's enthusiasm, a number the founder recalls from
memory, anything a tool scraped.

The loudest trigger: **you are about to write a number you did not compute, or a
noun phrase you did not observe.** "Keen", "committed", "basically signed",
"they have budget" — each is a claim about someone else's internal state, and
you have never observed one of those in your life.

Not for arithmetic over claims already in the file — that is derived, and
derived lines inherit their inputs (see Guardrails). Not for the founder's
instructions to you; an instruction is not a claim.

## Inputs

- `references/ingestion-gate.md` — the tier definitions, the precedence ladder,
  the worked examples. Read it. This file is the procedure; that one is what the
  procedure operates on, and restating it here would produce a second copy that
  goes stale the first time the ladder changes.
- **The claim, with its speaker.** If you cannot name who said it, when, and to
  whom, you are not at step 1 yet.
- The target file's existing lines on the same subject — for step 6.

## Steps

1. **Name the speaker, the channel, and the date.** "Per the client" is not a
   speaker; clients are companies and companies do not talk. A person did. An
   unattributable claim never reaches FACT, whatever it says.
2. **Ask what the speaker gains if you believe it.** Incentive is part of the
   tier, not a caveat bolted on afterwards. A counterparty describing their own
   situation is handing you a fact about themselves — "we have no budget until
   Q4" costs them the thing they were considering, which is a decent sign it is
   real. A counterparty describing what they will do *for you* is describing a
   sentence they chose to say in a meeting. What you say to win the room is
   positioning, and positioning does not get written down as though it were
   true — that holds for the founder's own deck.
3. **Assign the tier.** FACT, VALIDATE, DISREGARD; definitions in the reference.
   Caught between two, take the lower one. **A flattering number is guilty until
   validated**, and the tell is that you want it to be true.
4. **Assign the weight, separately.** Tier is *is it true*. Weight is *does it
   matter*, and it answers three questions: whose book does this touch — money,
   capacity, reputation; does it touch a live bet in `goals.md`; is it a one-off
   or the third time you have heard it. Weight never moves a tier in either
   direction, and high weight is precisely when the pressure to promote arrives.

   The rule with the threshold: **VALIDATE + touches money or a live bet — it is
   written only with a named validation step**: the artifact that would settle
   it, an owner, a date. A tier label without those three is a rumour wearing a
   badge, and it will be quoted without the badge.
5. **Stamp the provenance inline**, in the line carrying the claim. Not a
   footer, not a header block, not the commit message. Format below. The file's
   mtime tells you when somebody touched the file; it does not tell you when the
   claim was last true, and six weeks from now that difference is the entire
   question.
6. **Read the line you are about to overwrite.** If the file already says
   something else and the sources disagree, rank them on the ladder in the
   reference. The higher-ranked source takes the line; the loser is not deleted,
   it becomes the conflict note attached to it. **Never resolve a conflict
   silently** — a number that changed with no trace is indistinguishable from a
   number that was always wrong. If the conflict crosses an ownership boundary,
   name it and hand to the owner (`state-integrity`). Noticing a conflict does
   not make you the agent who settles it.
7. **DISREGARD does not enter.** Not as a "for context" bullet, not in
   parentheses, not in a file you happen to own. Say it in the session, say why,
   drop it. Writing it somewhere softer is the same routing-around that
   `state-integrity` step 5 forbids, and it fails the same way: next month
   nobody remembers which file was the soft one.

## Output

No file. A passing gate is silent — what it changes is the line you were going
to write anyway.

    FACT       <claim> (per <person, their relationship>, <channel>, <date>)
    VALIDATE   <claim> [VALIDATE] (per <person, relationship>, <channel>, <date>
               — validate: <artifact that settles it>, <owner>, by <date>)
    CONFLICT   <claim> (per <source>, <date>) [CONFLICT: <other source>, <date>
               says <other claim> — <owner> to settle]

An unlabelled line is FACT. The tag is the exception, so the workspace reads
normally and the doubt is what stands out. Every claim carries a stamp whatever
its tier, which gives the rule for everything written before this gate existed:
**a line with no stamp at all is VALIDATE**, however confident it reads.

When it blocks:

    Not written: <the claim>
    Tier: DISREGARD — <the speaker's incentive, in one clause>
    Enters as VALIDATE if: <the observable that would change it>

## Named failure modes

- **The promise as a number.** The CFO turns "we'll pay by the 30th" into a
  receivable in `metrics.md`, and runway is now forecast from a sentence. The
  buyer stating their own intent is FACT about the intent and VALIDATE about the
  money — two claims, and only one of them is theirs to settle. Tier the claim,
  not the sentence.
- **"They're keen."** An adjective with no speaker and no date lands in
  `pipeline.md` under `## Live`, and a deal now exists that nobody sold. Keenness
  is the state of another person's mind. What can be tiered is what they did:
  took the call, named a date, forwarded it to their CTO.
- **The ICP from one flattering call.** A prospect says "this is exactly what
  the market needs" and `offer.md` grows an attribute. n = 1, the speaker was
  being pleasant at no cost to themselves, and the bill arrives as a quarter of
  pipeline aimed at a segment that has never paid. `icp-definition` already
  demands every attribute cite a paid client — that rule is this gate applied to
  one file.

## Guardrails

**Derived claims inherit their weakest input.** An effective rate computed from a
promised payment is a promised rate, however many decimals the arithmetic
produced. Averaging does not launder; it hides the tier inside a number that
looks computed.

**Repetition is not validation.** Hearing it twice from the same speaker is one
claim heard twice. Validation is an artifact — a PO number, a signed line, a
bank credit, a calendar invite that exists.

**The founder is a source, not an exemption.** They are first-hand about their
own intent, and they recall numbers the way everyone recalls numbers. "I want to
raise rates" is FACT; "we bill about 40k a month" is VALIDATE against the
invoices. You do not revert or restamp a line the founder wrote themselves —
house rule 4 and `state-integrity` both still stand — but you do not quote their
undated line back as evidence either. That is precisely how a recollection
becomes a number.

**Consequence never moves a tier.** "The deal dies unless we log it as
committed" is a statement about a deal, not about the truth of a claim. When the
pressure to promote is coming from what the founder needs to be true, you have
found the reason this gate exists, not an exception to it.
