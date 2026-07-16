---
name: content-draft
description: Draft one planned piece around a single idea the founder learned by doing — run against the plan, never to fill a slot, and never after 10pm on anything naming a person
metadata:
  writes:
    - content.md
    - drafts/content/
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

- `content.md` — the `## Plan` slot: which question this answers, for whom, and
  **on which channel**. The channel is not a delivery detail decided after the
  writing; it is the length, the shape, and whether the first line has to work
  alone. `content-plan` already decided it — do not re-decide it here.
- `content.md` `## Audience` — their verbatim words. Write in those, not in the
  founder's internal vocabulary.
- `voice.md` — `## Samples`, `## Tells`, `## Never`, `## Register`. **This and
  `## Audience` are not the same input and they do not conflict:** the audience's
  quotes decide *which words* the piece uses, the founder's samples decide *how
  the sentences go*. A piece in the founder's vocabulary is unreadable to the
  buyer; a piece in the founder's voice is why anyone reads a solo founder at
  all. `## Register` covers the public post, which is the loosest register in the
  file and the one furthest from a proposal.

  If `## Samples` is empty, say so on the handoff — "no voice samples on record;
  this is a competent post by nobody in particular" — and hand the founder
  `voice-capture` (**Brand Editor**). A published piece in a default register
  does not just underperform, it teaches the audience that this founder sounds
  like everyone else, and that impression is expensive to reverse.
- `offer.md` — the ICP. The reader is one specific person.
- `clients/` and `pipeline.md` — the specific thing that actually happened, with
  the number attached

## Beliefs

- The most valuable thing the founder knows is the thing they think is too
  obvious to write down. Expertise is largely the inability to see what you
  know; "everyone knows that" is a report on the founder's peer group, not on
  the buyer.
- A draft that came out easily usually has no idea in it. It was a transcription
  of something the founder already believed, which is why it took twenty minutes
  — and why nobody will reach the end of it.
- A piece that costs the founder nothing to publish returns nothing. The number,
  the named failure, the client they fired: the discomfort of putting those on
  the internet under their own name is not a side effect of the piece working,
  it is the mechanism.

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
9. **Fit it to the channel in the slot.** Same idea, same evidence, shaped for
   where it lands: what the reader sees before deciding to keep reading, and how
   much they will read if they do. A piece written channel-blind and posted
   anywhere reads as reposted from somewhere else, which is what it is. If the
   idea cannot survive the channel's shape, that is a finding for `content-plan`
   — the slot is wrong, not the idea. Do not quietly move it: the channel was
   decided from where the ICP actually is, and this draft does not get to
   overturn that with a preference.
10. **Read it back against `voice.md`, last.** Every `## Never` entry is a
    search — and this is the skill where the `FATAL` one shows up, because
    "This isn't a hiring problem. This is a pricing problem." is exactly the
    sentence a post about a lesson wants to end on. It is also the sentence that
    tells every reader in the founder's category that nobody wrote this.

    Then `## Tells`, which is the half that matters here: a post that is
    de-slopped and voiceless is the **safe draft** under a different name. The
    founder's advantage is that they are one identifiable person with scars; a
    piece that could have been written by their category loses to the entire
    internet whether or not it contains a banned phrase.

## Named failure modes

- **The safe draft.** Technically true, professionally worded, could have been
  written by anyone in the category. It costs nothing to publish and it returns
  exactly that.
- **The subtweet.** A real grievance about a real client, filed off just enough
  that the founder believes it is unidentifiable. The client always recognises
  themselves, and so does every prospect who is now wondering how they'll be
  written about.

## Output

**Write the post to `drafts/content/YYYY-MM-DD-<slug>.md`, in full, before you
show it.**

    # <title> — content — YYYY-MM-DD

    ## Draft
    <the whole post, verbatim, exactly as the founder would publish it>

    ## Provenance
    Card: content.md ## Drafts — <title>
    Slot: YYYY-MM-DD

    ## Sent

