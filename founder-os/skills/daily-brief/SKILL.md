---
name: daily-brief
description: Open the day with the one thing that matters — run every weekday morning before the founder picks their own work
metadata:
  writes:
    - reviews/daily/
    - inbox.md
---

# Daily Brief

The founder's inbox will happily fill the day with other people's priorities.
This is the fifteen minutes that decides whether today moved the quarter.

## When to use

Weekday mornings, before opening email. Triggered automatically by
cron, if the founder ran `/setup-cadences`. Otherwise `/daily-brief`, by hand.

## First-run branch

Use this branch when `/founder-os-init` invokes the skill and there is no prior
daily review. Read the persisted owner outputs; do not reconstruct a history
that predates `YYYY-MM-DD`. `UNKNOWN` is eligible work when it blocks the
financial baseline, not a reason to invent a normal-looking day.

| Persisted state | Selection rule | Required action |
|---|---|---|
| `first move available` | Cash and real burn are known and `goals.md` carries a first move. | Make that first move `## The one thing`, preserving its bet link. |
| `cash on hand unknown` | Runway is blocked by cash on hand. | Make `resolve cash on hand` `## The one thing` and keep or add that item in `## Doing`; it outranks a planned bet move. |
| `burn unknown` | Cash is known but real monthly burn is missing. | Make `resolve real monthly burn` `## The one thing` and keep or add that item in `## Doing`; it outranks a planned bet move. |
| `no prior review` | No daily commitment has started a clock. | Write `Rotting: none — first run; no historical clock`; do not assign ages to empty clients, pipeline or review files. |
| `first move unknown` | Financial inputs are known but no owner-persisted first move exists. | Write the blocking first move as `UNKNOWN`, keep activation incomplete, and do not invent work. |

Write the same owned daily-review headings as every later brief:

    # YYYY-MM-DD
    ## The one thing
    [<existing queue id, or new id from queue>] <financial blocker or first move>
    ## Rotting
    none — first run; no historical clock
    ## The trade
    <what the selected blocker or move displaces today>
    ## Triage
    none

When the cash or burn item already exists in `queue.md`, reuse its id and move
it through `queue`; do not create a duplicate. The Chief of Staff owns both the
queue and daily review, so this is an ordinary owner-safe transition. On the
next day, leave this branch and apply the recurring Steps below to actual
history.

## Inputs

Read first, in order — house rule 1. **This list is longer than `context-load`
step 5 allows, and the exemption is written in that file as well as this one.**
Read it there: the brief is the only cadence whose decision is the ranking
*across* books, so it is the only one that cannot make its decision from two of
them. The price is that only the first three below are read whole; everything
else is one named section, read for one question.

Read whole:

- `charter.md` — what this business is, and therefore what to ignore. Mandatory
  under `context-load`; the brief was skipping it and ranking a day against a
  business nobody had described.
- `goals.md` — what this quarter is actually for
- `queue.md` — `## Doing` first: what the founder already has in flight, and how
  long it has been in flight. Yesterday's commitment is an item here, not a
  memory, and whether it closed is a fact rather than a conversation.
- `reviews/daily/` — yesterday's brief: what did they commit to?

Read for one named section only:

- `metrics.md` — the receivable lines under `## Close`. An invoice past terms is
  already in this skill's rotting definition, and until now it was rotting in a
  file the brief never opened. Not the effective rate, not the concentration, not
  the runway — those are the **CFO's** to narrate and reading them here is how a
  brief becomes a monthly close nobody asked for.
- `pipeline.md` — anything with a next action dated today or overdue
- `clients/<client>.md` `## Health` — the latest `Verdict:` line on each active
  engagement, **with its date**. `at-risk` or `failing` is rotting; `healthy`
  is not. That is `client-health`'s vocabulary and those are the only three
  words it writes. A verdict older than 45 days is not a verdict — it is a
  memory of one, and quoting it as current is how a client dies between
  check-ups. Read it as "no current verdict — `client-health` overdue", which
  is itself a rotting item, dated from the stale verdict.
