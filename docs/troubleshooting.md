# Troubleshooting & FAQ

The first tool for anything that looks wrong is `/founder-os-doctor`. It
diagnoses workspace rot and **reports before it repairs anything** — it proposes
each fix individually and waits for confirmation, and some findings it will never
repair because the fix is a decision, not a structural edit.

## Activation and install recovery

**The Founder OS command is missing.** Refresh the marketplace, update the
plugin, then reload active plugins:

```text
/plugin marketplace update founder-os
/plugin update founder-os@founder-os
/reload-plugins
```

**Preflight stopped before the interview.** `/founder-os-init` has not changed
the workspace. Follow the failed check's repair instruction, then run
`/founder-os-init` again.

**The interview or an owner stage stopped.** Run `/founder-os-init` again. It
classifies the workspace as incomplete, preserves populated sections, and
resumes at the first missing owned output. Do not delete the workspace and do
not manually replay Positioning Advisor, Strategist, CFO, or Daily Brief steps.

**There is no activation receipt.** Activation requires a valid
`reviews/daily/YYYY-MM-DD.md` in the resolved workspace. A scaffold, populated
charter, or successful install is not activation. Rerun `/founder-os-init`; a
failure branch reports the completed stages and exact resume command and never
prints `Activation complete`.

A valid brief has all four required headings from `ownership.yaml`: `## The one
thing`, `## Rotting`, `## The trade`, and `## Triage`, with non-empty `## The
one thing` and `## The trade`. An empty, malformed, or wrong-path file is not an
activation receipt.

**Init says this workspace is already activated.** That means a valid daily
review exists. Use `/founder-os-doctor` to inspect or repair the live workspace;
init will not reset it.

