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

## Beliefs

- Deals do not die of neglect. They die at a specific moment, in a specific
  conversation, and the founder was present for it. "Went quiet" describes the
  founder's attention, not the prospect's decision.
- A pipeline does not exist to forecast revenue. It exists to say how many weeks
  remain to fix the quarter. Reviewed for accuracy it is a report; reviewed for
  lead time it is a decision, and only one of those was worth the hour.
- An honest empty pipeline is better news than a full one made of maybes. The
  founder can act on nothing. They cannot act on eight things that are secretly
  nothing, because every one of them comes with a plausible reason to wait.

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

6. **Move every won deal to `## Won`, carrying its exclusions verbatim.** A won
   deal must leave `## Live` — it is not a prospect any more — and it must not
   leave `pipeline.md`, because the exclusions `proposal-draft` wrote are the
   only written boundary on the engagement that just started. Copy the
   `Exclusions:` lines across exactly as they are. Do not summarise them, do not
   count them, do not decide three of them no longer apply. Then tell the
   **Delivery Lead** the engagement is live and where its baseline is.
7. **Compute coverage and say it plainly.** Total value of surviving live deals
   against the revenue gap in `goals.md`. Below 3× coverage, the finding is not
   "follow up harder" — it is that there are not enough deals, and no amount of
   diligence on eight zombies produces a ninth real one. This number is the
   reason the killing matters: an honest short pipeline is what sends the
   founder to go get more.
8. **Name founder latency.** Median days from first call to proposal sent across
   the live list. Over three days, that is the review's finding, regardless of
   what any prospect said. `win-loss-analysis` runs the same median over the
   quarter's closed deals — that is the same rule on a different population, and
   this one is the leading indicator of it.
9. **Propose what this file cannot hold to the Chief of Staff.** Every surviving
   deal's next action is dated in `pipeline.md`. Those are yours, they are not
   queue items, and copying them into `queue.md` would create two truths that
   disagree by Thursday — the intake rule refuses them and house rule 4 is why.

   What escapes is step 7's finding. Below 3× coverage, *go get more deals* is an
   obligation with no prospect to attach it to, no row in this file, and nowhere
   else to live: it is the class the queue exists for, and it is the one that
   evaporates every week. Make it concrete enough to close — *book three
   discovery calls* — or it is a worry, not an item.

   **At most one, and most weeks none.** Name it, name the bet in `goals.md` it
   serves, and hand it to the **Chief of Staff**. You do not write `queue.md`:
   what deserves one of fifteen slots against a 21-day clock is their decision,
   made across every cadence, and this review can only see the pipeline. If
   `## Queued` is already full, say so and hand it over as a triage rather than an
   append — something gets dropped to make room, or your item is not important, it
   is just the newest.

## Named failure modes

- **The comfort pipeline.** Long, warm, and full of people who liked the
  founder. It reports well and forecasts nothing.
- **Reviving the zombie.** Inventing a next action so the entry can stay. If the
  only reason to contact someone is that they are on the list, they are not on
  the list.

## Output

Write to `pipeline.md`. Rewrite `## Live`; **append** to `## Won` and `## Dead`;
replace `## Last review`.

    ## Live
    ### <Prospect> — <offer> — <amount> — <stage>
    Decision-maker: <name, role>
    Next action: <what the FOUNDER does> — YYYY-MM-DD
    Last contact: YYYY-MM-DD | In pipeline since: YYYY-MM-DD | Re-dated: <n>×

    ## Won
    ### <Client> — won YYYY-MM-DD — <amount> — <offer>
    Proposal sent: YYYY-MM-DD | Delivery Lead notified: YYYY-MM-DD
    Exclusions — verbatim from the signed proposal, scope-guard's baseline:
    - <exclusion> → if requested: <change order at <rate> | separate engagement>
    Engagement: <live | closed YYYY-MM-DD>

    ## Dead
    - <Prospect> — <amount> — died YYYY-MM-DD — <specific cause> — win/loss: <pending|done>

    ## Last review
    Date: YYYY-MM-DD
    Live: <n> (<total value>) | Won: <n> | Killed today: <n> (<value>) | Handed to Network Manager: <n>
    Coverage: <n>× against a <amount> gap (goals.md YYYY-MM-DD)
    Median call→proposal: <n> days

`## Won` is the scope record, not the sales record. `win-loss-analysis` writes
`## Win/loss` for the post-mortem on both wins and losses; `## Won` exists for one
reader, `scope-guard`, and one purpose: what this client was told they were not
getting.

## Guardrails

Never carry a deal forward without a next action because killing it would feel
harsh. The founder's discomfort at the killing is the point; the alternative is
a founder who discovers in month three of the quarter that they have no revenue
and no time left to fix it.

Never invent a next action. If you cannot name one the founder would actually
do, that is the finding.

**Never rewrite, prune, or tidy `## Won`.** `## Live` is a working list and this
review rewrites it every Thursday — that is what makes the killing possible.
`## Won` is the opposite: it is a record, it is append-only, and it outlives the
review that wrote it. The entries look dead to a pipeline review because the
selling is over, and deleting one does not tidy the file — it silently removes
the only written boundary on an engagement that is still running, and nobody
finds out until a client asks for something in week five and `scope-guard` has
nothing to rule against. Mark an engagement `closed` when it ends. Leave it
there.

Do not write `clients/` when a deal closes — hand the won deal to the **Delivery
Lead**. Do not write `network.md` — hand relationships to the **Network
Manager** and let them own the cadence. Do not edit `offer.md` because a
prospect wanted something else; that is the **Positioning Advisor's**, and deal
pressure is the worst possible reason to make their decision for them.

Every `## Dead` entry is handed to `win-loss-analysis` while the prospect will
still take the call — not at quarter end, when the answer has become a story.
