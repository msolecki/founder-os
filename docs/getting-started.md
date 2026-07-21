# Getting started with Founder OS

Founder OS is a free, MIT-licensed Claude Code plugin for a company of one. It
adds 13 specialized business roles, 49 workflows, and 10 optional operating
cadences backed by a local Markdown workspace.

It does not run the company for you. It gives your decisions persistent state,
an owner, and a review rhythm.

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

## What the 13 agents are

The agents are specialized roles, not 13 autonomous processes running all day.
Each role owns one kind of decision and one part of the workspace. A workflow
invokes the relevant role when you ask for it; scheduled cadences invoke ten of
those workflows at defined times.

When you do not know which role or command to use, ask the **Chief of Staff**.
Routing is its one decision.

The full generated catalogue is [`founder-os/COMMANDS.md`](../founder-os/COMMANDS.md).

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
Claude Code are still governed by the data-handling terms of your Claude Code
environment.

## Install

Run these commands in Claude Code, in order:

```text
/plugin marketplace add msolecki/founder-os
/plugin install founder-os@founder-os
/founder-os-init
```

`/founder-os-init` takes about 20 minutes. It asks about the business, charter,
goals, metrics, offer, and voice, then creates a complete workspace and hands
you the first daily brief.

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

## See the result before installing

The fictional [`examples/studio-north/`](../examples/studio-north/) workspace
shows a daily brief linked to a real queue item, quarterly bet, weekly block,
pipeline action, weekly review, and irreversible decision.

Start with its
[`reviews/daily/2026-07-20.md`](../examples/studio-north/reviews/daily/2026-07-20.md),
then follow `q-0720a` and `B1` across the files.

## Your first week

1. Run `/daily-brief` before opening email.
2. Put unstructured thoughts in `inbox.md`; the next brief or `/triage` drains
   them.
3. Run `/pipeline-review` before calling a list of conversations a pipeline.
4. Run `/weekly-review` on Friday before memory rewrites the week.
5. Use `/founder-os-doctor` if the workspace looks stale or inconsistent.

You do not need to memorize all 49 commands. Ask the Chief of Staff what should
happen next.

## Help and source

- [Full documentation set](README.md) — architecture, agents, state model, enforcement, and the developer guide
- [Complete command catalogue](../founder-os/COMMANDS.md)
- [Product philosophy and agent map](../founder-os/README.md)
- [Source code](https://github.com/msolecki/founder-os)
- [Report an issue](https://github.com/msolecki/founder-os/issues)
- [MIT license](../LICENSE)
