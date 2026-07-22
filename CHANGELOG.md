# Changelog

All notable changes to Founder OS. Versions follow the plugin's
`founder-os/.claude-plugin/plugin.json`.

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
