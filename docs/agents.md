# The agents

Thirteen agents. Each owns **one decision no other agent can make** — that is the
test every one had to pass to ship. Twelve live inside a business; the
**Portfolio Manager** ranks *between* businesses and exists only on a
multi-business install.

They are role definitions invoked when needed, not always-on workers. A command
invokes the role that owns its decision. When you don't know who to ask, ask the
**Chief of Staff** — routing is its one decision.

## The org chart

The chart is decision ownership, not a nested process tree. No role invokes
another role. Managers return a bounded delegation request to the main thread;
the main thread opens a role capability, invokes the requested specialist as a
sibling, validates its persisted result, closes that session, and only then
advances.

```
founder / main thread (technical orchestrator)
  │
  ├─ resolve workspace + open one role session
  ├─ invoke one named role or the generic-agent fallback
  ├─ re-read expected persisted state + close the session
  └─ repeat for the next sibling named by the workflow
```

Manager routing relationships remain explicit without becoming nested edges:

| Manager | May request as a sibling |
|---|---|
| Chief of Staff | all 12 other agents |
| Positioning Advisor | Pipeline Coach, Brand Editor, Network Manager |
| Delivery Lead | CFO, Ops Engineer |
| Focus Coach | Skills Mentor |

The **Board Member** has no reports and owns no workspace path. It may read
bounded state through `founder-os-state`; any attempted persistence has no
owner match and fails closed. A board that can quietly edit the company's state,
or that agrees with the CEO, is decoration.

## The thirteen

Each agent below lists the decision it owns, the workspace files it may write
(from [`ownership.yaml`](../founder-os/references/ownership.yaml)), and its role
skills. Every agent *also* holds the three universal system skills —
`guardrails`, `state-integrity`, `ingestion-gate` — omitted from the lists below
for brevity. Full command descriptions are in [`commands.md`](commands.md).

### Chief of Staff
- **Decides:** what deserves the founder's attention right now, and who handles
  it.
- **Owns:** `charter.md`, `inbox.md`, `queue.md`, `decisions/`, `reviews/daily/`,
  `reviews/weekly/`, `reviews/monthly/`.
- **Skills:** `daily-brief`, `weekly-review`, `monthly-review`, `decision-log`,
  `triage`, `queue`, `situation-review`, `strategic-evaluation` (plus the system
  skills `founder-os-init`, `founder-os-doctor`, `context-load`).
- **Notes:** the default entry point and the role that decides routing. It
  returns the canonical delegation request; the main thread executes it.
  `queue.md` is the state between a cadence that produces an obligation and the
  day it is done or dropped — eight cadences *propose* into it, only this agent
  writes it. Owns the retrospectives but not the numbers: it narrates what the
  CFO's `metrics.md` means, never restating a number it did not read.

### Board Member
- **Decides:** whether a plan survives contact with reality — nothing else.
- **Owns:** *nothing.* It advises; its findings reach the workspace only if the
  founder logs them via `decision-log`. Tools: `Read, Glob, Grep`.
- **Skills:** `red-team`, `assumption-audit`, `premortem`.
- **Notes:** requested before something irreversible, and specifically when the
  founder sounds *certain*. Certainty is its trigger, not doubt.

### Strategist
- **Decides:** what bet the company makes this quarter, and what it kills.
- **Owns:** `goals.md`, `reviews/quarterly/`.
- **Skills:** `quarterly-planning`, `bet-sizing`, `kill-or-continue`,
  `annual-review`.

### Positioning Advisor
- **Decides:** exactly who the company serves and what it sells them.
- **Owns:** `offer.md`.
- **Skills:** `icp-definition`, `offer-design`, `pricing-strategy`.
- **May request as siblings:** Pipeline Coach, Brand Editor, Network Manager.

### Pipeline Coach
- **Decides:** what happens next with each prospect.
- **Owns:** `pipeline.md`, `drafts/outreach/`, `drafts/proposals/`.
- **Skills:** `pipeline-review`, `outreach-draft`, `proposal-draft`,
  `win-loss-analysis`.

### Delivery Lead
- **Decides:** whether the company can take work on, and whether what it ships is
  good enough.
- **Owns:** `clients/`.
- **Skills:** `capacity-check`, `scope-guard`, `client-health`, `delivery-retro`.
- **May request as siblings:** CFO, Ops Engineer.

### CFO
- **Decides:** whether the company can afford something and whether it actually
  makes money.
- **Owns:** `metrics.md`.
- **Skills:** `revenue-review`, `runway-forecast`, `profitability-analysis`,
  `rate-raise`.
- **Refuses:** tax and legal advice. Names the professional and what number to
  bring them.

### Focus Coach
- **Decides:** what goes in the calendar, and what comes out.
- **Owns:** `week.md`.
- **Skills:** `week-plan`, `calendar-audit`, `energy-audit`.
- **May request as a sibling:** Skills Mentor.
- **Refuses:** medical advice.

### Skills Mentor
- **Decides:** which capability to build next, and how.
- **Owns:** `skills.md`.
- **Skills:** `skill-gap`, `learning-plan`.

### Brand Editor
- **Decides:** what gets published and where, and how the founder sounds.
- **Owns:** `content.md`, `voice.md`, `drafts/content/`.
- **Skills:** `content-plan`, `voice-capture`, `content-draft`,
  `audience-research`.

### Network Manager
- **Decides:** who to talk to, and when to follow up.
- **Owns:** `network.md`.
- **Skills:** `relationship-map`, `follow-up-sweep`.
- **Notes:** owns the identity of every *person* — `network.md` `## Map` is the
  definition a `[[slug]]` for a person resolves to (people have no file).

### Ops Engineer
- **Decides:** what to automate vs. tolerate.
- **Owns:** `systems.md`.
- **Skills:** `automation-audit`, `tool-stack-review`.

### Portfolio Manager *(multi-business only)*
- **Decides:** how the founder's hours and cash split across businesses.
- **Owns:** `portfolio.md` (in the dedicated portfolio workspace, not in any
  business workspace).
- **Skills:** `portfolio-review`.
- **Notes:** the only agent that reads across businesses, and it reads only two
  sections per business (`goals.md` `## Bets`, `metrics.md` `## Close`/`## Runway`),
  not the books. Exists only when the registry lists two or more active
  businesses. See [`multi-business.md`](multi-business.md).

## Why "owning nothing" is a decision, not an omission

The Board Member owns no files on purpose: a board advises. Every other agent
owns something precisely because the alternative failed — an agent with a
scheduled task and nowhere to write, or an audit with no baseline to compare
against, is a bug. If a future agent owns nothing, it must be able to say why, as
the board can. This is enforced socially, not by regex; the validator checks that
declared writes are owned, not that owning-nothing is justified.
