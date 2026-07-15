---
name: Pipeline Review
assignee: pipeline-coach
metadata:
  skill: pipeline-review
schedule:
  timezone: UTC
  recurrence:
    frequency: weekly
    interval: 1
    weekdays: [thursday]
    time: { hour: 10, minute: 0 }
---

Run the `pipeline-review` skill. Every prospect gets a next action with a date,
or it leaves the pipeline.
