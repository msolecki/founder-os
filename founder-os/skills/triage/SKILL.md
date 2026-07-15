---
name: triage
description: Take the founder's pile of unsorted obligations, keep one, cost the rest, and route them by name — run when they arrive with five things and no idea which matters
metadata:
  writes:
    - reviews/daily/
---

# Triage

The founder arrives with five things and wants help with five things. Helping
with five things is what they can already do alone, badly, and it is why they
are here. One survives. The other four get a named cost and an owner.

This is also the company's front door. When the founder does not know who to
ask, they ask you, and the routing below is the implementation of the promise
in `COMPANY.md` — that a specialist owns every decision.

## When to use

The founder arrives with a pile: a client request, a half-idea, an overdue
invoice, someone's favour, a thing they read. No stated priority, or a stated
priority that is obviously the newest item.

Also mid-week, when the daily brief's one thing has been displaced three days
running — the displacement is the pile, and it is unsorted.

## Inputs

Read first — house rule 1:

- `goals.md` — the only ranking authority. Urgency is not one.
- `reviews/daily/` — the last three briefs: has this pile already been triaged?

**Then, deliberately, more than `context-load` allows.** `context-load` caps you
at one file beyond charter/goals/metrics, and that cap is right for every
cadence that works inside one domain. Triage does not: its input is five items
that each live in a different agent's file, and "is this real?" cannot be
answered for a pipeline item without `pipeline.md`. So this skill takes a
bounded exception, and the bound is what keeps it from becoming the averaging
failure `context-load` warns about:

- One file per item, five files maximum, **read only the section that item
  lives in** — not the file.
- Read to answer exactly one question: is this real and is it dated?
- **If an item needs the whole file to judge, it is not a triage item.** It is a
  session with that specialist. Route it and stop reading.

## Steps

1. **Make them list it, written, five maximum.** If more than five arrive, the
   list is the first finding: triage the first five in the founder's own order
   and say plainly that the rest were cut without examination, which is what
   was going to happen to them anyway.
2. **Give each item an owner and a next action with a date.** No next action
   means it is not a thing, it is a worry. Worries do not get triaged. Name it
   as a worry and drop it — this alone usually clears two of the five.
3. **Rank against `goals.md`, not against urgency.** The question the founder is
   avoiding: *which of these would still be on the list if nobody had asked me
   for it?* Everything that is on the list because someone else asked goes to
   the bottom, including the item they are most anxious about.
4. **Keep one.** Not two. Two is five with a smaller font.
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

## Output

Append to today's `reviews/daily/YYYY-MM-DD.md`:

    ## Triage
    Kept: <item> — <the bet in goals.md it serves>
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

Do not do any of the five. The moment you start the kept item you are not
triaging, you are the founder's second pair of hands, and the four dropped ones
stop being costed by anybody.

Do not soften the cost. If dropping the client's favour damages the
relationship, write that it damages the relationship.
