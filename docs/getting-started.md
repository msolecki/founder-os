# Getting started with Founder OS

**Know what matters today.** Founder OS turns your goals, cash, pipeline and
commitments into one daily decision — stored locally and traceable to its
source. It is a free, MIT-licensed Claude Code plugin for a company of one.

It does not run the company for you. It persists the decision, its owner, its
source and the trade you are making in a Markdown workspace you control.

## See the first brief

Start with the fictional but contract-shaped Studio North
[`reviews/daily/2026-07-20.md`](../examples/studio-north/reviews/daily/2026-07-20.md).
It selects one queue item tied to a quarterly bet, names the work that will not
happen, and cites the dates and files behind the decision. Follow `q-0720a` and
`B1` through the complete [`examples/studio-north/`](../examples/studio-north/)
workspace before installing.

## Before you install

| Requirement | Why it is needed |
|---|---|
| A recent [Claude Code](https://code.claude.com/docs) installation | Founder OS is a plugin, not a standalone app. |
| Python 3 | Runs the write-time ownership hook. |
| PyYAML | Enables the full ownership-map check. The hook degrades gracefully when PyYAML is unavailable. |
| Node.js 20+ *(development/tests only)* | Runs the landing-page behavior contract test. |
| `cron` *(optional)* | Runs scheduled cadences. Every workflow also works manually without it. |

Founder OS itself is free and MIT-licensed. Your existing Claude Code plan and
usage remain separate; Founder OS does not add another account or subscription.

## What Founder OS knows

Founder OS knows only what is recorded in its Markdown workspace or supplied in
the current Claude Code session. It does **not** automatically sync your:

- calendar;
- CRM or pipeline tool;
- inbox or social accounts;
- bank account, accounting system, or payment provider.

This is deliberate. No packaged agent has a browser, shell, or MCP tool. Agents
can draft a message, proposal, or plan, but cannot send, post, pay, sign, or
transfer anything.

Workspace files stay on your machine. The prompts and context you send through
Claude Code or Codex are still governed by that environment's data-handling
terms.

## Install

Run these commands in Claude Code, in order:

```text
/plugin marketplace add msolecki/founder-os
/plugin install founder-os@founder-os
/founder-os-init
```

`/founder-os-init` is one continuous, resumable flow from an empty folder to a
persisted first brief. It checks the install and target before writing, then
asks four short groups about the business, customer, quarter and money. It
delegates each answer to the role that owns the destination file, validates the
minimum state, and writes a dated brief at `reviews/daily/YYYY-MM-DD.md`.

A valid brief has all four required headings declared in `ownership.yaml`:
`## The one thing`, `## Rotting`, `## The trade`, and `## Triage`. `## The one
thing` and `## The trade` must be non-empty. An empty, malformed, or wrong-path
file does not activate the workspace.

The median target is ten minutes and the hard stop is fifteen minutes. Unknown
cash, revenue or burn stays unknown and becomes an owned follow-up; it is never
filled from inference. `Activation complete` appears only after that valid
brief passes the same check in the same resolved workspace. If the flow stops, run
`/founder-os-init` again: populated sections are preserved and the first missing
stage resumes.

## Optional: schedule the cadences

After the first brief, run:

```text
/setup-cadences
```

With your consent, this writes ten `cron` entries on your machine. Scheduled
cadences run only while that machine and its cron service are running; there is
no cloud scheduler and no catch-up run after a machine was off. Every cadence
can still be invoked manually.

Multi-business installs keep one workspace and one schedule fence per business.
The Portfolio Manager is the only role that reads across them.

## Your first five actions

1. Run `/daily-brief` before opening email.
2. Put unstructured thoughts in `inbox.md`; the next brief or `/triage` drains
   them.
3. Run `/pipeline-review` before calling a list of conversations a pipeline.
4. Run `/weekly-review` on Friday before memory rewrites the week.
5. Ask the **Chief of Staff** to route any uncategorized decision. You do not
   need to memorize all 49 workflows.

## What the 13 agents are

The agents are specialized roles, not 13 autonomous processes running all day.
Each role owns one kind of decision and one part of the workspace. A workflow
invokes the relevant role when you ask for it; scheduled cadences invoke ten of
those workflows at defined times.

When you do not know which role or command to use, ask the **Chief of Staff**.
Routing is its one decision. The full generated catalogue is
[`founder-os/COMMANDS.md`](../founder-os/COMMANDS.md).

## Update, repair, or uninstall

Refresh the marketplace, update the installed plugin, and load the new version
without restarting Claude Code:

```text
/plugin marketplace update founder-os
/plugin update founder-os@founder-os
/reload-plugins
```

These are the current
[Claude Code plugin-management commands](https://code.claude.com/docs/en/discover-plugins).

For a workspace that is missing files, stale, or structurally inconsistent,
run `/founder-os-doctor`. It reports before proposing any repair. For an
interrupted first run, rerun `/founder-os-init`; do not delete the workspace or
manually replay the owner workflows.

To remove the plugin:

```text
/plugin uninstall founder-os@founder-os
```

The Markdown workspace under `FOUNDER_OS_HOME` is separate from the installed
plugin and remains yours. Back it up before deleting it yourself. See
[`troubleshooting.md`](troubleshooting.md) for recovery branches.

## Help and source

- [Full documentation set](README.md) — architecture, agents, state model, enforcement, and the developer guide
- [Complete command catalogue](../founder-os/COMMANDS.md)
- [Product philosophy and agent map](../founder-os/README.md)
- [Source code](https://github.com/msolecki/founder-os)
- [Report an issue](https://github.com/msolecki/founder-os/issues)
- [MIT license](../LICENSE)