- `offer.md` `## ICP` `### Not this` — who this company decided not to serve. A
  client on the books that the offer excludes is rotting, and it is the one
  rotting item no other file can see: `clients/` knows the engagement is healthy
  and `pipeline.md` knows the deal was won. Only the exclusion knows it should
  never have been taken.
- `pipeline.md`, `content.md`, `network.md` and `metrics.md` `## Close` — the
  `Proposed:` lines, and nothing else; `goals.md` is read whole above, so the
  quarterly's line arrives on its own. Step 0. (`## Close` was already open for
  the receivables, so this widens nothing.)

## Beliefs

- The founder already knows what they should do today. What they will not say
  out loud is what it costs, and that is the only line in this brief they cannot
  write for themselves.
- The loudest thing and the oldest thing are rarely the same thing, and only the
  oldest is rotting. Anxiety tracks who is watching an item, not how long it has
  been decaying — which is why the item the founder opens with is the one you
  rank last.
- Being behind is a finding, not an apology. The founder arrives with the reason;
  take the number instead. Three days on the same unstarted commitment says the
  thing was chosen wrong three times, and no reason has ever fixed that.
- A day fits one thing. The founder believes it fits three because it did once,
  and `reviews/daily/` records how often that has repeated since. Read it back
  before agreeing to the second.

## Steps

0. **Drain the proposals, before you rank anything.**

   **Drain `inbox.md` first, before the `Proposed:` lines.** The founder wrote those
   lines themselves, which makes them the only input to this brief that is not an
   agent talking to another agent. Empty the file to zero: every line becomes a
   queue item under the `queue` intake rule, or it is named in the brief as refused
   with the owner whose file already holds it. Nothing stays.

   If the inbox holds more than the brief can rank, that is `triage`'s pile and this
   is not the cadence for it — say so, hand to `triage`, and still empty the file.

   Eight cadences produce obligations and none of them may write `queue.md` —
   `pipeline-review`,
   `revenue-review`, `content-plan`, `quarterly-planning`, `follow-up-sweep`, and
   the three draft skills, `outreach-draft`, `proposal-draft` and `content-draft`.
   All eight hand to the **Chief of Staff** by name. Five of them fire on a
   schedule, with nobody in the room to hand to; the three draft skills run with
   the founder present, so those the founder can hand over directly. **You are
   the Chief of Staff and this is the room.** Each leaves a `Proposed:` line in the
   section it owns; you read those sections; you take the item or you refuse it.

   **Eight cadences, still five sections, no new file.** `outreach-draft` and
   `proposal-draft` propose into `pipeline.md`; `content-draft` proposes into
   `content.md`. You already open both. This does not widen the `context-load`
   exemption you run under, and that is not luck — the draft skills propose into
   the file they already own precisely so that the brief's read set could stay
   where it is. A draft skill that wanted a book of its own would have cost you the
   exemption, and `context-load` step 5 is where that argument gets settled, not
   here.

   Run `queue` on each. Taking it means an id and a bet. **Refusing it is equally
   a result and it must be said out loud** — name the owner whose file already
   holds the thing, exactly as the intake rule requires. A proposal that is
   neither taken nor refused has not been deferred, it has evaporated, which is
   the failure `queue.md` was built to stop and the one it relocated one level up.

   Every item you take carries `from: <file> <date>` — the proposal it came from.
   That is not a field the founder can renew and it is not a priority: it is a
   lookup, so tomorrow's brief can see this proposal was already answered and
   leave it alone. Without it the Thursday pipeline proposal enters the queue
   again on Friday, and again on Monday, under three ids.

   **Then stop.** The proposals are an intake, not the brief. If draining them
   fills `## Doing` to its cap of three, that is step 2's finding arriving early —
   say it there, not here.

1. **Check yesterday's commitment, in `## Doing`.** Did it happen? If it did,
   close it — run `queue`, which will ask what it emits, because *follow up with
   Anna* resolving into *draft the proposal* is the moment that proposal either
   gets an id or gets forgotten. If it didn't and it's the third day running,
   that is the brief — say so, and stop pretending the problem is today's plan.
