---
name: queue
description: Hold the founder's live obligations with a cap, an expiry and one owner — run whenever a cadence produces work that would otherwise live in a paragraph nobody reopens
metadata:
  writes:
    - queue.md
---

# Queue

Every cadence in this company produces obligations and not one of them holds one.
The daily brief says *follow up with Anna* and closes. Tomorrow's brief says it again,
or forgets — and neither the founder nor any agent can answer whether Anna was
followed up with, because the only record is a sentence in a file indexed by date
rather than by whether the thing happened.

`queue.md` is where an obligation lives between the cadence that produced it and
the day it is done, dropped, or proved across three weeks to be neither.

It is not a to-do list. The founder has one of those and it is the problem the
daily brief exists to refuse. A to-do list only grows. This file has a cap of
fifteen, every item carries an expiry it cannot renew, and `## Dropped` is a
section rather than a delete key — dropping is a decision, and a decision is worth
reading in November.

## When to use

Whenever a session or a cadence produces an obligation that no other owner's file
will hold: a `triage` keep, the brief's one thing, the next item emitted by closing
the last one.

And every Friday, from `weekly-review` step 5 — the sweep, which is step 7 below.
The sweep is the only thing standing between this file and the graveyard every
queue eventually becomes.

## Inputs

Read first — house rule 1:

- `queue.md` — all five sections, whole. Its state machine does not survive being
  read in parts: whether an item in `## Blocked` is still blocked is answered by
  what sits in `## Done`.
- `goals.md` `## Bets` — every item names one bet or names `none`.

**Two files, and this skill does not sweep for more.** `context-load` caps a
cadence at its own file plus one, and names its exemptions — `triage` and
`daily-brief` — and says they do not extend by analogy to other Chief of Staff
cadences. This is one of those cadences, so the intake is not a sweep of every
agent's file looking for work. It is the two doors below, and the cost of that is
written down in `## Guardrails` rather than quietly paid.

## What belongs here

**An obligation that no other owner's file already holds.** That is the whole
intake rule, and it is the difference between a queue and a second copy of the
workspace:

- A prospect's next action, dated in `pipeline.md` → **not a queue item.** It is the
  Pipeline Coach's. Copying it here creates two truths that disagree by Thursday,
  and house rule 4 exists to prevent exactly that.
- A person deferred with a date under `network.md` `## Sweep` → not a queue item.
- An hour booked under `week.md` `## Blocks` → not a queue item.
- *Follow up with Anna about the retainer*, said out loud on Tuesday, owned by no
  file → **queue item.** This is the class that evaporates today, and it is the only
  class this file exists for.

Items are business work: `follow up with Anna`, `draft the proposal for X`, `raise
the rate on Y`. Never a file edit. Never `think about pricing` — that is a worry,
and `triage` step 2 already says what worries get.

**An item whose next action is dated more than 21 days out is not a queue item
either.** It outlives the clock below, so it would age out unstarted and be dropped
for a reason that is a lie. Work dated for September belongs to whoever owns
September: a renewal to `clients/<client>.md` `## Scope`, a deal to `pipeline.md`.
If no owner's file will take the date, the item is not real yet.

## Beliefs

- A cap is only real on the day it hurts. Three in `## Doing` costs nothing until
  the founder wants a fourth, and that Tuesday is the only moment this file has
  ever done anything. Every argument for an exception arrives on exactly that day,
  and every one of them is individually well-reasoned.
- Guilt is not a priority signal. An item the founder feels bad about is an item
  that has been visible for a long time — a fact about the file, not about the
  work. The clocks exist because the feeling and the importance come apart at
  roughly the same rate.
- Every request for one more field — `bumped:`, `priority:`, `waiting_on:` — is a
  request to become a to-do list again, and it always arrives with a reasonable
  individual case attached. The absence of those fields is the product. A queue an
  item can talk its way out of has no clocks, only decor.
- An item passed over fifteen times has been rejected fifteen times. The founder
  did not forget it — they chose against it every morning and declined to say so,
  and the age-out is this file finally saying it on their behalf.

## Steps

1. **Refuse it, or take it.** Apply the intake rule before anything else. A refused
   item is not lost — name it, and name the owner whose file already holds it.
2. **Name the bet, from `goals.md`.** `bet: none` is legal: an overdue invoice
   serves no bet and still has to be paid. Leaving the field off is not legal,
   because the count of `none` is a measurement of the quarter and the sweep
   reports it.
3. **Give it an id, and the id is its clock.** `q-MMDDx` — the date it was raised
   plus a letter for that day's second and third item: `q-0715a`, `q-0715b`. The
   date is in the id so the age of every item is legible without a field, and so
   there is no counter to drift.

   **There is no `touched:` field and there will not be one.** Re-reading an item is
   not progress. A field the founder can update is the field the founder will use to
   keep a dead item alive forever, with a completely clear conscience, which is how
   every graveyard is built.
