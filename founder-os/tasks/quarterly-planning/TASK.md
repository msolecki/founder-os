---
name: Quarterly Planning
assignee: strategist
metadata:
  skill: quarterly-planning
schedule:
  timezone: UTC
  startsAt: 2026-01-01T11:00:00Z
  recurrence:
    frequency: monthly
    interval: 3
    monthdays: [1]
    time: { hour: 11, minute: 0 }
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

**`startsAt` is the anchor and it is a calendar quarter boundary on purpose.**
`interval: 3` counts from the first fire, not from the calendar: without an
anchor, installing in February gives you Feb / May / Aug / Nov forever, while the
skill writes `reviews/quarterly/YYYY-Qn.md` — a filename asserting a calendar
quarter the schedule never honours. Anchored to 1 January, the interval lands on
1 Jan / 1 Apr / 1 Jul / 1 Oct regardless of install date.

`founder-os-init` moves this date forward to the next quarter boundary in the
founder's own timezone, because 09:00 UTC is not 09:00 anywhere else and a
boundary in the wrong zone is not a boundary. Re-run init's step 3 after any
package update — an update restores the shipped values here, and this schedule
fails quietly rather than loudly.
