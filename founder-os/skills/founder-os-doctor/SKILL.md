---
name: founder-os-doctor
description: Diagnose workspace rot — missing files, stale metrics, goals without bets, orphan clients, drifted schedules — and report before repairing anything
---

# Founder OS Doctor

The workspace is the company's memory, and every agent's advice is only as good
as the state it read. Corrupt state does not announce itself. It produces
confident, well-structured, wrong advice — which is strictly worse than no
advice, because the founder acts on it.

This skill finds the rot. It reports first and repairs only what the founder
confirms, because a doctor that silently fixes things is indistinguishable from
the thing that broke them.

## When to use

Monthly, and immediately after any of these:

- A package update or reinstall — see the timezone check below.
- An agent said something that felt wrong. It usually read something stale.
- The founder returns after two weeks away.
- `founder-os-init` refused to run because a workspace already exists.

## Inputs

- `references/ownership.yaml` — `workspace_files:` is the expected inventory and
  `sections:` is the expected structure inside each flat file. Both are checks.
- Every file in `$FOUNDER_OS_HOME`, plus its last-modified date. The dates are
  half the diagnosis.
- `.paperclip.yaml` `routines:` and `charter.md` `## Timezone` for the timezone
  check, and all 8 `tasks/*/TASK.md` for the missing-trigger check.

## The checks

Each has a threshold. Report the ones that trip and stay quiet about the rest —
a health report that lists a screen of green checks trains the founder to skim it.

| Check | Trips when | Why it matters |
|---|---|---|
| **Missing files** | An entry in `workspace_files:` does not exist | Its owner has nowhere to write. The gap is silent until the agent needs it. |
| **Section drift** | A flat file is missing a heading `sections:` declares for it, or carries a `##` heading the map does not declare | Existence was never the contract. `energy-audit` replaces `## Shape` and `revenue-review` replaces `## Close`; told to replace a heading that is not there, a skill writes its own spelling, and now two headings hold one section — one gets read, the other is wallpaper the founder can see and no agent will. An undeclared heading is the same bug caught earlier. |
| **Stale metrics** | `metrics.md` unmodified > 30 days | House rule 2 collapses. Every agent quotes `metrics.md`; all twelve are now confidently quoting a number from last quarter. |
| **Metrics abandoned** | `metrics.md` unmodified > 60 days | Stop reporting and escalate. Every claim downstream is a guess and must be labelled one until the **CFO** closes the month. |
| **Goals without bets** | `goals.md` has no bet with a numeric kill condition, and the quarter is > 1/3 gone | A bet without a threshold cannot be killed, so it will not be. `kill-or-continue` has nothing to force. |
| **Orphan clients** | A `clients/*.md` file names no client that `metrics.md` shows revenue for, and is unmodified > 90 days | Two possibilities and both matter: the engagement ended and nobody closed the file, or work is being delivered and not billed. |
| **Empty decision log** | `decisions/` is empty after 30 days of use | House rule 3 is not being followed. Six months from now the founder asks why they raised rates and the answer will not exist. `annual-review` has nothing to read. |
| **Cadence gone quiet** | No file in `reviews/daily/` for the last 5 weekdays | The scheduler is not firing, or it is firing at an hour the founder ignores. Check the timezone. |
| **Timezone drift** | Any `.paperclip.yaml` `routines.<slug>.triggers[].timezone` ≠ `charter.md` `## Timezone` | A package update reset it to UTC. The cadences did not break — they fire at the wrong hour and get ignored, which looks identical to the founder losing interest. |
| **Cadence with no trigger** | A `tasks/*/TASK.md` with `recurring: true` has no `.paperclip.yaml` `routines.<slug>` entry, or that entry has no `kind: schedule` trigger | The task exists, names an agent, names a skill, and will never once fire. This is the failure that shipped: `quarterly-planning` carried a legacy `monthly`/`interval: 3` recurrence the importer rejected outright, and a whole quarterly cadence was silently absent. Nothing in the workspace shows it — there is no file missing, because a review that never ran leaves nothing behind. |

## Steps

1. **Inventory against `ownership.yaml`.** Files against `workspace_files:`,
   headings against `sections:`. Not against this skill's memory of what the
   workspace should contain — a check that runs from memory is a second map, and
   it will pass a workspace that has quietly rotted.
2. **Run every check. Collect, do not narrate.** Diagnose the whole workspace
   before saying anything; the interesting finding is usually the pattern across
   two checks — stale metrics *and* a quiet cadence is one problem, not two.
3. **Report, ranked by what is producing wrong advice right now.** Stale
   `metrics.md` outranks a missing `content.md` every time: one is corrupting
   twelve agents' output, the other is an empty file nobody has needed yet.
4. **Propose each repair, individually, and wait.** No batch confirmation. "Fix
   all of it" is how the founder approves something they did not read.
5. **Repair only what was confirmed.** Then re-run the tripped check and show
   the founder it passes. A repair reported but not verified is how this skill
   becomes the thing that lies.

## What it may repair

Only three things, and all of them are structural:

- **Create a missing file as an empty stub**, carrying its H1 and the headings
  `sections:` declares for it. Nothing under them.
- **Restore a missing section heading, empty**, to a file that already exists —
  only a heading the map declares. A heading the map does not declare is a
  finding for its owner, never a repair: deleting it would destroy content.
- **Rewrite `timezone` on `.paperclip.yaml` `routines.<slug>.triggers[]`** to
  match `charter.md` `## Timezone`. That field only. The cron expression and the
  policies beside it are not yours, and a cadence firing at the right hour on the
  wrong day is not an improvement.

Everything else is a handoff, by name and with the finding attached: stale
metrics → **CFO**. Goals without kill conditions → **Strategist**. Orphan client
files → **Delivery Lead**. Empty decision log → **Chief of Staff**.

A cadence with no trigger is a report, never a repair, and it goes to the
founder. Restoring it means writing a cron expression, and a cron this skill
invented is worse than the missing one it replaced: the founder now believes the
cadence is back, and it fires on a schedule nobody chose. Name the slug, say it
has never fired and cannot, and point at reinstalling the package — the shipped
`.paperclip.yaml` carries all 8 routines. `scripts/validate_package.py` catches
this at build time; you are the check that catches it in an install that has
already drifted.

This skill and `founder-os-init` are the only two that may create a file — or a
declared heading — across an ownership boundary, and only ever an empty one.
Creation is lifecycle; content is ownership. A doctor that writes a plausible
revenue number into an empty `metrics.md` has not repaired the workspace — it has
poisoned it, in the one file every other agent trusts. The heading is scaffolding
and yours to restore; the line under it is the CFO's and never yours to write.

## Output

No file. A health report written into `$FOUNDER_OS_HOME` would itself be an
unowned file, which is a finding this skill is supposed to report, not create.

Deliver in conversation:

    Workspace: <path> — <N> finding(s)

    <severity>. <check>: <what tripped, with the number or the date>
       -> <repair offered, or the agent it hands to>

If nothing tripped, say so in one line. Do not enumerate the passing checks.

## Guardrails

Never delete. Never truncate. Never "clean up" a file that looks abandoned — an
orphan client file is a finding for the Delivery Lead, not garbage.

Never repair without confirmation, and never treat one confirmation as covering
the next repair.

Never write content into a file this skill's holder does not own, including
content it just read from somewhere else in the workspace. See
`state-integrity`; that skill's exemption for this one is narrow on purpose.
