# The workspace and its state

Founder OS keeps everything in a directory of Markdown files —
`FOUNDER_OS_HOME`, default `./founder-os/`. **One file, one owner.** Agents read
anything and write only what they own. This page is the full map of that state:
every file, who owns it, and the headings that must live inside it.

The source of truth is [`references/ownership.yaml`](../founder-os/references/ownership.yaml).
It has two halves that together form one contract:

- **`owns:`** — who may *write* a file.
- **`sections:`** — what headings are *inside* it. An owner who invents a heading
  every run produces a file only that run can read, so the sections are pinned
  too. A heading may carry a dated suffix (`## Close — 2026-07`); the section
  *name* is pinned, the suffix is free.

Both halves are enforced three ways: `founder-os-init` scaffolds exactly these
headings, `founder-os-doctor` reports a file that has lost one or grown one, and
the build validator fails if a skill writes a path the map does not declare.

## The files

| File / dir | Owner | Sections |
|---|---|---|
| `inbox.md` | chief-of-staff | `## Inbox` |
| `charter.md` | chief-of-staff | `## Business`, `## North star`, `## Timezone` |
| `queue.md` | chief-of-staff | `## Doing`, `## Queued`, `## Blocked`, `## Done`, `## Dropped` |
| `decisions/` | chief-of-staff | `## Context`, `## Rejected`, `## What would change our mind`, `## Supersedes` |
| `reviews/daily/` | chief-of-staff | `## The one thing`, `## Rotting`, `## The trade`, `## Triage` |
| `reviews/weekly/` | chief-of-staff | `## Committed vs done`, `## Days per bet`, `## The pattern`, `## Next week` |
| `reviews/monthly/` | chief-of-staff | `## What the month says we do`, `## vs the charter`, `## Bets`, `## Decisions`, `## Last month's correction`, `## The correction` |
| `goals.md` | strategist | `## Bets` |
| `reviews/quarterly/` | strategist | `## Last quarter's verdicts`, `## Never measured`, `## This quarter's bets`, `## What we are not doing`, `## Verdicts`, `## Scorecard`, `## Bad call, good outcome`, `## Falsifiers that fired and were ignored`, `## Blind months`, `## Rules for next year` |
| `metrics.md` | cfo | `## Close`, `## Runway`, `## Profitability`, `## Rate` |
| `offer.md` | positioning-advisor | `## ICP`, `## Offer`, `## Pricing` |
| `pipeline.md` | pipeline-coach | `## Live`, `## Won`, `## Dead`, `## Win/loss`, `## Last review` |
| `drafts/outreach/` | pipeline-coach | `## Draft`, `## Provenance`, `## Sent` |
| `drafts/proposals/` | pipeline-coach | `## Draft`, `## Provenance`, `## Sent` |
| `week.md` | focus-coach | `## Arithmetic`, `## Shape`, `## Blocks`, `## Unfunded`, `## The trade`, `## Audit`, `## Ledger` |
| `clients/` | delivery-lead | `## Scope`, `## Health`, `## Retro` |
| `network.md` | network-manager | `## Map`, `## Not in the map`, `## Sweep` |
| `skills.md` | skills-mentor | `## Gap`, `## Hypotheses`, `## Learning plan` |
| `content.md` | brand-editor | `## Plan`, `## Shipped`, `## Drafts`, `## Audience` |
| `voice.md` | brand-editor | `## Samples`, `## Tells`, `## Never`, `## Register` |
| `drafts/content/` | brand-editor | `## Draft`, `## Provenance`, `## Sent` |
| `systems.md` | ops-engineer | `## Stack`, `## Automation decisions` |
| `portfolio.md` *(portfolio workspace)* | portfolio-manager | `## Businesses`, `## Allocation`, `## Starving`, `## Review` |

Directory paths (`clients/`, `decisions/`, `reviews/*/`, `drafts/*/`) hold one
file per instance. `founder-os-init` creates the directory, not its members; for
those paths the sections above are the *vocabulary* each member file uses,
enforced at write time by the skill that owns the template.
`clients/_capacity.md` is an aggregate, not a client file, and carries none of
the client sections.

