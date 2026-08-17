---
# promptscript-generated: 2026-08-14T09:55:27.938Z | source: .promptscript/project.prs | target: claude
name: founder-os-doctor
description: Diagnose workspace rot — missing files, stale metrics, goals without bets, orphan clients, silent cadences — and report before repairing anything
references:
  - agents/openai.yaml
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

- An agent said something that felt wrong. It usually read something stale.
- The founder returns after two weeks away.
- `founder-os-init` refused to run because a workspace already exists.
- The founder is about to report a problem with this package upstream —
  see `## The shareable report`, which is the only output of this skill that
  is meant to leave the machine, and leaves it in the founder's hands.

## Inputs

- `references/ownership.yaml` — `workspace_files:` is the expected inventory and
  `sections:` is the expected structure inside each flat file. Both are checks.
- Every file in `$FOUNDER_OS_HOME`, plus its last-modified date. The dates are
  half the diagnosis.
- `$FOUNDER_OS_HOME/_local/`, if it exists — the founder's local overlay, and
  `references/extensibility.md` is its contract. **This is the only validation
  the overlay ever gets.** `scripts/validate_package.py` checks the package in
  CI, on a machine that will never see a stranger's `_local/`, so every check
  that file's contract needs has to run here — weeks later, on real state, at a
  moment nobody chose. That is worse than build time and it is the only option
  available; say so in the report rather than implying the overlay was vetted.
- `~/.founder-os/businesses.yaml`, if it exists — the multi-business registry.
  It scopes the run: **you doctor one workspace per run**, the one resolved by
  `context-load` step 0, and the portfolio check below is the one place you
  look outside it. No registry, no portfolio check — a single-business install
  has nothing there to be sick.

**You have no shell, and the cadence checks are the place that hurts.** The
schedule lives in the founder's scheduler, on their host, and you cannot read it.
So you diagnose the cadences the only way available to you — by what did or did
not get written to `reviews/daily/` — and you hand the *why* to
`/setup-cadences`, which can look. Do not guess at a cause you cannot see.

**The link check needs no shell and no host.** Every `[[slug]]` and every target
is in the workspace you already read, which makes it the cheapest real check here
— and the only one that gets more valuable as the workspace grows, because it is
the one that catches two agents drifting apart on the same entity.

## The checks

Each has a threshold. Report the ones that trip and stay quiet about the rest —
a health report that lists a screen of green checks trains the founder to skim it.

