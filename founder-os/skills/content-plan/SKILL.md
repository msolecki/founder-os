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

Monthly. Triggered automatically by `tasks/content-plan`. Also when the founder
has gone quiet for a month, or has a plan and nothing to say — which means the
plan was built from topics rather than from questions.

## Inputs

Read first, in order — house rule 1:

- `content.md` — the `## Shipped` list. **What actually went out, not what was
  scheduled.** This number sets next month's cadence and nothing else does.
- `offer.md` — the ICP, the trigger, the offer. Every piece serves this or it
  is out.
- `pipeline.md` — what prospects actually asked on calls. These are the posts.
- `content.md` `## Audience` — the verbatim quotes from `audience-research`

## Steps

1. **Count what shipped last month.** Not scheduled. Shipped, with a date.
2. **Set the cadence to that number.** Not higher. If they shipped one, plan
   one. This is the rule that makes the plan survive a bad week, and a bad week
   is not a hypothetical — it is roughly one week in four. A founder who ships
   one a month for a year has twelve pieces; a founder who plans twelve a month
   has four pieces and a year of guilt. Raise the cadence only after a month
   where the plan was met with room to spare.
3. **Give every piece a source question.** A real question, asked by a real
   person who fits the ICP, on a real call — from `pipeline.md` or the audience
   quotes. Write the question, not the topic.
4. **Cut every piece with no source question.** If you cannot name which ICP
   attribute the reader has and what they asked, it is a hobby post. At most one
   speculative piece per month; that one is for the founder, and calling it what
   it is keeps it from eating the plan.
5. **Ask the question the founder is avoiding: of the last ten things you
   published, which produced a conversation?** If the answer is "I don't know",
   the first task is not more posts — it is finding out. A year of publishing
   into an unmeasured void is not a content strategy, it is a habit with a
   plausible cover story.
6. **Check where the attention is actually landing.** If what performs best is
   aimed at people outside the ICP, do not quietly follow it — that is
   repositioning the company one post at a time, without a decision. Hand the
   finding to the **Positioning Advisor**.
7. **Schedule against the founder's real week.** Look at what happened the last
   time a piece was due mid-delivery-crunch. Plan around the crunch, or the plan
   is fiction with dates.

## Named failure modes

- **The aspiration cadence.** Set by what a serious founder "should" publish.
  It is always three to five times the shipped number and it always ends in
  silence.
- **The content-as-cure.** Publishing more because prospects don't understand
  the offer. If the message doesn't hold together, volume just distributes the
  confusion more efficiently. That is a positioning problem — hand it over.

## Output

Write to `content.md`, replacing `## Plan`:

    ## Plan — <Month YYYY>
    Cadence: <n>/month — last month shipped <n>
    ICP: <one line, from offer.md YYYY-MM-DD>

    | date | piece | the ICP question it answers | source | status |
    |------|-------|-----------------------------|--------|--------|
    | YYYY-MM-DD | <title> | "<the question, verbatim>" | <call with X, YYYY-MM-DD> | planned |

    Speculative this month: <n>/1

Append to `## Shipped` as pieces go out — this is what next month's cadence is
computed from, so it is not optional bookkeeping:

    ## Shipped
    - YYYY-MM-DD — <title> — <link> — conversations produced: <n | unknown>

## Guardrails

Never plan a cadence above last month's shipped count. If the founder insists,
write their number and the shipped number next to each other in the file and let
the next plan settle it.

Never plan a piece without a source question. "Thought leadership on <topic>" is
not a piece, it is a category, and nobody has ever finished writing one.

Do not write `pipeline.md` when a post produces a lead — hand to the **Pipeline
Coach**. Do not write `offer.md` when the audience turns out to be someone else
— hand to the **Positioning Advisor**.