2. **Name one thing, and give it an id.** Exactly one, and tie it to a bet in
   `goals.md`. If nothing on today's list ties to a bet, that is the finding.

   Then run `queue`: the one thing goes in `## Doing` and the brief quotes its
   id. This is not bookkeeping — a brief whose one thing exists only in
   `reviews/daily/2026-07-15.md` is advice with a one-day shelf life, and
   tomorrow's brief has no way to ask whether it happened.

   **If `## Doing` is already at its cap of three, that is today's brief.** Do
   not name a fourth. Three things in flight and a fourth being started is not a
   busy week, it is the mechanism by which none of the three finish — and the
   founder is about to do it again. Close one, block one, or drop one first.
3. **Name what's rotting — at most three, ranked by days.** An overdue pipeline
   action, a client whose `Verdict:` is `at-risk` or `failing`, an invoice past
   terms, a client whose latest `Verdict:` is older than 45 days (`client-health`
   overdue — an unexamined client is not a healthy one, it is an unexamined
   one), a `## Dead` deal whose `win/loss: pending` is older than 5 business days (the
   lesson is expiring — `win-loss-analysis`'s own window is five business days), **a client
   on the books that `offer.md` `### Not this` excludes**. One line each with
   the number of days attached, no editorializing.

   The excluded client is the odd one out and it is the most valuable line this
   brief ever produces. The others rot on a clock — days past terms, days
   since contact, days since a verdict. That one has been wrong since the day
   it was signed and no clock will ever fire on it, because the engagement is
   healthy, the invoices clear, and every file in the workspace is content.
   Date it from the day the
   exclusion was written, not from the engagement: the founder decided against
   this client on that date and has been serving them every day since.

   **Ranked by age, not by anxiety.** The loudest item is rarely the oldest, and
   the oldest is the one that is actually rotting — the founder already knows
   about the thing they are worried about, which is precisely why it is not the
   finding.

   **Above three, stop listing and hand the pile to `triage`.** Three is a
   warning; six is wallpaper. A brief carrying six warnings is the to-do list
   this skill exists not to produce: the founder reads two, feels behind, and
   opens email — which is the exact morning this cadence was built to prevent.
   More than three things rotting at once is not a briefing problem, it is an
   unsorted pile, and the **Chief of Staff** has a skill for that.
4. **Say what today costs.** If the founder does the one thing, what doesn't
   happen? Make the trade explicit — a plan with no cost is a wish.

5. **On an empty input, say so in one line and do not fill the gap.** `clients/`
   is empty on day one and stays empty until the first engagement; `reviews/daily/`
   is empty until tomorrow; `pipeline.md` is empty until the Pipeline Coach has
   run once. *"No clients on the books yet, so nothing to score"* is a true line
   that costs four words. The brief that invents a rotting item to look useful on
   a thin workspace has taught the founder on day one that this file is padded,
   and they will read it accordingly for as long as they keep it.

   This is not only onboarding's problem. The activation receipt explains the
   first day's thinness; **day two's 08:00 cron brief has the same three empty
   inputs and nothing to explain them.** The rule lives here for that morning.

## Output

Append to `reviews/daily/YYYY-MM-DD.md`:

    # YYYY-MM-DD
    ## The one thing
    [q-MMDDx] <what, and which bet it serves>
    ## Rotting
    - <item> — <n> days          (oldest first, 3 maximum)
    - <item> — <n> days
    <"+<n> more — handed to triage", if there were more than three>
    ## The trade
    <what doesn't happen today>
    ## Triage
    none | <+n items handed to triage>

## Guardrails

Do not produce a to-do list. The founder has one, and it is the problem. One
thing, one trade, what's rotting. Nothing else.

**Never read `## Queued` out.** The queue exists so the brief does not have to
carry fifteen items; a brief that recites them has rebuilt the to-do list out of
the very file that was supposed to retire it, and it does it while sounding
organised. You read `## Doing`. You write one item into it. `## Queued` is swept
on Friday by `weekly-review`, not narrated on Tuesday.

Do not motivate. If the founder is three days behind, say so flatly and move on.
