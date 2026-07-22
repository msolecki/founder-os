# Founder OS Dual-Host Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver situation-first routing, strategic evaluation, local-overlay parity and a Trust Center with one behavioral contract on Claude Code and Codex.

**Architecture:** Canonical logic stays in shared `SKILL.md` files and the ownership map. Claude agent files and Codex `agents/openai.yaml` files are discovery adapters. The package moves from the current 50 workflows to 52; 13 roles and 10 cadences stay unchanged.

**Tech Stack:** Markdown/YAML, Python 3 validator and `unittest`, dependency-free Node behavior tests, JSON plugin/hook manifests, Claude Code/Codex plugin CLIs.

## Global constraints

- Same workflow inputs, outputs, writes and guardrails on both hosts.
- No `npm install`, outbound action, money movement, telemetry or cloud service.
- Preserve the current local-overlay implementation and extend it to Codex.
- Do not alter authentication, middleware or fail-open policy.
- Every stage ends with validator + Python + Node green.
- A fresh-context reviewer must inspect the final agent-generated diff.

## Task 1 — Dual-host structural contract (M)

**What:** Validate one Codex adapter per canonical workflow and permit only dated
active specs/plans under `docs/superpowers/`.

**Where:** `scripts/validate_package.py`, `tests/test_validate_package.py`,
`tests/test_release_metadata.py`, `docs/development.md`, this spec and plan.

**How:** Add `check_codex_skill_interfaces`; mutation-test missing/malformed
YAML, required fields and `$skill` prompt identity. Replace the obsolete blanket
ban on `docs/superpowers/` with `plans/` + `specs/` shape validation.

**Test:** Targeted validator tests fail before implementation and pass after;
full package/Python/Node gate passes at 13 agents, 50 skills.

- [x] Write and observe failing adapter tests.
- [x] Implement the validator and add it to `CHECKS`.
- [x] Update the release-material contract and validator documentation.
- [x] Run the complete gate successfully.
- [ ] Commit only Task 1 paths.

## Task 2 — Shared situation and evaluation workflows (L)

**What:** Add both workflows in one deployable change, including state schema,
decision-log handoff, all catalogue entries and 50→52 current counts.

**Where:**

- `founder-os/skills/{situation-review,strategic-evaluation}/`
- `founder-os/skills/decision-log/SKILL.md`
- `founder-os/agents/chief-of-staff.md`
- `founder-os/references/ownership.yaml`
- `founder-os/CLAUDE.md`, `founder-os/COMMANDS.md`
- `docs/{index.html,commands.md,workspace-state.md,README.md,getting-started.md,og-image.svg}`
- `README.md`, `founder-os/README.md`, `CONTRIBUTING.md`, example README
- onboarding/docs/Node behavior tests and Codex manifest count

**How:** Start with static behavioral tests. Add `evaluations/` to the canonical
map, the two shared skills, and two Codex adapters. Add both to the Chief of
Staff. Regenerate commands. Add both landing articles to the Chief of Staff
`focus` group, increasing its group/category count by two and total to 52.

**Test:** Routing has four-question cap/exactly-one output/no write; evaluation
pins nine sections, `O#`/`I#`, perspective mode, non-overwrite and decision-log
separation; landing has 52 unique workflows and 10 cadence badges.

- [ ] Write and observe failing workflow/docs tests.
- [ ] Add ownership/state and both canonical skills.
- [ ] Add Claude and Codex discovery adapters over the same core.
- [ ] Update generated/manual catalogues and every current 50→52 claim.
- [ ] Run complete gate and commit Task 2.

## Task 3 — Local-overlay parity (L)

**What:** Make founder-created local workflows install and drift-check on Claude
Code and Codex from one overlay source directory.

**Where:** `founder-os/skills/skill-forge/SKILL.md`, its Codex metadata,
`founder-os/references/extensibility.md`, doctor/troubleshooting/architecture,
`tests/test_extensibility_overlay.py` and doctor/docs tests.

**How:** Test first for both user-scope destinations and source
`agents/openai.yaml`. Install identical source directories to
`~/.claude/skills/...` and `~/.codex/skills/...` only after one explicit consent.
Doctor treats either missing/diverged copy as installed-copy drift.

**Test:** Tests fail on the Claude-only contract, then pass with two destinations,
one shared source, valid `$local-slug` prompt and no extra global writes.

- [ ] Write and observe failing local-overlay parity tests.
- [ ] Update forge source/output/install consent contract.
- [ ] Update doctor and operator/technical docs.
- [ ] Run complete gate and commit Task 3.

## Task 4 — Trust Center and Codex presentation (L)

**What:** Publish boundaries and dual-host install/update paths; improve manifest
truthfulness and hook visibility without behavior changes.

**Where:** `docs/trust.md`, landing/getting-started/docs hub/enforcement/
architecture/development, both READMEs, Codex manifest, hooks JSON and tests.

**How:** Test required trust statements, manifest prompts/counts/role wording and
hook status messages. Add Claude and Codex install/update instructions. Keep the
same hook matcher/scripts and shared workflows.

**Test:** Trust links resolve; required boundary tokens exist; manifest validates;
all three hook commands have status text and existing hook tests stay green.

- [ ] Write and observe failing trust/manifest/hook tests.
- [ ] Add Trust Center and cross-links.
- [ ] Add both host installation/update/cache/trust instructions.
- [ ] Update Codex interface metadata and hook status messages.
- [ ] Run complete gate, installed-copy smoke and plugin validation; commit.

## Task 5 — Release, isolated Codex install and review (M)

**What:** Release as 2.5.0 from the current feature branch, perform a real
isolated Codex CLI installation, obtain fresh review, and finish cleanly.

**Where:** both plugin manifests, repo marketplace, changelog, release tests,
this plan and final diff.

**How:** Test version metadata first. Keep concurrent/local-overlay history.
Use a temporary Codex home and local repo marketplace so the founder's personal
marketplace/install is untouched. Spawn a `fork_turns: none` read-only reviewer.

**Test commands:**

```bash
python3 scripts/generate_commands.py founder-os --check
python3 scripts/validate_package.py founder-os
python3 -m unittest discover -s tests
node --test tests/*.behavior.test.js
python3 scripts/smoke_installed_copy.py
python3 /Users/msolecki/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py founder-os
git diff --check
```

- [ ] Write failing 2.5.0 release contract.
- [ ] Version both manifests and marketplace; add changelog section.
- [ ] Run all local gates and isolated Codex CLI install.
- [ ] Run fresh-context review; address verified findings test-first.
- [ ] Update this plan, commit release, and verify final status/log/gates.
