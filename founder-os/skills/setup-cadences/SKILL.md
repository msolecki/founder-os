---
# promptscript-generated: 2026-08-14T09:55:27.938Z | source: .promptscript/project.prs | target: claude
name: setup-cadences
description: Turn the cadences into real scheduled jobs on the founder's own machine — run once, after their first brief, so the package stops waiting to be opened
references:
  - agents/openai.yaml
---

# Setup Cadences

Use the packaged `scripts/cadence_manager.py` to preview, back up, install,
remove, and smoke-test cadences. Never construct scheduler edits with `sed`, a
shell pipeline, or string interpolation. Host state is outside the business
workspace and changes only after one explicit founder confirmation.

Run this after the founder has completed their first `daily-brief`. On a
multi-business install, run the business schedule once per active business and
the portfolio schedule once when at least two businesses are active.

## Inputs

- The chosen host: `claude` or `codex`. Resolve each candidate with
  `command -v`; if both exist, ask which one should run unattended. If neither
  exists, stop.
- The scheduler: `launchd` for a sleeping macOS laptop, persistent user
  `systemd` timers for a sleeping Linux machine, or user `cron` for an
  always-on machine. Never use `sudo`, `/etc/crontab`, or `/etc/cron.d`.
- Absolute paths for the host binary, workspace, workspace parent, and
  `~/.founder-os/logs`. Relative paths are invalid.
- The exact registry slug, or no slug when the registry is absent. A portfolio
  job uses the literal slug `portfolio` and the portfolio workspace.
- `charter.md` `## Timezone`, only to report drift from the host timezone. The
  schedule stays in the host timezone.

WSL reports Linux but normally has no durable always-running user scheduler.
If `/proc/version` contains `microsoft`, stop and explain the limitation.

## Schedule

| workflow | when | cron |
|---|---|---|
| `/daily-brief` | weekdays 08:00 | `0 8 * * 1-5` |
| `/portfolio-review` | Monday 08:15, portfolio only | `15 8 * * 1` |
| `/week-plan` | Monday 08:30 | `30 8 * * 1` |
| `/weekly-review` | Friday 16:00 | `0 16 * * 5` |
| `/pipeline-review` | Thursday 10:00 | `0 10 * * 4` |
| `/follow-up-sweep` | Friday 14:00 | `0 14 * * 5` |
| `/content-plan` | Wednesday 10:00 | `0 10 * * 3` |
| `/calendar-audit` | Friday 15:00 | `0 15 * * 5` |
| `/revenue-review` | first of month 09:00 | `0 9 1 * *` |
| `/quarterly-planning` | Jan/Apr/Jul/Oct first 11:00 | `0 11 1 1,4,7,10 *` |

Do not schedule `monthly-review` or `annual-review`. Do not schedule
`portfolio-review` when fewer than two registry businesses are active.

## Beliefs

- A preview is a promise: apply installs those exact bytes or stops when host
  state has changed. Apply recomputes the expected artifacts from the sealed
  config and snapshot instead of trusting a forgeable checksum alone.
- A schedule that misses sleeping hours is not automation. Catch-up behavior
  determines the scheduler; operating-system familiarity does not.
- Unattended permission is a narrow capability, not trust in the whole host.
  Claude receives only the Founder OS MCP tool pattern; Codex runs with no
  approvals in a workspace-write sandbox.
- Exact identity beats prefix matching. `a`, `acme`, `portfolio`, and the
  legacy unslugged fence are four different schedules.

## Steps

1. **Resolve and validate the host.** Record the absolute binary path. For
   Claude, the generated argv is:

       claude -p /founder-os:<workflow> --permission-mode dontAsk --allowedTools 'mcp__plugin_founder-os_founder-os-state__*' --max-turns 50 --no-session-persistence

   For Codex, it is:

       codex -a never exec --sandbox workspace-write --ephemeral -C <workdir> '$founder-os:<workflow>'

   If the binary is under `/.nvm/`, disclose that a Node upgrade can move it.

   Run `<binary> --help` before the preview, but do not treat it as the
   complete flag list. Hosts hide accepted flags from help output: Claude Code
   2.1.x accepts `--max-turns` and does not print it, so a missing flag is a
   reason to test that one flag, never a reason to stop. Confirm the flags help
   does list, and prove the rest with the step 7 smoke test — an argv the host
   rejects fails there, loudly, before any schedule is trusted.

