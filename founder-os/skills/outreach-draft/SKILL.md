---
name: outreach-draft
description: Draft a first contact or a follow-up written from the prospect's problem — run when a deal needs a next action, and never to send "just checking in"
metadata:
  writes:
    - pipeline.md
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

The draft goes to the founder to send. This skill does not send.

**If the founder edits it before sending, ask for the sent version and hand it to
`voice-capture` (Brand Editor) — the same day.** That diff is the founder
correcting you on their own name with a live deal at stake, and it is the best
voice evidence this company will ever get. It also evaporates fastest: by
tomorrow the founder remembers only that they "tweaked it a bit". You do not
write `voice.md` — you hand over the text and let its owner decide what it means.

Record it in `pipeline.md` under the prospect's entry in `## Live`:

    ### <Prospect> — <offer> — <amount> — <stage>
    Next action: <what the founder does next> — YYYY-MM-DD
    Outreach: YYYY-MM-DD — angle: <the specific thing> — ask: <the one ask>
    Touch: <n> | Last reply: <YYYY-MM-DD | none>

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
