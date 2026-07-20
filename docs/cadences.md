# Cadences and scheduling

Most tools wait to be opened. A personal-development tool that only runs when you
remember to run it is the failure mode of every productivity system ever shipped.
Founder OS can run on a **schedule** instead: a brief every weekday morning, and a
cadence for every file that rots.

Every cadence is also just a normal skill you can type by hand. The rhythm is the
point, not the mechanism.

## The 10 cadences

| Command | When | Run by |
|---|---|---|
| `/daily-brief` | weekdays 08:00 | chief-of-staff |
| `/portfolio-review` | Monday 08:15 *(multi-business only)* | portfolio-manager |
| `/week-plan` | Monday 08:30 | focus-coach |
| `/weekly-review` | Friday 16:00 | chief-of-staff |
| `/pipeline-review` | Thursday 10:00 | pipeline-coach |
| `/follow-up-sweep` | Friday 14:00 | network-manager |
| `/content-plan` | Wednesday 10:00 | brand-editor |
| `/calendar-audit` | Friday 15:00 | focus-coach |
| `/revenue-review` | 1st of month 09:00 | cfo |
| `/quarterly-planning` | Jan/Apr/Jul/Oct 1st 11:00 | strategist |

## How scheduling works — and why it is local

**Claude Code cannot ship a schedule inside a plugin.** Session loops expire
after seven days; cloud routines can't see your local files, and the workspace is
local Markdown by design. So `/setup-cadences` writes **cron entries on your
machine** that call the skills headless.

- One setup, then it runs while that machine and its cron service are on.
- Missed cron times do **not** become cloud catch-up runs. If the machine was
  off at 08:00, that morning's brief did not run — type `/daily-brief` when you
  sit down.
- There is no Founder OS cloud scheduler. Everything stays on your machine.

This honesty is the point: the package will not pretend the plumbing is magic.

## Running `/setup-cadences`

Run it once, after your first brief:

```
/setup-cadences
```

It writes the cron lines **with your consent** — it shows you what it will add
before it adds it. Each line calls the skill headless (with
`--permission-mode acceptEdits`, the namespaced command, and a per-cadence log).
The `/portfolio-review` line is added only when the registry lists two or more
active businesses.

`setup-cadences` is a **standalone** skill: it belongs to no agent, because
editing the crontab takes tools no agent may hold (house rule 0). It is the one
skill you invoke directly and knowingly.

## Logs

Cadence output is logged so you can see whether a scheduled run happened and what
it did:

- Single business: per-cadence logs.
- Multi-business: split per business — `~/.founder-os/logs/<slug>/<cadence>.log`.
  *Which* business's cadence stopped is the first question; a shared log answers
  the wrong one.

`founder-os-doctor` reads these to detect a **silent cadence** — one that was
scheduled but has not produced output when it should have.

## Multi-business: one fence per business

On a multi-business install, `setup-cadences` runs **per business** and fences
each business's lines with its slug so two schedules live in one crontab without
touching each other:

```
# BEGIN founder-os:acme — /setup-cadences, YYYY-MM-DD. Do not remove these markers.
…nine lines, each carrying FOUNDER_OS_HOME=<acme's absolute home>…
# END founder-os:acme
```

- Re-running for `acme` strips and rewrites **only** the `founder-os:acme` fence.
  Another business's fence, and everything outside all fences, survives byte for
  byte. This is why the slug is in the marker — the old unslugged fence made the
  second business's setup silently delete the first's schedule.
- `/portfolio-review` is scheduled **once**, in its own
  `# BEGIN founder-os:portfolio` fence, only when two or more businesses are
  active — Monday 08:15, before the earliest `week-plan`, because the split is
  that plan's input.
- A legacy unslugged fence is **migrated, not accumulated**: setup-cadences
  removes it and rewrites those lines under the business's slug, saying so in the
  confirmation.

See [`multi-business.md`](multi-business.md) for the full model.

## Turning it off or changing it

The cron lines are plain crontab entries between named markers. To remove a
business's schedule, delete its fence (marker to marker). To change a time,
re-run `/setup-cadences` — it rewrites the fence rather than appending a second
copy. Because everything lives between markers, nothing outside them is ever
touched.
