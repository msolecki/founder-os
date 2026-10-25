---
title: "Backlog"
status: current
owner: Mateusz Solecki
last-verified: 2026-10-25
---

# Backlog

Follow-ups from the 2026-10-16 audit (branch fix/audit-2026-10-16-int). Each was
deliberately left out of that batch; the reason is given. Items about Codex were
dropped when Codex support was removed ([decisions D11](decisions.md)).

## Needs a host or a tool not available in the batch

- Verify on a live Claude Code host that a role subagent whose `tools:` lists only the gateway tools can call ToolSearch (the guard now allows it; `scripts/probe_installed_hosts.py`).
- Regenerate `founder-os/images/org-chart.png` from the updated `.mmd` (needs mermaid-cli), or embed the `.mmd` as a mermaid block in `founder-os/README.md`.
- Add a Linux CI job running `systemd-analyze --user verify` on `render_systemd` output.

## Decisions

- `scripts/validate_package.delegation_request_errors`: expose it where the main thread validates delegation, or move it into `tests/test_orchestration_contract.py` as a contract model (audit deadcode-7).
- strategic-evaluation read-only perspective siblings need a read-only delegation mode in `references/orchestration.md` (audit content-9).
- Directory members are an ordered subset with no completeness floor; give any member with a mandatory heading (e.g. `## Sent` in drafts/) its own key, like `clients/_capacity.md`.
- pipeline-review's unattended `Founder input: blocked …` line has no `Proposed:` line, so the daily brief never queues it.

## Cleanups (P3)

- Test-only helpers: `SafeStateIO.list_markdown`, `OwnershipSchema.derived_paths`, `RoleSessionStore.resolve(workspace_id=, role=)`, `cadence_manager.decode_artifact`, gateway `TOOL_SCHEMAS` alias (removing them means removing their tests).
- `ownership-guard.py` `__main__`: an unexpected exception exits 0 even on a role path.
- A Claude payload with only `session_id` binds every generic agent in that session.
- A paused default business silently re-homes to the one active business; log it.
- Dashboard: week-age fact changes the week panel hash daily; a future week should read "starts in N days"; `none —` with nothing after the dash is not read as zero.
- Dashboard Integrity findings and Track record tab are not built (audit dashboard-6).
- perf-1/2/3/6 measured as not user-visible.