## The files with special jobs

Four files behave differently from the rest, and understanding them is most of
understanding the system.

### `inbox.md` — the founder's door

One section, **no fields, no dates, no ids, no clock.** Every one of those is a
reason not to write a thought down at 15:00 walking out of a meeting, and the
whole value of the file is that it costs nothing to use. It has no clock because
it has a *drain*: `triage` and `daily-brief` empty it to zero every time they
run. A non-empty inbox the morning after a brief is a bug in the brief, and
`founder-os-doctor` reports it as exactly that.

### `queue.md` — what is outstanding

Every other file answers *what is true*; the queue answers *what is
outstanding* — the state between a cadence that produces an obligation and the
day it is done or dropped. It has a cap (`## Doing` holds at most three), an
expiry (an item nobody started in 15 working days is dropped, with a reason), and
one owner. **Eight cadences propose into it** — `pipeline-review`,
`revenue-review`, `content-plan`, `quarterly-planning`, `follow-up-sweep`, and
the three draft skills — but only the Chief of Staff writes it. A queue that only
grows is a to-do list, and you already have one of those.

Every taken item carries `from: <file> <date>` (the proposal it came from) so
tomorrow's brief can see a proposal was already answered and leave it alone.

### `drafts/{outreach,proposals,content}/` — bodies, and what was sent

Each draft file has `## Draft` (the body the founder is about to send),
`## Provenance` (where its claims came from, the founder-only reader), and
`## Sent` (what actually went out). `## Sent` is why these files exist: it is the
only place in the workspace where the founder's own edit to the machine's draft
survives the session, and `voice-capture` reads exactly that diff.

**House rule 0 is untouched by this.** A body on disk is not a sent body.
`## Sent` is written only when the founder *reports* what went out — no agent may
fill it in, and no agent may infer it from `## Draft`.

### `decisions/` — why, not just what

`decisions/YYYY-MM-DD-<slug>.md` records an irreversible decision: what was
decided, the option rejected (`## Rejected`), and the falsifier that would
reverse it (`## What would change our mind`). Six months from now this is the
file that answers "why did we raise rates / drop that client."

## How work moves — the studio-north tour

The [`examples/studio-north/`](../examples/studio-north/) workspace is fictional
but contract-shaped: every heading and cross-file link follows the real
ownership contract. It is the fastest way to see the state model in motion.
Follow one commitment (`q-0720a`) and one bet (`B1`) across the files:

1. [`reviews/daily/2026-07-20.md`](../examples/studio-north/reviews/daily/2026-07-20.md)
   — the brief names one commitment, `q-0720a`, serving bet `B1`.
2. [`queue.md`](../examples/studio-north/queue.md) — that commitment is the only
   item in `## Doing`, with a start date.
3. [`goals.md`](../examples/studio-north/goals.md) — bet `B1` has a threshold, a
   judgment date, and a downside cap.
4. [`week.md`](../examples/studio-north/week.md) — Monday has a funded block for
   the same commitment; the website redesign is explicitly traded away.
5. [`pipeline.md`](../examples/studio-north/pipeline.md) — Acme has a
   founder-owned next action with a date; Northwind is overdue and therefore
   shows up under the brief's `## Rotting`.
6. [`reviews/weekly/2026-W29.md`](../examples/studio-north/reviews/weekly/2026-W29.md)
   — records the cross-week pattern instead of narrating Friday's mood.
7. [`decisions/2026-07-18-raised-sprint-floor.md`](../examples/studio-north/decisions/2026-07-18-raised-sprint-floor.md)
   — stores the rejected option and the evidence that would reverse the call.

What it demonstrates: agents share explicit state, not a chat transcript; a
brief is one commitment plus a trade, not a to-do list; ids and bet references
make work traceable; pipeline claims carry a speaker and date while founder
decisions do not; a decision log stores the falsifier.
