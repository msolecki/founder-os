---
name: dashboard
description: Render the workspace as one page — what the bets, pipeline, week, queue and close actually say right now, every number carrying the file it came from
---

# Dashboard

Twenty files hold the company. Each is legible on its own and the joins between
them are not, which is why a weekly review tends to run on what the founder
remembers rather than on what the workspace says. This renders the joins.

It reads. It writes one directory, `_dashboard/`, which no agent owns and no
agent may cite. **Nothing on the page is evidence.** If a number matters, it
matters in the file it came from, and the page prints that file beside it.

## When to use

Before a weekly or monthly review, and any time the founder asks what the state
of the company is. Not daily — `daily-brief` is the daily surface and it gives
one decision, which is the whole argument of this package.

## How to run it

```
python3 <plugin>/scripts/dashboard [slug] [--open] [--out PATH] [--now YYYY-MM-DD]
```

Then tell the founder the path it printed. Never construct the HTML yourself and
never edit what it wrote; the script is the renderer and a hand-edited page is a
page that disagrees with the workspace.

`--json` prints the facts and writes nothing, which is the mode to use when the
founder asks a question the page already answers.

## What it refuses

- It does not repair state. A missing section is reported, never filled in.
- It does not send, publish, or upload. It writes a local file.
- It does not invent a figure. A value it could not read renders as
  "not recorded", never as zero.
- Where two files disagree, it shows both readings and names the field that
  would settle it. It does not choose.
