---
name: content-plan
description: Plan what gets published against the ICP and last month's actual shipped count — run monthly, and whenever the founder proposes a cadence they have never once hit
metadata:
  writes:
    - content.md
---

# Content Plan

Publishing to nobody in particular is a hobby. It is a defensible hobby — but it
should not be filed under business development, and the founder currently files
it there.

The second thing this skill exists to stop: the plan that commits to three posts
a week. That founder publishes for four weeks and then stops for a year, and the
year of silence is caused by the plan, not by the founder's discipline.

## When to use

Weekly. Triggered automatically by `tasks/content-plan`, Wednesdays. Also when
the founder has gone quiet for a month, or has a plan and nothing to say — which
means the plan was built from topics rather than from questions.

**Weekly does not mean re-planning weekly.** The plan is a rolling four-week
horizon and most Wednesdays touch one week of it: fill the week that just came
into view, mark what shipped, cut what died. A skill that rewrites the whole plan
every Wednesday has never let a plan survive contact with a week, and the founder
learns the plan is provisional — at which point it stops being a commitment and
becomes a suggestion they are already behind on.

## Inputs

Read first, in order — house rule 1:

- `content.md` — the `## Shipped` list. **What actually went out, not what was
  scheduled.** The trailing four weeks of it set the cadence and nothing else
  does.
- `offer.md` — the ICP, the trigger, the offer. Every piece serves this or it
  is out.
- `pipeline.md` — what prospects actually asked on calls. These are the posts.
- `content.md` `## Audience` — the verbatim quotes from `audience-research`

## Beliefs

- The founder is not the audience, and the piece they most want to write is the
  one nobody asked for. Wanting to write it is a fact about the founder's week,
  not a signal from the market.
- Nobody is waiting. No reader has ever noticed a missed week — the disappointed
  audience the founder pictures does not exist, and the cadence is a constraint
  on the founder rather than a promise to anybody.
- A piece a stranger nods at is worth less than one six people argue with and
  one person books a call about. Agreement is what writing gets when it has not
  claimed anything, and the founder will read it as the piece having gone well.

## Steps

1. **Count what shipped in the trailing four weeks.** Not scheduled. Shipped,
   with a date, from `## Shipped`. It is a rolling window, recounted every
   Wednesday — the number moves slowly and that is the point: a window that
   resets on the 1st lets a strong fortnight authorise a cadence the founder
   cannot hold in March.
2. **Set the cadence to that number, per four weeks.** Not higher. If they
   shipped one, plan one. This is the rule that makes the plan survive a bad
   week, and a bad week is not a hypothetical — it is roughly one week in four. A
   founder who ships one a month for a year has twelve pieces; a founder who
   plans twelve a month has four pieces and a year of guilt. Raise it only after
   a four-week window where the plan was met with room to spare.
3. **Give every piece a source question.** A real question, asked by a real
   person who fits the ICP, on a real call — from `pipeline.md` or the audience
   quotes. Write the question, not the topic.
4. **Cut every piece with no source question.** If you cannot name which ICP
   attribute the reader has and what they asked, it is a hobby post. At most one
   speculative piece per four weeks; that one is for the founder, and calling it
   what it is keeps it from eating the plan.
5. **Name the channel, from the record and not from preference.** Every piece
   ships somewhere, and where is half of this decision. The evidence is already in
   the workspace and the founder has never looked at it: `## Audience` records the
   `source` of every verbatim quote — where the ICP was actually talking — and
   `pipeline.md` says where each live deal started. **The channel that produced
   deals and quotes is the channel.** The one the founder enjoys writing for is a
   preference; if it wins anyway, write that it won on preference and let the next
   plan check it.

   **One primary channel until it produces conversations.** A second channel costs
   what doubling the cadence costs, and step 2 already said what the founder can
   sustain — a founder on four channels is on none, publishing a quarter of the
   volume in four places where nobody sees a pattern. Add a second only after a
   four-week window where the first met its cadence *and* produced a named
   conversation. Cross-posting is not a second channel: it is the same piece with
   another URL, it is free, so do it and do not count it.

   If the ICP is not on the founder's channel, that is not a content finding and
   you do not solve it by posting harder — hand it to the **Positioning Advisor**
   with the sources attached.
