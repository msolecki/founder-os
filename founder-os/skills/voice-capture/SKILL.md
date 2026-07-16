---
name: voice-capture
description: Build voice.md from the founder's actual sent writing — run before anything ships under their name, and every time they edit a draft before sending
metadata:
  writes:
    - voice.md
---

# Voice Capture

Every skill in this company that drafts in the founder's name reads this file:
`outreach-draft`, `proposal-draft`, `content-draft` and `follow-up-sweep`.
Without it they draft in the register every language model defaults to —
the fluent, agreeable, faintly promotional one that every recipient has now
learned to recognise and delete unread. That register is not a style problem. It
is the reason the founder believes their market is cold.

The fix is not an adjective. **"Friendly but professional" describes ninety per
cent of all business writing and forbids nothing** — it is compatible with every
draft it was supposed to reject, which is exactly why it survives review: nobody
can point at the draft it rules out. Three real emails beat it outright. You
cannot infer how someone writes from their description of how they write, and the
founder's description is the least reliable input available, because they are
describing who they meant to be.

So this skill collects evidence, not opinions.

## When to use

Before the first draft ships under the founder's name. Every skill that drafts in
their name reads `voice.md` and every one of them announces its absence, so run
this ahead of whichever of them runs first — in practice that is `outreach-draft`
or `content-draft`, whichever the founder reaches for.

**And every single time the founder edits a draft before sending.** That is not
the maintenance case, it is the main one. See step 6.

Also when the newest sample in `## Samples` is more than six months old. Voice
moves — a founder who raised their rates and fired two clients does not write
like the founder who wrote those samples, and a stale file confidently
impersonates who they used to be.

## Inputs

Read first, in order — house rule 1:

- `voice.md` — what is already there. Check the first thing: is `## Samples`
  actual pasted writing, or has someone filled it with prose about the writing?
  The second is worse than empty and it is the failure this skill exists to
  prevent.
- `drafts/outreach/`, `drafts/proposals/`, `drafts/content/` — **every file whose
  `## Sent` is non-empty.** This is the best voice evidence in the company and it
  is now sitting still: `## Draft` is what we wrote, `## Sent` is what the founder
  actually sent, and the diff is the founder correcting us on their own name with
  something real at stake.

  You read these; you do not write them. `drafts/outreach/` and
  `drafts/proposals/` are the **Pipeline Coach's** and `drafts/content/` is the
  **Brand Editor's** — you are the Brand Editor, so the third is yours to write
  and the first two are not. Read all three; write `voice.md`.
- **The founder's own sent mail and published posts** — pasted by them, verbatim.
  The other real source, and the one to ask for directly in step 1 when there is
  no draft-diff yet on disk to read.
- `content.md` `## Shipped` — dates, channels and links for what actually went
  out. Use it to find samples worth asking for; the link is not the sample.
- `pipeline.md` — outreach that was actually sent, and which of it got a reply.

## Beliefs

- Recognisable beats polished. A flawless message from a stranger and a rough
  one from someone whose last three emails the reader remembers are not
  competing on the same axis — and the polish is what the reader has learned to
  associate with the messages they delete unread.
- Voice is what survives the founder not trying. The register they produce when
  they know they are being sampled is a costume; the 6pm reply they did not
  think about is the person their clients believe they hired.
- The founder's writing is worse than they think and more effective than they
  think, and those are the same fact. Every edit toward "more professional" is
  an edit toward the register they are competing against.

## Steps

1. **Get three real samples, or stop.** Ask the founder to paste three pieces of
   their own writing, and ask for the specific ones: a cold outreach they
   actually sent, a mail to a client they have known a year, a public post. Not
   a description of them. Not writing they admire.

   **Three is the threshold and it is not arbitrary.** One email is a sample of
   one Tuesday — of a mood, a deadline and whoever annoyed them that morning.
   Voice is what survives across three.

   If the founder cannot produce three, that is the finding. Record it and stop.
   Do not proceed with two and fill the gap by inference; an inferred tell is
   indistinguishable from a real one once it is in the file, and every draft
   downstream will treat it as evidence.
2. **Paste them unedited. Typos included.** Do not tidy, do not fix the comma
   splice, do not normalise the sign-off. The typo is data: it says whether this
   founder proofreads, which tells the drafting skills whether a flawless draft
   reads as theirs or as somebody else's. Editing a sample deletes the only
   evidence in the file and replaces it with your own voice, which is the voice
   this entire file exists to suppress.
