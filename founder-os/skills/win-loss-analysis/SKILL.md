---
name: win-loss-analysis
description: Reconstruct why a deal was won or lost from the record and the prospect's own words — run within five business days of any deal ending, while they will still take the call
metadata:
  writes:
    - pipeline.md
---

# Win/Loss Analysis

The founder's memory of a loss is "they went with someone cheaper". That is not
what happened. That is the sentence the prospect used to end an awkward
conversation kindly, and the founder accepted it because it is the only
explanation that costs them nothing — price is the socially acceptable no, for
both parties, every time.

The record is less charitable and it does not forget. Run this from `pipeline.md`
dates, `decisions/`, and the prospect's actual words. Not from memory.

## When to use

Within **five business days** of any deal closing or dying. After that the
prospect has constructed a tidy story and will tell you that instead of what
happened. Every entry in `## Dead` gets one. So does every win — a win nobody
understands is a lucky accident the founder cannot repeat.

## Inputs

Read first, in order — house rule 1:

- `pipeline.md` — the dates. First call, proposal sent, each follow-up, last
  reply. Who went quiet first, and on what day.
- `decisions/` — what was decided during this deal, and why. If a discount or a
  scope change happened, it is here.
- `offer.md` — what they were actually sold, and the ICP. A loss from outside
  the ICP is a qualification finding, not a sales one.
- The prospect — a call, if they will take one.

## Beliefs

- The prospect is not lying and also does not know why they didn't buy. People
  reconstruct their own decisions afterwards, so an honest answer and an
  accurate one are different objects, and only the second one is worth a call.
- Every stated reason has passed one filter: it could be said to a near-stranger
  without causing offence. That filter removes precisely the reasons worth
  having.
- An unexamined win is more expensive than a loss. A loss costs one quarter; a
  win nobody can explain becomes a theory of the business, and the founder will
  run it for two years before anything is permitted to contradict it.

## Steps

1. **Reconstruct from the record before you speak to anyone.** Days from first
   call to proposal sent. Number of follow-ups. Who went quiet first. Do this
   first, because once you have heard the founder's account you cannot unhear
   it, and it will feel like a memory rather than a story.
2. **Ask the prospect the question that works.** For a loss: *"When did you
   decide it wasn't us — and what was happening at that moment?"* Ask for the
   moment, not the reason. The reason is a story they assembled afterwards; the
   moment is a fact, and it is usually two weeks earlier than the founder
   thinks. For a win: *"What nearly stopped you?"* — that answer is the
   objection every other prospect had and never said.
3. **Interrogate "cheaper".** Cheaper than what — a competitor's quote, a junior
   hire, doing nothing, or the number they had in their head before you spoke? If
   nobody named a competitor, this was not a price loss. It was a value loss,
   and those have completely different fixes.
4. **Compare the record with the founder's account.** Where they diverge, the
   record wins. It has dates.
5. **Compute founder latency.** Median days from first call to proposal across
   the quarter's closed deals. Over three days is a finding regardless of what
   any prospect said — and it is the most common real cause, precisely because
   no prospect will ever tell you "you were slow". They just stop caring.
6. **Cluster and hand off at three.** Three losses in a quarter on the same
   cause is a system problem, not three bad days:
   - **price or "I didn't understand what you do"** → **Positioning Advisor**.
     Their decision, their file.
   - **trust, credibility, never heard of you** → **Brand Editor**.
   - **outside the ICP** → **Positioning Advisor**, and it is a qualification
     failure in this pipeline; you let them in.
   - **the founder took nine days to send the proposal** → yours. Fix it here.
7. **Name the one cause you would bet on.** Not a list of factors. If it is a
   guess, label it a guess (house rule 2). A win/loss that concludes "several
   things contributed" has concluded nothing.

## Named failure modes

- **The comfortable cause.** Every loss attributed to price or budget; every win
  attributed to the founder's expertise. Both are the explanations that require
  no change.
- **The pitch in disguise.** Using the win/loss call to reopen the deal. The
  prospect notices immediately, the conversation ends, and you have traded the
  most valuable information available for a rejection you already had.

## Output

Append to `pipeline.md` under `## Win/loss`:

    ## Win/loss
    ### <Prospect> — <won | lost> YYYY-MM-DD — <amount>
    Stated reason: "<what they said, verbatim>"
    Record says: <n>d call→proposal | <n> follow-ups | <who> went quiet first, YYYY-MM-DD
    Actual cause: <the one you'd bet on> <— GUESS if unverified>
    Prospect spoke: <yes YYYY-MM-DD | declined | not asked>
    Pattern: <n>th <cause> this quarter → handed to <Agent Name>

When a cluster reaches three, that is material — log it via `decision-log` with
what would change your mind, so the next quarter can check whether the fix
worked instead of re-litigating the theory.

## Guardrails

Never accept "went with someone cheaper" without asking what it was cheaper
than. Never run this from the founder's memory alone — if the prospect will not
talk, say the finding is unverified, use the record, and label the cause a
guess.

Do not log the founder's self-criticism as a cause. "I wasn't confident enough
on the call" is a feeling. "The proposal sat for nine days" is a cause, and it
is the one with a fix.

Do not use the call to sell. Do not re-open the deal. Do not argue with the
answer — the moment you defend the price, the information stops.

Do not edit `offer.md` when the losses cluster on price. Hand it to the
**Positioning Advisor** with the count. Their decision.
