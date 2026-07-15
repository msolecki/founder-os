---
name: founder-os-init
description: Run first-install onboarding — interview the founder, scaffold the workspace, and rewrite the scheduled tasks to their timezone
---

# Founder OS Init

This runs once, at install, and it decides whether the founder is still using
this package in three weeks.

A new installer faces twelve agents and an empty directory. Nothing in that
directory can be advised on, because house rule 1 forbids advice without state,
so the entire company is inert until this skill runs. The failure mode is not
that onboarding is hard — it is that onboarding is *thorough*: forty questions,
fifteen carefully scaffolded files, and a founder who closes the terminal and
never opens it again. Get the four files that matter real, stub the rest, and
let the cadences fill them in.

## When to use

Immediately after install, before any other agent runs. Also after moving
`FOUNDER_OS_HOME`, and — for the timezone step only — after every package
update. See *The package rewrites its own files* below; this is not optional
housekeeping.

Do not run it to "refresh" a live workspace. That is `founder-os-doctor`.

## Inputs

- `references/ownership.yaml` — `workspace_files:` is the scaffold list. Read it;
  do not scaffold from memory or from this skill. The list changes and this file
  does not.
- `$FOUNDER_OS_HOME`, default `./founder-os/`.
- Existing `charter.md`, if any — the abort check in step 1.

## Steps

1. **Refuse to init over a live workspace.** If `charter.md` exists and has
   content, stop and say so. Re-running init over real state is the one way this
   skill can destroy something irreplaceable, and "it looked empty" is not a
   defence. Route to `founder-os-doctor`, which repairs without clobbering.

2. **Ask the timezone first.** It is needed before step 3 and the founder is
   never more willing to answer questions than in the first minute. IANA form —
   `Europe/Warsaw`, `America/Denver`. Store it in `charter.md`.

3. **Rewrite `schedule.timezone` in all 8 `tasks/*/TASK.md` files.** Every one,
   to the value from step 2. See below for why this is strange and why it stays.

4. **Scaffold every entry in `workspace_files:`.** Directories as directories,
   files with their heading and nothing else. Empty is honest; a stub full of
   plausible placeholder content is a lie the next agent will read as state and
   quote as fact.

5. **Run `projects/onboarding` in order, and only in order** — `write-charter` →
   `define-icp` → `set-quarter-goals` → `baseline-metrics`. The order is the
   product: goals set before the offer is named are hopes about a business that
   hasn't been described, and metrics baselined before goals exist have nothing
   to be a baseline *of*.

6. **Stop at twenty minutes.** Hard rule, not a target. Past twenty minutes you
   are conducting an interview, not onboarding, and the founder is answering to
   be polite. A thin charter that exists beats a rich one that was abandoned in
   the middle. Anything unanswered gets a `TODO` line and the first weekly review
   picks it up.

7. **End by running the first `daily-brief`.** The founder must see the company
   produce something on day one, or the install was a chore with no payoff.

## The interview

Four questions. They are chosen because each is one a founder is actively
avoiding, and because each has a file that cannot be written without it.

- **What is this business, in one sentence, without the word "and"?** The `and`
  is the tell. It is where two businesses are hiding in one calendar. →
  `charter.md`
- **Name two clients you would take again, and one you would not. What is
  different about them?** Founders cannot describe their ICP in the abstract and
  can always describe it by example. The one they would not take again is where
  the actual answer is. → `offer.md`
- **What has to be true in 90 days for this quarter to have been worth it — and
  what number would tell you it wasn't?** A bet without a kill condition is a
  hope; the second half of the question is the half that matters. → `goals.md`
- **Cash on hand, revenue *collected* in the last three months, and monthly burn
  including paying yourself.** Collected, not booked — an invoice sent is not
  money. Burn that omits the founder's own pay describes a company that is
  subsidised, not profitable. → `metrics.md`

If the founder does not know their cash number, that is the most important
finding of the onboarding. Write it down as unknown and hand to the **CFO**.
Do not estimate it for them.

## The package rewrites its own files

Step 3 edits files inside this package's own installation. That is unusual, and
it is deliberate — flagged as a known trade-off in the design spec (§4), not
discovered later.

`TASK.md` schedules embed a literal `schedule.timezone`. This package ships to
strangers. The alternative is shipping the author's timezone and hoping: every
founder outside that zone gets a daily brief at the wrong hour, turns the
cadence off in week one, and is left with a prompt library — the scheduled
cadences are the only thing that makes this an OS rather than a folder of
prompts.

**The consequence, which you must tell the founder:** reinstalling or updating
the package overwrites `tasks/*/TASK.md` and restores the shipped timezone. The
cadences do not break loudly when this happens; they fire at the wrong hour and
get ignored. After any update, re-run step 3. `founder-os-doctor` checks for
this drift specifically.

## Output

- `$FOUNDER_OS_HOME/` containing every entry from `workspace_files:` —
  `charter.md`, `offer.md`, `goals.md` and `metrics.md` with real content from
  the interview; the rest as empty stubs with headings.
- All 8 `tasks/*/TASK.md` with `schedule.timezone` set to the founder's zone.
- `decisions/YYYY-MM-DD-founder-os-installed.md` — the timezone chosen, the
  workspace path, and any question the founder could not answer. This is the
  first entry in the decision log and it establishes the habit that makes
  `annual-review` possible twelve months from now.
- The first daily brief.

## Guardrails

Never overwrite a workspace that has content. Never invent a number the founder
did not give you — an empty `metrics.md` is a known gap, and a plausible one is
a lie every agent downstream will quote as fact under house rule 2.

Never scaffold beyond `workspace_files:`. Extra files are unowned files, and
`state-integrity` will refuse to write them for the rest of the package's life.

No tax, legal, or medical advice, including in the interview. The entity
question — sole trader, limited company, which jurisdiction — will come up
inside the first five minutes because it feels like setup. It is not setup. See
`guardrails`.
