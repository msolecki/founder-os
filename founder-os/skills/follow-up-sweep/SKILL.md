---
name: follow-up-sweep
description: Surface everyone past their contact interval and give each one a real reason to hear from the founder — run weekly, capped at five, and never with "just checking in"
metadata:
  writes:
    - network.md
---

# Follow-up Sweep

"Just checking in" is a request for the recipient to invent a reason for the
conversation on the founder's behalf. Nobody does that work. The founder reads
the silence as a cold network and concludes their relationships have decayed.

The network is fine. The message was empty.

This sweep finds everyone past their interval and gives each one something real
— given before anything is asked. If there is nothing real to give, the sweep's
answer for that person is: not this week.

## When to use

Weekly. Triggered automatically by `tasks/follow-up-sweep`. Also when the
quarter's pipeline is thin and cold outreach is being proposed before the warm
list has been touched.

## Inputs

Read first, in order — house rule 1:

- `network.md` `## Map` — the `days` and `what they need` columns. If the map is
  stale or missing, run `relationship-map` first; a sweep against an unknown list
  is a mail merge.
- `pipeline.md` — **anyone with a live deal is excluded.** They are the
  **Pipeline Coach's** this week.
- `clients/` — what was actually delivered for the past clients on this list.
  The result of that work is the best reconnect reason available and it is free.
- `content.md` — anything published that answers a question a specific person on
  this list once asked
- `voice.md` — **read this before you write a sentence, not after.** `## Samples`
  is the founder's actual sent mail; `## Tells` is what makes it recognisably
  theirs; `## Never` is the phrase list that gets a message deleted on sight;
  `## Register` says how writing to someone the founder has not spoken to in a
  year differs from writing to a client of two years. This is the register the
  founder gets wrong most reliably: long silence reads to them as distance to be
  apologised for, and the apology is the first sentence that makes the message
  about them.

  **If `## Samples` is empty, say so out loud in the handoff** — "no voice samples
  on record; these are written in a default register and will read like it" — and
  hand the founder `voice-capture` (**Brand Editor**). Drafting silently on an
  empty voice file is how a message that is right about the person still arrives
  sounding like a mail merge, which is the exact thing this sweep exists to
  prevent — and the recipient will blame the founder, not the draft. Do not
  reconstruct a voice from `content.md`, from published posts, or from the
  founder's description of themselves. `content.md` is on this list for reconnect
  reasons; published writing is a different register performed for strangers, and
  it is not evidence of how this founder writes to someone who knows them.

## Beliefs

- The gap holds itself open. Every month of not writing raises the perceived
  cost of writing, so the message that eventually goes out is over-explained,
  apologetic, and — for the first time in the entire relationship — about the
  founder.
- Nobody remembers being reconnected with; they remember what they were told. A
  message the recipient could not repeat to a colleague the next morning did not
  happen, however good it felt to send.
- The name the founder is most embarrassed to contact is the most valuable one
  on the list, and the embarrassment is proportional to how well it went.
  Sweeping in order of comfort is how a founder spends a decade of goodwill on
  the people who were never going to help.

## Steps

1. **List everyone past their interval, sorted by days over.** Past clients at
   90 days, referred-once at 90, could-refer and peers at 180 — from the map's
   categories, not from a single global number.
2. **Remove anyone with a live deal in `pipeline.md`.** Two agents contacting the
   same person in one week makes the founder look disorganised to precisely the
   audience that was already inclined to help.
3. **Cap the sweep at five.** Per week. A founder who sends forty reconnects in
   one afternoon is running a mail merge, the recipients can tell — they compare
   notes — and the founder will never do it again because the shame of the reply
   rate ends the habit. Five a week clears a forty-person map twice a year, which
   is the cadence the map was built for. Everything else is deferred with a date,
   not dropped.
4. **Find the real thing for each person, from their `what they need` column.**
   Working reasons, in order of quality:
   - an introduction you can actually make, to someone specific
   - a result from the work you did together: *"the thing we shipped in 2024 —
     here's what it's doing now"*. Past clients almost never learn this and it
     is the single best message in this list.
   - something you saw that is relevant to a problem **they named**, not one you
     assume they have
   - an answer to a question they asked once and never got