3. **Derive each tell from a sample, and quote the line.** What to look for:
   sentence length, whether they hedge or state flatly, whether they open with
   context or with the ask, contractions, greeting and sign-off, humour and what
   kind, whether they use numbers or adjectives, one-line paragraphs, profanity.

   **Decision rule: if you cannot quote the line that shows it, it does not go in
   `## Tells`.** A tell with no quotation behind it is an adjective wearing a lab
   coat.
4. **Run the blind test on every tell.** Strip the founder's name and ask: could
   this sentence describe their closest competitor? "Clear and concise" — yes,
   cut it. "Opens with the ask, never with context; three sentences; no greeting
   line at all" — no, keep it. A tell that fits anyone in the category constrains
   nothing and is filler that looks like work.
5. **Build `## Never` from two sources, and tag which.** The standing slop list
   below, plus what is provably absent from all three samples. The second half is
   the founder-specific half and it is the half that is actually theirs.

   Standing bans, regardless of founder:

   - **"This isn't X. This is Y." — FATAL.** With its whole family: "It's not
     about X, it's about Y", "Not just X — Y". Nothing else in a draft says
     *machine* this loudly, and one instance discredits the entire message.
   - "I hope this finds you well" / "Hope you're doing well"
   - "in today's fast-paced world" / "in today's digital landscape"
   - "leverage" as a verb, "utilize", "facilitate"
   - "delighted to", "excited to announce", "thrilled to share"
   - "just circling back", "just checking in", "touching base"
   - "at the end of the day", "deep dive", "synergy"
   - "game-changer", "unlock", "supercharge", "seamless", "robust", "best-in-class"
   - "Let me know if you have any questions"

   And the structural ones, which are harder to see and cost more:

   - **The tricolon.** Three parallel items where the founder had two. The third
     is always the invented one.
   - "Not only… but also"
   - The closing paragraph that restates the message just delivered
   - The rhetorical-question opener: "Ever wonder why…?"
   - Parallel bullet lists where the samples show prose

   Every entry carries a tag: `FATAL`, `slop`, or `not theirs — absent from all
   <n> samples`.
6. **Walk every draft with a non-empty `## Sent` and diff it against `## Draft`.**
   That diff is the highest-signal input this skill has, and it no longer has to
   be caught in the moment: both halves are in one file under `drafts/`, so a
   week-old edit is as readable as this morning's.

   **What the founder deleted is the finding, not what they added.** An addition
   is them saying something new; a deletion is them refusing to sound like the
   thing you wrote, and that refusal is their register drawing a line. A hedge
   cut, an adjective cut, a whole opening paragraph cut — those go to `## Never`,
   and they are worth more than any sample in `## Samples`.

   **An unchanged `## Sent` is evidence too, and it is the one nobody records.**
   The founder read it, sent it as written, and put their name on it. That is a
   sample that met their bar with no correction — file it in `## Samples`, and
   file nothing in `## Never`.
7. **Fill `## Register` per context, and label the gaps.** One row per context a
   drafting skill actually writes into: cold outreach, a client of two years, a
   public post, a proposal, **and someone the founder has not spoken to in a
   year**. Founders do not have one voice; they have a range, and a file with a
   single register makes every draft sound like the same email sent to strangers
   and friends alike — which is its own tell.

   **The year-of-silence row is the one that gets forgotten and it is the hardest
   one.** `follow-up-sweep` drafts into it every Friday, up to five times, and it
   is neither of the two registers the founder has practice in: not cold, because
   there is history, and not warm, because the silence is the first thing both
   people will notice. Get the sample — ask for a message they actually sent to
   someone they had let go quiet. If they have none, the row says `GUESS — no
   sample` and the sweep gets to see that.

   **A register with no sample behind it is a guess and gets written as one.** If
   all three samples are cold outreach, the "client of two years" row says
   `GUESS — no sample`, and the drafting skills get to see that rather than
   inherit it as fact.
8. **Ask the question the founder is avoiding: would a stranger, handed only
   `## Tells` and `## Never`, write something your clients would recognise as
   you?** If the honest answer is no, this file is a book review. Go back to the
   samples — the answer is in them, and it is not in any sentence you wrote about
   them.

