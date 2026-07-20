# Founder OS — external user clarity

Status: complete with documented review limitation
Date: 2026-07-20

## Goal

Make the public landing page and repository documentation understandable to a
founder who has never seen Founder OS, does not know its repository, and may
not yet understand Claude Code plugins.

## Decisions

- Keep the core positioning: an executive team for a company of one.
- Say plainly that agents are specialized roles invoked when needed, not 13
  always-running autonomous processes.
- Say plainly that Founder OS knows only what is recorded in its Markdown
  workspace. It does not sync calendars, CRMs, inboxes, or bank accounts.
- Make price and requirements explicit: Founder OS is free and MIT-licensed;
  Claude Code is required; Python 3 and PyYAML power the ownership hook; cron
  is optional and the machine must be running for scheduled cadences.
- Keep every install path identical: add marketplace, install plugin, run init.
- Use a real, contract-shaped example workspace as proof instead of relying on
  a visual mockup alone.
- Shorten the landing by removing the outcomes section, whose message repeats
  the memory, cadence, and decision sections.
- Do not edit `founder-os/COMMANDS.md` manually because it is generated.

## Step 1 — example workspace [M]

**What:** Add a small but internally coherent Studio North workspace tour with
real file headings and outputs.

**Where:** `examples/studio-north/`.

**How:** Use the section contract from `references/ownership.yaml` and output
formats from `daily-brief`, `weekly-review`, `pipeline-review`, and
`decision-log`. Clearly label all people, companies, and numbers as fictional.

**Test:** Every `##` heading used by the example is allowed for that path; the
daily brief points to a real queue item and bet; the pipeline, metrics, and
weekly review agree on their numbers and dates.

## Step 2 — landing clarity [L]

**What:** Remove every ambiguity found in the external-user audit.

**Where:** `site/index.html`.

**How:** Fix demo wording, show all install commands, add requirements and
license, explain the agent execution model and data boundary, add links to the
sample workspace, command catalogue, GitHub, and support, then remove the
repeated outcomes section and its unused CSS.

**Test:** A text-only read answers six questions without repository knowledge:
what it is, what it requires, where data comes from, what it cannot do, what it
costs, and exactly how to start.

## Step 3 — repository docs [M]

**What:** Make the same six answers visible in both GitHub entry points.

**Where:** `README.md`, `founder-os/README.md`.

**How:** Add concise "before you install", "how agents run", "what it knows",
sample, cost/license, and help sections. Link to generated `COMMANDS.md` rather
than duplicating its catalogue.

**Test:** Claims and commands match between both README files and the landing;
all relative links resolve inside the repository.

## Step 4 — validation and review [M]

**What:** Validate documentation, examples, package integrity, and tests.

**Where:** Entire changed set.

**How:** Run HTML/anchor/ARIA checks, scan links and example headings, run
`python3 scripts/validate_package.py founder-os` and unit tests, inspect the
staged diff, then commit only files from this task.

**Test:** Zero broken internal links, zero example contract violations, package
validator reports zero errors, and all unit tests pass.

## Invariant

The plugin's runtime behavior, ownership map, skills, hooks, and generated
command catalogue do not change. Existing unrelated working-tree changes stay
untouched.

## Next step

Push the resulting commit when ready; no implementation work remains.

## Progress

- Added a fictional, contract-shaped Studio North workspace across ten files,
  with consistent bet, queue, pipeline, review, decision, and weekly-plan data.
- Added a complete getting-started guide and synchronized the six essential
  answers across the landing page and both README entry points.
- External clarity audit passes: four documentation entry points, ten example
  contracts, 21 HTML IDs, internal anchors, ARIA targets, local links, inline
  JavaScript syntax, and the nine-hour weekly-plan arithmetic.
- Package validation passes with 13 agents, 49 skills, and zero errors. All 80
  unit tests pass.
- The required fresh subagent review could not read the changed files because
  the current ownership guard classifies every subagent shell read as blocked
  `Bash`. The guard was not bypassed or changed for this task; deterministic
  checks and a main-thread diff review are the available review evidence.
