---
name: Quarterly Planning
assignee: strategist
recurring: true
metadata:
  skill: quarterly-planning
---

Run the `quarterly-planning` skill. Verdict last quarter's bets, then set this
quarter's — each with a kill condition, because a bet without one is a hope.

Fires on day 1 of the quarter, not in the last week of the outgoing one. You
cannot verdict a quarter that has not finished, and step 1 of the skill is the
verdicting: judged early, the bets still pending get marked won on optimism, and
"never measured" — the finding this skill exists to surface — never gets counted.

**11:00, behind `monthly-close`, which fires the same morning at 09:00.** The
skill refuses to run without the final month's close in `metrics.md`, so the two
tasks are ordered, not merely coexisting on the 1st. The gap is the CFO's window.
If the close is still not in, the skill stops and hands to the CFO rather than
verdicting a quarter against last month's numbers.

**The cron names the months, so the quarters are real ones.** The schedule lives
in `.paperclip.yaml` under `routines.quarterly-planning`: `0 11 1 1,4,7,10 *`
fires 1 Jan / 1 Apr / 1 Jul / 1 Oct from any install date. This was once a
`monthly` recurrence with `interval: 3`, which counts from the first fire rather
than from the calendar — installing in February bought you Feb / May / Aug / Nov
forever, while the skill writes `reviews/quarterly/YYYY-Qn.md`, a filename
asserting a calendar quarter the schedule never honoured. It was worse than that
in practice: the importer rejected a monthly interval above 1 outright, so the
cadence returned no trigger and never fired at all.

`founder-os-init` sets the trigger's timezone during onboarding. There is no
start date to move forward — a cron anchored to named months cannot drift. Re-run
init's step 3 after any package update: an update restores `timezone: UTC` on the
trigger, and this schedule fails quietly rather than loudly.
