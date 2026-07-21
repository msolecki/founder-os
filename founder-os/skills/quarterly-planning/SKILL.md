---
name: quarterly-planning
description: Close last quarter's bets with verdicts and commit at most three new ones, each with a kill condition — run in the first days of the quarter, once the numbers that settle the old one are in
metadata:
  writes:
    - goals.md
    - reviews/quarterly/
---

# Quarterly Planning

A bet without a kill condition is a hope, and hopes do not get killed — they
get rolled forward. Roll four hopes forward three times and the founder has
eleven active priorities, no wins, and a strong sense of being busy.

The planning half of this skill is easy and the founder will enjoy it. The
first step is the one that matters.

## When to use

**The first days of the quarter**, once the CFO's close for the final month is in
`metrics.md`. If the founder ran `/setup-cadences`, a cron job fires this on day
1 — 1 January, 1 April, 1 July, 1 October.

At the start and not the end, because **step 1 is not optional and it is not
possible early**. Verdicting a quarter in its last week means verdicting it
against numbers that are not in yet: two bets are pending, the close has not
landed, and the founder marks them won because the week has been going well.
A quarter you judge before it ends is a quarter you judge on mood, and this
skill's whole argument is that "never measured" is the most damning verdict
available. Wait the four days. Judge the finished thing.

Never mid-quarter. A new opportunity mid-quarter is `bet-sizing`, and an
underperforming bet mid-quarter is `kill-or-continue` — neither is a reason to
reopen the plan, and reopening the plan is how the quarter's commitments become
suggestions.

If `metrics.md` has no close for the quarter's final month, stop and hand to the
**CFO** — the same rule `monthly-review` runs on. Step 1 has nothing to settle
verdicts with and the rest of this skill is built on step 1.

## First-run branch

Use this branch only when `/founder-os-init` invokes the skill, `goals.md` has
no bets and `reviews/quarterly/` has no prior quarter. It creates a truthful
partial-quarter starting state, not a fictional recurring review. Record the
run date as `YYYY-MM-DD`.

Commit the first bet only when all five fields are non-empty and valid: numeric
outcome, numeric kill condition, hours cap, cash cap and one concrete first
move that can start within 21 days. Otherwise persist the blocked state.

| Input state | Completion rule | Required action |
|---|---|---|
| `complete onboarding answer` | Outcome, failure threshold, hours and cash cap are supplied. | Write one partial-quarter bet opened mid-quarter; preserve the supplied 90-day horizon, which may cross a calendar-quarter boundary; include the numeric outcome, kill condition, hours, cash cap and one first move. |
| `outcome unknown` | The numeric outcome is `UNKNOWN`. | Write a blocked first-run state, do not commit a bet, and hand the missing number to the Chief of Staff for the queue. |
| `kill condition unknown` | The numeric failure threshold is `UNKNOWN`. | Write a blocked first-run state, do not commit a bet, and hand the missing kill condition to the Chief of Staff for the queue. |
| `hours unknown` | Available hours are `UNKNOWN`. | Write a blocked first-run state, do not commit an unsized bet, and hand the hours question to the Chief of Staff for the queue. |
| `cash cap unknown` | Available cash cap is `UNKNOWN`. | Write a blocked first-run state, do not commit an unsized bet, and hand the cash-cap question to the Chief of Staff for the queue. |
| `first move unknown` | No concrete first move can be named from the persisted result. | Write a blocked first-run state with first move `UNKNOWN`, do not commit a bet, and hand the missing first move to the Chief of Staff for the queue. |

On the complete path, write one `### Bet` under `goals.md` `## Bets`:

    # Partial quarter — as of YYYY-MM-DD
    ## Bets
    Activation status: ready
    Proposed: <first move> — bet: B1
    ### Bet B1: <name>
    Status: first-run 90-day bet opened mid-quarter
    Start date: YYYY-MM-DD
    Judgment date: <the supplied 90-day horizon; exactly 90 days after start>
    Outcome: <metric> reaches <numeric value> by <date>
    Cost: <supplied hours> h + <supplied cash cap>
    Kill if: <metric> is below <numeric threshold> on <date>