| Check | Trips when | Why it matters |
|---|---|---|
| **Missing files** | An entry in `workspace_files:` does not exist | Its owner has nowhere to write. The gap is silent until the agent needs it. |
| **Section drift** | A flat file is missing a heading `sections:` declares for it, or carries a `##` heading the map does not declare. A dated suffix after the section name (`## Close — 2026-07`, `## Gap — 2026-07-15`) is not drift — the name is pinned, the suffix is free, and flagging it would report `revenue-review` doing its job | Existence was never the contract. `energy-audit` replaces `## Shape` and `revenue-review` replaces `## Close`; told to replace a heading that is not there, a skill writes its own spelling, and now two headings hold one section — one gets read, the other is wallpaper the founder can see and no agent will. An undeclared heading is the same bug caught earlier. |
| **Stale metrics** | `metrics.md` unmodified > 30 days | House rule 2 collapses. Every agent quotes `metrics.md`; all of them are now confidently quoting a number from last quarter. |
| **Metrics abandoned** | `metrics.md` unmodified > 60 days | Stop reporting and escalate. Every claim downstream is a guess and must be labelled one until the **CFO** closes the month. |
| **Goals without bets** | `goals.md` has no bet with a numeric kill condition, and the quarter is > 1/3 gone | A bet without a threshold cannot be killed, so it will not be. `kill-or-continue` has nothing to force. |
| **Orphan clients** | A `clients/*.md` file names no client that `metrics.md` shows revenue for, and is unmodified > 90 days | Two possibilities and both matter: the engagement ended and nobody closed the file, or work is being delivered and not billed. |
| **Empty decision log** | `decisions/` is empty after 30 days of use | House rule 3 is not being followed. Six months from now the founder asks why they raised rates and the answer will not exist. `annual-review` has nothing to read. |
| **Cadence never fired** | `reviews/daily/` is empty, and `charter.md` is more than 3 days old | `setup-cadences` was never run. The workspace looks installed and no cadence exists: scheduled state is installed on the founder's machine only after they approve that skill. This is the most common finding on a workspace that "went quiet in week one", and it is the cheapest to fix. |
| **Cadence gone quiet** | `reviews/daily/` has files, but none for the last 5 weekdays | It fired before and it stopped. **You cannot see why** — the scheduler is on the host and you have no shell. The job may have been removed, the host binary or authentication may have changed, or cron may have missed sleeping-machine runs. Report the last date you can see and hand to `setup-cadences`; its per-cadence logs and smoke test are where the answer actually is. |
| **Broken link** | A `[[slug]]` in any file resolves to neither a workspace file nor a `network.md` `## Map` row | House rule 6 says a name another file holds is a link. A link that resolves to nothing is worse than the retyped name it replaced: it looks joined. `follow-up-sweep` reads `## Map` and `pipeline-review` reads `pipeline.md`, and a dangling `[[acme-corp]]` means one of them is advising on a company the other cannot see. Report the file, the line and the slug, and hand to the owner of the file holding the link — the fix is theirs, and inventing the missing row would be inventing an entity. |
| **Inbox not drained** | `inbox.md` `## Inbox` is non-empty and `reviews/daily/` has a file from today or later | The inbox has no clock because it has a drain — `triage` and `daily-brief` empty it every run. A brief that ran and left lines behind is a brief that skipped step 0, and those lines are now in the one file with no cap, no clock and no reaper. This is the graveyard forming in the door built to have none. Hand to the **Chief of Staff**; do not drain it yourself, because draining means deciding what each line is, and that is the triage you are not running. |
| **Briefs nobody acted on** | 10+ files in `reviews/daily/`, and fewer than 1 in 5 of their `## The one thing` items appear in `queue.md` `## Done` or `## Dropped` | The company is writing and nobody is reading. Every other check here finds state that is wrong; this one finds state that is fine and ignored, which is the failure that ends the install — the cadences fire, the files fill, and the founder stopped opening them in week three. **Say what this does and does not measure**: it sees whether the one thing reached the queue, not whether the founder did the work. A founder who does the work and never closes the item trips this check and is right to be annoyed. Report the ratio and the window, ask which of the two it is, and hand to the **Chief of Staff**. Never repair — there is nothing structural here to fix. |
| **Portfolio dark** | The registry lists 2+ active businesses, and the portfolio workspace is missing, `portfolio.md` lacks a heading `sections:` declares (or carries one the map does not), or `## Review` has no entry from the last 21 days | Two businesses and no living `portfolio.md` means the one decision only the portfolio chair can make — the split of the founder's hours and cash — is being made by default, weekly, with no record. The per-business cadences cannot notice: each grades on its own curve, which is exactly how a starving business stays invisible. Report which of the three it is and hand to the **Portfolio Manager** (`/portfolio-review`); if the workspace itself is missing, the scaffold is `founder-os-init`'s second-business flow, not yours. |
| **Overlay unreadable** | `_local/ownership.yaml` exists and does not parse, or carries no usable `owns:` map | The guard has been ignoring it since the moment it broke — correctly, because an overlay that fails closed would deny the founder their own files. The cost is silent and it is not nothing: every local path is unowned, so any agent may write any of them, and the founder believes otherwise. Report the parse error verbatim and hand it back to them; `_local/` is theirs and this skill does not edit it. |
| **Overlay claims a packaged path** | An entry under `owns:` in `_local/ownership.yaml` names a path `references/ownership.yaml` already owns | The overlay is additive only (`references/extensibility.md`). The guard already drops the entry and logs it, so nothing is currently mis-owned — but the founder wrote it meaning something, and what they meant is usually "the CFO should not be the one writing this". That is a conversation about the packaged map, not an override to leave in place where it reads as active. Report the path, name both claimants. |
| **Overlay incoherent** | A path in the overlay's `workspace_files:` or `sections:` has no `owns:` entry; or two local agents claim one path; or a local skill's `metadata.writes` names a path its agent does not own | The three joins `scripts/validate_package.py` runs against the package, run here against the overlay. The third is the one nothing else catches: `agent -> skill` and `file -> owner` can both be right while `skill -> file` is wrong, and the result is a local skill that produces a deny every time it runs. Report each join that failed. |
| **Local agent overreaches** | A file in `_local/agents/` omits `tools:`, or names `Bash`, `WebFetch`, `WebSearch`, `Agent`, or an `mcp__*` tool | Omitting `tools:` inherits everything, including Bash. **You are the only check that reads this rule.** The guard's `check_outbound` denies outbound tools to the thirteen packaged roles; a local agent is not one of them, so the role lockdown never applies to it and a granted `Bash` is a capability the founder really has. The gateway still refuses it — no role capability, no `founder-os-state` call — but nothing stops the shell. Report the tool by name and say plainly that it is live, not pending a mid-run denial. House rule 0 binds every packaged role; it cannot bind an agent the founder wrote, which is why this finding is theirs to act on. |
| **Local skill off template** | A file in `_local/skills/` is missing `## Beliefs`, carries fewer than 3 belief bullets, places them after `## Steps`, or its slug lacks the `local-` prefix or collides with a packaged skill | The template's bar does not lapse because the founder is the author — a local skill with no beliefs is the generic advisor with a custom name on it, which is the thing this package exists not to be. The slug rules are collision insurance: a packaged skill added upstream next year must not silently shadow one they wrote this year. |
| **Installed copy drift** | A skill in `_local/skills/` has no identical installed copy under either `~/.claude/skills/` or `~/.codex/skills/`, or either copy differs from its source | Two host copies are required by the one-contract rule. Uninstalled means a workflow exists and one host cannot run it; diverged means the founder edited a copy the doctor cannot vouch for. Report the host and hand to `/skill-forge`; **never sync them yourself** — you cannot tell which side is intended. |
| **Queue rotting** | `## Doing` holds more than 3 items, `## Queued` more than 15, or any item sits past its own clock — 21 days queued, 14 blocked, 5 in `## Doing` | The caps and clocks live in `queue` and the Friday sweep in `weekly-review` is the only thing that enforces them. If the sweep stalls, the queue bloats into the graveyard `queue` warns about and nothing else notices — every other check reads state some cadence maintains, and this is the state the missing cadence was maintaining. Report the counts and the oldest offender; hand to the **Chief of Staff**. Never drop items yourself — the drop rule wants a reason written, and that is the sweep's job, not yours. |

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
   the org's output, the other is an empty file nobody has needed yet.
