---
name: content-draft
description: Draft one planned piece around a single idea the founder learned by doing — run against the plan, never to fill a slot, and never after 10pm on anything naming a person
metadata:
  writes:
    - content.md
---

# Content Draft

A company of one has exactly one content advantage: specific, real, first-person
experience with numbers attached. The migration that went wrong and what it
cost. The client they fired and why. Everything else — the frameworks, the
trends, the advice — competes against the entire internet and loses silently.
Nobody tells the founder the post was boring. It just does nothing, forever.

So the bar is: **does this contain something the founder learned by doing it?**
If not, don't publish it. Saying no is most of this skill's value; the founder
can generate drafts endlessly and has no editor, which is exactly why the output
drifts toward safe.

## When to use

Against a slot in `## Plan` with a source question. Not to fill a gap, not
because it has been a while, and not at 11pm when a prospect has annoyed them
into eloquence.

## Inputs

Read first, in order — house rule 1:

- `content.md` — the `## Plan` slot: which question this answers, for whom
- `content.md` `## Audience` — their verbatim words. Write in those, not in the
  founder's internal vocabulary.
- `offer.md` — the ICP. The reader is one specific person.
- `clients/` and `pipeline.md` — the specific thing that actually happened, with
  the number attached

## Steps

1. **Get the source before you write a sentence.** The real project, the real
   call, the real number. If the founder cannot produce a specific — what
   happened, when, what it cost — the piece is not ready. Do not proceed to
   write it generically; that is the exact drift this skill exists to stop.
2. **Write the one idea as one sentence.** The thing you would put on a slide.
   Everything else in the piece is evidence for it. If you cannot compress the
   piece to one sentence, the piece does not have an idea yet — it has a topic.
3. **If there are two ideas, it is two pieces.** And note which one the founder
   was hiding: the second idea is usually where the weaker, less defensible claim
   is parked, on the theory that nobody will notice it in a list. They won't
   notice it. That's the problem.
4. **Refuse the listicle reflex.** "5 lessons from X" is five posts each with a
   fifth of the evidence. It reads as a list because the founder did not want to
   commit to a claim — a list cannot be wrong, which is precisely why it cannot
   be interesting either.
5. **Replace every adjective with a number.** "It went badly" → "it ran 38 hours
   over and I ate the difference". The number is the piece. The adjective is
   what every competitor also wrote.
6. **Run the tomorrow test.** If a prospect quotes this back on a call next
   week, does the founder still stand behind it? Publish only what they can
   defend in a live conversation with the person it was aimed at.
7. **Apply the morning rule.** Anything naming a client, a former employer, or a
   competitor — or written while annoyed — is held until the next morning and
   re-read before it ships. Not a suggestion. Written at 11pm it feels like
   candour; at 9am it reads as a grievance, and it is on the internet either way.
8. **Cut the throat-clearing.** The first two paragraphs are almost always the
   founder warming up. Start at the third — where the specific thing happens.

## Named failure modes

- **The safe draft.** Technically true, professionally worded, could have been
  written by anyone in the category. It costs nothing to publish and it returns
  exactly that.
- **The subtweet.** A real grievance about a real client, filed off just enough
  that the founder believes it is unidentifiable. The client always recognises
  themselves, and so does every prospect who is now wondering how they'll be
  written about.

## Output

The draft goes to the founder. This skill does not publish.

Record in `content.md` under `## Drafts`:

    ## Drafts
    ### <title> — for the YYYY-MM-DD slot
    Answers: "<the source question, verbatim>"
    One idea: <the single sentence>
    Evidence: <what happened, when, the number>
    Status: draft | HELD for morning re-read | shipped YYYY-MM-DD

On publication, move it to `## Shipped` with its date and link — `content-plan`
computes next month's cadence from that list, and a piece that shipped without
being recorded makes the next plan smaller than the truth.

## Guardrails

Never publish. The founder publishes.

**Never invent the anecdote, the client, or the number.** A fabricated specific
is the one thing that permanently ends a founder's credibility, and it is the
single easiest thing for an agent to produce — it costs nothing to write "we cut
their build time by 40%" and everything to be asked about it on a call. If the
specific does not exist, the piece does not exist.

Never name a client without recorded permission. If the founder is unsure
whether a contract permits it, that is a lawyer's question and they should
answer it before the piece goes out, not after. See `guardrails`.

Do not draft a piece with no slot in `## Plan`. Publishing to fill silence is
how the plan becomes decorative.

Do not write `pipeline.md` or `offer.md`. A post that generates a lead goes to
the **Pipeline Coach**; a message that will not hold together goes to the
**Positioning Advisor**.
