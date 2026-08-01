# Changelog

All notable changes to Founder OS. Versions follow the plugin's
`founder-os/.claude-plugin/plugin.json`.

## Unreleased

## 2.6.0 — 2026-08-01

**Decision-first activation.** The public path now starts with one Studio North
decision moving from current state through one owner into a local daily review,
then presents fit, trust, requirements, and installation before the complete
catalogue. `/founder-os-init` asks an optional activation intent, shows purpose
and time across all four state groups, reports each verified owner checkpoint,
and emits a six-line value-first activation receipt only after the first brief
is re-read.

**Workflow receipts and quick capture.** Every role now returns the same
structured workflow result. The main thread renders the workflow receipt as
Decision, Evidence, Changed, Gaps, Returns, and Your move; `Changed` comes only
from verified persistence. Freshness uses threshold-backed `current`, `stale`,
or `unknown`, and all seven gateway errors add a five-fact recovery wrapper.
`/situation-review` previews one route and waits for **Continue** or **Stop**.
The new `/capture` safely appends one unchanged line to `inbox.md`, bringing the
package to **53 workflows**.

**Verification.** The package now runs **17 build-time checks**, including the
mutation-tested capture contract. The release gate covers package validation,
generated commands, Python and Node behavior tests, local links, and the clean
installed-copy lifecycle.

**The 2.5.0 role contract now executes on Claude Code.** It could not before.
The package pinned internal shapes the host never sends, so the whole gateway
contract was correct on paper and inert in practice.

- **Roles spawned with zero tools.** Claude Code registers a plugin's MCP tools
  under a namespaced name — `mcp__plugin_founder-os_founder-os-state__<action>`
  — and the agent allowlists named the packaged form. Every one of the six
  entries resolved to nothing, and the host refused the spawn outright rather
  than starting a role that could do nothing. The allowlists, the validator and
  the contract tests now name the registered form.
- **The guard locked every other subagent out of every tool.** It treated any
  subagent it could not identify as a role under the role lockdown, so a code
  reviewer, an `Explore` pass, or an unrelated plugin's agent was denied Bash,
  Read and foreign MCP — machine-wide, in any repository the hook ran in. A
  subagent that is not one of the thirteen roles is now bound by two checks and
  nothing more: no write under `_local/`, no write to a file the ownership map
  gives someone else. Both read the path out of the tool call, so they bind
  `Write`, `Edit`, `NotebookEdit` and `apply_patch` and they do not inspect a
  shell command — a non-role subagent holding `Bash` can still write anything
  its own permissions allow, and this hook is not what stops it. That is the
  trade for not locking reviewers out of unrelated repositories, and the module
  docstring now says so instead of implying the two checks are absolute.
- **The guard reads the identities and tool names the host actually sends.**
  Claude Code names plugin subagents `<plugin>:<agent>`, so `founder-os:cfo` is
  the CFO and is locked down as one. The gateway is recognized under both the
  packaged and the host-wrapped server name; a foreign server that merely looks
  like ours is treated as ours and capability-checked, which fails closed.

**Four fail-open trades, found by auditing the accommodation itself.** Teaching
the guard to accept two tool-name shapes and two identity shapes is a matching
problem, and every loose match trades a false deny for a false allow. A
fresh-agent audit of the change found four, each now pinned by a test that fails
against the unfixed guard.

- **Any MCP server whose name merely ended in `_founder_os_state` was adopted as
  the founder's own gateway.** `mcp__evil-founder-os-state__write_owned_state`
  was allowed, and the founder's live capability token travelled to it in the
  tool payload; `resolve_workspace` reached it with no check at all. The
  suffix test was written believing it failed closed — it inverts the decision
  it guards, because an unrecognized server's baseline is *denied*, so adopting
  one turns a deny into an allow. Now an exact allowlist of the two names the
  guard actually needs.
- **A second plugin's agent named `cfo` inherited the founder's CFO authority.**
  Role identity was read as "the segment after the last colon", so
  `acme-analytics:cfo` was the CFO — at the gateway, holding a live capability,
  writing owned state. Only this plugin's namespace counts now; another
  plugin's agent is a stranger and is handled as one.
- **A role could walk its own lockdown out through a child.** `Task` and `Agent`
  were absent from the hook's matcher entirely, so a role — which holds no
  shell — could spawn a general-purpose subagent that does. One-level
  orchestration was already the packaged contract; the guard enforces it now
  rather than assuming the frontmatter will.
- **`founder-os:CFO` was not a role to the lockdown and the CFO to the ownership
  map at the same time**, because role matching was case-sensitive while
  `owner_of` and the filesystem are not. Role matching is casefolded, so a near
  miss resolves toward the restricted reading.
- Also fixed, and older than this batch: an `apply_patch` header whose verb was
  lowercased yielded no paths, and no paths means no opinion — so
  `*** update File: _local/ownership.yaml` was allowed where
  `*** Update File: …` was denied.

