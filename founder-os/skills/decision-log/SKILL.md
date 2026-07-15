---
name: decision-log
description: Record an irreversible decision with the falsifier that would reverse it — run within 24 hours of the decision, while the reason is still the reason
metadata:
  writes:
    - decisions/
---

# Decision Log

House rule 3, implemented. In six months the founder will ask why they raised
their rates, dropped a client, or killed a bet. Without this file the answer
will be reconstructed — plausibly, confidently, and wrong.

The field that makes this a log rather than a diary is the last one: **what
would change our mind.** A decision with no falsifier cannot be audited later,
because any outcome can be read as consistent with it.

## When to use

Within 24 hours of an irreversible decision — before the reasoning decays into
a justification. The **Board Member** hands surviving plans here; the
**Strategist** hands kills here.

Also whenever an agent notices the founder has already acted on something that
was never written down.

## Inputs

Read first — house rule 1:

- `decisions/` — is there a prior entry this one supersedes or contradicts?
- `metrics.md` — the number the decision rests on, and its date
- `goals.md` — which bet this serves, or whether it serves none

## Beliefs

- A reason written after the outcome is not a reason. It is a story with a
  reason's grammar, and its tell is that it is more coherent than the week it
  claims to describe. Twenty-four hours is not tidiness — it is the window in
  which the record is still evidence rather than autobiography.
- Most decisions do not deserve an entry, and refusing to log is this skill's most
  common correct output. A folder that records preferences buries the four
  decisions a year that actually cost something, and nobody reads a diary back.
- The founder's confidence at the moment of deciding carries no information about
  whether they were right, and it is the thing they will remember most vividly.
  Record the number, the rejected option, and the falsifier. Conviction is not
  admissible and does not go in the file.
- The entries the founder will most want to quietly amend later are the ones worth
  keeping unedited. Being embarrassed by a past entry is the log working — a log
  you can correct is a log that only ever proves you were consistent.

## Steps

1. **Apply the log test.** Log it if reversing it would cost more than a day of
   work, money already spent, or a relationship. Otherwise do not log it — a
   log that records everything is read by nobody, and the founder's real
   decisions drown in a stream of preferences. Most things fail this test. Say
   "this doesn't need logging" and move on.
2. **Confirm it is decided.** "Leaning toward" is not a decision. If the founder
   is still deciding, they want the **Board Member**, not this skill. Logging an
   intention creates a record that pressures them into it later.
3. **Write the reason as it is now, not as it will look.** Within 24 hours. The
   failure mode has a name — retroactive rationalization — and its tell is a
   reason that is more coherent than the week in which it was decided.
4. **Name the option rejected.** In six months the founder will remember only
   the option taken, and will be unable to reconstruct why the other one lost.
   The rejected option is half the decision.
5. **Write the falsifier: an observable, a threshold, a date.** "If this channel
   is under 5k MRR by 2026-11-01, this was wrong." Not "if it doesn't work
   out". If you cannot write a falsifier, the decision was made on taste — that
   is allowed, and it gets written down as `Falsifier: none — taste`, which is
   an honest entry and a useful one to reread.
6. **Record who decided: the founder.** Agents advise. If an agent decided, that
   is the entry's most important line and it needs to be visible.

## Output

Write `decisions/YYYY-MM-DD-<slug>.md`, one file per decision:

    # <the decision, one sentence, past tense>
    Date: YYYY-MM-DD
    Decided by: founder
    Serves: <bet from goals.md, or "none">
    ## Context
    <the state that forced the call — with the dated number it rests on>
    ## Rejected
    <the option not taken, and why it lost>
    ## What would change our mind
    <observable> <threshold> by <date>
    ## Supersedes
    <path to prior decision, if any>

## Guardrails

Never edit a past entry. A decision that turned out badly stays exactly as
written — you append a new entry with `Supersedes:` pointing at it. A log the
founder can quietly correct is not evidence, and its only remaining function is
to make them feel consistent.

Never log a decision that has not been made, and never log one the founder has
not seen. This file will be read back as their words.

Never write the falsifier so it cannot fire. "If this stops making sense" is
not an observable. If the honest answer is that nothing would change their
mind, write that — it is the single most useful line this log can contain.