If any required field is unknown or invalid, write the same dated `## Bets`
section with `Activation status: blocked`, `Status: blocked — <field>:
UNKNOWN` and `Proposed: resolve <field> — bet: none`; do not create a `### Bet`
block. This is resumable evidence, not activation readiness. Hand that proposal
to the Chief of Staff, who owns `queue.md`, without inventing an answer.

For `reviews/quarterly/YYYY-Qn.md`, use the recurring section vocabulary while
making the absent history explicit:

    # YYYY-Qn — first run on YYYY-MM-DD
    ## Last quarter's verdicts
    Not applicable — first run; no prior bets or review.
    ## Never measured
    Not applicable — no prior bets existed to measure.
    ## This quarter's bets
    <the first-run bet above, or blocked state with UNKNOWN>
    ## What we are not doing
    UNKNOWN — no alternatives were supplied during onboarding.

Never create wins, losses or a never-measured count. Skip recurring Steps 1, 2
and 7 because there is no record. Step 6 still applies to a complete answer.
Future quarter plans must return to the recurring path: verdict every prior bet
and run `red-team` before writing. "Never mid-quarter" governs reopening a
plan, not creating the first one. Here, "partial-quarter" means opened partway
through the current calendar quarter: preserve the supplied 90-day judgment
horizon even when it crosses the next quarter boundary, and size capacity from
the start through that date.

## Inputs

Read first, in order — house rule 1:

- `goals.md` — the bets currently committed, and their thresholds
- `metrics.md` — the numbers that settle each verdict, and the close date
- `reviews/quarterly/` — the last two quarters: what was promised, twice. Empty
  on a first run, and that is a state rather than a fault — see the first-run
  branch above.
- `charter.md` — what the business is for, in case three quarters of drift have
  quietly answered that question differently

## Beliefs

- "Never measured" is a worse verdict than "lost". A lost bet bought information
  and can be reasoned from; an unmeasured bet consumed a quarter and returned
  nothing — and it is the one the founder will file under "we learned a lot".
  Read the count out before anyone is allowed to enjoy the new plan.
- A quarter is thirteen weeks and every founder plans for about eighteen. This is
  not a discipline problem to be exhorted away: it is the base rate, it is in
  `reviews/quarterly/` in their own handwriting, and the correct response is to
  commit three bets rather than to promise better execution.
- Optimism is not the enemy of a plan — it is the reason the plan exists. What
  kills the quarter is optimism with no date attached. A kill condition expresses
  no doubt about the bet; it is what makes committing to it a decision rather than
  a mood.
- The bet the founder least wants to cut is usually the one with the most already
  spent on it, not the one most ahead of its case. Capacity does not know the
  difference, and neither does the quarter.

## Steps

1. **Close the old quarter first. Verdict every bet, no exceptions.** Won,
   lost, or **never measured** — against the threshold written in `goals.md`,
   using a number from `metrics.md`. "Never measured" is the most common verdict
   and the most damning one: it means the bet shipped without a threshold, and
   the quarter therefore produced no information. Count how many. That count is
   the honest score of last quarter's planning, not the wins.
2. **Catch the silent rollover.** Any bet appearing in two consecutive quarters
   without a verdict was never a bet. It may be re-bet — explicitly, with a new
   threshold and a new date — but it does not get to continue by inertia.
3. **Cap at three.** Three bets. Four only if one of them is maintenance. Six is
   zero, and a founder who commits to six has committed to whichever one is
   loudest in week three. If the founder insists on six, write three and say the
   other three did not make the cut — a list you know is fiction is worse than a
   short list they resent.
4. **Give each bet a measurable outcome from the CFO's vocabulary.** The outcome
   must be a number that already exists in `metrics.md`. If it does not, either
   the **CFO** starts tracking it before the quarter starts, or the bet does not
   ship. A bet measured by a number nobody collects will be judged on vibes in
   thirteen weeks — that is exactly how step 1's "never measured" pile got so
   large.
