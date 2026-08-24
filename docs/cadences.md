# Cadences and scheduling

Founder OS can run ten recurring workflows per business and one conditional
portfolio review. Every workflow still works manually; scheduling is optional
and local to your machine. There is no Founder OS cloud scheduler.

## The schedule

| Workflow | When | Owner |
|---|---|---|
| `daily-brief` | weekdays 08:00 | chief-of-staff |
| `portfolio-review` | Monday 08:15, two or more active businesses only | portfolio-manager |
| `week-plan` | Monday 08:30 | focus-coach |
| `weekly-review` | Friday 16:00 | chief-of-staff |
| `pipeline-review` | Thursday 10:00 | pipeline-coach |
| `follow-up-sweep` | Friday 14:00 | network-manager |
| `content-plan` | Wednesday 10:00 | brand-editor |
| `calendar-audit` | Friday 15:00 | focus-coach |
| `signal-check` | Friday 15:30 | cfo |
| `revenue-review` | first of month 09:00 | cfo |
| `quarterly-planning` | Jan/Apr/Jul/Oct first 11:00 | strategist |

## Invoke setup on your host

Claude Code:

```text
/founder-os:setup-cadences
```

Codex:

```text
$founder-os:setup-cadences
```

The workflow uses the packaged `founder-os/scripts/cadence_manager.py`; it does
not edit schedules with `sed` or an interpolated shell command.

## Pick the scheduler by sleep behavior

- A sleeping macOS laptop uses per-cadence LaunchAgents. Calendar intervals
  run after wake when their scheduled time was missed.
- A sleeping Linux machine uses persistent user systemd timers when available.
  `Persistent=true` supplies catch-up behavior.
- An always-on desktop or server may use the current user's crontab. Cron does
  not catch up after sleep: a missed 08:00 run is simply missed.
- WSL normally has no durable always-running scheduler. Setup stops instead of
  installing a schedule that disappears with the distro.

No path uses `sudo`, `/etc/crontab`, `/etc/cron.d`, or another user's service
directory.

## Unattended host commands

Claude jobs use a namespaced workflow and grant only the packaged MCP surface:

```text
claude -p /founder-os:<workflow> --permission-mode dontAsk \
  --allowedTools 'mcp__plugin_founder-os_founder-os-state__*' --max-turns 50 \
  --no-session-persistence
```

Codex jobs use the documented non-interactive command and dollar skill syntax:

```text
codex -a never exec --sandbox workspace-write --ephemeral \
  -C <workspace-parent> '$founder-os:<workflow>'
```

The manager passes argument arrays, never `/bin/sh -c`. Cron fields use POSIX
quoting and escape cron's special percent sign. Launchd uses
`ProgramArguments`; systemd uses direct `ExecStart` tokens. Each scheduler gets
a minimal `PATH` beginning with the selected host binary's directory, which
keeps `/usr/bin/env`-based installations working without loading a shell
profile.

Both hosts run scheduled sessions without persisting their conversation
rollouts. Durable decisions and receipts stay in the Founder OS workspace;
recurring host transcripts do not accumulate separately.

Official host contracts:

- [Codex non-interactive mode](https://developers.openai.com/codex/noninteractive)
- [Codex CLI reference](https://developers.openai.com/codex/cli/reference)
- [Claude Code headless mode](https://code.claude.com/docs/en/headless)
- [Claude MCP permissions](https://code.claude.com/docs/en/agent-sdk/mcp)

## Preview, backup, confirm, apply

Setup resolves absolute binary, workspace, working-directory, and log paths.
It then:

1. renders the exact cron block, LaunchAgent plists, or systemd user units into
   a checksummed, create-only preview manifest outside the workspace;
2. snapshots the exact current scheduler state under `~/.founder-os/` and
   reports the create-only backup path;
3. shows the artifacts and asks once for confirmation; and
4. re-reads scheduler state and applies only if its digest is unchanged.

If another process edits the crontab or selected unit files while you inspect
the preview, apply stops. Before writing, it also recomputes the only valid
artifacts from the manifest config and snapshot; a resealed but changed cron,
plist, or unit is rejected. Existing manifest and backup paths are never
overwritten.

Cron fences use exact identities: legacy `founder-os`, a business such as
`founder-os:a`, sibling `founder-os:acme`, and `founder-os:portfolio` never
prefix-match one another. Registry migration removes the legacy fence only
when preview explicitly requests `--migrate-legacy`.

## Logs and smoke test

Every cadence receives its own append-only log under
`~/.founder-os/logs/`; multi-business logs add the business slug. Apply creates
per-identity directories with mode `0700`, and cron, LaunchAgents, and systemd
services all run with umask `077`. Setup then runs one exact host argv in a
cron-like minimal environment. Authentication, missing flags, and
workspace-access failures therefore surface immediately.

`founder-os-doctor` detects a schedule that has gone quiet, but does not mutate
the host scheduler.

## Removal

Use the manager through `setup-cadences` or its `remove` subcommand. Removal
requires one exact identity. The literal `all` is the only request that removes
every Founder OS schedule. Uninstalling the plugin leaves the Markdown
workspace and scheduler state untouched until you explicitly remove them.

See [`multi-business.md`](multi-business.md) for registry and portfolio rules.
