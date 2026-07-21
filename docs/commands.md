# Commands

Every skill is a slash command: `/founder-os:<name>` (the bare `/<name>` works
until another package claims it). On a multi-business install, pass the business
slug first — `/founder-os:daily-brief acme`.

Don't know which command? Ask the **chief-of-staff** — routing is its decision.

> This page is the annotated, grouped reference. The **generated, always-current
> catalogue** is [`founder-os/COMMANDS.md`](../founder-os/COMMANDS.md), derived
> from the package by `scripts/generate_commands.py` and checked in CI. If the
> two ever disagree, the generated one is right.

## Start here: the first five actions

After `/founder-os-init` persists and validates the first brief:

1. Run `/daily-brief` before opening email.
2. Put an unstructured thought in `inbox.md`; the next brief or `/triage`
   drains it.
3. Run `/pipeline-review` so every live deal has a dated next action.
4. Run `/weekly-review` on Friday before memory rewrites the week.
5. Ask the **Chief of Staff** to route any uncategorized decision.

The examples use bare commands. If another plugin claims the same name, use the
qualified form: `/founder-os:daily-brief`,
`/founder-os:pipeline-review`, or `/founder-os:weekly-review`.

## The 10 cadences

Scheduled by `/setup-cadences`; every one also works typed by hand. See
[`cadences.md`](cadences.md) for the scheduling mechanics.

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

## Role commands, by agent

### chief-of-staff — attention & routing
| Command | What it does |
|---|---|
| `/daily-brief` | Open the day with the one thing that matters; name what's rotting and what today costs. Never a to-do list. |
| `/weekly-review` | Score the week's commitments against what actually happened; name the cross-week pattern. |
| `/monthly-review` | Read the month back against the charter and name the drift — after the CFO closes the books. |
| `/decision-log` | Record an irreversible decision with the falsifier that would reverse it, within 24 hours. |
| `/triage` | Keep one obligation, cost the rest, route them by name — when the founder arrives with five things. |
| `/queue` | Hold live obligations with a cap, an expiry, and one owner. |

### strategist — bets
| Command | What it does |
|---|---|
| `/quarterly-planning` | Close last quarter's bets with verdicts and commit at most three new ones, each with a kill condition. |
| `/bet-sizing` | Price a bet by what it costs when wrong; cap the downside in writing before it starts. |
| `/kill-or-continue` | Force a verdict on a bet against its threshold, with the sunk cost named out loud. |
| `/annual-review` | Read twelve months of decisions back and score the judgment, not the outcome. |

### board-member — surviving reality
| Command | What it does |
|---|---|
| `/red-team` | Attack a finished plan as a hostile reader; return a verdict, not a list of concerns. |
| `/assumption-audit` | List what must be true, strike what is already evidence, rank the rest by cost to test. |
| `/premortem` | Declare the plan already dead six months out and write the story of how it happened. |

### positioning-advisor — who & what
| Command | What it does |
|---|---|
| `/icp-definition` | Narrow who this company serves until the definition excludes real, nameable people. |
| `/offer-design` | Turn what the founder does into an outcome with an explicit boundary. |
| `/pricing-strategy` | Price against the buyer's outcome and their real alternative; name the walk-away floor in writing. |

### pipeline-coach — prospects
| Command | What it does |
|---|---|
| `/pipeline-review` | Force every deal to have a next action with a date, or leave the pipeline. |
| `/outreach-draft` | Draft a first contact or follow-up written from the prospect's problem. Drafts; never sends. |
| `/proposal-draft` | Draft a proposal with scope, price, exclusions, and an expiry — never before `capacity-check`, never with empty exclusions. |
| `/win-loss-analysis` | Reconstruct why a deal was won or lost, within five business days of it ending. |

### delivery-lead — the work
| Command | What it does |
|---|---|
| `/capacity-check` | Compute real deliverable hours before any yes to new work. |
| `/scope-guard` | Rule on whether an ask is inside scope by checking the proposal's exclusions. |
| `/client-health` | Score an engagement on payment, scope, tone, and effort before it becomes a crisis. |
| `/delivery-retro` | Compare estimated vs. actual hours within five days of shipping. |

### cfo — money
| Command | What it does |
|---|---|
| `/revenue-review` | Close the month on booked, collected, and effective rate. |
| `/runway-forecast` | Compute months of survival at real burn, pipeline discounted by stage. |
| `/profitability-analysis` | Rank every client by effective hourly rate to find where the margin dies. |
| `/rate-raise` | Decide whether the rate rises, by how much, and hand over the script. |

### focus-coach — the calendar
| Command | What it does |
|---|---|
| `/week-plan` | Turn the quarter's bets into blocks with dates, before the week fills itself. |
| `/calendar-audit` | Diff where the week actually went against where it was planned. |
| `/energy-audit` | Read the calendar record for when the founder's output is good and when it isn't. |

### skills-mentor — capability
| Command | What it does |
|---|---|
| `/skill-gap` | Name the gap between the offer sold today and the offer the quarter's bets require. |
| `/learning-plan` | Attach one capability to one project that forces it and one real deadline. |

### brand-editor — publishing & voice
| Command | What it does |
|---|---|
| `/content-plan` | Plan what gets published against the ICP and last month's *actual* shipped count. |
| `/voice-capture` | Build `voice.md` from the founder's actual sent writing. |
| `/content-draft` | Draft one planned piece around a single idea the founder learned by doing. |
| `/audience-research` | Collect what the ICP actually says about their problem, verbatim and sourced. |

### network-manager — relationships
| Command | What it does |
|---|---|
| `/relationship-map` | Map who the founder actually knows, by category and days since real contact. |
| `/follow-up-sweep` | Surface everyone past their contact interval, each with a real reason to hear from the founder. Capped at five. |

### ops-engineer — systems
| Command | What it does |
|---|---|
| `/automation-audit` | Decide whether a manual task is worth automating, using payback arithmetic. |
| `/tool-stack-review` | Decide what is paid for and unused; hand over the cancel list. |

### portfolio-manager — across businesses *(multi-business only)*
| Command | What it does |
|---|---|
| `/portfolio-review` | Rank the businesses against each other and set this week's split of hours and cash. The one cadence that crosses workspaces. |

## System commands

Cross-cutting; not tied to one agent's decision.

| Command | What it does |
|---|---|
| `/context-load` | Load charter, goals, and metrics with dates stamped before any cadence runs — the house-rule-1 check that starts every session. On multi-business installs, step 0 resolves which business the session means. |
| `/founder-os-init` | Run or resume first-install onboarding through owner-safe state and a valid persisted first daily brief. |
| `/founder-os-doctor` | Diagnose workspace rot — missing files, stale metrics, goals without bets, orphan clients, silent cadences — and report before repairing anything. |
| `/guardrails` | Enforce the hard refusals every agent obeys — nothing outbound, nothing paid; tax/legal/medical escalated to a professional. |
| `/ingestion-gate` | Tier every claim arriving from outside — fact, validate, or disregard — before it enters a file, stamping speaker and date inline. |
| `/state-integrity` | Resolve every write against the ownership map before making it; refuse and hand off by name when the acting agent is not the owner. |
| `/setup-cadences` | Turn the cadences into real scheduled jobs on the founder's machine — run once, after the first brief. *(standalone — run it yourself)* |
