# The dashboard

`/dashboard` reads a Founder OS workspace and writes one self-contained HTML
page: what the bets, pipeline, week, queue and close say right now, with the file
and section each number came from printed beside it.

It reads state. A run that writes at all — not `--json`, and not refused —
writes three files into every readable active business's own `_dashboard/`:
`facts.json`, rewritten each run; `snapshots.csv`, with the day's row merged
into the series; and a `.gitignore`, created only when that directory has none.
It writes one more file, the page, and `--out` moves that one alone; the flag
is refused when the path it names is one the ownership map gives an agent, or
one of the three the run maintains itself. `_dashboard/` appears in
`references/ownership.yaml` under `derived_files:`, so no agent owns it and the
ownership guard denies every agent a write under it. An unowned path is allowed
by the ownership baseline, so that deny is a rule of its own, written beside
the one that protects `_local/`; like every rule in the guard it reads the file
arguments of the write tools and does not read shell commands. And **nothing on
the page is evidence**. If a number matters, it matters in the file it came
from.

## Running it

```
python3 <plugin>/scripts/dashboard [slug] [--open] [--out PATH] [--now YYYY-MM-DD]
```

In Claude Code, `/founder-os:dashboard`; in Codex, `$founder-os:dashboard`.

| Flag | What it does |
|---|---|
| `slug` | The business to open first. On a multi-business install the page still contains every active business. A slug no readable active business answers to is refused, and so is a slug passed together with `--home`: nothing checks that the two agree, so the pair would file one workspace's numbers under the other's name. |
| `--home PATH` | Read one workspace root directly and skip the registry. It stays skipped for everything that is read and rendered. With `--out` the registry's active roots are loaded for the refusal below and nothing else, so the page cannot land on a file an agent owns in a second registered business; a registry the parser rejects narrows that refusal back to this root rather than failing the run. |
| `--out PATH` | Write the page — `index.html`, and nothing else — somewhere other than `_dashboard/`; the other three files in the table below are written where they always are. Refused, with nothing written, when the path resolves onto one `references/ownership.yaml` gives an agent, and when it resolves onto one of those three files. A rendered page is not state and may not land on top of it, and `snapshots.csv` is the series this same run just merged. |
| `--json` | Print one business's facts to stdout and write nothing at all, in every configuration. Use this when the founder asks a question the page already answers. Where more than one business is readable it answers about the slug you passed; else the workspace `FOUNDER_OS_HOME` names, when that matches exactly one registered home; else the registry's `default:`. A `FOUNDER_OS_HOME` matching no registered home, or matching more than one, resolves nothing and does not fall through to `default:` — the more explicit setting pointing somewhere unknown is a reason to stop, not a reason to consult the vaguer one. With nothing resolved this mode refuses rather than filing one company's figures under another's name. The same three steps choose the business the page opens on, and — where the registry configures no portfolio root — the `_dashboard/` the page is written into. On the page, unlike here, resolving nothing is not a refusal: it opens the first readable business, because the page carries every one of them. |
| `--now YYYY-MM-DD` | The date the page treats as today. Defaults to the system clock, and is never inferred from file contents or timestamps. |
| `--open` | Open the finished page in the default browser. |
| `--max-bytes N` | Refuse to write a page larger than N bytes. Defaults to 8 MiB. |

Exit codes: `0` success. `2` nothing was resolved — no readable workspace, an
unknown slug, a slug passed with `--home`, `--json` with nothing to say which
business is meant, an unreadable registry, or a `--now` that is not an ISO date.
`3` the page was not written. Three refusals return above the first write of
any kind, so after those nothing at all changed: the page is over
`--max-bytes`, `--out` names a path an agent owns, or `--out` names one of the
three files the run maintains. A write that fails part-way through exits `3`
too. The per-business loop is not a transaction, so the businesses it finished
keep the `facts.json` and `snapshots.csv` this run gave them, and stderr
carries a second line naming those directories: "Already written this run and
left in place: ...".

## The four views

Only **Today** ships so far. The other three tabs render disabled.

| View | Shows |
|---|---|
| Today | The one thing, the trade, bets against their thresholds, pipeline, signals, this week's blocks, the queue against its caps, and the close. |
| Track record | *(not yet built)* the series in `snapshots.csv` over time. |
| Integrity | *(not yet built)* the findings the collector raised — absent files, unreadable files, missing sections. |
| State | *(not yet built)* every declared path, its owner, and when it last changed. |

## What `_dashboard/` holds

Every readable active business gets these in its own `_dashboard/` on a run
that writes at all. Without `--out` the page joins them there — under the
portfolio root when the registry configures one, otherwise under the business
the `--json` precedence above selects, or the first readable one when that
precedence selects none — at a path resolved to absolute before it is written,
printed, or opened. With `--out` the page goes where you said and the rest do
not follow it.

| File | Regenerable | Notes |
|---|---|---|
| `index.html` | yes | The page. One file, no network: no web fonts, no CDN, no requests of any kind. It renders identically from `file://` on a machine with no connectivity. |
| `facts.json` | yes | The same figures as a machine-readable envelope, with a hash per panel. |
| `snapshots.csv` | **no** | One row per `(date, business)`. This is the only file here whose loss costs history — everything else is rebuilt by the next run. |
| `.gitignore` | yes | Written once, ignoring `index.html` and `facts.json` only. `snapshots.csv` is deliberately not ignored. Without `--out` the directory the page lands in gets one too, which is what covers a portfolio root holding no business of its own. |

Running twice on one day updates that day's row rather than appending a second
one. A dated file that appends produces two answers for one day, and a chart
drawn over it is a chart of how often the script ran.

## What it refuses

- **It does not repair state.** A missing section is reported, never filled in.
  No agent-owned file is created, modified, or reformatted, even when provably
  malformed.
- **It does not invent a figure.** A value it could not read renders as "not
  recorded" and its CSV cell is written empty. An empty cell says the run has no
  answer it can trace to the workspace — either it did not look, or it looked
  and part of the answer was missing, the way one unpriced deal among ten stops
  the pipeline total rather than shrinking it. A zero says the company did
  nothing. Those are different sentences.
- **It does not read prose as an empty list.** A `## Live` describing two deals
  in a sentence is a section the reader could not list, not a section holding
  nothing, and it reports "not recorded" rather than nought deals under a
  citation to the file that names them. `None.` is still a real zero.
- **It does not strip a tier.** An amount the ingestion gate stamped
  `[VALIDATE]` is counted, and the panel says how many of the amounts behind the
  total carry that stamp. `references/house-rules.md` allows such a figure to be
  written "but only carrying its tier", and the page is the surface most likely
  to be quoted back.
- **It does not resolve a disagreement.** Where two files support two readings —
  a pipeline carrying more than one currency, say — the page shows both and names
  the field that would settle it.
- **It does not send, publish, or upload anything.** It writes a local file, and
  house rule 0 applies to it exactly as it applies to every agent.

## Where the numbers come from

The set of files read is `references/ownership.yaml`, not a list inside the
renderer — a path added to the map surfaces on the page with no code change. The
caps the queue panel draws against come from `references/thresholds.yaml`, the
file that settles those numbers; `queue` and `founder-os-doctor` cite the same
file, and `check_thresholds` fails the build if either of those two states a
limit without naming it, or if a sentence it has registered prints a number
that file does not agree with.