5. **If there is no real thing, do not send.** The founder will resist giving
   before asking as manipulative. It is not — provided the useful thing is real.
   The moment it is manufactured, they are right, and the recipient will feel it
   before they can articulate it. No reason means: defer with a date, and go
   find one.
   The honest fallback is a specific question about **their** work — not a fake
   gift. "How did the migration land?" beats a forwarded article they didn't ask
   for, every time.
6. **Ask nothing on the first touch after a long silence.** Anything over about
   nine months, the touch is the message. A reconnect with an ask attached after
   fourteen months of silence tells the recipient exactly what they were: an
   entry in a file, contacted when needed.
7. **Write per-person, then read it back against `voice.md`.** If two messages in
   the sweep could be swapped between recipients, both are broadcasts. Rewrite
   both.

   Every `## Never` entry is a search, not a vibe — find and cut each one, and
   treat a `FATAL` hit as a rewrite rather than a substitution. Then the harder
   half: does the draft do what `## Tells` says the founder does? A message that
   passes `## Never` and fails `## Tells` is de-slopped, not theirs — the filter
   is the easy half. And it fails worse here than anywhere else in the company:
   these people have heard from this founder before. A stranger reading an
   off-voice message learns nothing; someone who knows them hears that something
   is off, cannot name it, and files the whole reconnect as insincere — which
   costs the relationship rather than the reply.
8. **Apply the two-touch rule.** Two unanswered touches → stop, drop the
   interval to annual, and note it. Chasing is what turns a network into an
   ex-network. The non-reply is information; it is not an invitation to try
   harder.
9. **Ask the question the founder is avoiding: what have you got that they'd
   actually want?** If the answer is nothing, across the whole list, the finding
   is not about the list. It is that the founder has been taking from this
   network for a year and putting nothing back.
10. **Propose what this file cannot hold to the Chief of Staff.** Everyone on this
    sweep is held by `network.md` — a row under `## Sweep`, or a deferral with a
    date — and neither is a queue item. The founder sending the messages is not a
    queue item either; it needs no id, and this skill could not close it anyway.

    What escapes is the giving. An introduction the founder has now committed to
    making is work owed to a third person, it closes or it doesn't, and no file on
    this list holds it — `network.md` records that a message went out, not that
    the founder still owes Marta an intro to Piotr three weeks later.

    **At most one, and most weeks none.** Name it, name the bet, and hand it to
    the **Chief of Staff**. You propose; you do not write `queue.md` — what
    deserves one of fifteen slots against a 21-day clock is their decision, and
    this sweep sees one week of one map. The arithmetic says why the cap on this
    step is one: five
    reconnects a week each proposing an item would fill the entire queue by the
    third week and starve every other cadence, and the age-out would then kill
    them at the rate they arrived.

## Named failure modes

- **The empty touch.** "Hey, how have you been? Just checking in" — sent to
  eleven people in one sitting, all of whom recognise it.
- **The reconnect-with-invoice.** A warm greeting and then, one paragraph later,
  the reason. Everyone can feel the pivot; some of them will reply anyway, and
  the founder will conclude it works.

## Output

The messages go to the founder to send. This skill does not send.

Append to `network.md` under `## Sweep`:

    ## Sweep — YYYY-MM-DD
    Due: <n> | Sent: <n>/5 | Deferred to <date>: <n> | Excluded (live deal): <n>

    | person | days over | the real thing given | ask | sent | reply |
    |--------|-----------|----------------------|-----|------|-------|
    | <name> | <n> | <the specific thing> | <none | the one ask> | YYYY-MM-DD | |

Update each swept person's `last real contact` and `next contact` in `## Map`
only when the founder confirms it went out. A sweep row is not contact; a
conversation is.

## Guardrails

Never send anything. The founder sends.

**Never invent the useful thing.** A manufactured reason reads as manufactured,
and it costs more than silence — silence is neutral, a fake gift is evidence.
If you cannot find something real, defer the person with a date and say why.

Never sweep someone with a live deal in `pipeline.md`. Never write `pipeline.md`
yourself — a swept contact who turns into a deal is handed to the **Pipeline
Coach**, not entered by you.

Never batch identical messages, and never send an ask on a long-silence
reconnect.

If the sweep needs hours the founder's week does not have, hand to the **Focus
Coach** rather than quietly producing a list they will not action. An
unactioned sweep is worse than none: it converts a live network into a chore
with a bad conscience attached.
