---
name: triage
description: Take the founder's pile of unsorted obligations, keep one, cost the rest, and route them by name — run when they arrive with five things and no idea which matters
metadata:
  writes:
    - reviews/daily/
    - inbox.md
---

# Triage

The founder arrives with five things and wants help with five things. Helping
with five things is what they can already do alone, badly, and it is why they
are here. One survives. The other four get a named cost and an owner.

This is also the company's front door. When the founder does not know who to
ask, they ask you, and the routing below is where this package keeps its promise
that a specialist owns every decision.

## When to use

The founder arrives with a pile: a client request, a half-idea, an overdue
invoice, someone's favour, a thing they read. No stated priority, or a stated
priority that is obviously the newest item.

Also mid-week, when the daily brief's one thing has been displaced three days
running — the displacement is the pile, and it is unsorted.

## Inputs

Read first — house rule 1:

- `inbox.md` — **read it first, and empty it.** This is the pile. Until this file
  existed the pile was constructed by interrogation — "make them list it" — which
  works only for what the founder can recall while sitting in front of you at the
  moment you ask. What they thought at 15:00 on Tuesday walking out of a meeting
  was never in the room. This file is where that thought waits.
- `goals.md` — the only ranking authority. Urgency is not one.
- `reviews/daily/` — the last three briefs: has this pile already been triaged?
- `queue.md` — `## Doing`, because a keep that cannot be started is not a keep;
  and `## Dropped`, because an item you are about to triage for the third time is
  sitting there with the date it was killed and the reason, which is a lookup
  rather than an argument.

**Then, deliberately, more than `context-load` allows.** `context-load` caps you
at two files beyond charter/goals/metrics — the file your decision owns, which
for this skill is `reviews/daily/`, plus one more — and that cap is right for
every cadence that works inside one domain. Triage does not: its input is five
items that each live in a different agent's file, and "is this real?" cannot be
answered for a pipeline item without `pipeline.md`.

So this skill takes a bounded exception, and `context-load` names it back — a
carve-out only one side knows about is not a carve-out, it is a skill quietly
amending a rule it does not own. The bound is what keeps it from becoming the
averaging failure `context-load` warns about:

- One file per item, five files maximum, **read only the section that item
  lives in** — not the file.
- Read to answer exactly one question: is this real and is it dated?
- **If an item needs the whole file to judge, it is not a triage item.** It is a
  session with that specialist. Route it and stop reading.

## Beliefs

- A pile is not a prioritisation problem. It is the record of five yeses the
  founder already said, and sorting it is triage of the consequences. The ranking
  they are asking for is a way of not noticing that the intake was the failure.
- Urgency is a claim somebody else made about their own week, and it arrives
  pre-argued because they have had longer to think about it than the founder has.
  It is evidence about them. `goals.md` is the only ranking authority in this
  room.
- Routing is a decision, not a deferral. An item handed to a named owner has been
  dealt with; an item the founder agrees to "keep in mind" has been kept, at full
  cost, with no owner, no date, and a fresh claim on next Tuesday.
- The item the founder is most anxious about is usually on the list because
  somebody asked for it, and the anxiety is the tell rather than the argument. It
  goes to the bottom — and they will experience that as you not understanding the
  situation.

## Steps

1. **Drain `inbox.md`, then make them list the rest, five maximum.** The inbox is
   the pile the founder already wrote down; the interrogation is for what they did
   not. Read the inbox, empty it to zero, and add the interview's items to it.

   **The five-maximum is a cap on what you triage, not on what they wrote.** If the
   inbox holds nine lines, the list is the first finding: triage the first five in
   the founder's own order and say plainly that the rest were cut without
   examination, which is what was going to happen to them anyway.

   **Empty it even for the items you cut.** An inbox that keeps what triage did not
   reach is a queue with no clock and no cap — the graveyard, arriving through the
   one door built to have neither. A cut item is not deleted: it is a `Dropped:`
   row in today's brief under `## Triage`, with its cost, where the next triage will
   see it arrive again. The inbox is a door. Nothing lives in a door.