**Guidance corrections.**

- The always-loaded `CLAUDE.md` file map omitted `evaluations/`, a directory the
  ownership map has always shipped — and so did `docs/workspace-state.md`, the
  page that calls itself the full map of workspace state. Both now match
  `workspace_files:` by contract test: the prose sentence is expanded and
  compared as a set, and the public table's first column must equal the map
  exactly.
- Rule 0's enumeration gained "no subscription cancelled" wherever the rule is
  recited — the canonical text, the public mirror, and `docs/concepts.md`, which
  introduces it as "the load-bearing rule" and carried a version one item short.
  A cancellation is money moving and was already covered by the rule's intent;
  leaving it unnamed in the copy an agent reads every session was the risk. The
  test now *discovers* every file reciting the enumeration rather than checking a
  hand-kept list, and fails if that discovery ever returns nothing.
- The planning-artifact test asserted that `docs/superpowers/` was absent from
  the working tree, which failed on any machine with an open plan and never
  checked the property that actually matters. It now pins that nothing under
  that path is tracked, which is what "not shipped" means for a directory
  published from tracked files.

**Verification.** The guard's runtime shapes are pinned by unit tests and by the
installed-copy smoke, including the self-elevation deny — a subagent opening its
own role session picks its own capability, which makes every other gateway check
advisory — under the host-registered tool name and the namespaced identity, not
only under the packaged ones.

## 2.5.0 — 2026-07-27

**Full host parity.** Claude Code and Codex now execute the same packaged role
and workflow instructions through one local `founder-os-state` process. Its
seven gateway tools resolve a workspace, open a short-lived role capability,
list/read bounded Markdown state and approved references, atomically write only
role-owned state, and close the session. State writes fail closed on unknown
identity, ownership, path, structure, capability, or current-file hash.

Managers no longer attempt nested agents. The main thread invokes sibling roles
from structured delegation requests and validates persisted checkpoints before
advancing. A named native role and the portable generic-agent fallback receive
the same role bytes, workflow, bounded handoff, workspace, and capability.

**Trust and reliability.** The public Trust Center now ships at the manifest
URL. SessionStart failures are visible to the model and stderr; invalid YAML
container shapes become controlled validator findings; workspace-demo focus
moves out of a hidden panel; and clipboard success is announced only after a
confirmed native or fallback copy.

**Verification.** The release gate covers the copied MCP lifecycle, real
SubagentStart identity mapping, role-owned writes and denials, both plugin
validators, Claude/Codex installed-host discovery and role I/O, all local links,
Python tests, Node behavior tests, generated commands, and package validation.

**Codex parity foundation.** Added situation review and strategic evaluation
workflows, Codex skill interfaces for every workflow, dual-host local overlays,
and the Trust Center source contract.

**Extensibility.** A founder can add a file, a workflow, or a role their
business needs without forking — and none of it can weaken the ownership
contract, the tool allowlist, or house rule 0.

- **The local overlay** (`founder-os/references/extensibility.md`):
  `$FOUNDER_OS_HOME/_local/` carries an additive-only `ownership.yaml`, plus
  optional local skills and agents. It may add a path; it may never reassign or
  remove one the package ships. A collision is a finding, not a precedence
  contest — the packaged owner stays and the doctor reports the overlay entry.
- **`/skill-forge`** (50th workflow, standalone like `setup-cadences` because
  running it as a subagent is denied by construction). Its commonest correct
  outcome is a refusal: a packaged agent already owns that decision, named, with
  the command. It extracts beliefs rather than supplying them, registers every
  new path in the same run, and installs the runnable copy only after naming the
  exact file and being told yes.
- **The guard merges the overlay per workspace** and denies **every subagent**
  any write under `_local/`. An agent that can edit the map that governs it does
  not have a map. An unreadable overlay is ignored and logged, never obeyed and
  never a deny — the fail-open posture is unchanged.
- **`founder-os-doctor` gains six overlay checks** — unreadable, claims a
  packaged path, incoherent, local agent overreaches, local skill off template,
  installed copy drift. None is repairable: the doctor does not edit the map
  deciding who may write company state. This is late-binding validation and the
  skill says so, because CI will never see a stranger's `_local/`.

**Feedback channel.**

- `founder-os-doctor` gains a **shareable report**: a paste-able install
  summary built from a fixed field list rather than by redacting the health
  report, so it carries version, host, activation state, missing declared files
  and headings, and the checks that tripped with their numbers — and no file
  content, entity slug, amount, path or date. Offered once after a run that
  tripped a structural check; printed in the conversation, never written, filed
  or sent. House rule 0 covers the package's own bug tracker too.
- `docs/troubleshooting.md` documents it as the way to report a bug without
  publishing the business.

## 2.4.0 — 2026-07-22

**Activation.**

