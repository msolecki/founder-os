# The dashboard

`/dashboard` reads a Founder OS workspace and writes one self-contained HTML
page: what the bets, pipeline, week, queue and close say right now, with the file
and section each number came from printed beside it.

It reads state and writes exactly one directory, `_dashboard/`. That directory
appears in `references/ownership.yaml` under `derived_files:`, which means no
agent owns it, no agent may write it, and **nothing on the page is evidence**. If
a number matters, it matters in the file it came from.

## Running it

```
python3 <plugin>/scripts/dashboard [slug] [--open] [--out PATH] [--now YYYY-MM-DD]
```

In Claude Code, `/founder-os:dashboard`; in Codex, `$founder-os:dashboard`.

| Flag | What it does |
|---|---|
| `slug` | The business to open first. On a multi-business install the page still contains every active business. |
| `--home PATH` | Read one workspace root directly and skip the registry. |
| `--out PATH` | Write `index.html` somewhere other than `_dashboard/`. |
| `--json` | Print the facts to stdout and write nothing at all. Use this when the founder asks a question the page already answers. |
| `--now YYYY-MM-DD` | The date the page treats as today. Defaults to the system clock, and is never inferred from file contents or timestamps. |
| `--open` | Open the finished page in the default browser. |
| `--max-bytes N` | Refuse to write a page larger than N bytes. Defaults to 8 MiB. |

Exit codes: `0` success, `2` no workspace resolved or `--now` was not an ISO
date, `3` the page could not be written.

## The four views

Only **Today** ships so far. The other three tabs render disabled.

| View | Shows |
|---|---|
| Today | The one thing, the trade, bets against their thresholds, pipeline, signals, this week's blocks, the queue against its caps, and the close. |
| Track record | *(not yet built)* the series in `snapshots.csv` over time. |
| Integrity | *(not yet built)* the findings the collector raised — absent files, unreadable files, missing sections. |
| State | *(not yet built)* every declared path, its owner, and when it last changed. |

## What `_dashboard/` holds

| File | Regenerable | Notes |
|---|---|---|
| `index.html` | yes | The page. One file, no network: no web fonts, no CDN, no requests of any kind. It renders identically from `file://` on a machine with no connectivity. |
| `facts.json` | yes | The same figures as a machine-readable envelope, with a hash per panel. |
| `snapshots.csv` | **no** | One row per `(date, business)`. This is the only file here whose loss costs history — everything else is rebuilt by the next run. |
| `.gitignore` | yes | Written once, ignoring `index.html` and `facts.json` only. `snapshots.csv` is deliberately not ignored. |

Running twice on one day updates that day's row rather than appending a second
one. A dated file that appends produces two answers for one day, and a chart
drawn over it is a chart of how often the script ran.

## What it refuses

- **It does not repair state.** A missing section is reported, never filled in.
  No agent-owned file is created, modified, or reformatted, even when provably
  malformed.
- **It does not invent a figure.** A value it could not read renders as "not
  recorded" and its CSV cell is written empty. An empty cell says "we did not
  look"; a zero says the company did nothing. Those are different sentences.
- **It does not resolve a disagreement.** Where two files support two readings —
  a pipeline carrying more than one currency, say — the page shows both and names
  the field that would settle it.
- **It does not send, publish, or upload anything.** It writes a local file, and
  house rule 0 applies to it exactly as it applies to every agent.

## Where the numbers come from

The set of files read is `references/ownership.yaml`, not a list inside the
renderer — a path added to the map surfaces on the page with no code change. The
caps the queue panel draws against come from `references/thresholds.yaml`, the
one place those numbers are written down; `queue` and `founder-os-doctor` read
the same file, and `check_thresholds` fails the build if a skill states a limit
without citing it.
