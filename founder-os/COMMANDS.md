# Commands

<!-- GENERATED FILE — do not edit. `python3 scripts/generate_commands.py`
     regenerates it from the agents' and skills' own frontmatter; CI fails
     when this file and the package disagree. A hand edit here is a second
     map, and second maps go stale silently. -->

Every skill is a slash command: `/founder-os:<name>` (the bare `/<name>` works
until another package claims it). On a multi-business install, pass the
business slug first — `/founder-os:daily-brief acme`.

Don't know which command? Ask the **chief-of-staff** — routing is its decision.

## The cadences

Scheduled by `/setup-cadences`; every one also works typed by hand.

| Command | When | Run by |
|---|---|---|
| `/daily-brief` | weekdays 08:00 | chief-of-staff |
| `/portfolio-review` | Monday 08:15, multi-business installs only | portfolio-manager |
| `/week-plan` | Monday 08:30 | focus-coach |
| `/weekly-review` | Friday 16:00 | chief-of-staff |
| `/pipeline-review` | Thursday 10:00 | pipeline-coach |
| `/follow-up-sweep` | Friday 14:00 | network-manager |
| `/content-plan` | Wednesday 10:00 | brand-editor |
| `/calendar-audit` | Friday 15:00 | focus-coach |
| `/revenue-review` | 1st of month 09:00 | cfo |
| `/quarterly-planning` | Jan/Apr/Jul/Oct 1st 11:00 | strategist |

## By agent

### board-member

Decides whether a plan survives contact with reality. Use to red-team a plan, audit its assumptions, or run a premortem before something becomes irreversible.

| Command | What it does |
|---|---|
| `/red-team` | Attack a finished plan as a hostile reader and return a verdict, not a list of concerns — run when the founder sounds certain |
| `/assumption-audit` | List what must be true for a plan to work, strike what is already evidence, and rank the rest by cost to test — run before the plan is expensive |
| `/premortem` | Declare the plan already dead six months out and write the story of how it happened — run while the answer can still change the plan |

### brand-editor

Decides what gets published and where, and owns how the founder sounds. Use for the content plan, drafting, audience research, and capturing the founder's voice.

| Command | What it does |
|---|---|
| `/content-plan` | Plan what gets published against the ICP and last month's actual shipped count — run weekly, and whenever the founder proposes a cadence they have never once hit |
| `/voice-capture` | Build voice.md from the founder's actual sent writing — run before anything ships under their name, and every time they edit a draft before sending |
| `/content-draft` | Draft one planned piece around a single idea the founder learned by doing — run against the plan, never to fill a slot, and never after 10pm on anything naming a person |
| `/audience-research` | Collect what the ICP actually says about their problem, verbatim and sourced — run before a content plan, and whenever the founder is about to write about a topic instead of a question |

### cfo

Decides whether the company can afford something and whether it actually makes money. Use for the monthly close, runway, profitability, and rate raises. Gives no tax or legal advice.

| Command | What it does |
|---|---|
| `/revenue-review` | Close the month on booked, collected and effective rate — run on the first of the month, fired by cron if the founder ran /setup-cadences |
| `/runway-forecast` | Compute months of survival at real burn with the pipeline discounted by stage — run monthly after the close, and before any spending commitment |
| `/profitability-analysis` | Rank every client by effective hourly rate to find where the margin dies — run quarterly, before any renewal, and before agreeing to more of the same work |
| `/rate-raise` | Decide whether the rate rises, by how much, and hand over the script — run when profitability-analysis says the rate is below target, not when the founder feels brave |

### chief-of-staff

Decides what deserves the founder's attention right now and which specialist handles it. Use for the daily brief, the weekly and monthly review, triage of a pile of obligations, the work queue, or when you don't know who to ask.

| Command | What it does |
|---|---|
| `/daily-brief` | Open the day with the one thing that matters — run every weekday morning before the founder picks their own work |
| `/weekly-review` | Score the week's commitments against what actually happened and name the pattern across weeks — run Friday afternoon, before the week is remembered kindly |
| `/monthly-review` | Read the month back against the charter and name the drift — run after the CFO closes the books, never before |
| `/decision-log` | Record an irreversible decision with the falsifier that would reverse it — run within 24 hours of the decision, while the reason is still the reason |
| `/triage` | Take the founder's pile of unsorted obligations, keep one, cost the rest, and route them by name — run when they arrive with five things and no idea which matters |
| `/queue` | Hold the founder's live obligations with a cap, an expiry and one owner — run whenever a cadence produces work that would otherwise live in a paragraph nobody reopens |

### delivery-lead

Decides whether the company can take work on and whether what it ships is good enough. Use for capacity checks, scope creep, client health, and delivery retros.

| Command | What it does |
|---|---|
| `/capacity-check` | Compute real deliverable hours before accepting work — run before any yes to a new client, an extra deliverable, or a start date |
| `/scope-guard` | Rule on whether an ask is inside scope by checking it against the proposal's exclusions — run the moment a client asks for something that was not quoted |
| `/client-health` | Score an engagement on payment, scope, tone and effort before it becomes a crisis — run monthly per active client, and always before a renewal |
| `/delivery-retro` | Compare estimated against actual hours within five days of shipping — run at every project end, before memory replaces the timesheet |

### focus-coach

Decides what goes in the calendar and what comes out. Use for the week plan, calendar audits, and reading energy from the record.

