# Founder OS v2.2 — Design Spec

**Date:** 2026-07-16
**Status:** Approved by founder (direction questions answered 2026-07-16), ready for implementation
**Input:** Full-repo audit of 2026-07-16 — three parallel reviews (12 agent files; 48 skills; hooks/validator/cadence mechanics) plus repo-state checks.

---

## 1. What v2.2 is

**v2.2 makes the shipped thing true.** The audit's headline finding is not a
missing feature — it is that the product's central promise has never run:

- No workspace exists on the author's machine, no cron entries, the plugin is
  not installed locally, and `feat/founder-os-v21` (17 commits) is unmerged.
  The package has never been through `/founder-os-init` for real. Our own spec
  (§10.5) says the differentiator is an end-to-end run; we don't have one.
- The cadence lines `/setup-cadences` writes **do not work headless.**
  `claude -p "/daily-brief"` cannot approve its own `Write` — every one of the
  eight cadences runs, is denied its output file, and logs the denial to a file
  nobody reads. The README's "It comes to you" is currently false on every
  machine that runs it.
- The repo has no remote, the README says `/plugin marketplace add
  <owner>/founder-os` with a literal `<owner>`, and there is no marketplace
  manifest. There is nothing to install from.

v2.2 therefore has one goal: **a stranger can install it, and the author does —
and both get a real brief two mornings in a row.** Everything in scope serves
that; everything else moves to v2.3.

## 2. Decisions recorded (founder, 2026-07-16)

1. **Product first.** Merge v2.1, fix mechanics, publish (remote + marketplace).
   Personal tailoring comes after.
2. **Life-minimum, not full life OS** — and in **v2.3**, not v2.2: time off
   visible to capacity and week-plan, a dated-obligations file (tax/ZUS/renewal
   deadlines) drained into the queue, private runway at the CFO.
3. **Read-only overlay for the author's own use** (Calendar/ClickUp/Gmail →
   workspace through `ingestion-gate`) — lives in a **private overlay, never in
   the core package**. House Rule 0 is untouched: nothing sends, ever.
4. **Plan before code.** This spec + the v2.2 plan are the deliverable of the
   2026-07-16 session; implementation is a follow-up session.

## 3. Scope — the six fix families

### 3.1 Land v2.1
Merge `feat/founder-os-v21` → `main` (validator and tests are green).

### 3.2 Cadences that actually run (P0)
`setup-cadences`' cron/launchd templates gain what headless needs:
`FOUNDER_OS_HOME` embedded per line (cron reads no shell profile), `cd` to the
workspace **parent** (kills the `./founder-os/` phantom-nesting), the
**namespaced** command form `/founder-os:<slug>` (collision-proof), 
`--permission-mode acceptEdits` and `--max-turns 50` (a headless session that
cannot approve a Write produces logs, not briefs), a credentials/keychain note,
and a documented removal path (today the fence outlives the plugin).
Additionally `calendar-audit` gets scheduled (Friday 15:00) — it is the one
weekly skill with no cron row, and it silently starves `week-plan`'s ledger and
`energy-audit`'s 4-week minimum. Eight cadences become **nine**; every count in
prose moves with it (the repo has hit stale-count drift four times).

### 3.3 Guard + validator hardening (P0/P1)
- `ownership-guard.py`: case-fold path comparison (APFS is case-insensitive —
  `Goals.md` currently dodges the map), and `NotebookEdit` handled as a write
  (`notebook_path`), added to the `hooks.json` matcher.
- `validate_package.py`: new `check_hooks` (hooks.json exists/parses, matcher
  covers the write+outbound set, guard compiles), and frontmatter errors
  contained as FAIL lines instead of a traceback that kills the whole run.
- New `tests/test_ownership_guard.py` — the guard currently has zero tests.

