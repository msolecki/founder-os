---
name: outreach-draft
description: Draft a first contact or a follow-up written from the prospect's problem — run when a deal needs a next action, and never to send "just checking in"
metadata:
  writes:
    - pipeline.md
    - drafts/outreach/
---

# Outreach Draft

The founder's outreach fails for one reason: it is about the founder. It opens
with who they are, describes what they do, and asks the prospect to work out
whether any of it is relevant to them. The prospect does not do that work. They
do not do it for anyone.

The second reason is "just checking in" — a message that asks the recipient to
invent a reason for the conversation on the founder's behalf. Its reply rate is
why the founder believes their market is cold. The market is fine. The message
was empty.

## When to use

When `pipeline-review` produced a next action that is an outreach. When a deal
has gone quiet and the founder wants to follow up. When the founder is about to
send something at 11pm because a prospect crossed their mind.

## Inputs

Read first, in order — house rule 1:

- `pipeline.md` — this prospect: what has already been sent, when, and what they
  said. Repeating an angle they already ignored is worse than silence.
- `offer.md` — the ICP and the trigger. If this prospect does not fit the ICP,
  say so before drafting a word.
- `voice.md` — **read this before you write a sentence, not after.** `## Samples`
  is the founder's actual sent mail; `## Tells` is what makes it recognisably
  theirs; `## Never` is the phrase list that gets a message deleted on sight;
  `## Register` says how cold outreach differs from a mail to a client of two
  years — this is the coldest register in the file and the least forgiving of a
  wrong one.

  **If `## Samples` is empty, say so out loud in the handoff** — "no voice
  samples on record; this is written in a default register and will read like
  it" — and hand the founder `voice-capture` (**Brand Editor**). Drafting
  silently on an empty voice file is how a message that is correct about the
  prospect still reads like every other automated email in the inbox. Do not
  reconstruct a voice from `content.md`, from published posts, or from the
  founder's description of themselves.
- `network.md` — is this person already the **Network Manager's**? If there is
  no deal, they are, and cold outreach against a warm relationship burns it.

## Beliefs

- Every convention of business email is a tax levied on someone who owes you
  nothing. The greeting, the credentials, the pleasantry — the prospect pays all
  of it before reaching anything that concerns them, and most messages never get
  that far.
- Volume is how a founder launders having nothing to say. Ten researched
  messages beat two hundred, not because ten is a virtuous number, but because
  the research is the product and the message is only its delivery.
- If the founder would not send it to someone they respect and expect to meet at
  a conference next year, they should not send it at all. Cold outreach is not a
  lower-standard genre; it is the same genre with a worse audience, and the
  founder has been using the audience as permission.

## Steps

1. **Find the specific thing.** One fact true only of this prospect, that took
   real effort to find. Not "I saw you're hiring" — everyone is hiring, and that
   sentence proves only that you can read a careers page. Something that took
   five minutes: what they shipped, what they said on a podcast, the thing in
   their job ad that reveals the trigger from `offer.md`.
2. **Open with their problem, in their words.** The first sentence is about
   them or the message is deleted. The founder's name, credentials, and years of
   experience are not an opening — they are what the prospect checks *after*
   they care.
3. **Run the swap test.** Replace the prospect's name with a competitor's. Does
   the message still read fine? Then it is a broadcast, it will be received as
   one, and you have written a template. Delete it and go back to step 1.
4. **Say the useful thing before the ask.** A diagnosis, a number, an observation
   about their situation they haven't had for free. If you have nothing useful,
   you are not ready to send — that is the finding, not a reason to send anyway.
5. **Make one ask, small and cheap and answerable.** A 15-minute call with a
   stated agenda, or a yes/no question. "Let me know if you'd like to chat" is
   not an ask; it delegates the decision *and* the next step to someone who owes
   you nothing.
6. **Cut to a phone screen.** Under about 120 words. If it needs scrolling, it
   is a document, and nobody reads a document from a stranger.
7. **Read it back against `voice.md`.** Every `## Never` entry is a search, not
   a vibe — find and cut each one, and treat a `FATAL` hit as a rewrite rather
   than a substitution. Then the harder half: does the draft do what `## Tells`
   says the founder does? If the samples open with the ask in three sentences and
   this draft opens with two paragraphs of context, you have written a good email
   that the prospect will not associate with the person who eventually calls
   them. A draft that passes `## Never` and fails `## Tells` is de-slopped, not
   theirs — that is a filter's output, and the filter is the easy half.
8. **For follow-ups: bring new information every time.** A new angle, a relevant
   thing that happened, an answer to the objection they didn't voice. Follow up
   more often than feels comfortable — the founder's fear of being annoying is
   the single most expensive emotion in this pipeline — but never empty-handed.
9. **Ask why they would reply today rather than never.** If the honest answer is
   "because the founder needs revenue this month", that is not a reason for
   them, and the message will read exactly like what it is.

## Named failure modes

