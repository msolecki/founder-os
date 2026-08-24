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

## The website

`msolecki.github.io/founder-os/` is a separate thing from the plugin, and this
section exists so the two are not confused. **The plugin sends nothing. It has
no telemetry, not even opt-in**, and that is the sentence the rest of this page
rests on.

The site is static files served by GitHub Pages. Founder OS runs **no analytics
script on it** — no page-view counter, no cookies, no fingerprinting, no
third-party tag. Its `Content-Security-Policy` allows scripts only from the
site's own origin, so a third-party tag could not load even if one were added by
accident.

What does exist is what exists for any hosted page: GitHub serves the request
and keeps its own server-side logs, and the repository's owner can see the
aggregate visit and clone counts GitHub reports for any public repository. That
is GitHub's collection under GitHub's terms, not ours, and it is not linked to
anything in a founder's workspace — there is no identifier that could join them.

If a cookieless page counter is ever added, it will be named here, in this
section, in the release that adds it. A trust center that describes the site as
measuring nothing while a script counts visitors is worth less than no trust
center, and the two paragraphs above are the standard this project is holding
itself to rather than a description of a limitation.

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

**A security issue goes to the private form first**, at
[Security → Report a vulnerability](https://github.com/msolecki/founder-os/security/advisories/new),
which is private between the reporter and the maintainer until an advisory is
published. That is a hook that allows what it should deny, an outbound or
spending path reachable from a packaged role, a path escape out of the
workspace, or anything touching the no-telemetry promise. The full scope, and
the list of documented boundaries that are not vulnerabilities, is in
[`SECURITY.md`](https://github.com/msolecki/founder-os/blob/main/SECURITY.md).

**A trust question is not a security issue and is better in public.** What the
package does with data, where state lives, what reaches the model host: read the
[enforcement guide](enforcement.md) and the
[getting-started guide](getting-started.md), then ask in
[Discussions](https://github.com/msolecki/founder-os/discussions) or open a
[bug report](https://github.com/msolecki/founder-os/issues/new?template=bug.yml).

Either way, never paste credentials, private business state, client names,
entity slugs, amounts, or absolute paths. A private advisory becomes public when
it is published.

This page describes product boundaries. It is not legal, tax, medical, or
investment advice and does not replace Claude Code or Codex policies.