4. **Put it in exactly one section, and respect the cap.**

   - `## Doing` — **maximum three.** The founder is one person and the daily brief
     names one thing. To start a fourth, one of the three must close, block or drop.
     That forced choice on a Tuesday is the entire value of the cap; without it,
     `## Doing` becomes `## Queued` with better lighting.
   - `## Queued` — **maximum fifteen.** Fifteen is not taste, it is the age-out rule
     arriving three weeks early: 21 days is 15 working days is 15 daily briefs is 15
     one-things. A queue holding a sixteenth item is holding at least one item that
     is arithmetically certain to expire unstarted — it is already a graveyard, three
     weeks before it looks like one. Adding the sixteenth means dropping one first,
     and choosing which is the work. **If nothing can be dropped to make room, the new
     item is not important — it is just the newest.**
   - `## Blocked` — only with `blocked_by` naming another item's id. See step 6.
   - `## Done`, `## Dropped` — closed. Nothing returns from either. An item that
     comes back is a new item with a new id, and `## Dropped` is what lets `triage`
     see it come back.
5. **Close it by deciding what it emits.** Closing is not a tick. Half the
   obligations in this company resolve into the next obligation: *follow up with
   Anna* resolves into *draft the retainer proposal*, and if that proposal does not
   land in `## Queued` at the same moment, the follow-up was theatre and the queue
   just watched it happen.

   Every close writes `emits: q-XXXXx` or `emits: none`, explicitly. `none` is the
   more common answer and it must be said, because "what does this turn into?"
   asked at the close is the only time anybody knows.

   **At most one emit.** A close that wants to emit three items is not a close, it
   is a pile — hand it to `triage` and let it keep one.
6. **Unblock by lookup, not by memory.** An item is unblocked when **every id in its
   `blocked_by` sits in `## Done`.** That is a text lookup in one file, it needs no
   database, and it is correct even after the session that wrote it is long gone.

   **`blocked_by` names item ids. Never a person, never an event, never a date.**
   "Waiting for Anna to reply" is not a blocker, it is a hope, and this queue has no
   waiting state — waiting is how an item survives six months with a clean
   conscience. If Anna's reply is genuinely required, then chasing Anna is work the
   founder can do, and it is an item with an id: `[q-0716a] get the scope
   confirmation from Anna`. Block on that.

   **Every blocker is therefore something someone can do.** If you cannot name the
   item that unblocks it, it is not blocked — it is unstarted, and it goes back to
   `## Queued` where its clock runs.
7. **Sweep, every Friday.** Walk the clocks below, top to bottom, and act on each
   one in the file. Do not defer a reap to next week: a reaper that can be postponed
   is a reaper the founder will postpone every week for a quarter.

   The question they are avoiding, and the sweep should ask it out loud once:
   **which of these are you keeping because dropping it would mean admitting you were
   never going to do it?** Every item that answer applies to belongs in `## Dropped`
   today, and the founder will feel better on Monday than the item ever made them
   feel.

   Then report the counts — the line under `## Output`. The caller writes it up; the
   sweep just states the numbers.

## The clocks

Every section has a cap or a clock, and nothing is exempt from both:

| section | cap | clock | when it fires |
|---|---|---|---|
| `## Doing` | 3 | 5 working days from `started` | it is not an item, it is a project — split it into items that close in a day, or drop it |
| `## Queued` | 15 | 21 days from the id date | **dropped**, reason `aged out` |
| `## Blocked` | — | 14 days from `blocked` | dropped, or its blocker is promoted to `## Doing` — decide which, do not renew |
| `## Done` | — | 30 days | deleted. Done is evidence and its half-life is a month; `weekly-review` and `monthly-review` have both read it by then |
| `## Dropped` | — | 90 days | deleted |

**The 21 days is the rule that matters, and it is not negotiable by anybody.** An
item that has sat in `## Queued` for 21 days has been passed over by fifteen daily
briefs and three weekly reviews. It has been decided against fifteen times. All the
queue does is write down a decision the founder has already made, repeatedly, and
declined to say out loud. Drop it with `aged out` and move on.

Blocked runs a *shorter* clock than Queued, deliberately. Blocked feels like nobody's
fault, and that is exactly what makes it the back door to the graveyard.

**Five or more `bet: none` items in `## Queued` is a finding, not a queue problem.**
The founder's obligations and the quarter's bets have become two different
companies, and the bets are the one losing. Report it and hand to the **Strategist**:
either `goals.md` is wrong or the week is, and neither is fixed by re-sorting a
queue.

