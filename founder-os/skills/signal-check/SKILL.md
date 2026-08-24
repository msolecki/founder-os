---
name: signal-check
description: Read the three behaviours the founder can still change this week and record them against their normal range — run Friday afternoon, before the weekly review scores the week
metadata:
  writes:
    - metrics.md
---

# Signal Check

`metrics.md` holds Close, Runway, Profitability and Rate. All four describe a
month that is over. They are the right numbers and they arrive too late to
change anything: by the time the close says revenue fell, the quarter that
caused it happened eleven weeks ago.

`## Signals` is the other kind. Three behaviours, read weekly, each one
something the founder can do differently on Monday. It exists so `weekly-review`
can say *you are having fewer conversations than you were in March* — which is
a sentence no lagging measure can produce, and the only sentence that arrives
early enough to matter.

## When to use

Every Friday, before `weekly-review`. The order is load-bearing: the review
reads this section, and a review that reads last week's signals scores the
wrong week.

Also when the founder says a month was bad and cannot say what they did
differently. That is the question this section answers and nothing else in the
workspace does.

## Inputs

Read first — house rule 1. This cadence's licence is exactly this list, fixed in
the package — `context-load` step 5 — and the bound is **sections, not files**:

- `metrics.md` `## Signals` — the three signals already chosen and their last
  four readings. Which three they are is not decided again every week; see
  step 2.
- `pipeline.md` `## Live` — the conversation count, read from the deals that
  already exist there.
- `drafts/proposals/` `## Sent` — what actually went out, as the founder
  reported it. Never `## Draft`; a body on disk is not a sent body.
- `content.md` `## Shipped` and `network.md` `## Sweep` — the two other places a
  weekly behaviour is already recorded, read only when a signal names one as its
  source.

Nothing here is counted by hand and nothing new is asked of the founder. Step 2
is why.

## Beliefs

- A signal the founder has to count by hand does not survive its third week. The
  measurement everyone agrees is the right one and nobody performs on a Friday
  afternoon is worth less than a rough one read off a file that already exists —
  and the rough one has the enormous advantage of still being there in November.
- A lead measure is only a lead measure if a different Monday changes it.
  Revenue is not a signal. Conversations booked is. The test is not whether the
  number predicts anything; it is whether it sits under the founder's hand, and
  most proposed signals fail that test while passing every other one.
- Three is the cap, and the fourth signal is always the most interesting one in
  the room. Six rows is a dashboard, and a dashboard gets read the way weather
  gets read: with genuine interest and no consequence.
- Changing which three you track resets the series to zero, and almost every
  request to swap one arrives in the week it reads badly. The swap will be
  argued on the merits and it will be correct on the merits, and it will still
  cost the founder the only comparison that was going to tell them anything.
- A signal outside its range is not automatically a problem, and this is the
  belief that keeps the section usable. The range makes the reading legible; a
  founder who acts on every deviation has traded a measure that arrives late for
  one that is wrong every third week.

## Steps

1. **Read the existing three.** If `## Signals` is empty this is a first run and
   step 2 applies in full. If it is not, the three are already chosen and step 2
   is a check, not a selection.
2. **Derive each signal from state that already exists.** A signal is legal only
   when its value can be read out of a file some other cadence already
   maintains — `pipeline.md` `## Live`, `drafts/proposals/` `## Sent`,
   `content.md` `## Shipped`, `network.md` `## Sweep`, `week.md` `## Ledger`.
   **If a candidate signal requires the founder to record something new, refuse
   it and say so.** The refusal is not a limitation of this skill; it is the only
   reason the section will still be accurate in six months.
3. **Cap at three, and make the fourth cost something.** To add one, name which
   of the three it replaces and write the swap with its date, so the reset in
   the series is visible rather than discovered later as a gap. **Never swap in
   a week the signal reads badly** — that week, the answer is no, and the reason
   is in `## Beliefs`.
4. **Read each value with the date you read it.** Not today's date by default —
   the date of the state you read. A count taken from a `pipeline.md` that was
   last touched on Tuesday is a Tuesday number, and saying so is the difference
   between a measurement and a claim.
5. **State the normal range, and state it from the readings you have.** With
   fewer than four readings there is no range yet — write `range: not yet` and
   do not invent one. A range guessed in week one becomes the target the founder
   manages against for a quarter.
6. **Name what moved, in one sentence, or say nothing moved.** One sentence, and
   only for a signal outside its range or crossing into it. A weekly commentary
   on three numbers that did not move is how this section becomes furniture.
7. **Write `## Signals` and touch nothing else in `metrics.md`.** Close, Runway,
   Profitability and Rate belong to the monthly cadences. A weekly skill that
   edits a monthly close is the failure `state-integrity` exists to catch.

## Named failure modes

- **The vanity three.** Followers, page views, newsletter subscribers. Each is
  real, each is under the founder's hand, and none of them has ever changed what
  the company does on Monday. The test in `## Beliefs` is not "can I move it" —
  it is "would a bad reading make me do something different this week".
- **The signal with a target.** Someone writes `conversations booked: 4 (target
  6)` and the number is now a score. Within a month it reads 6 every week and
  two of them are calls that would not have been booked otherwise. A range says
  what normal is; a target says what to produce.
- **The quiet reset.** A signal is swapped, the section still shows four
  readings, and three of them are from a different measurement. Step 3 makes the
  swap dated and visible for exactly this reason.
- **The Friday that never happens.** The section holds three signals read six
  weeks ago and nothing says so. The `Read:` date is the guard: `weekly-review`
  reads it, and a signals block older than 14 days is reported as stale rather
  than quoted.

## Output

Rewrite `metrics.md` `## Signals`, in place, one block, always all three lines
even when a value is zero:

    ## Signals

    Read: 2026-08-21 — week 2026-W34

    - Conversations booked — source: pipeline.md ## Live — 4 — normal 3-6 — last four: 6, 5, 6, 4
    - Proposals sent — source: drafts/proposals/ ## Sent — 1 — normal 1-2 — last four: 2, 1, 1, 1
    - Case studies shipped — source: content.md ## Shipped — 0 — normal 1 — last four: 1, 1, 0, 0

    Moved: case studies shipped, second week at zero against a normal of 1.

    Swapped: none

`last four` is a rolling window of four readings and never grows past four. A
year of weekly history in a file the CFO rewrites monthly is an archive, and the
comparison that matters — this week against a normal month — needs four numbers,
not fifty-two.

Then give the caller one line, before anything else it writes:

    Signals: read <date> | outside range <n>/3 | swapped <n> | stale <yes|no>

## Guardrails

**Never invent a signal that needs manual counting**, however good it is. The
founder will agree to it in the session and stop doing it in week three, and the
section will then hold a number that is quietly six weeks old.

**Never write a target next to a signal.** The range is the whole vocabulary
here. A target turns a measurement into a performance, and the founder is both
the performer and the only audience.

**Never touch `## Close`, `## Runway`, `## Profitability` or `## Rate`.** They
are the same file and different cadences, and a weekly job that edits a monthly
close is how `metrics.md` starts disagreeing with itself.

**Never read a signal out of `## Draft`.** A proposal body on disk is not a
proposal sent — house rule 0, and `## Sent` is the founder's own report. A
signal that counts drafts measures this package's output, not the founder's.

**Never swap a signal to make the section read better**, and say plainly when
that is what is being asked. The request always arrives with a sound argument
attached, and the week it arrives is the evidence.