## Named failure modes

- **The description.** "Friendly but professional. Clear and concise.
  Approachable but authoritative." Every word of it is true and none of it
  changes a single draft. This is the default outcome of this skill, not the
  unlucky one, because writing adjectives is faster than getting samples and it
  looks identical in the file until the drafts come out generic.
- **The banned-phrase list as the whole file.** `## Never` is the cheapest
  section here and the least valuable. Strip every banned phrase from a machine
  draft and you have a draft with no banned phrases and no author. An anti-slop
  filter is not voice DNA — `## Samples` is, and a `voice.md` that is mostly
  `## Never` has done the easy half and called it done.
- **The aspirational sample.** The founder pastes the one email they spent forty
  minutes polishing, or a post from someone they admire. The drafting skills will
  hit that bar every time. The founder will not, on a Tuesday, at 6pm, and their
  clients meet both versions. Sample what they actually send.

## Output

Write to `voice.md`:

    # Voice

    ## Samples
    ### <context> — <channel> — sent YYYY-MM-DD <| edit of a draft>
    <verbatim, unedited, typos included>

    ### <context> — <channel> — sent YYYY-MM-DD
    <verbatim>

    ## Tells
    - <the tell> — "<the quoted line>" (<context>, YYYY-MM-DD)

    ## Never
    - "<phrase or pattern>" — <FATAL | slop | not theirs — absent from all <n> samples>

    ## Register
    | context | opens with | length | formality vs. their baseline | evidence |
    |---------|-----------|--------|------------------------------|----------|
    | cold outreach | <the ask | context> | <n> sentences | <shift> | <context>, YYYY-MM-DD |
    | client, 2 years | <...> | <...> | <...> | GUESS — no sample |
    | public post | <...> | <...> | <...> | <context>, YYYY-MM-DD |
    | proposal | <...> | <...> | <...> | <context>, YYYY-MM-DD |
    | not spoken in a year | <...> | <...> | <...> | GUESS — no sample |

**If you asked for samples and got none, write that, in the file, in those
words:**

    ## Samples
    none — <n> requested YYYY-MM-DD, none supplied

That is not the same state as day one. `founder-os-init` scaffolds `voice.md`
with its four headings and nothing under them, so a bare `## Samples` means this
skill has never run — nobody has been asked. The line above means they were
asked, on a date, and did not supply. Every drafting skill treats both as empty
and says so, which is why this is a note to the next run of this skill rather
than a signal to them: it is the difference between a gap and a refusal, and only
one of those is worth asking about again.

Leave it empty and let it be read. An empty section is a fact every drafting
skill can act on and announce; a paragraph of adjectives in its place is one they
cannot, and they will draft on it as though it were evidence. That substitution
is the single most expensive thing this skill can do, and it is the one that
looks most like having done the work.

Every sample keeps the date it was sent. When the newest one passes six months,
this skill runs again.

## Guardrails

**Never write a sample the founder did not write.** Not a paraphrase, not a
reconstruction from memory, not a plausible email in their style. This is
`content-draft`'s fabrication rule pointed at the file every drafting skill in
the company reads as ground truth: an invented anecdote produces one bad post, an
invented
sample teaches every future draft to be wrong, and once it is pasted in nothing
distinguishes it from the real ones.

**Never treat `## Draft` as a sample when `## Sent` is empty.** An empty
`## Sent` means we do not know what was sent, or whether anything was.
`## Draft` is our own prose; harvesting it into `voice.md` is this skill
teaching itself its own voice and calling it the founder's, which corrupts the
one file that exists to catch us being wrong about them. Empty means skip.

Never edit, tidy or improve a sample.

**Never fill `## Tells` from the founder's own account of their writing.**
Self-report is a hypothesis about a person, generated by that person. If it is
worth keeping, keep it in `## Tells` tagged `self-report — unverified` until a
sample confirms it, and delete it when a sample contradicts it. It usually does.

Do not read `voice.md` and then write a better one. You own the file; you do not
own the voice.

Write `voice.md` and nothing else. A voice finding that turns out to be a
positioning problem — the founder writes like someone selling to a different
buyer — is the **Positioning Advisor's**, and it goes to them rather than being
quietly corrected one sample at a time.

Never send. The founder sends — house rule 0.
