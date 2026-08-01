# Getting started with Founder OS

**Know what matters today.** Founder OS is for a solo service founder already
using Claude Code or Codex. It turns current business state into one
source-linked decision, saves it to local Markdown, and produces a valid first
brief in less than fifteen minutes.

Start with a situation such as **“I do not know what matters today”** or run
`/situation-review`. The Chief of Staff selects one owner, one workflow, and the
state destination; you do not need the command catalogue first. It previews the
decision, route, missing state, and expected destination; the specialist starts
only after you choose **Continue**, while **Stop** ends without running it.
Founder OS never sends, pays, signs, cancels, or publishes. The founder remains
the CEO.

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
| A recent [Claude Code](https://code.claude.com/docs) or [Codex](https://developers.openai.com/codex/plugins/build) installation | Founder OS is a plugin, not a standalone app. |
| Python 3.9+ | Runs the local state gateway and host hooks. |
| PyYAML *(development/tests only)* | Runs the full package validator; the installed runtime remains dependency-light. |
| Node.js 20+ *(development/tests only)* | Runs the landing-page behavior contract test. |
| A user scheduler *(optional)* | `launchd`, user `systemd`, or cron runs cadences. Every workflow also works manually. |

Founder OS itself is free and MIT-licensed. Your existing host plan and
usage remain separate; Founder OS does not add another account or subscription.

## What Founder OS knows

Founder OS knows only what is recorded in its Markdown workspace or supplied in
the current host session. It does **not** automatically sync your:

- calendar;
- CRM or pipeline tool;
- inbox or social accounts;
- bank account, accounting system, or payment provider.

This is deliberate. Packaged roles have no browser, shell, direct file tool, or
external MCP tool. Their only MCP surface is the bounded local state gateway.
They can draft a message, proposal, or plan, but cannot send, post, pay, sign,
or transfer anything.

Workspace files stay on your machine. The prompts and context you send through
Claude Code or Codex are still governed by that environment's data-handling
terms.

## Install

Run these commands in Claude Code, in order:

```text
/plugin marketplace add msolecki/founder-os
/plugin install founder-os@founder-os
/founder-os:founder-os-init
```

In Codex, install the same package from the repository marketplace:

```text
codex plugin marketplace add msolecki/founder-os
codex plugin add founder-os@founder-os
$founder-os:founder-os-init
```

Review and trust bundled hooks when prompted. After updating or reinstalling in
Codex, start a new conversation so the cached copy is refreshed.

`founder-os-init` is one continuous, resumable flow from an empty folder to a
persisted first brief. It checks the install and target before writing, then
asks four short groups about the business, customer, quarter and money. It
delegates each answer through a short-lived role capability to the sibling that
owns the destination file, validates each persisted checkpoint, and ends with a
dated brief at `reviews/daily/YYYY-MM-DD.md`.

After the read-only preflight, it asks one optional intent question: **“What
made you install Founder OS today?”** A supplied answer is saved as the
founder's stated context, not treated as business evidence and not allowed to
choose the first bet or commitment by itself. Each of the four groups shows its
position, expected time, the decision it supports, and that `UNKNOWN` is an
acceptable answer. After every owner checkpoint, you see the owner, persisted
file, and any honest gap.

A valid brief has all four required headings declared in `ownership.yaml`:
`## The one thing`, `## Rotting`, `## The trade`, and `## Triage`. `## The one
thing` and `## The trade` must be non-empty. An empty, malformed, or wrong-path
file does not activate the workspace.

The median target is ten minutes and the hard stop is fifteen minutes. Unknown
cash, revenue or burn stays unknown and becomes an owned follow-up; it is never
filled from inference. `Activation complete` appears only after that valid
brief passes the same check in the same resolved workspace. If the flow stops,
repeat the host-specific init command: populated sections are preserved and the
first missing stage resumes.

The activation receipt leads with the value you can inspect:

- **You came with:** the optional install reason, or `not supplied`.
- **Your first decision:** today's one thing and its trade.
- **Based on:** the source files and dates used by the brief.
- **Saved to:** the exact daily-review path.
- **Founder OS will remember:** the live queue item, bet link, and explicit
  missing inputs.
- **Recommended next move:** one workflow derived from current state.

If you supplied an install reason, Founder OS may then preview how
`/situation-review` would route it. The preview shows the owner, workflow,
required state, and expected persistence, then offers **Continue** or **Stop**.
The specialist workflow runs only after you choose **Continue**. At the
fifteen-minute hard stop, onboarding shows a copyable `/situation-review`
command carrying the reason instead of opening another role session.

## What every completed workflow shows

Founder OS ends each successful workflow with one receipt:

- **Decision:** the verdict or result.
- **Evidence:** workspace paths and source dates used.
- **Changed:** only paths re-read and verified after the role returned.
- **Gaps:** missing or stale state that constrained the answer, or `none`.
- **Returns:** the cadence or date that revisits the decision, or `none`.
- **Your move:** exactly one human action, or `none`.

A read-only workflow reports **Changed:** `none`. A failed or uncertain write
produces an error receipt, never a success claim. Freshness is explicit:
`current` and `stale` require a named workflow or doctor threshold; `unknown`
means a required value is absent. When no threshold exists, the receipt shows
the source date without inventing a freshness label.

## Optional: schedule the cadences

After the first brief, run the command for your host:

```text
/founder-os:setup-cadences       # Claude Code
$founder-os:setup-cadences       # Codex
```

With your consent, this writes local LaunchAgents, persistent user-systemd
timers, or cron entries. Launchd and persistent systemd catch up after sleep;
cron does not. There is no cloud scheduler, and every cadence can still be
invoked manually.

Multi-business installs keep one workspace and one schedule fence per business.
The Portfolio Manager is the only role that reads across them.

## Your first five actions

1. Run `/daily-brief` before opening email.
2. Run `/capture Call Anna about the Acme scope`; the next brief or `/triage`
   drains the saved line.
3. Run `/pipeline-review` before calling a list of conversations a pipeline.
4. Run `/weekly-review` on Friday before memory rewrites the week.
5. Ask the **Chief of Staff** to route any uncategorized decision. You do not
   need to memorize all 53 workflows.

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

Codex keeps a marketplace snapshot and an installed cache. Refresh and replace
that cached copy, then start a new conversation:

```text
codex plugin marketplace upgrade founder-os
codex plugin remove founder-os@founder-os
codex plugin add founder-os@founder-os
```

For a workspace that is missing files, stale, or structurally inconsistent,
run `/founder-os-doctor`. It reports before proposing any repair. For an
interrupted first run, repeat the host-specific init command; do not delete the
workspace or manually replay the owner workflows.

To remove the plugin:

```text
/plugin uninstall founder-os@founder-os
```

In Codex, use `codex plugin remove founder-os@founder-os`.

The Markdown workspace under `FOUNDER_OS_HOME` is separate from the installed
plugin and remains yours. Back it up before deleting it yourself. See
[`troubleshooting.md`](troubleshooting.md) for recovery branches.

## Help and source

- [Full documentation set](README.md) — architecture, agents, state model, enforcement, and the developer guide
- [Complete command catalogue](../founder-os/COMMANDS.md)
- [Product philosophy and agent map](../founder-os/README.md)
- [Source code](https://github.com/msolecki/founder-os)
- [Report an issue](https://github.com/msolecki/founder-os/issues)
- [Trust Center](trust.md) — data boundaries, permissions, and host parity
- [MIT license](../LICENSE)