5. **Give each bet a kill condition.** A value and a date, below which it stops.
   Written now, while the bet is cheap to abandon and nobody has spent anything
   on it. This is the single hardest sentence to write later, and
   `kill-or-continue` is worthless without it.
6. **Size each bet before committing it.** Hand to `bet-sizing`. An unsized bet
   does not enter `goals.md`.
7. **Send the plan to the Board Member.** `red-team` before you write. You pick
   the direction; they tell you if it holds. If you find yourself defending the
   plan instead of forwarding it, that is the signal to forward it.
8. **Write `goals.md`, then `reviews/quarterly/`.** `goals.md` is the live plan;
   the review is the record of what was decided and what last quarter returned.
9. **Propose the first move on each bet to the Chief of Staff — and almost nothing
   else.** A quarter is thirteen weeks; `queue.md` runs a 21-day clock. Most of
   this plan is therefore not queue work, and putting it there would be a lie with
   an id attached: an item dated for September ages out in August having never
   been startable, and it gets dropped with the reason `aged out`, which is false.
   It was not passed over — it was not due. Work dated for September belongs to
   whoever owns September. A quarter is held in `goals.md`, which you just wrote,
   and a bet is not an obligation — it is a wager with a kill condition.

   What escapes is the first move: the one thing per bet that must happen inside
   three weeks or the bet has not started. **One per bet, three maximum**, because
   step 3 caps the bets at three and a bet with two first moves has not been
   sized.

   Hand them to the **Chief of Staff** with each bet named — you do not write
   `queue.md`, because what deserves a slot is decided against everything else the
   founder owes, and this skill has spent the last hour looking at thirteen weeks
   rather than at Tuesday. Three items on day 1 is already a fifth of the cap. **If
   `## Queued` cannot take them, that is the finding, and it is a better one than
   anything in this plan:** the founder is opening a quarter with a queue still
   full of last quarter's obligations, and no new plan has ever fixed that.

## Output

Replace `goals.md` with this quarter's bets:

    # Q<n> YYYY
    ## Bets
    Proposed: <first move> — bet: B<n> | none
    ### Bet <n>: <name>
    Outcome: <metric that exists in metrics.md> reaches <value> by <date>
    Cost: <hours> h + <cash>   (from bet-sizing)
    Kill if: <metric> is below <value> on <date>

**`Proposed:` is how step 9's handoff survives the 1st at 11:00 with nobody in
the room.** One line per bet's first move, three maximum, under `## Bets` and
above the bet blocks; the next `daily-brief` drains them — step 0 there. This is
the cadence where losing the handoff costs most: a quarter whose three first
moves never reached the queue is a quarter that was planned and not started, and
nothing will notice until the verdicts in October.

`## Bets` is the section `ownership.yaml` pins for `goals.md` and it is the one
`founder-os-init` scaffolds; the bets are `###` blocks under it. `bet-sizing`
appends `Cost:` and `Cap:` to a bet's block and `kill-or-continue` writes its
verdict line there — both need to find the block, and they find it under this
heading.

Append to `reviews/quarterly/YYYY-Qn.md`:

    # YYYY-Qn
    ## Last quarter's verdicts
    - <bet>: won | lost | never measured — <number from metrics.md, dated>
    ## Never measured
    <N of M> — <what that says about last quarter's thresholds>
    ## This quarter's bets
    <the three, with kill conditions>
    ## What we are not doing
    <what was cut to make three fit>

## Guardrails

Never carry a bet forward without a verdict. Re-betting is allowed; drifting is
not, and the difference is a date.

Never write a bet whose kill condition is a feeling. "Kill if it isn't working"
survives every quarter.

You do not own `metrics.md` or `offer.md`. If the plan needs a new metric, the
**CFO** adds it. If it changes what the company sells, the **Positioning
Advisor** writes `offer.md`. If the plan is irreversible, the **Chief of Staff**
logs it in `decisions/` — you do not write there.
