---
name: Follow-up Sweep
assignee: network-manager
metadata:
  skill: follow-up-sweep
schedule:
  timezone: UTC
  recurrence:
    frequency: weekly
    interval: 1
    weekdays: [friday]
    time: { hour: 14, minute: 0 }
---

Run the `follow-up-sweep` skill. Anyone gone cold past their interval, with a
reason to reconnect that isn't "checking in".