Uninstall instructions and the distinction between plugin files and your
Markdown workspace are in [`getting-started.md`](getting-started.md#update-repair-or-uninstall).

## `/founder-os-doctor` — what it checks

The doctor runs 20 health checks. Each has a threshold; it reports only the ones
that trip and stays quiet about the rest (a screen of green trains you to skim). It diagnoses the
whole workspace first, then reports ranked by *what is producing wrong advice
right now*.

| Check | Trips when | Hands to |
|---|---|---|
| **Missing files** | An entry in `workspace_files:` doesn't exist — its owner has nowhere to write. | repair (scaffold) |
| **Section drift** | A flat file lost a heading `sections:` declares, or grew one the map doesn't. (A dated suffix like `## Close — 2026-07` is *not* drift.) | repair |
| **Stale metrics** | `metrics.md` unmodified > 30 days — every agent is quoting last quarter's number. | CFO |
| **Metrics abandoned** | `metrics.md` unmodified > 60 days — stop reporting, escalate; label everything downstream a guess. | CFO |
| **Goals without bets** | `goals.md` has no bet with a numeric kill condition and the quarter is > ⅓ gone. | Strategist |
| **Orphan clients** | A `clients/*.md` names no client `metrics.md` shows revenue for, unmodified > 90 days (ended-and-not-closed, or delivered-and-not-billed). | Delivery Lead |
| **Empty decision log** | `decisions/` empty after 30 days of use — house rule 3 isn't being followed. | Chief of Staff |
| **Cadence never fired** | `reviews/daily/` empty and `charter.md` > 3 days old — `/setup-cadences` was never run. The most common "went quiet in week one" finding, and the cheapest fix. | `/setup-cadences` |
| **Cadence gone quiet** | `reviews/daily/` has files but none for the last 5 weekdays. The doctor has no shell and cannot see *why* — crontab dropped, `claude` off cron's PATH, or the machine asleep at 08:00. | `/setup-cadences` (its logs have the answer) |
| **Broken link** | A `[[slug]]` resolves to neither a file nor a `network.md` `## Map` row — worse than a retyped name because it looks joined. | owner of the file holding the link |
| **Inbox not drained** | `inbox.md` non-empty *and* today's brief already ran — a brief that skipped step 0. | Chief of Staff |
| **Briefs nobody acted on** | 10+ daily reviews and fewer than 1 in 5 `## The one thing` items reached `queue.md` `## Done`/`## Dropped` — the company is writing and nobody's reading. Never repaired. | Chief of Staff |
| **Portfolio dark** | 2+ active businesses and `portfolio.md` missing, drifted, or `## Review` silent > 21 days. | Portfolio Manager |
| **Queue rotting** | `## Doing` > 3, `## Queued` > 15, or an item past its clock (21 days queued / 14 blocked / 5 in Doing) — the Friday sweep stalled. | Chief of Staff |
| **Overlay unreadable** | `_local/ownership.yaml` exists and doesn't parse, so the overlay owner cannot be resolved. Packaged roles cannot use it as gateway authority; founder-run local workflows remain outside the role gateway. | you (`_local/` is yours) |
| **Overlay claims a packaged path** | The overlay's `owns:` names a path the packaged map already owns. The guard drops the entry, so nothing is mis-owned — but it reads as active and it isn't. | you |
| **Overlay incoherent** | A local path with no owner or two owners, or a local skill writing a path its agent doesn't own — the last one denies every time that skill runs. | `/skill-forge` |
| **Local agent overreaches** | A `_local/agents/*.md` omits `tools:` or names an outbound tool. The guard denies those regardless, so this is early warning, not a breach. | `/skill-forge` |
| **Local skill off template** | A `_local/skills/*/SKILL.md` has no `## Beliefs` (or fewer than 3, or after `## Steps`), or a slug without the `local-` prefix / colliding with a packaged one. | `/skill-forge` |
| **Installed copy drift** | A local skill is missing from `~/.claude/skills/` or `~/.codex/skills/`, or either installed copy differs from `_local/`. Never synced automatically — the doctor can't tell which side is intended. | `/skill-forge` |

**What the doctor will *not* repair:** the link, inbox, brief-not-acted-on,
cadence, queue, and every overlay check. `_local/` is your map, and a doctor
that edits the map deciding who may write company state has not repaired
anything — see [`extensibility.md`](#extending-founder-os-for-one-business). Each fix is a decision — draining the inbox means
deciding what each line is (that's triage); dropping a queue item wants a reason
written (that's the sweep); a silent cadence's cause is outside the workspace. A
doctor that acts on "briefs nobody acted on" would be repairing the fact that the
founder stopped reading, which it cannot fix by editing a file.

## Common situations

**"It went quiet in week one."** First inspect `reviews/daily/`. If it has no
valid dated brief, activation never completed: rerun `/founder-os-init`. If the
valid first brief exists but no later weekday brief does, `/setup-cadences` was
probably never run. No schedule is written until you say yes to that skill.

**"The morning brief stopped appearing."** **Cadence gone quiet.** The machine
was likely asleep at 08:00, or `claude` isn't on the PATH that cron uses. Check
the per-cadence logs (`~/.founder-os/logs/<slug>/…` on multi-business installs);
re-run `/setup-cadences` to rewrite the fence.

**"An agent refused to write a file."** Read the stable gateway code. A
`ROLE_NOT_OWNER` denial names the canonical owner; hand off to that role.
`STALE_WRITE` means the file changed after the role read it; re-read and
reconcile once. `INVALID_DOCUMENT_STRUCTURE` means the proposed full document
does not match `ownership.yaml`. Do not route around any of these with a direct
file tool. See [`enforcement.md`](enforcement.md).

**"An agent refused to send / post / pay."** By design (house rule 0). No agent
sends, ever. It drafts to `drafts/…`; you press the button. Saying "just send it"
does not change this — the agent hands you the finished text.

**"The guard isn't blocking anything."** First distinguish the host hook from
the state boundary. The hook can stay silent for main-thread or malformed
non-role traffic; it is defense in depth, not a security sandbox. A known role,
however, has no direct file tool and must present a live role capability to the
local `founder-os-state` gateway. Gateway write uncertainty fails closed. See
[`enforcement.md`](enforcement.md).

**"Advice landed against the wrong company."** Multi-business resolution. Name the
business in the invocation (`/founder-os:daily-brief acme`) or set `default:` in
`~/.founder-os/businesses.yaml`. `context-load` stamps the resolved business into
the context line — check that line before trusting the advice. See
[`multi-business.md`](multi-business.md).

**"`COMMANDS.md` looks out of date after I edited a skill."** Regenerate it:
`python3 scripts/generate_commands.py founder-os`. It is generated, never
hand-edited; CI's `--check` fails a stale copy.

**"The build fails on a count."** `check_readme_counts` — the README's
Agents/Skills/Cadences table drifted from the package. Fix the number; a count
that drifts is a second map.

## Extending Founder OS for one business

Thirteen agents and fifty-two workflows are the shape of a company of one *in
general*. If your business has a decision none of them covers — a licensing
partner, a production rhythm, a regulator — you do not have to fork. Run
`/skill-forge`.

It writes a **local overlay** in your workspace, at `$FOUNDER_OS_HOME/_local/`:
a skill, the ownership entry for anything it writes, and, if you genuinely need
one, a local agent. The overlay survives `/plugin update` and `/plugin
uninstall`, and on a multi-business install each business has its own.

Three things to know before you use it:

- **It can only add.** The overlay may declare a new file, section, skill or
  agent. It can never reassign or remove one the package ships — an entry that
  tries is dropped by the guard and reported by the doctor. If a packaged file
  has the wrong owner for your business, that is an issue upstream, not
  something to shadow locally.
- **It is validated by `/founder-os-doctor`, not by CI.** The build validator
  runs on this repository and will never see your `_local/`. So the checks that
  hold the overlay to the contract run at diagnosis time, on your machine,
  weeks later. Run the doctor after forging anything.
- **A local skill needs installing to be runnable.** `_local/` is the source of
  truth; Claude Code and Codex load cached copies from `~/.claude/skills/` and
  `~/.codex/skills/`. `/skill-forge` names both exact paths and asks before
  writing them — same as `/setup-cadences` with a cron line — and the doctor
  reports when either copy drifts apart.

The full contract, including the merge rules and what the overlay deliberately
does *not* enforce, is
[`founder-os/references/extensibility.md`](https://github.com/msolecki/founder-os/blob/main/founder-os/references/extensibility.md).

## Reporting a bug without publishing your business

Founder OS has no telemetry, so a maintainer reading your issue can see nothing
about your install except what you paste — and a full doctor report is your
client names, your runway and your pipeline.

Ask the doctor for the **shareable report**. It is built from a fixed field
list rather than by redacting the health report, so it carries version, host,
whether the workspace ever activated, which declared files and headings are
missing, and the checks that tripped with their numbers — as counts, ages and
this package's own vocabulary. No file content, no entity slugs, no amounts, no
paths, no dates.

```
/founder-os-doctor      # then ask for the shareable report
```

It is printed in the conversation and never written, filed, or sent: you read
it, you paste it. Attach it to an issue on the repository.

## FAQ

**Does Founder OS read my email / calendar / bank?** No. Its persistent business
state is the Markdown workspace, plus context you explicitly supply in the
current session. Packaged roles have no browser, shell, direct file tool, or
external MCP tool; their only MCP surface is the bounded local state gateway.

**Is my data sent anywhere?** Workspace files stay on your machine. The prompts
and context you send through Claude Code or Codex remain governed by that
environment's data-handling terms — that is separate from Founder OS. Founder OS
does not claim offline operation or zero transmission by the host environment.

**Do I need cron?** No. Cron only powers the optional scheduled cadences. Every
cadence also works typed by hand.

**Do I need PyYAML?** The installed gateway and hooks keep dependency-light
ownership readers, including the packaged fallback parser. Repository
development and the full package validator install PyYAML. Missing PyYAML does
not turn a role capability into permission to write an unknown owner.

**Can I run more than one business?** Yes — one workspace per business plus a
registry. See [`multi-business.md`](multi-business.md).

**How do I know which command to use?** Ask the **chief-of-staff** — routing is
its one decision. Or browse [`commands.md`](commands.md).

**Where do I see everything working before I install?** The
[`examples/studio-north/`](../examples/studio-north/) workspace, and the guided
tour in [`workspace-state.md`](workspace-state.md).

**How do I contribute / extend it?** See [`development.md`](development.md) and
[`CONTRIBUTING.md`](../CONTRIBUTING.md).