4. **Propose each repair, individually, and wait.** No batch confirmation. "Fix
   all of it" is how the founder approves something they did not read.
5. **Repair only what was confirmed.** Then re-run the tripped check and show
   the founder it passes. A repair reported but not verified is how this skill
   becomes the thing that lies.

## What it may repair

Only two things, and both of them are structural:

- **Create a missing file as an empty stub**, carrying its H1 and the headings
  `sections:` declares for it. Nothing under them.
- **Restore a missing section heading, empty**, to a file that already exists —
  only a heading the map declares. A heading the map does not declare is a
  finding for its owner, never a repair: deleting it would destroy content.

Everything else is a handoff, by name and with the finding attached: stale
metrics → **CFO**. Goals without kill conditions → **Strategist**. Orphan client
files → **Delivery Lead**. Empty decision log → **Chief of Staff**.

**A silent cadence is a report, never a repair.** Both cadence checks hand to
`/setup-cadences`, and neither is yours to fix: repairing one means writing a
scheduler artifact on the founder's machine, and you have no shell, no confirmation, and
no business doing it. **Never invent scheduler state.** One invented here is worse
than the silence it replaced — the founder believes the cadence is back and it
fires on a schedule nobody chose, or it does not fire at all and they have
stopped looking. Say what you saw: the date of the last brief, or that there has
never been one. Name `/setup-cadences` as what installs and inspects the
schedule. Stop there.

