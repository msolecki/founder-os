---
name: quarterly-planning
description: Close last quarter's bets with verdicts and commit at most three new ones, each with a kill condition — run in the last week of the quarter
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

Last week of the quarter. Triggered automatically by `tasks/quarterly-planning`.

Never mid-quarter. A new opportunity mid-quarter is `bet-sizing`, and an
underperforming bet mid-quarter is `kill-or-continue` — neither is a reason to
reopen the plan, and reopening the plan is how the quarter's commitments become
suggestions.

## Inputs

Read first, in order — house rule 1:

- `goals.md` — the bets currently committed, and their thresholds
- `metrics.md` — the numbers that settle each verdict, and the close date
- `reviews/quarterly/` — the last two quarters: what was promised, twice
- `charter.md` — what the business is for, in case three quarters of drift have
  quietly answered that question differently

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

## Output

Replace `goals.md` with this quarter's bets:

    # Q<n> YYYY
    ## Bet <n>: <name>
    Outcome: <metric that exists in metrics.md> reaches <value> by <date>
    Cost: <hours> h + <cash>   (from bet-sizing)
    Kill if: <metric> is below <value> on <date>

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
