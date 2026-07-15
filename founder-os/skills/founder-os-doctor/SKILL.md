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

- `references/ownership.yaml` — `workspace_files:` is the expected inventory.
- Every file in `$FOUNDER_OS_HOME`, plus its last-modified date. The dates are
  half the diagnosis.
- All 8 `tasks/*/TASK.md` and `charter.md` for the timezone check.

## The checks

Each has a threshold. Report the ones that trip and stay quiet about the rest —
a health report that lists eleven green checks trains the founder to skim it.

| Check | Trips when | Why it matters |
|---|---|---|
| **Missing files** | An entry in `workspace_files:` does not exist | Its owner has nowhere to write. The gap is silent until the agent needs it. |
| **Stale metrics** | `metrics.md` unmodified > 30 days | House rule 2 collapses. Every agent quotes `metrics.md`; all twelve are now confidently quoting a number from last quarter. |
| **Metrics abandoned** | `metrics.md` unmodified > 60 days | Stop reporting and escalate. Every claim downstream is a guess and must be labelled one until the **CFO** closes the month. |
| **Goals without bets** | `goals.md` has no bet with a numeric kill condition, and the quarter is > 1/3 gone | A bet without a threshold cannot be killed, so it will not be. `kill-or-continue` has nothing to force. |
| **Orphan clients** | A `clients/*.md` file names no client that `metrics.md` shows revenue for, and is unmodified > 90 days | Two possibilities and both matter: the engagement ended and nobody closed the file, or work is being delivered and not billed. |
| **Empty decision log** | `decisions/` is empty after 30 days of use | House rule 3 is not being followed. Six months from now the founder asks why they raised rates and the answer will not exist. `annual-review` has nothing to read. |
| **Cadence gone quiet** | No file in `reviews/daily/` for the last 5 weekdays | The scheduler is not firing, or it is firing at an hour the founder ignores. Check the timezone. |
| **Timezone drift** | Any `tasks/*/TASK.md` `schedule.timezone` ≠ the timezone in `charter.md` | A package update reset it. The cadences did not break — they fire at the wrong hour and get ignored, which looks identical to the founder losing interest. |

## Steps

1. **Inventory against `ownership.yaml`.** Not against this skill's memory of
   what the workspace should contain.
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

Only two things, and both are structural:

- **Create a missing file as an empty stub with its heading.** Nothing else.
- **Rewrite `schedule.timezone` in `tasks/*/TASK.md`** to match `charter.md`.

Everything else is a handoff, by name and with the finding attached: stale
metrics → **CFO**. Goals without kill conditions → **Strategist**. Orphan client
files → **Delivery Lead**. Empty decision log → **Chief of Staff**.

This skill and `founder-os-init` are the only two that may create a file across
an ownership boundary, and only ever an empty one. Creation is lifecycle;
content is ownership. A doctor that writes a plausible revenue number into an
empty `metrics.md` has not repaired the workspace — it has poisoned it, in the
one file every other agent trusts.

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
