---
name: Daily Brief
assignee: chief-of-staff
recurring: true
metadata:
  skill: daily-brief
---

Run the `daily-brief` skill.

The schedule lives in `.paperclip.yaml` under `routines.daily-brief`, not here.
Its trigger ships as `timezone: UTC` and `founder-os-init` rewrites it during
onboarding. If you installed this package manually, set it to your own timezone
— a brief that fires at 3am is a brief you will turn off.
