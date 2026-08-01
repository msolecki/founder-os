# Founder OS Trust Center

Founder OS is one workflow system on Claude Code and Codex. The host adapter
changes discovery; it does not change the workflow, workspace write, output, or
guardrail contract.

The deployable version of this page is the [public Trust Center](trust.html).

## One product on Claude Code and Codex

The same `skills/<name>/SKILL.md` is the business logic on both hosts. Claude
Code may select it through `agents/*.md`; Codex discovers it through
`agents/openai.yaml`. Founder-created local skills follow the same contract and
are installed to both host user scopes by `/skill-forge` after consent.

## What stays local — and what may reach the model host

Canonical business state is local Markdown. Founder OS has no cloud service,
telemetry, or automatic calendar, CRM, email, bank, or accounting sync. Prompts,
attached context, and tool results sent through Claude Code or Codex are still
governed by that model host's account and data settings. Local workspace does
not mean that model context never leaves the machine.

Packaged role reads and writes pass through a local state gateway. Every
workspace file has one owner; roles can read shared state but write only their
owned paths and sections.

## What Founder OS can and cannot do

Workflows draft but never send, publish, pay, sign, cancel, transfer, or buy.
No packaged role has shell or network-capable tools. Tax, legal, medical, and
investment questions are escalated to a qualified professional.

In short: Founder OS never sends and never pays. The founder performs every
outbound or financial action.

## Hooks, ownership, and the fail-open boundary

Bundled hooks require review and trust where the host asks for it. If hooks are
disabled or not trusted, session guidance and runtime guard coverage are absent.
Ownership and hooks are operational guardrails, not a security sandbox. Unknown
inputs and main-thread writes deliberately fail open because the founder is the
CEO and a broken guard must not block their workspace. The build validator and
tool allowlists remain the stronger package contract.

## Scheduled work

Cadences use local LaunchAgents, persistent user-systemd timers, or cron.
Launchd and persistent systemd catch up after sleep; cron does not. There is no
Founder OS cloud scheduler.

## Multiple businesses

Each business has its own workspace and overlay. Only the Portfolio Manager's
portfolio workspace crosses business boundaries.

## Installation, updates, cache, and removal

Codex plugins use cached installed copies. After an update or reinstall, review
and trust the bundled hooks if prompted, then start a new conversation so the
new skills and metadata are loaded. Claude Code and Codex expose the same
workflow contract despite different discovery adapters. Uninstalling Founder OS
does not delete the founder's Markdown workspace or local overlay.

## Reporting a security or trust issue

Read the detailed [enforcement guide](enforcement.md) and
[getting-started guide](getting-started.md) first. Report issues at the
[repository issue tracker](https://github.com/msolecki/founder-os/issues), but
never paste credentials, private business state, client names, entity slugs,
amounts, or absolute paths into a public issue.

This page describes product boundaries. It is not legal, tax, medical, or
investment advice and does not replace Claude Code or Codex policies.
