# Founder OS — Design Spec

**Date:** 2026-07-15
**Status:** Approved, ready for implementation planning
**Deliverable:** A public [Agent Company](https://agentcompanies.io/specification) package, distributed via [companies.sh](https://companies.sh), installable with `npx companies.sh add <owner>/founder-os`.

---

## 1. Problem & positioning

### The market gap

The companies.sh directory holds 18 packages (as of 2026-07-15). Every one of them is **a company that does work for you**: engineering shops (`gstack`, `superpowers`, `fullstack-forge`, `agentsys-engineering`, `compound-engineering-co`), agencies (`agency-agents`, `taches-creative`, `minimax-studio`), research labs (`kdense-science-lab`, `clawteam-research-lab`), specialists (`trail-of-bits-security`, `redoak-review`, `clawteam-capital`, `product-compass-consulting`, `donchitos-game-studio`, `aeon-intelligence`).

**Not one is about the operator themselves.** There is no founder OS, no personal or business development package, nothing that runs *you*. Founder OS is first in the category.

### The product

**Name:** Founder OS
**Slug:** `founder-os` (verified free in the registry)
**Tagline:** *The executive team you can't afford yet — strategy, offer, pipeline, delivery, money and focus for a company of one.*

**Framing:** You are the Founder. The package is your executive team. Every other package in the directory is staff you hire; this one is the org that holds you accountable.

**Target user:** Founder / solopreneur — someone building their own business. Personal development in service of the business: goals and strategy, positioning and offer, client acquisition, revenue, delivery, focus and energy, capability building, and the review cadences that tie them together.

**Language:** English only. The directory is international; English maximizes installs and matches every existing package.

### Design philosophy

Adapted from gstack's principle that *planning is not review, review is not shipping, founder taste is not engineering rigor*: **each agent is a specialist you summon for the right job.**

Founder OS adds the piece a reactive tool can't provide — **an accountability loop**. A personal-development product that only runs when the user remembers to run it is the failure mode of every productivity system ever shipped. Scheduled cadences (`TASK.md` recurrence) are what make this an OS rather than a prompt library.

### Anti-goal (the thing most likely to kill this)

A 12-agent org only works if **each agent owns a decision no other agent can make**. The moment two agents could answer the same question, the user doesn't know who to summon, and the whole org reads as filler. The directory contains packages with 167 agents and 177 skills; headcount is not the differentiator, category and sharpness are.

**Enforced rule:** one agent = one decision domain, or it gets merged. Same test for skills.

---

## 2. Architecture

Chosen: **org chart + cadences, with pipeline-style handoff discipline**.

- **Org chart** — Chief of Staff routes to 11 specialists.
- **Cadences** — `TASK.md` recurrence drives daily/weekly/monthly/quarterly rhythms. Nothing else in the directory uses the scheduler this way.
- **Handoff discipline** — every agent body follows gstack's structure: *What triggers you / What you do / What you produce / Who you hand off to*.
- **State** — a markdown workspace, because agents have amnesia and a founder OS without memory is worthless.

### Org chart

```
        [ YOU — Founder ]
               │
      ┌────────┴─────────┐
 Chief of Staff      Board Member        ← reportsTo: null
   (routes,           (red-teams
    cadences)          everything)
        │
  ┌─────┼───────────┬──────────┬──────────┐
Strategist      Positioning  Delivery   Focus
                 Advisor       Lead      Coach
                     │           │          │
              Pipeline Coach    CFO    Skills Mentor
              Brand Editor   Ops Engineer
              Network Mgr
```

**Two deliberate decisions:**

1. **Chief of Staff is the top agent, not a CEO.** The user is the CEO. An agent CEO would compete with the human for the role — which is exactly the mistake that makes personal-development tools feel patronizing.
2. **Board Member has `reportsTo: null`**, parallel to Chief of Staff. A board sits outside the org. This produces a two-root org chart, which is unusual but semantically correct.

### Agent roster

Each agent passed one test: *name a decision only this agent makes*.

| Slug | Title | reportsTo | Only this agent decides… |
|---|---|---|---|
| `chief-of-staff` | Chief of Staff | `null` | What deserves your attention now, and who handles it |
| `board-member` | Board Member | `null` | Whether a plan survives contact with reality |
| `strategist` | Chief Strategy Officer | `chief-of-staff` | What bet we make this quarter — and what we kill |
| `positioning-advisor` | Head of Positioning | `chief-of-staff` | Exactly who we serve and what we sell them |
| `delivery-lead` | COO | `chief-of-staff` | Whether we can take this on, and if it's good enough to ship |
| `focus-coach` | Head of Focus | `chief-of-staff` | What goes in the calendar — and what comes out |
| `pipeline-coach` | Revenue Lead | `positioning-advisor` | What happens next with each prospect |
| `brand-editor` | Head of Content | `positioning-advisor` | What to publish, and where |
| `network-manager` | Head of Relationships | `positioning-advisor` | Who to talk to, and when to follow up |
| `cfo` | CFO | `delivery-lead` | Whether we can afford it and if it actually makes money |
| `ops-engineer` | Head of Ops | `delivery-lead` | What to automate vs. tolerate |
| `skills-mentor` | Head of Learning | `focus-coach` | Which capability to build next, and how |

**Merged during design:** a separate Health/Performance agent was folded into `focus-coach` (energy is inseparable from calendar decisions, and merging shrinks the medical-advice surface).

### Teams

| Team | Manager | Includes |
|---|---|---|
| `growth` | `positioning-advisor` | `pipeline-coach`, `brand-editor`, `network-manager` |
| `operations` | `delivery-lead` | `cfo`, `ops-engineer` |
| `self` | `focus-coach` | `skills-mentor` |
| `board` | `strategist` | `board-member` |

---

## 3. Workspace (state model)

**Location:** defaults to `./founder-os/`, overridable via the `FOUNDER_OS_HOME` environment variable, declared as an input in `.paperclip.yaml` (the same vendor-extension mechanism gstack uses for `GH_TOKEN`).

```
founder-os/
├── charter.md              # who you are, what business, north star — the constitution
├── goals.md                # this quarter's bets + outcomes
├── metrics.md              # the numbers: revenue, pipeline, runway, hours
├── offer.md                # ICP + offer + pricing
├── pipeline.md             # prospects + next action each
├── week.md                 # current week's blocks, rewritten each Monday
├── queue.md                # v1.1 — durable work: Doing/Queued/Blocked/Done/Dropped
├── clients/<slug>.md       # scope, health, revenue per client
├── network.md              # relationships + follow-up queue
├── skills.md               # capability map + learning plan
├── content.md              # content plan + backlog
├── voice.md                # v1.1 — how the founder writes: samples, not adjectives
├── systems.md              # automation/tool inventory
├── decisions/YYYY-MM-DD-<slug>.md
└── reviews/
    ├── daily/YYYY-MM-DD.md
    ├── weekly/YYYY-Www.md
    ├── monthly/YYYY-MM.md
    └── quarterly/YYYY-Qn.md
```

### File ownership map

**The rule that keeps 12 agents from trampling each other: every file has exactly one owner.** This is the file-level twin of the one-decision-per-agent rule, and it is what makes a 12-agent org safe to run against shared state. Everyone may *read* anything; only the owner *writes*.

| File | Owner |
|---|---|
| `charter.md` | `chief-of-staff` |
| `goals.md` | `strategist` |
| `metrics.md` | `cfo` |
| `offer.md` | `positioning-advisor` |
| `pipeline.md` | `pipeline-coach` |
| `week.md` | `focus-coach` |
| `queue.md` | `chief-of-staff` (v1.1) |
| `voice.md` | `brand-editor` (v1.1) |
| `clients/` | `delivery-lead` |
| `network.md` | `network-manager` |
| `skills.md` | `skills-mentor` |
| `content.md` | `brand-editor` |
| `systems.md` | `ops-engineer` |
| `decisions/` | `chief-of-staff` |
| `reviews/daily/`, `reviews/weekly/`, `reviews/monthly/` | `chief-of-staff` |
| `reviews/quarterly/` | `strategist` |

**Corrected 2026-07-15 during implementation.** `reviews/monthly/` was originally assigned to `cfo`, which contradicted §6 giving the `monthly-review` skill to `chief-of-staff` — an agent cannot run a skill whose output it may not write. The CFO's monthly close writes `metrics.md` (which is what a numbers close *is*); the Chief of Staff writes the retrospective. This produces a clean handoff — CFO closes the numbers, CoS says what they mean — and keeps all three recurring retrospectives with one owner.

A skill's declared output must be owned by the agent that holds the skill. This is now enforced mechanically: SKILL.md declares `metadata.writes`, and `check_skill_writes` in `scripts/validate_package.py` fails the build if the holder does not own the path.

**Also corrected 2026-07-15:** `week.md` was added, owned by `focus-coach`. The original map listed only 10 owners, leaving Focus Coach with three skills and a scheduled Monday `week-plan` task but nowhere to write — and leaving `calendar-audit` ("planned vs. actual") with no baseline to compare against. `week.md` holds the current week's blocks and is rewritten each Monday.

**Two agents deliberately own nothing:** `board-member` (a board advises; it does not write company state — its findings reach the workspace only if the founder logs them via `decision-log`) and — no longer — `focus-coach`, whose lack of ownership was an oversight rather than a design choice. That distinction is the test for any future agent: owning nothing must be a decision, not an omission.

### The decision log

`decisions/` is the sleeper feature. Six months later the user can ask *why* they raised rates or dropped a client. It is also what gives `board-member` something real to audit instead of vibes, and what makes `win-loss-analysis` and `kill-or-continue` grounded rather than speculative.

---

## 4. Cadence engine

Eight scheduled tasks via `TASK.md` `schedule.recurrence`.

Each task names the single skill it invokes. Task slug and skill slug match wherever possible, so the mapping stays obvious.

| Task | Assignee | Invokes skill | Cadence |
|---|---|---|---|
| `daily-brief` | `chief-of-staff` | `daily-brief` | weekdays 08:00 |
| `week-plan` | `focus-coach` | `week-plan` | Monday 08:30 |
| `weekly-review` | `chief-of-staff` | `weekly-review` | Friday 16:00 |
| `pipeline-review` | `pipeline-coach` | `pipeline-review` | Thursday, weekly |
| `follow-up-sweep` | `network-manager` | `follow-up-sweep` | Friday, weekly |
| `content-plan` | `brand-editor` | `content-plan` | weekly |
| `monthly-close` | `cfo` | `revenue-review` | 1st of month |
| `quarterly-planning` | `strategist` | `quarterly-planning` | quarterly |

Two mappings are deliberately not 1:1 and are called out here so implementation doesn't "fix" them by accident:

- **`monthly-close` invokes `revenue-review`, not `monthly-review`.** The CFO owns the monthly numbers close. The Chief of Staff's `monthly-review` skill is a broader manual retrospective the founder runs when they want it — scheduling both would mean two competing monthly rituals.
- **`annual-review` is not scheduled.** A once-a-year task that fires unprompted eleven months after install is noise; the founder invokes it deliberately.

### Known issue: timezone

`TASK.md` schedules embed a hardcoded `schedule.timezone`, but this package ships to strangers in unknown timezones.

**Resolution:** `founder-os-init` rewrites the installed `TASK.md` timezone values during onboarding, rather than shipping `Europe/Warsaw` and hoping. This means the package mutates its own installed files — unusual, and documented here deliberately so it is a known trade-off rather than a discovered surprise.

### Onboarding project

`projects/onboarding/` — the first-run flow, producing in order: charter → ICP/offer → quarterly goals → metrics baseline.

Without this, a new installer faces 12 agents and an empty directory, and churns immediately. This project is the single highest-leverage retention artifact in the package.

Tasks: `write-charter`, `define-icp`, `set-quarter-goals`, `baseline-metrics`.

---

## 5. Rules layer

`agentcompanies/v1` has **no `rules` kind**. Rules must therefore be enforced by real artifacts, or they are prose nobody reads. Three tiers, hardest first.

### Tier 1 — Constitution (`COMPANY.md` `goals[]`)

What the org optimizes for:
- Durable revenue over vanity growth.
- Every irreversible decision gets logged with its reasoning.
- Evidence over vibes — advice is grounded in recorded numbers or labelled a guess.
- The founder stays the CEO; the org serves the founder's judgment, it does not replace it.

### Tier 2 — House rules (`references/house-rules.md`)

Referenced by every agent body:

1. **No advice without state** — an agent reads its file before it opines. No pipeline advice without reading `pipeline.md`.
2. **Evidence over vibes** — no claim about the business without a number from `metrics.md`, or it is explicitly labelled a guess.
3. **Decisions get logged** — anything irreversible writes to `decisions/`.
4. **Stay in your lane** — never write a file you don't own.

### Tier 3 — Guardrail skills (enforcement, not suggestion)

- **`guardrails`** — hard refusals with escalation. **`cfo` gives no tax or legal advice. `focus-coach` gives no medical advice.** Both name the class of professional to consult instead. This is the tier that protects the author when a stranger installs the package and takes its output seriously.
- **`state-integrity`** — validates the ownership map before writes; blocks cross-owner writes.

---

## 6. Skills catalog

**47 skills** (v1.1; 44 at v1.0). All authored **inline** (`usage: vendored`, not `referenced`) — there is no upstream to point at, and vendoring is what makes the package self-contained and ownable.

Ownership splits into two classes, and conflating them is a trap:

- **41 role skills** — each owned by exactly one agent and listed only in that agent's `skills[]`. (v1.1 added `queue` and `voice-capture`.)
- **6 system skills** — `founder-os-init`, `founder-os-doctor`, `context-load`, `guardrails`, `state-integrity`, `ingestion-gate`. These are cross-cutting. `guardrails` and `state-integrity` **must** appear in every agent's `skills[]`, because a refusal rule that only one agent carries is not a rule. The remaining three (`founder-os-init`, `founder-os-doctor`, `context-load`) attach to `chief-of-staff`, which owns the workspace lifecycle.

| Owner | Skills |
|---|---|
| *system (cross-cutting)* | `founder-os-init`, `founder-os-doctor`, `context-load`, `guardrails`, `state-integrity` |
| `chief-of-staff` | `daily-brief`, `weekly-review`, `monthly-review`, `decision-log`, `triage` |
| `strategist` | `quarterly-planning`, `bet-sizing`, `kill-or-continue`, `annual-review` |
| `board-member` | `red-team`, `assumption-audit`, `premortem` |
| `positioning-advisor` | `icp-definition`, `offer-design`, `pricing-strategy` |
| `pipeline-coach` | `pipeline-review`, `outreach-draft`, `proposal-draft`, `win-loss-analysis` |
| `delivery-lead` | `capacity-check`, `scope-guard`, `client-health`, `delivery-retro` |
| `cfo` | `revenue-review`, `runway-forecast`, `profitability-analysis`, `rate-raise` |
| `focus-coach` | `week-plan`, `calendar-audit`, `energy-audit` |
| `skills-mentor` | `skill-gap`, `learning-plan` |
| `brand-editor` | `content-plan`, `content-draft`, `audience-research` |
| `network-manager` | `relationship-map`, `follow-up-sweep` |
| `ops-engineer` | `automation-audit`, `tool-stack-review` |

### Cut during design

Each failed the test *name a job the survivor doesn't already do*:

| Cut | Reason |
|---|---|
| `positioning-statement` | folded into `offer-design` |
| `deliberate-practice` | folded into `learning-plan` |
| `burnout-check` | folded into `energy-audit` |
| `os-upgrade` | v1 has nothing to migrate from |

---

## 7. Package layout

Standard `agentcompanies/v1` layout, in a new public git repo named `founder-os`:

```
founder-os/
├── COMPANY.md              # name, description, slug, schema, version, license, authors, goals
├── README.md               # org chart, skills, install instructions
├── LICENSE                 # MIT
├── .paperclip.yaml         # FOUNDER_OS_HOME input declaration
├── agents/<slug>/AGENTS.md         # 12
├── teams/<slug>/TEAM.md            # 4
├── skills/<slug>/SKILL.md          # 44
├── projects/onboarding/
│   ├── PROJECT.md
│   └── tasks/<slug>/TASK.md        # 4
├── tasks/<slug>/TASK.md            # 8 scheduled
├── references/house-rules.md
└── images/org-chart.png
```

**Totals (v1.1):** 12 agents · 4 teams · 47 skills (41 role + 6 system) · 18 workspace files · 1 project (4 tasks) · 8 scheduled cadences.

### Required frontmatter

`COMPANY.md`:
```yaml
name: Founder OS
description: The executive team you can't afford yet — strategy, offer, pipeline, delivery, money and focus for a company of one.
slug: founder-os
schema: agentcompanies/v1
version: 1.0.0
license: MIT
authors:
  - name: Mateusz Solecki
goals: [...]
```

`AGENTS.md`:
```yaml
name: <Agent Name>
title: <Role Title>
reportsTo: <agent-slug or null>
skills:
  - <skill-shortname>
```

Agent bodies follow: **What triggers you / What you do / What you produce / Who you hand off to**.

### Org chart image

`images/org-chart.png`, generated from a mermaid source committed alongside it so it can be regenerated when the roster changes.

---

## 8. Distribution

1. Public git repo `founder-os`, MIT licensed.
2. README with `npx companies.sh add <owner>/founder-os`.
3. Submit to the directory via companies.sh `/submit`.
4. Optionally PR into `paperclipai/companies` (their `CONTRIBUTING.md` requires: `COMPANY.md` frontmatter with `name`/`description`/`slug`/`schema`/`version`/`license`/`authors`/`goals`, a `README.md`, a `LICENSE`, and a clean `--dry-run` import).

### Verification before submission

- `paperclipai company import --from ./founder-os --dry-run` passes.
- Every `AGENTS.md` `skills[]` entry resolves to a real `skills/<shortname>/SKILL.md`.
- Every `reportsTo` resolves to a real agent slug or `null`.
- Every team `manager`/`includes` path resolves.
- Every scheduled `TASK.md` `assignee` resolves to a real agent, and the skill it invokes is in that agent's `skills[]`.
- The file-ownership map covers every workspace file, with exactly one owner each.
- No **role** skill is listed under two agents. (System skills are exempt by design — `guardrails`, `state-integrity` and `ingestion-gate` appear under all 12.)
- Every one of the 47 skills is reachable from at least one agent; no orphans.

---

## 9. Open questions

None blocking.

---

## 10. v1.1 — competitor analysis and the defect it found (2026-07-15)

Five rival `founder-os` repos and the paperclipai platform were analysed. Findings that changed the design.

### 10.1 The cadence engine was partly fiction — CRITICAL, fixed

`TASK.md` `schedule.recurrence` is the **legacy** path. The Paperclip importer names the field `legacyRecurrence` and, at `server/src/services/company-portability.ts:1321`, hard-errors on any weekly/monthly/yearly `interval > 1`, returning `trigger: null`:

```ts
} else if (frequency === "monthly") {
    if (interval !== 1) {
      errors.push(`... legacy monthly recurrence with interval > 1 ...`);
      return { trigger: null, warnings, errors };
```

§4 shipped `quarterly-planning` as `frequency: monthly, interval: 3`. **The quarterly cadence never existed.** Our validator proved every internal reference resolved; it could not see the importer. That gap was a direct consequence of treating companies.sh as a reference rather than a dependency — the same mistake that left `thecloudtips/founder-os` with 395 files, a fabricated MCP config, and 3 stars.

**Resolution.** `TASK.md` now carries only `recurring: true` (portable, per spec §10). Schedules live in `.paperclip.yaml routines.<slug>.triggers` as cron. `quarterly-planning` is `0 11 1 1,4,7,10 *` — true calendar quarters, which also removes the drift that `schedule.startsAt` was patching. `startsAt` is gone.

`catchUpPolicy: enqueue_missed_with_cap` is set explicitly on all 8. The runtime default is `skip_missed`: a closed laptop on Friday makes the weekly review silently never happen — a promise that fails exactly when it was needed.

`check_routines` in the validator now hard-fails any `schedule:` block in a TASK.md and any recurring task without a firing trigger. **The legacy path cannot return.**

### 10.2 Guardrails guarded the wrong axis — House Rule 0

Every guardrail was organised by **topic** (CFO refuses tax/legal, Focus Coach refuses medical). Topic guardrails cannot see irreversibility: *"send the follow-up to Anna"* is not a tax, legal, or medical question. Nothing in v1.0 stopped an agent from **sending** the outreach it drafted, on a founder whose Claude has a mail MCP connected.

**House Rule 0: Never outbound. Never money.** Adapted from `tomkels987/founder-os`, which repeats the invariant in every routine. Drafting is permitted; sending, paying, posting and signing are not, regardless of agent or instruction. The capability existing is not the permission.

### 10.3 Nothing governed whether a claim was true — House Rule 5 + `ingestion-gate`

`ownership.yaml` governs *who may write* a file. It says nothing about the truth of what goes in. Without a gate, House Rule 2 ("evidence over vibes") is a laundering machine: a guess written once is quoted as a number forever.

`ingestion-gate` becomes the **third universal skill** (all 12 agents, alongside `guardrails` and `state-integrity`). Claims are tiered FACT / VALIDATE / DISREGARD before entering a canonical file, with provenance stamped **inline** — a file's mtime says when someone touched the file, not when the claim was last true. Adapted from `tomkels987`'s `INGESTION_GATE.md` and `SOURCES_OF_TRUTH.md`.

### 10.4 New workspace files

| File | Owner | Why |
|---|---|---|
| `queue.md` | `chief-of-staff` | Cadences produced advice that evaporated — "follow up with Anna" left no artifact. Durable states: Doing / Queued / Blocked / Done / Dropped. Concept from `cloudrepo-io/founder-os`; its approval gate was rejected (a solo founder approving their own plan is ceremony — the gate that matters is House Rule 0, on *sending*). |
| `voice.md` | `brand-editor` | Three skills draft text that goes out under the founder's name with no voice spec at all. Concept from `jermaine-craig/Founder-OS`, whose version is an anti-slop filter with no samples and — their bug — is wired into no skill. |

### 10.5 Rejected, with reasons

- **OAuth integrations** (`jermaine-craig`): BYO-GCP + Testing status expires the refresh token every **7 days**, forever; escaping that makes `gmail.modify` a restricted scope requiring a CASA assessment. Their `output/` is not gitignored while their Gmail tool writes 5,000 chars of every email body into it — in a repo whose headline feature is forking. If external reads are ever added: MCP connectors, read-only, opt-in, never core.
- **Chasing skill count**: `thecloudtips` ships ~10× our surface and was never run once. Size is not the differentiator; an end-to-end run is.
- **A named authorial POV** (`yomidenzel/BOS`): unupdatable and must be defended. Its principles file also trains the agent to override the user by authority (*"90% chance you're the one who's wrong"*) alongside *"dopamine cycles feed retention"*. The **mechanism** (opinionatedness) is worth taking; the doctrine is not.

### 10.6 Market position (verified 2026-07-15)

**Zero of the 18 companies in the companies.sh directory use routines** — not one recurring trigger; only 7 `TASK.md` total, all one-shot starters. Founder OS would be the only company in the directory that runs on a schedule. That, plus being the only package about the operator rather than the work, is the position.

The runtime **does** enforce the org chart (`agent-invokability.ts` blocks on `reporting_cycle`, `manager_terminated`, and cancels live runs on a broken graph), so `reportsTo` is load-bearing. **Single-owner-per-file is ours alone** — zero references in the runtime. Our validator is the only thing enforcing it; it must not be marketed as runtime-guaranteed. `.paperclip.yaml` `permissions` / `permissionGrants` is the only real backstop and is not yet used.