- `founder-os-init` is now a continuous, resumable path from first answer to a
  valid daily brief, with explicit stops instead of a false completion state.
- The landing page and onboarding now lead with the first useful outcome: one
  source-linked decision for today, grounded in goals, cash, pipeline and live
  commitments.

**Trust.**

- A valid brief uses the same invariant at creation and validation: one owned
  action, linked to current source state, with ambiguity made visible.
- Ownership and provenance stay explicit; Founder OS keeps state local and
  never sends messages or spends money for the founder.

**Verification.**

- Installed-copy smoke tests now exercise the packaged lifecycle and exported
  controller paths, while release metadata is pinned by contract tests.
- The marketplace passes the official Claude validator without warnings. The
  package's single addressed warning is the canonical `CLAUDE.md`: Claude does
  not auto-load it as plugin context, so the `SessionStart` hook injects it and
  `tests/test_session_context.py` pins that behavior.

**Host status.**

- Claude Code is the verified release path. Codex remains beta/manual until a
  separate clean-install validation; this release makes no cross-host claim.

## 2.3.0 — 2026-07-19

**Multi-business.** One founder, several companies of one — without changing
the model for anyone running a single business (no registry, no change).

- Registry at `~/.founder-os/businesses.yaml`: one workspace per business,
  same ownership map in each. Full procedure in
  `founder-os/references/multi-business.md`.
- **Portfolio Manager** (13th agent) — owns the one decision no per-business
  file can hold: how the founder's hours and cash split across businesses.
  Writes `portfolio.md` in a dedicated portfolio workspace.
- **`/portfolio-review`** (49th skill, 10th cadence) — Monday 08:15, written
  into cron only when the registry lists two or more active businesses.
- `setup-cadences` fences are slugged per business
  (`# BEGIN founder-os:<slug>`), with migration from the legacy fence — two
  businesses hold two schedules in one crontab without clobbering each other.
  Logs split per business (`~/.founder-os/logs/<slug>/`).
- `context-load` step 0 resolves which business a session means (invocation
  slug → `FOUNDER_OS_HOME` → registry default → ask) and stamps it into the
  context line.
- `founder-os-init` registers a second business instead of refusing, and
  scaffolds the portfolio workspace when the second active business lands.
- The ownership hook resolves every registered workspace root, so
  cross-business writes are checked, not invisible.
- `founder-os-doctor` check #14, *Portfolio dark*: two active businesses with
  a missing, drifted or 21-days-silent `portfolio.md`.

**Documentation.**

- `founder-os/COMMANDS.md` — the full command catalogue (command, owner,
  schedule), generated from the package by `scripts/generate_commands.py` and
  checked in CI so it cannot drift.
- README: *A day with Founder OS* (the daily workflow, concretely) and *More
  than one business*.

**Decision quality.**

- Written kickoff debate: before a large kill (`kill-or-continue`) or a
  bet-the-company sizing (`bet-sizing`), the Chief of Staff convenes the
  agents whose files the decision touches; each commits a position in writing
  before the Board Member red-teams it, and the debate follows the decision
  into `decisions/`.
- `monthly-review` revisits decisions 90+ days old against their own
  *What would change our mind*: held, fired-and-ignored, or overtaken.
- `## Refusals` for the Chief of Staff.

**Repo.** Stale staging copies removed; design-phase documents retired from
the repo (they live in git history before this release).

## 2.2.0 — 2026-07-18

- Cadences became real: `setup-cadences` writes host cron/launchd entries
  calling skills headless (`--permission-mode acceptEdits`, namespaced
  commands, per-cadence logs), with `calendar-audit` as the ninth cadence.
- Write-time guard hardened: casefold path matching, `NotebookEdit` coverage,
  fallback `owns:` parser for machines without PyYAML; hook subprocess tests.
- Validator: `check_hooks` (matchers and guard compile at build time),
  `check_readme_counts` (a count that drifts fails the build), contained
  per-file parse failures.
- Review findings B1–B6 fixed; `## Named failure modes` sanctioned in the
  skill template.

## 2.1.0 — 2026-07-15

- Drafts persist: `drafts/{outreach,proposals,content}/` with
  `## Draft / ## Provenance / ## Sent` — the founder's own edits survive the
  session, and `voice-capture` harvests the diff.
- `inbox.md` — the founder's door: no fields, no clock, drained to zero by
  `triage` and `daily-brief`.
- Entity linking (house rule 6): `[[slug]]` across files,
  `references/linking.md`.
- `queue.md` caps and clocks; `founder-os-doctor` grew the checks that watch
  a live workspace rot.

## 2.0.0 and earlier

Retargeted from a hosted-runtime package format to a native Claude Code
plugin: agents as `agents/*.md` with explicit `tools:` allowlists, skills as
`skills/*/SKILL.md`, the ownership map + write-time hook + build validator
triad, seven house rules with rule 0 (*never outbound, never money*) enforced
at the tool layer.