### 3.4 Prose rejoins the map (P1)
Agent bodies drifted from `ownership.yaml` — the exact failure the map's own
comment warns about: `pipeline-coach` ("You own `pipeline.md`. Nothing else")
and `brand-editor` ("Those two files, and nothing else") deny the `drafts/`
dirs they own; `chief-of-staff` never mentions `inbox.md`. Also:
`board-member` holds `Write, Edit` while owning nothing (its own skills say "the
Board writes no company state") — tools trimmed to `Read, Glob, Grep`;
`positioning-advisor` is told to consult the Board Member it cannot summon —
fixed in prose (route via founder/CoS), with a house-rules paragraph defining
what a handoff is (spoken, not spawned; `Agent(...)` = the org chart's
manager→report edges only); `focus-coach` cites `metrics.md` for evidence that
lives in `week.md`'s ledger.

### 3.5 Paper cuts (P1) — the one-line bugs
`rate-raise` output hardcodes "60 days' notice" three paragraphs after its own
step forbids naming a number; `content-plan` description says monthly, body says
weekly; `revenue-review` and `monthly-review` cite a `monthly-close` task that
does not exist; `icp-definition` cites a `define-icp` that does not exist;
`audience-research` has guardrails but no `## Guardrails` heading;
`founder-os-init`'s install decision file ignores the four `decisions/`
headings the map declares; `skill-template.md` omits `STANDALONE_SKILLS`
(`setup-cadences` looks like an unregistered orphan when it is standalone by
design — no agent may hold the tools it needs).

### 3.6 Dead triggers come alive (P1)
Four loops end in a handoff nobody catches:
- **monthly-review** — `revenue-review`'s close now emits a second `Proposed:`
  line ("write the monthly review"), and `daily-brief`/`context-load` name
  `metrics.md ## Close` in the drain set (today the brief drains `Proposed:`
  from three files while two more emit it).
- **win-loss-analysis** — `pipeline-review`'s `## Last review` reports
  `Win/loss pending: <n>`, and pending >5 days joins the brief's rotting scan.
- **client-health** — the brief date-checks `Verdict:` lines; older than 45
  days reads as "no current verdict — client-health overdue", not as fresh.

### 3.7 Ship it (P0 for "product first")
`plugin.json` → 2.2.0; a public GitHub repo mirroring `founder-os/` + `scripts/`
+ `tests/` with a root `.claude-plugin/marketplace.json` (source
`./founder-os`); README `<owner>` replaced with the real login (`gh api user`);
local marketplace-install verification; then the **dogfood gate**: real
`/founder-os-init` on the author's machine, `/setup-cadences`, and the
acceptance test — a real brief lands two consecutive mornings with zero
permission denials in the cadence logs.

## 4. Out of scope — v2.3 parking lot (design notes recorded now)

1. **Dedup extraction first.** The `Proposed:` protocol is restated in ~10
   files (~250 lines) and the voice-check in 4. Extract
   `references/proposing.md` + `references/voice-check.md` **before** v2.3 adds
   new proposers, or the copies multiply again.
2. **Post-delivery loop** (the one solo-founder chain with zero coverage):
   testimonial capture folds into `delivery-retro` (same 5-day window);
   referral ask folds into `follow-up-sweep` (the "Could refer, never has"
   category exists with no action); **dunning-draft** is the open design
   question — a new draft skill needs an owner (`cfo` decides "chase", but
   drafts live in a `drafts/` dir the CFO would have to own) and a
   `drafts/dunning/` map entry. Decide owner in the v2.3 spec.
3. **Life-minimum** (decision 2): time off recorded where `capacity-check` and
   `week-plan` must read it; a dated-obligations file (owner: chief-of-staff,
   drained by `daily-brief`); private runway section at the CFO. Also the
   ownerless decisions the audit flagged: subcontracting (natural owner:
   delivery-lead), firing a client (delivery-lead decides, CFO informs, board
   reviews).
4. **Private overlay repo** for the author: read-only MCP ingestion (Calendar →
   `week.md`, ClickUp → `pipeline.md`/`clients/`, Gmail → `follow-up-sweep`
   evidence), Polish workspace conventions. Never in core.
5. **follow-up-sweep voice hole**: its drafts never land in `drafts/`, so
   founder edits to sweep messages are never harvested — either a
   `drafts/followups/` (network-manager) or soften `brand-editor`'s claim.

## 5. Open questions (resolve during v2.2, not before)

1. **Does the plugin's `CLAUDE.md` actually load into sessions?** It claims
   "loaded into every session"; plugin-cache memory semantics may say
   otherwise, and headless cadences are where it matters. **Verify at the
   dogfood gate**; contingency (v2.2.1): a `SessionStart` hook injecting the
   house rules as additional context.
2. **GitHub owner/repo name** — resolved at execution via `gh api user -q
   .login`; repo name `founder-os`.

## 6. Acceptance

- `python3 scripts/validate_package.py` → `12 agent(s), 48 skill(s), 0 error(s)`
- `python3 -m pytest tests/ -q` → all pass (including the new guard tests)
- `grep -rn -i "Eight, and not nine" founder-os/` → no hits, and no stale
  *scheduled*-count "eight" in `setup-cadences`/README (the proposer set in
  `queue`/`daily-brief` is a different eight and stays eight)
- A stranger-shaped install works: `claude plugin marketplace add <staging>` →
  `/plugin install founder-os@founder-os` → skills visible namespaced.
- **Dogfood gate:** two consecutive weekday mornings produce a real
  `reviews/daily/` brief on the author's machine via cron/launchd, with zero
  permission denials in `~/.founder-os/logs/`.
