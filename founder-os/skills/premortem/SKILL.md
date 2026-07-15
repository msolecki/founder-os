---
name: premortem
description: Declare the plan already dead six months out and write the story of how it happened — run while the answer can still change the plan
---

# Premortem

It is six months from now. This failed. Not "might have" — did.

The tense is the technique. Asked what might go wrong, a founder produces a risk
register: vague, balanced, and hedged, because part of them is still defending
the plan while listing its flaws. Told the thing is already dead and asked for
the coroner's account, the same founder produces specific causes with dates in
them. Same information, same person. The difference is that the second question
does not let them argue.

## When to use

Before commitment, on anything hard to reverse — the `bet-sizing` runway rule
routes bet-the-company moves here automatically.

While the answer can still change the plan. If the decision is already made and
the premortem cannot alter it, do not run it: it becomes reassurance theatre,
and its only product is a story the founder can tell later about how they knew.

## Inputs

Read first — house rule 1:

- **The plan**, and its judgement date
- `goals.md` — what else is running, competing for the same founder
- `metrics.md` — the numbers the story will have to break
- `reviews/weekly/` — the record of how this founder's plans have actually
  failed before. The boring cause is already in there, in writing.
- `clients/` — revenue concentration, if delivery is in the path

## Beliefs

- The tense is doing the work, not the imagination. "Might fail" produces a
  balanced risk register, because half the founder is still defending the plan
  while listing its flaws; "did fail" produces causes with months attached. Same
  person, same information — so a slide back into the conditional is not a wording
  slip, it is the exercise switching itself off.
- Founders premortem the exciting death and die of the boring one, and the reason
  is not a failure of imagination: the competitor shipping first is nobody's
  fault. Getting busy is. A story is only useful once it names a cause the founder
  is standing in.
- Count the live bets in `goals.md` that need the same single pair of hands. Above
  three, stop investigating the market — the story is already written, the cause
  is attention, and the only open question is which of them dies first.
- A risk register is how a founder imagines failure without thinking about it, and
  it leaves them feeling rigorous, which is the product it actually delivers.
  Having pictured the death is not a defence against it. The tripwire is, and it
  is the only line here that will still exist in month five.

## Steps

1. **Set the date and state the death as fact.** "It is <plan date + 6 months>.
   This failed." Do not hedge back into the conditional at any point. The moment
   the words "could" or "might" appear, the exercise has stopped working and
   you are writing a risk register.
2. **Write a story, not a list.** Chronological, with months and named actors:
   month 1 this happened, month 3 the founder responded by doing this, month 5
   they were doing something else entirely. A list ranks risks; a story exposes
   the sequence — and the sequence is where plans actually break, because the
   third failure is usually caused by the response to the first.
3. **Make the cause boring.** Founders premortem the exciting death — a
   competitor ships it, the market turns, the platform changes the rules — and
   then die of the boring one: the founder got busy, a client's project overran
   by 38 hours, the emails never got written. Check `reviews/weekly/`. The boring
   cause has already happened, more than once, and it is on the record with
   dates. Use those dates.
4. **Check the two deaths a company of one always has.**
   - **The founder ran out of attention, not money.** Look at `goals.md`: how
     many live bets already have the same single pair of hands?
   - **The plan needed a person who does not exist** — a salesperson, an editor,
     a second founder, someone to answer the phone in August. Walk the plan and
     mark every task nobody in this company does. That is where it stops.
5. **Find the earliest point the story could have been interrupted, and say what
   the founder would have had to see.** An observable with a threshold and a
   date. That is the tripwire, and it is the only durable output of this skill —
   hand it to the **Strategist** as the bet's kill condition, so the story has a
   place to be stopped next time.

## Output

No file. The Board writes no company state. Hand back:

    It is <date>. <The plan> failed.
    ## The story
    Month 1: <what happened>
    Month 3: <what the founder did about it — this is where it compounds>
    Month 5: <where the founder actually was>
    ## The boring cause
    <the one already in reviews/weekly/, with the date it last happened>
    ## The person who doesn't exist
    <the task nobody in this company does>
    ## Tripwire
    <observable> <threshold> by <date>

The tripwire becomes a `Kill if:` line in `goals.md` only when the **Strategist**
accepts it. If the premortem changes the plan, the founder logs that through the
**Chief of Staff** and `decision-log` — not you.

## Guardrails

**No balanced view.** There is no paragraph about how it might go well. The
optimistic case has an author, they are in the room, and they wrote the plan.

**Never give a probability.** You are generating causes, not forecasting. "30%
chance of failure" is a number with no source that will be quoted back for a
quarter as though it had one.

**Do not run this after commitment.** A premortem that cannot change anything is
theatre, and the founder will mistake having imagined the failure for having
prevented it.

Stop at the tripwire. Fixing the plan is the **Strategist's** job; you have just
shown them where it dies.
