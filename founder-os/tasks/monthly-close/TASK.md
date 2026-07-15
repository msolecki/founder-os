---
name: Monthly Close
assignee: cfo
metadata:
  skill: revenue-review
schedule:
  timezone: UTC
  recurrence:
    frequency: monthly
    interval: 1
    monthdays: [1]
    time: { hour: 9, minute: 0 }
---

Run the `revenue-review` skill — the monthly numbers close, written to
`metrics.md`.

This task invokes `revenue-review`, not `monthly-review`. That is deliberate:
the CFO closes the numbers, and the Chief of Staff's `monthly-review` is a
separate retrospective the founder runs when they want it. Scheduling both
would create two competing monthly rituals.