2. **Resolve the scheduler and absolute paths.** `FOUNDER_OS_HOME` is the
   workspace; the working directory is its parent. Cron and system services do
   not load the interactive shell profile. Create no scheduler artifact inside
   `FOUNDER_OS_HOME`.

3. **Preview exact artifacts.** Run:

       python3 <plugin>/scripts/cadence_manager.py preview \
         --host <claude|codex> --binary <absolute-binary> \
         --workspace <absolute-workspace> --workdir <absolute-parent> \
         --log-root <absolute-home>/.founder-os/logs \
         --scheduler <cron|launchd|systemd> [--slug <exact-slug>] \
         --output <absolute-preview.json>

   Add `--migrate-legacy` only when a registry now exists and this business is
   replacing the old unslugged fence. Show the emitted manifest and artifacts.
   The output path must be new, absolute, and outside `FOUNDER_OS_HOME`.
   Cron paths are POSIX-quoted, including spaces, quotes, dollars,
   metacharacters, and cron percent signs. Launchd uses argument arrays.
   Systemd services use direct `ExecStart`, never `/bin/sh -c`, and timers set
   `Persistent=true`. Every scheduler receives a minimal `PATH` that begins
   with the selected binary's directory, so an `/usr/bin/env` shebang can find
   a colocated runtime without loading an interactive shell profile. Both
   hosts disable scheduled-session persistence; durable business state remains
   in the workspace instead of accumulating host transcripts.

4. **Snapshot current scheduler state.** Before confirmation, run the matching
   `snapshot` command with `--backup-root ~/.founder-os` and an output JSON
   path. Both the backup and output paths are create-only: an existing path
   stops the flow instead of being overwritten. Name the returned
   `backup_path`. A missing crontab is a valid empty snapshot; any other
   scheduler read error stops the flow.

5. **Ask once.** Show the host, scheduler, identity, exact artifact diff,
   preview checksum, and backup path. Ask one question covering the whole
   schedule. If the founder declines, write nothing.

6. **Apply the confirmed preview.** Run:

       python3 <plugin>/scripts/cadence_manager.py apply \
         --manifest <absolute-preview.json> \
         --snapshot <absolute-snapshot.json>

   Apply re-reads scheduler state. If it differs from the preview/snapshot
   digest, or if the artifacts do not exactly match a fresh derivation from
   the confirmed config and backup, it stops before installation. It never
   silently overwrites a change made while the founder was reviewing the
   preview.

7. **Smoke-test the exact host argv.** Run the manager's `smoke` command for
   `daily-brief` (or `portfolio-review` for the portfolio identity). It uses a
   cron-like minimal environment and the previewed working directory. A failed
   auth or flag check is a failed setup, not a warning to discover tomorrow.

8. **Report the installed identity and next run.** Name the scheduler, backup,
   log directory, and next cadence time. Do not prescribe recurring scheduler
   maintenance; `founder-os-doctor` detects a cadence that has gone quiet.

## Removal

Removal is exact and explicit:

    python3 <plugin>/scripts/cadence_manager.py remove \
      --host <host> --binary <binary> --workspace <workspace> \
      --workdir <parent> --log-root <log-root> --scheduler <scheduler> \
      [--slug <slug>] --identity <exact-slug|founder-os|all>

One identity never prefix-matches a sibling. The literal `all` is required to
remove every Founder OS schedule. Uninstalling the plugin does not implicitly
remove scheduler state.

## What you produce

- One checksummed preview manifest containing exact artifacts.
- One snapshot manifest and an exact backup under `~/.founder-os/`.
- The selected user scheduler artifacts and per-cadence log directories, only
  after confirmation. Jobs use umask `077`; per-identity log directories are
  mode `0700`.
- One smoke result and the next scheduled run.

## Guardrails

This skill modifies only the current user's scheduler and its own files under
`~/.founder-os/`. It never uses `sudo`, never touches another user's schedule,
never executes through `shell=True`, and never sends or spends anything. A host
change requires preview, disclosed backup, and explicit confirmation every
time.
