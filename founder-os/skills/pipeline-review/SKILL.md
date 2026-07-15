---
name: pipeline-review
description: Force every deal to have a next action with a date or leave the pipeline — run weekly, and any time the founder says they have more conversations than they can name
metadata:
  writes:
    - pipeline.md
---

# Pipeline Review

A founder with "eleven active conversations" has three deals and eight people
who were nice to them once. The eight are not harmless: they are what lets the
founder feel busy at exactly the moment they should be alarmed.

Every deal has two required fields — the next action, and the date it happens.
A deal with neither is not in the pipeline, it is a memory. This review's output
is the killing.

## When to use

Weekly. Triggered automatically by `tasks/pipeline-review`. Also before any
quarterly planning that assumes revenue, and whenever the founder is "waiting to
hear back" — which is not a pipeline stage, it is the absence of one.

## Inputs

Read first, in order — house rule 1:

- `pipeline.md` — every entry, including the ones that have been there since
  spring
- `offer.md` — what is actually being sold, and the ICP. Deals outside the ICP
  get named as such.
- `goals.md` — this quarter's revenue bet. The gap is what the pipeline is
  measured against.
- `metrics.md` — cash and burn, for what the gap actually means

## Steps

1. **Test each entry against the deal definition.** A deal has: a named amount,
   an identified decision-maker, and a date. Missing one, it is at risk. Missing
   two, it is not a deal — it is a relationship, and it belongs to the **Network
   Manager**. Hand it over; do not keep it for the count.
2. **Reject next actions that belong to the prospect.** "Waiting to hear back",
   "they're discussing internally", "checking in when they're ready" — none of
   these are next actions, because the founder does not do them. Every next
   action is something the founder does, on a date, alone.
3. **Apply the re-dating rule.** If a deal's next action has been moved forward
   in three consecutive reviews, the deal is dead and is being kept for morale.
   Kill it out loud. The date moved because nothing happened, and nothing
   happened because the prospect is not buying.
4. **Ask the question that ends the argument: if this prospect said no
   tomorrow, would you be surprised?** If the founder would not be surprised, it
   is already a no and the only thing missing is the writing down.
5. **Move every failed entry to `## Dead` with a cause.** Not "went quiet" —
   what specifically was the last thing that happened, and who went quiet first.
   Each entry in `## Dead` is an input to `win-loss-analysis`; a cause of "went
   quiet" teaches nothing next quarter.
6. **Compute coverage and say it plainly.** Total value of surviving live deals
   against the revenue gap in `goals.md`. Below 3× coverage, the finding is not
   "follow up harder" — it is that there are not enough deals, and no amount of
   diligence on eight zombies produces a ninth real one. This number is the
   reason the killing matters: an honest short pipeline is what sends the
   founder to go get more.
7. **Name founder latency.** Median days from first call to proposal sent across
   the live list. Over three days, that is the review's finding, regardless of
   what any prospect said.

## Named failure modes

- **The comfort pipeline.** Long, warm, and full of people who liked the
  founder. It reports well and forecasts nothing.
- **Reviving the zombie.** Inventing a next action so the entry can stay. If the
  only reason to contact someone is that they are on the list, they are not on
  the list.

## Output

Write to `pipeline.md`. Rewrite `## Live` and append to `## Dead`:

    ## Live
    ### <Prospect> — <offer> — <amount> — <stage>
    Decision-maker: <name, role>
    Next action: <what the FOUNDER does> — YYYY-MM-DD
    Last contact: YYYY-MM-DD | In pipeline since: YYYY-MM-DD | Re-dated: <n>×

    ## Dead
    - <Prospect> — <amount> — died YYYY-MM-DD — <specific cause> — win/loss: <pending|done>

    ## Last review
    Date: YYYY-MM-DD
    Live: <n> (<total value>) | Killed today: <n> (<value>) | Handed to Network Manager: <n>
    Coverage: <n>× against a <amount> gap (goals.md YYYY-MM-DD)
    Median call→proposal: <n> days

## Guardrails

Never carry a deal forward without a next action because killing it would feel
harsh. The founder's discomfort at the killing is the point; the alternative is
a founder who discovers in month three of the quarter that they have no revenue
and no time left to fix it.

Never invent a next action. If you cannot name one the founder would actually
do, that is the finding.

Do not write `clients/` when a deal closes — hand the won deal to the **Delivery
Lead**. Do not write `network.md` — hand relationships to the **Network
Manager** and let them own the cadence. Do not edit `offer.md` because a
prospect wanted something else; that is the **Positioning Advisor's**, and deal
pressure is the worst possible reason to make their decision for them.

Every `## Dead` entry is handed to `win-loss-analysis` while the prospect will
still take the call — not at quarter end, when the answer has become a story.