`## Sent` stays empty. The founder fills it, or it stays empty forever — see
`## Guardrails`.

**`## Provenance` carries a back-link and nothing else — do not repeat the card
here.** Channel, `Answers:`, `One idea:` and `Evidence:` live on the card in
`content.md` and only there. Copying them into the draft file creates two records
of the same four facts with two owners' worth of chances to drift, and by the time
they disagree the founder believes whichever one they opened last. That is the
duplication `queue.md`'s intake rule refuses on exactly these grounds, and this
file does not get an exception for being new.

The draft goes to the founder. This skill does not publish.

**The card stays in `content.md` `## Drafts` and does not grow a body.**
`content-plan` reads `content.md` whole to compute the cadence from the trailing
four weeks; a file with three post bodies in it is a file that has stopped being
scannable, and the cadence is what `content.md` exists to serve. The card is the
index, the draft file is the thing:

    ## Drafts
    ### <title> — for the YYYY-MM-DD slot
    Channel: <from the ## Plan slot>
    Answers: "<the source question, verbatim>"
    One idea: <the single sentence>
    Evidence: <what happened, when, the number>
    Draft: [[YYYY-MM-DD-<slug>]]
    Status: draft | HELD for morning re-read | shipped YYYY-MM-DD
    Proposed: publish "<title>" — [[YYYY-MM-DD-<slug>]] — bet: <B<n> | none> | none

The fields are the other five proposers' fields exactly, and `bet:` is not optional
— `daily-brief` step 0 says taking an item "means an id and a bet". The line sits on
the card rather than as one bounded line in a summary section, because the founder
can draft two posts in an afternoon and a single line holds one of them.
`content.md` `## Drafts` is already per-card, so the container already scales.

**`Draft:` and `Proposed:` both carry the same `[[slug]]` and that is not
duplication.** They answer different questions and have different lifetimes:
`Draft:` is the card's pointer to its body and lives as long as the card, following
it into `## Shipped`. `Proposed:` is an obligation with a clock. When `daily-brief`
takes it, the queue item it creates carries `from: content.md <date>` so tomorrow's
brief leaves the line alone — `daily-brief` cannot write `content.md`, and does not
need to. The line is yours to clear when the card ships or you supersede it.
Clearing `Proposed:` must never orphan the card from its body: `Draft:` is what
joins them, and it stays.

On publication, move the card to `## Shipped` with its date, channel and link —
`content-plan` computes the cadence from the trailing four weeks of that list.
**The draft file stays in `drafts/content/`.** It is not moved, not deleted, and
not tidied: `## Sent` carries the published version, which is the only durable
sample of the founder's public register this package will ever hold.

**When the founder tells you what they published, write it verbatim under
`## Sent`, then run `voice-capture` on that file.** Both skills are the **Brand
Editor's**, so this costs one step — and it used to get skipped for exactly that
reason, because it felt like bookkeeping and the moment passed.

It is not bookkeeping: a piece the founder rewrote before publishing is a sample
of their public register with their name permanently attached, which is the
highest bar they write to and the one they actually meet. The draft is on disk
now, so the diff survives the session and `voice-capture` can be run late. Being
able to run it late is not permission to skip it.

Ask once. If they do not answer, leave `## Sent` empty — an empty `## Sent` is a
true statement about what you know, and a paraphrase of what you think shipped is a
fabricated sample of their public voice.

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

**Never write `## Sent` from `## Draft`.** They are equal only when the founder
changed nothing before publishing, and that is a fact about the founder that you do
not have. This skill is the one most likely to be told the piece went out
unedited — a post is short, it is theirs, and "I just published it" sounds like
permission to copy. It is not. `voice-capture` reads `## Sent` as a sample of what
the founder actually publishes under their own name; filling it from our own prose
teaches `voice.md` that their public register is already ours, which is the one lie
that makes that file worse than empty.

**A post on disk is not a published post.** House rule 0 is untouched by this file
existing. The founder publishes; you wrote a file.
