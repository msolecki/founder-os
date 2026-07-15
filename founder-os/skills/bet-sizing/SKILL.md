---
name: bet-sizing
description: Price a bet by what it costs when it is wrong and cap the downside in writing before it starts — run before any bet enters goals.md
metadata:
  writes:
    - goals.md
---

# Bet Sizing

The founder has already computed the upside. That arithmetic is why they are in
the room, and it is not in dispute. This skill computes the other number.

The cap is the product here. A maximum spend chosen now, before anything is
sunk, is a real constraint. The same number chosen in month three, with 60
hours already in the ground, is a rationalization with a spreadsheet attached.

## When to use

Before any bet is written into `goals.md` — every bet in `quarterly-planning`
passes through here.

Also whenever an opportunity arrives mid-quarter and the founder wants to know
whether it is worth doing. It usually is, at some size. The question is which
size.

## Inputs

Read first — house rule 1:

- `metrics.md` — the effective hourly rate, cash position, and runway, with
  their dates
- `goals.md` — what is already committed, because the founder's hours are
  already spent on paper
- `decisions/` — has a bet of this shape been made before, and what did it
  actually cost?

## Steps

1. **Price the hours at the rate in `metrics.md`.** Founder hours are the most
   expensive input in the company and the only one that gets called free. If
   `metrics.md` has no effective rate, stop and hand to the **CFO** — you cannot
   size a bet in a currency that does not exist.
2. **Answer the question that is being avoided: what does this cost if it is
   wrong?** Not "what if it works". Hours, cash, and the thing you cannot get
   back — the client you deprioritized, the quarter you spent, the positioning
   you moved. Write it as a sentence a person could be held to.
3. **Set the cap before the start.** The maximum hours and cash spent before the
   judgement date, whichever comes first. Written into `goals.md` now, while
   saying a small number is free.
4. **Apply the runway rule.** If the downside exceeds one month of runway from
   `metrics.md`, this is not a bet — it is a bet-the-company move. It goes
   through the **Board Member** (`premortem`) first, and it gets logged in
   `decisions/` by the **Chief of Staff** whichever way it goes.
5. **Apply the reversibility rule.** How long to undo if wrong?
   - **Under a week** — stop analyzing and run it. The deliberation now costs
     more than the mistake would. A founder who red-teams a reversible bet is
     avoiding a different decision; ask which one.
   - **A week to a month** — cap it and go.
   - **Over a month** — `red-team` before committing. Irreversibility is the
     only thing that earns a delay.
6. **Write the size into the bet's block in `goals.md`.** A bet whose size lives
   in the conversation is unsized.

## Output

Append to the bet's block in `goals.md`:

    Cost: <hours> h @ <rate from metrics.md, dated> + <cash>
    Cap: stop at <hours> h or <cash>, or <date> — whichever comes first
    If wrong: <what is lost, concretely> — reversible in <time>

## Guardrails

Never size a bet without `metrics.md`. A cost estimate with no rate and no
runway behind it is a wish with units.

Never size the upside. It is not this skill's job, the founder has done it, and
adding a second optimistic number to the page will not improve the decision — it
will balance it, which is worse.

Refuse to size a bet with no judgement date. Send it back to
`quarterly-planning`. Without a date, "the cap or the date, whichever comes
first" has no second half, and the cap will be quietly renegotiated instead.

Do not decide whether to take the bet. You price it. Taking it is the founder's
call, and if the price kills it, that is the price talking.