| Command | What it does |
|---|---|
| `/week-plan` | Turn this quarter's bets into blocks with dates — run every Monday before the week fills itself |
| `/calendar-audit` | Diff where the week actually went against where it was planned — run every Friday, and whenever the founder claims they have no time |
| `/energy-audit` | Read the calendar record for when the founder's output is good and when it isn't — run monthly, once the ledger has enough weeks to mean something |

### network-manager

Decides who to talk to and when to follow up. Use for relationship mapping and the follow-up sweep.

| Command | What it does |
|---|---|
| `/relationship-map` | Map who the founder actually knows by category and days since real contact — run quarterly, before any conference, and whenever cold outreach is proposed with the warm list untouched |
| `/follow-up-sweep` | Surface everyone past their contact interval and give each one a real reason to hear from the founder — run weekly, capped at five, and never with "just checking in" |

### ops-engineer

Decides what to automate and what to tolerate. Use for automation audits and reviewing the tool stack.

| Command | What it does |
|---|---|
| `/automation-audit` | Decide whether a manual task is worth automating using payback arithmetic — run before building anything internal, and especially when the founder is enjoying it |
| `/tool-stack-review` | Decide what is paid for and unused, and hand the founder the cancel list — run quarterly, and 30 days before any annual renewal bills |

### pipeline-coach

Decides what happens next with each prospect. Use for pipeline review, outreach and proposal drafts, and win/loss analysis.

| Command | What it does |
|---|---|
| `/pipeline-review` | Force every deal to have a next action with a date or leave the pipeline — run weekly, and any time the founder says they have more conversations than they can name |
| `/outreach-draft` | Draft a first contact or a follow-up written from the prospect's problem — run when a deal needs a next action, and never to send "just checking in" |
| `/proposal-draft` | Draft a proposal with scope, price, exclusions and an expiry date — run when a qualified deal is ready to close, never before capacity-check, and never with an empty exclusions list |
| `/win-loss-analysis` | Reconstruct why a deal was won or lost from the record and the prospect's own words — run within five business days of any deal ending, while they will still take the call |

### portfolio-manager

Decides how the founder's hours and cash split across businesses. Use for the portfolio review, for "which business gets me this week", and whenever two businesses both claim the same block of time or the same money.

| Command | What it does |
|---|---|
| `/portfolio-review` | Rank the businesses against each other, set this week's split of the founder's hours and cash, and name what the split is starving — the one cadence that crosses workspace boundaries |

### positioning-advisor

Decides exactly who the company serves and what it sells them. Use for ICP definition, offer design, and pricing.

| Command | What it does |
|---|---|
| `/icp-definition` | Narrow who this company serves until the definition excludes real, nameable people — run before any pipeline or content work, and whenever the founder describes their buyer in adjectives |
| `/offer-design` | Turn what the founder does into an outcome with an explicit boundary — run when work is quoted in hours, when every project is bespoke, or when a prospect can't repeat the offer to a colleague |
| `/pricing-strategy` | Price the offer against the buyer's outcome and their real alternative, and name the founder's walk-away floor in writing before any negotiation starts |

### skills-mentor

Decides which capability to build next and how. Use for skill-gap analysis and learning plans.

| Command | What it does |
|---|---|
| `/skill-gap` | Name the capability gap between the offer sold today and the offer the quarter's bets require — run before any learning is committed to |
| `/learning-plan` | Attach one capability to one project that forces it and one real deadline — run after skill-gap names the gap, never before |

### strategist

Decides what bet the company makes this quarter and what it kills. Use for quarterly planning, sizing a bet, kill-or-continue calls, and the annual review.

| Command | What it does |
|---|---|
| `/quarterly-planning` | Close last quarter's bets with verdicts and commit at most three new ones, each with a kill condition — run in the first days of the quarter, once the numbers that settle the old one are in |
| `/bet-sizing` | Price a bet by what it costs when it is wrong and cap the downside in writing before it starts — run before any bet enters goals.md |
| `/kill-or-continue` | Force a verdict on a bet against the threshold it was given, with the sunk cost named out loud — run the moment a judgement date passes |
| `/annual-review` | Read twelve months of decisions back and score the judgment rather than the outcome — run once a year, from decisions/ and nothing else |

## System commands

Cross-cutting; not tied to one agent's decision.

| Command | What it does |
|---|---|
| `/context-load` | Load charter, goals and metrics with their dates stamped before any cadence runs — the house-rule-1 check that starts every session |
| `/founder-os-doctor` | Diagnose workspace rot — missing files, stale metrics, goals without bets, orphan clients, silent cadences — and report before repairing anything |
| `/founder-os-init` | Run first-install onboarding — interview the founder, scaffold the workspace, and hand each answer to the agent that owns it |
| `/guardrails` | Enforce the hard refusals every agent obeys — nothing outbound and nothing paid, ever; tax, legal, and medical questions get escalated to a real professional, never answered |
| `/ingestion-gate` | Tier every claim arriving from outside the workspace — fact, validate, or disregard — before it enters a canonical file, and stamp its speaker and date inline in the line that carries it |
| `/setup-cadences` | Turn the cadences into real scheduled jobs on the founder's own machine — run once, after their first brief, so the package stops waiting to be opened *(standalone — run it yourself)* |
| `/state-integrity` | Resolve every workspace write against the ownership map before making it — refuse and hand off by name when the acting agent is not the owner |