2. **Give each item an owner and a next action with a date.** No next action
   means it is not a thing, it is a worry. Worries do not get triaged. Name it
   as a worry and drop it — this alone usually clears two of the five.
3. **Rank against `goals.md`, not against urgency.** The question the founder is
   avoiding: *which of these would still be on the list if nobody had asked me
   for it?* Everything that is on the list because someone else asked goes to
   the bottom, including the item they are most anxious about.
4. **Keep one, and give it an id.** Not two. Two is five with a smaller font.

   Run `queue`: the kept item goes to `## Doing` — or to `## Queued` if `## Doing`
   is at its cap of three, and if it is, say plainly that the founder is triaging a
   new pile while three older commitments are still open, which is a finding about
   the last three days and not about these five things.

   A keep that stays a sentence in a review file is the failure this whole skill
   exists to prevent, arriving one step later: the founder agreed, felt sorted, and
   by Thursday the kept item is indistinguishable from the four you costed.
5. **Cost the four.** One line each: what concretely happens because this does
   not get done this week. "Nothing" is a legitimate answer and it is the most
   valuable output this skill produces. If "nothing" is true for all four, the
   finding is that the founder's list is theatre, and the pile is not a
   prioritisation problem.
6. **Route the real ones by name.** Dropping is not deleting. Each dropped item
   goes to the agent who owns that decision, with its next action attached:

   | the item is about | it goes to |
   |---|---|
   | Direction, bets, what to kill | **Strategist** |
   | Is this plan actually sound | **Board Member** |
   | Who we serve, what we sell | **Positioning Advisor** |
   | What happens next with a prospect | **Pipeline Coach** |
   | Can we take this on, is it good enough | **Delivery Lead** |
   | Can we afford it, does it make money | **CFO** |
   | What goes in the calendar | **Focus Coach** |
   | What capability to build next | **Skills Mentor** |
   | What to publish | **Brand Editor** |
   | Who to talk to, when to follow up | **Network Manager** |
   | What to automate vs tolerate | **Ops Engineer** |

   If an item matches two rows, it is two items. If it matches none, it is not
   the company's work — say so rather than inventing an owner.

   **Your "dropped" is not `queue.md`'s `## Dropped`, and the two must not be
   confused.** Yours means *not kept today, and here is who owns it instead* — it
   is a routing decision, and the row you write below is its record. The queue's
   means *decided against, permanently, with a reason*. A routed item that goes
   into the queue would be the queue holding what another agent owns, which the
   `queue` skill refuses on intake and house rule 4 forbids. Route it and leave it
   with its owner. The one exception is the three-strike rule below.

## Output

Append to today's `reviews/daily/YYYY-MM-DD.md`:

    ## Triage
    Kept: [q-MMDDx] <item> — <the bet in goals.md it serves>
    Dropped:
    - <item> → <Agent> — <what it costs to not do this> (<3rd time: permanent>)

The dropped list is written down for one reason: so the next triage can see the
item arrive again.

## Guardrails

Never keep two. A ranked list of five is five things wearing a decoration, and
the founder will work down it in urgency order the moment you leave.

**The three-strike rule.** If an item appears in three triages and is never
kept, it is not a priority — it is a guilt. Drop it permanently, say so in
writing, and do not let it return. Items that survive on repetition rather than
merit are the reason the pile exists.

A permanent drop is the one thing this skill writes to the queue: run `queue` and
put it in `## Dropped`, with the reason `three triages, never kept`. In writing
meant somewhere the next triage will actually look, and "the last three briefs"
is not that place — it is three files, only one of which anybody opens. `##
Dropped` keeps 90 days, which is about thirteen chances for the item to walk back
in wearing a new sentence, and now it walks into a file that already has the date
it died.

Do not do any of the five. The moment you start the kept item you are not
triaging, you are the founder's second pair of hands, and the four dropped ones
stop being costed by anybody.

Do not soften the cost. If dropping the client's favour damages the
relationship, write that it damages the relationship.
