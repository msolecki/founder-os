---
name: Daily Brief
assignee: chief-of-staff
metadata:
  skill: daily-brief
schedule:
  timezone: UTC
  recurrence:
    frequency: weekly
    interval: 1
    weekdays: [monday, tuesday, wednesday, thursday, friday]
    time: { hour: 8, minute: 0 }
---

Run the `daily-brief` skill.

`timezone` ships as UTC and is rewritten by `founder-os-init` during
onboarding. If you installed this package manually, set it to your own
timezone — a brief that fires at 3am is a brief you will turn off.