- **The résumé opener.** "I'm a consultant with 12 years' experience in…" — the
  prospect has no reason to have reached sentence two.
- **The false familiarity.** A manufactured compliment about work the founder
  hasn't read. Prospects can tell, and it costs the relationship permanently,
  not just the deal.

## Output

**Write the draft body to `drafts/outreach/YYYY-MM-DD-<prospect-slug>.md`, in
full, before you show it.** This file is the product. The record in `pipeline.md`
is bookkeeping about it.

    # <Prospect> — outreach — YYYY-MM-DD

    ## Draft
    <the message, verbatim, exactly as the founder would send it>

    ## Provenance
    Prospect: [[<prospect-slug>]]

    ## Sent

`## Sent` stays empty. The founder fills it, or it stays empty forever — see
`## Guardrails`.

The draft then goes to the founder to send. This skill does not send.

**When the founder tells you what they actually sent, write it verbatim under
`## Sent` — and hand the file to `voice-capture` (Brand Editor) by path.** That
diff is the founder correcting you on their own name with a live deal at stake,
and it is the best voice evidence this company will ever get.

It no longer has to be caught in the moment. The draft is on disk, so the diff is
`## Draft` against `## Sent` and `voice-capture` can compute it a week later. What
still evaporates is the founder *saying* what they sent — ask, once, and if they
do not answer, leave `## Sent` empty. An empty `## Sent` is a true statement about
what you know. A guess at what they sent is a fabricated writing sample in the one
file whose entire job is to hold real ones.

You do not write `voice.md`. You hand over the path and let its owner decide what
it means.

**Leave a `Proposed:` line under the prospect's entry in `pipeline.md`.** A draft
that exists and is owed a send is an obligation, and until now this skill created
none: it handed the founder a message and closed, and the only thing standing
between that message and oblivion was the founder's memory. The Chief of Staff
owns `queue.md` and you are not them, so you propose and `daily-brief` drains it
— the same path `pipeline-review` already uses, for the same reason.

Record it in `pipeline.md` under the prospect's entry in `## Live`:

    ### <Prospect> — <offer> — <amount> — <stage>
    Next action: <what the founder does next> — YYYY-MM-DD
    Outreach: YYYY-MM-DD — angle: <the specific thing> — ask: <the one ask>
    Touch: <n> | Last reply: <YYYY-MM-DD | none>
    Proposed: send the outreach to <Prospect> — [[YYYY-MM-DD-<prospect-slug>]] — bet: <B<n> | none> | none

**The fields are the other five proposers' fields exactly** —
`Proposed: <item> — bet: <B<n> | none> | none`, as `pipeline-review`,
`revenue-review`, `content-plan`, `quarterly-planning` and `follow-up-sweep` all
emit it. `bet:` is not optional: `daily-brief` step 0 says taking an item "means an
id and a bet", and a proposal that arrives without one makes the brief work it out
at 08:00 from a file it opened for one section.

**The line is per-deal, under the prospect, and that is the one deliberate
departure.** The other five are scheduled cadences: each runs once per period and
writes its proposals in a single pass, so a bounded block in a summary section
survives the period intact — however many lines the pass emits. You are
on-demand and repeatable: the founder can run you at 10:00 for Anna and at 14:00
for Kowalski, and a summary block rewritten per run holds only the last run. The second write would silently drop the first — Anna's
draft would sit on disk with an empty `## Sent` and no obligation anywhere, which is
the exact failure this skill was changed to fix. `## Live` is already per-deal
(`Outreach:`, `Touch:`, `Last reply:` all sit under the prospect), so the container
already scales and the line goes where the rest of the deal's state lives.

If this is the fourth touch with no reply, note it and let `pipeline-review`
decide whether the deal is alive. Persistence is a virtue up to the point where
it becomes the only remaining evidence of a deal.

## Guardrails

Never send anything. The founder sends.

Never fabricate the specific thing. If five minutes of looking produced nothing,
the finding is that the founder has not done the research — and an invented
detail is not a shortcut, it is the fastest way to be caught being fake by
exactly the person you were trying to impress.

Never claim a shared connection, a read of their work, or a referral that did
not happen.

Never invent a price or a scope. Both come from `offer.md`. If the prospect
wants something not in the offer, that is the **Positioning Advisor's**
decision, not something you improvise into an email.

If the person is in `network.md` with no deal in play, hand to the **Network
Manager** and let them run `follow-up-sweep` instead. Two agents contacting the
same person in one week makes the founder look disorganised to the one audience
that was already inclined to help.

**Never write `## Sent` from `## Draft`.** They are equal only when the founder
changed nothing, and that is a fact about the founder that you do not have. A
copied `## Sent` teaches `voice-capture` that the founder's voice is already
yours, which is the one lie that makes `voice.md` worse than empty — it is the
file that exists to catch you being wrong about their register, and this would
fill it with your own prose wearing their name.

**A draft on disk is not a sent draft.** House rule 0 is untouched by this file
existing. The founder sends; you wrote a file.