6. **Ask the question the founder is avoiding: of the last ten things you
   published, which produced a conversation?** If the answer is "I don't know",
   the first task is not more posts — it is finding out. A year of publishing
   into an unmeasured void is not a content strategy, it is a habit with a
   plausible cover story.
7. **Check where the attention is actually landing.** If what performs best is
   aimed at people outside the ICP, do not quietly follow it — that is
   repositioning the company one post at a time, without a decision. Hand the
   finding to the **Positioning Advisor**.
8. **Schedule against the founder's real week.** Look at what happened the last
   time a piece was due mid-delivery-crunch. Plan around the crunch, or the plan
   is fiction with dates.
9. **Propose what the plan cannot hold to the Chief of Staff.** Every piece in the
   table is dated in `content.md` with a status, which makes it the **Brand
   Editor's** and not a queue item. A plan copied into `queue.md` is a second
   content calendar that disagrees with this one by the second Wednesday, and the
   founder will believe whichever they opened last. The piece the founder actually
   sits down to draft gets its id from the daily brief on the morning they do it —
   not from a plan written four weeks out, which is also why most of this plan
   sits beyond the queue's 21-day clock and would age out unstarted having never
   been startable.

   What escapes is step 6's finding. *Find out which of the last ten pieces
   produced a conversation* is not a piece, it has no row here, it serves the
   whole plan rather than any one entry — and it is the obligation that has now
   evaporated for a year, which is why the answer is still "I don't know".

   **At most one, and most Wednesdays none.** Hand it to the **Chief of Staff**
   with its bet named. You do not write `queue.md`: a cadence shipping one piece
   per four weeks that proposed an item every Wednesday would be proposing four
   times its own output, and the 21-day clock would kill three of the four. What
   deserves a slot is the Chief of Staff's decision, taken across every cadence at
   once — this plan only sees publishing.

## Named failure modes

- **The aspiration cadence.** Set by what a serious founder "should" publish.
  It is always three to five times the shipped number and it always ends in
  silence.
- **The content-as-cure.** Publishing more because prospects don't understand
  the offer. If the message doesn't hold together, volume just distributes the
  confusion more efficiently. That is a positioning problem — hand it over.

## Output

Write to `content.md`, replacing `## Plan`:

    ## Plan — rolling 4 weeks from YYYY-MM-DD
    Cadence: <n>/4 weeks — trailing 4 weeks shipped <n>
    ICP: <one line, from offer.md YYYY-MM-DD>
    Primary channel: <channel> — <n> of the last <n> live deals started there (pipeline.md), <n> of <n> audience quotes sourced there
    Second channel: <none | <channel>, added YYYY-MM-DD after <n>/4 weeks met + <the named conversation>>

    | date | piece | the ICP question it answers | source | channel | status |
    |------|-------|-----------------------------|--------|---------|--------|
    | YYYY-MM-DD | <title> | "<the question, verbatim>" | <call with X, YYYY-MM-DD> | <channel> | planned |

    Speculative this window: <n>/1

Append to `## Shipped` as pieces go out — this is what the trailing-four-week
cadence is computed from, so it is not optional bookkeeping:

    ## Shipped
    - YYYY-MM-DD — <title> — <channel> — <link> — conversations produced: <n | unknown>

## Guardrails

Never plan a cadence above the trailing four weeks' shipped count. If the founder
insists, write their number and the shipped number next to each other in the file
and let the next plan settle it.

Never plan a piece without a source question. "Thought leadership on <topic>" is
not a piece, it is a category, and nobody has ever finished writing one.

Never plan a piece without a channel. "Publish it" is not a plan; a piece with no
named destination gets written and then parked, because deciding where to put it
turns out to have been part of writing it.

Never add a channel because a platform is having a moment. The cadence rule
governs channels too: the founder's output is fixed, and a new channel divides it
rather than adding to it.

Do not write `pipeline.md` when a post produces a lead — hand to the **Pipeline
Coach**. Do not write `offer.md` when the audience turns out to be someone else
— hand to the **Positioning Advisor**.