This skill and `founder-os-init` are the only two that may create a file — or a
declared heading — across an ownership boundary, and only ever an empty one.
Creation is lifecycle; content is ownership. A doctor that writes a plausible
revenue number into an empty `metrics.md` has not repaired the workspace — it has
poisoned it, in the one file every other agent trusts. The heading is scaffolding
and yours to restore; the line under it is the CFO's and never yours to write.

**No overlay finding is repairable, and that is one rule rather than six.**
`_local/` is the founder's own map (`references/extensibility.md`), and this
skill does not edit the map that decides what agents may write — for the same
reason the guard denies every subagent that directory. Report the finding, name
the file and the line, hand it to `/skill-forge` or to the founder. A doctor
that quietly rewrites an ownership entry to make its own check pass has not
repaired anything; it has changed who is allowed to write the company's state,
which is not a repair at any size.

**None of the link, inbox or brief checks is repairable, and each for its own
reason.** A broken link needs an entity created — that is the Network Manager's
decision or the founder's, never a doctor's guess at which `[[acme-corp]]` was
meant. An undrained inbox needs each line triaged, which is `triage`, not a
cleanup. A brief nobody acted on is not damage: the files are correct, and what
is wrong is outside the workspace. **A doctor that acts on the third check is
managing the founder**, which is not a repair and not this package's business.

## Output

No file. A health report written into `$FOUNDER_OS_HOME` would itself be an
unowned file, which is a finding this skill is supposed to report, not create.

Deliver in conversation:

    Workspace: <path> — <N> finding(s)

    <severity>. <check>: <what tripped, with the number or the date>
       -> <repair offered, or the agent it hands to>

If nothing tripped, say so in one line. Do not enumerate the passing checks.

## The shareable report

Everything above is written for the founder, about their own company, and none
of it can leave this machine. That is correct, and it costs something: the
people maintaining this package cannot see whether a single install ever
reached a valid brief, which failure the founder is describing, or whether the
workspace they are describing is even shaped the way they think it is.

There is no telemetry here and there will not be — a package whose one promise
is that state stays local does not get to make an exception for its own
metrics. So the only channel is the founder deciding to paste something into a
public issue, and the reason they do not is the obvious one: a health report is
full of their client names, their runway, and their pipeline.

This is the version they can paste.

### Built from a list, never filtered from a report

**Construct it from the field list below and nothing else.** Do not take the
health report you just wrote and strip the sensitive parts out of it.

Redaction is a filter, a filter is judged line by line, and the line nobody
judged is the one carrying the client's name — in a public issue, under the
founder's own account, permanently. A fixed field list fails the other way: a
check added next month that leaks nothing at all also appears nowhere until
somebody adds it here. That is a missing line in a bug report. The other one is
a disclosure the founder cannot take back.

Every field below is a name from this package's own vocabulary, a count, a day
count, or a ratio. **Nothing the founder wrote enters it.**