## Named failure modes

- **The graveyard.** Two hundred items, nobody opens it, the founder feels guilty
  every time they see the filename and eventually stops looking. It never arrives
  as a decision — it accumulates one reasonable-looking item at a time, and every
  single one of them was worth keeping on the day it went in. The caps and the
  clocks above are the only defence, and they only work if they are applied to items
  that are still, genuinely, worth keeping. That is the whole discipline: the reaper
  is meant to hurt slightly.
- **The back door.** `blocked_by: waiting on the client`. Not an id, not work, not
  anybody's — a permanent parking space with an alibi.
- **The treadmill.** *Follow up with Anna* emits *follow up with Anna again* emits
  *check whether Anna saw it*. **Three emits deep with no change in `pipeline.md`
  or `metrics.md` and it is not work, it is a relationship on hold.** Drop the chain
  and hand Anna to the **Network Manager**, who has a two-touch rule for precisely
  this and will not pretend the non-reply is a scheduling problem.

## Output

Rewrite `queue.md`. Five sections, exactly these headings, always all five, even
when a section is empty — an absent heading is the one that gets invented back with
a different spelling:

    ## Doing
    - [q-0715a] draft the retainer proposal for Anna — bet: B2 — started 2026-07-15
    ## Queued
    - [q-0714b] write the case study for the Northwind migration — bet: B1
    - [q-0709c] pay the overdue ZUS invoice — bet: none
    ## Blocked
    - [q-0710a] send Anna the retainer — bet: B2 — blocked_by: q-0715a — blocked 2026-07-12
    ## Done
    - [q-0708b] get the scope confirmation from Anna — bet: B2 — done 2026-07-14 — emits: q-0715a
    ## Dropped
    - [q-0620a] rebuild the website — bet: none — dropped 2026-07-14 — aged out; passed over by three weekly reviews

Every drop carries a reason. A drop with no reason is a delete wearing a section
heading, and a founder who catches the file deleting things stops trusting it — at
which point they have a to-do list again, in a different app, and this file is
furniture.

Then give the caller one line, before anything else it writes:

    Queue: doing <n>/3 | queued <n>/15 | blocked <n> | aged out this sweep <n> | bet:none <n>/<n>

## Guardrails

**The Chief of Staff writes this file. Nobody else** — house rule 4. Other agents
propose: they hand the obligation to the Chief of Staff by name, in the handoff, and
the Chief of Staff writes it here. An agent that writes `queue.md` itself has not
saved an obligation, it has broken the one property that makes a company of this
many agents safe to run against shared state.

And the honest cost of that, since the intake is two doors and not a sweep.
**Five cadences propose** — `pipeline-review` (Thu), `revenue-review` (1st),
`content-plan` (Wed), `quarterly-planning` (1 Jan/Apr/Jul/Oct) and
`follow-up-sweep` (Fri). Four of the five fire on a schedule with no founder and
no Chief of Staff in the room, so their handoff has nobody to hand to. Each
therefore leaves a `Proposed:` line in the section it owns, and the next
`daily-brief` drains all five — step 0 there, and it is the receiving half of
this guardrail.

**The residual hole, stated at its real size:** a proposal made on Wednesday
morning waits until Thursday 08:00, and one made on Friday afternoon waits until
Monday. Up to three days, on one weekday cadence out of five. That is a real hole
and it is smaller than the one it replaces — before the brief drained anything,
the obligation reached nothing, ever, on all five. Do not patch the rest by having
this skill read every agent's file; that is the averaging failure `context-load`
step 5 describes, and it would arrive here first. The brief is allowed to read
across books because ranking across books is its decision. This file's decision is
one item's fate, and it needs two doors to make it.

**Never mark a send done.** House rule 0: the founder sends. An item like `send Anna
the retainer` may sit in this queue — the queue holds it, the founder does it — but
this skill cannot know whether it went out, and drafting the thing is not sending
it. Close a send item only when the founder confirms it went, exactly as
`follow-up-sweep` refuses to count a sweep row as contact.

**Never renew an item.** No `bumped:`, no `priority:`, no second look that resets a
clock. The only way to keep an item alive is to move it to `## Doing` and actually
start it. Everything else is the item asking to be let off.

**Never rank `## Queued`.** It is a set, not a list. Ranking happens once a day, in
the daily brief, against `goals.md`, and its output is one item in `## Doing`. A
ranked queue is a to-do list with a state machine bolted on, and the founder will
work down it in urgency order the moment you leave — which is the failure `triage`
already names.

**Never let this file hold what another file owns.** Every duplicated item is a
future disagreement between two owners, and the founder will believe whichever one
they opened last.