| Field | Value | Why this is not the founder's data |
|---|---|---|
| `founder-os` | Version, read from `.claude-plugin/plugin.json` | The package's own number. |
| `host` | `claude-code` or `codex` | Which host is running you. |
| `businesses` | The count of active entries in the registry, or `1` | A count. Never a slug — a business slug is a company name. |
| `activated` | `yes` / `no` — is there a `reviews/daily/` file with the four required headings, `## The one thing` and `## The trade` non-empty | The answer maintainers most need and cannot otherwise get. |
| `workspace` | `<present>/<declared>` against `workspace_files:`, then the names of any missing entries | Those names come from `ownership.yaml`. The founder did not choose them. |
| `sections` | Per file, the *declared* headings that are missing, spelled from the map. Undeclared headings by **count only** | An undeclared heading is text the founder wrote. `## Acme renewal` is a client name in a heading. |
| `metrics` | Days since `metrics.md` was last modified | An age, not a number from inside the file. |
| `cadence` | `live`, `quiet <N>d`, or `never` | Derived from filenames and dates. |
| `briefs` | Count, and days since the newest | Counts. |
| `queue` | Item counts per section | Counts. Never an item's text — a queue line is usually a client obligation. |
| `clients` | Count, and how many tripped **Orphan clients** | Counts. Never a filename: `clients/*.md` is named after the client. |
| `decisions` | Count of files in `decisions/` | A count. Decision titles are strategy. |
| `links` | Count of broken `[[slug]]` links | A count. **Never the slug** — a slug is an entity, which is to say a person or a company. |
| `overlay` | `none`, or counts: local paths, local skills, local agents, installed copies | Counts. **Never a local slug, path or heading** — the founder named all three, and `local-acme-renewals` is a client in a filename. The overlay is the single most useful thing in this report for whoever reads the issue and the single easiest place to leak from; the field list is what keeps those two facts apart. |
| `tripped` | The names of the checks that tripped, each with the number that tripped it | Check names are this file's vocabulary; the numbers are ages, counts and ratios. |

Never include, whatever the founder says about how urgent the bug is: any line
of content from any file; any `[[slug]]`, client name, business slug or
person's name; any undeclared heading spelled out; any amount of money,
runway figure or deal value; any absolute path — `$FOUNDER_OS_HOME` is a
directory the founder named, and they named it after the company, so report it
as `default` or `custom` and stop. **Day counts, not dates.** A calendar date
is the one field that looks harmless in isolation and is not, because a public
issue keeps it next to everything else in the report.

### Format

One fenced block, in the conversation, ready to select and copy:

    founder-os 2.4.0 · host claude-code · businesses 1
    activated: yes · cadence: quiet 12d · briefs: 34
    workspace: 21/22 present — missing: voice.md · home: default
    sections: metrics.md missing "## Rate" · 2 undeclared (not shown)
    metrics: 47d · decisions: 6 · clients: 3 (1 orphan) · links: 2 broken
    queue: doing 5 / queued 18 / blocked 2 / done 41
    overlay: 2 paths · 1 skill · 0 agents · 1 installed
    tripped: stale metrics 47d · metrics abandoned · cadence gone quiet 12d ·
             queue rotting (doing 5, queued 18) · orphan clients 1

Then one line to the founder: **read it before you paste it.** It is built from
a list rather than a filter precisely so it cannot carry their state — and they
are still the last check, because they are the only reader who knows what is in
their own workspace.

### You do not send it

Show it. The founder pastes it. **This skill does not open a browser, does not
file an issue, does not call an API, and does not put the report anywhere but
the conversation** — house rule 0 is not suspended because the destination
happens to be this package's own bug tracker. It writes no file either, for the
same reason `## Output` writes none: a report saved into `$FOUNDER_OS_HOME`
would be an unowned file, which is a finding this skill exists to report rather
than create.

Offer it **once**, at the end of a run that tripped a structural check —
missing files, section drift, portfolio dark. Never after a clean run, never
twice in a session, and never instead of the health report the founder actually
asked for.

## Guardrails

Never delete. Never truncate. Never "clean up" a file that looks abandoned — an
orphan client file is a finding for the Delivery Lead, not garbage.

Never repair without confirmation, and never treat one confirmation as covering
the next repair.

Never write content into a file this skill's holder does not own, including
content it just read from somewhere else in the workspace. See
`state-integrity`; that skill's exemption for this one is narrow on purpose.

Never put a founder's own words into the shareable report, and never build that
report by removing things from this one. The field list is the contract; a
field it does not name does not go in, however useful it would be to whoever
reads the issue.
