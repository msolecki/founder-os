# Security

Founder OS reads and writes the founder's own Markdown files on their own
machine. It sends nothing — no telemetry, not even opt-in. That is the promise
the rest of this file exists to protect.

## Reporting a vulnerability

**Report privately first, at
[Security → Report a vulnerability](https://github.com/msolecki/founder-os/security/advisories/new).**
That form is private between you and the maintainer until an advisory is
published. Do not open a public issue for any of the following, because the
issue tracker is the place the problem gets read by everyone before it gets
fixed:

- a hook that allows what it should deny, or a path around the ownership guard;
- an outbound or spending capability reachable from a packaged role — house
  rule 0 says the package never sends and never moves money, and a way around it
  is the most serious bug this project can have;
- anything that would put a founder's workspace contents somewhere they did not
  put them, including the no-telemetry promise;
- a path escape out of `$FOUNDER_OS_HOME` in the state gateway.

**Never paste workspace contents into a report, private or not.** Paths are
useful — `metrics.md`, `drafts/proposals/`. Client names, revenue figures,
rates, entity slugs and absolute paths are not, and a private advisory becomes a
public one when it is published.

Include the plugin version (`founder-os/.codex-plugin/plugin.json`), the host
(Claude Code or Codex), and what you expected the boundary to be.

## What is in scope

The package: the state gateway (`founder-os/mcp/`), the hooks
(`founder-os/hooks/`), the ownership map, and the packaged agents and skills.

## What is not a vulnerability

- **Hooks are not a security sandbox.** They are defense in depth and they fail
  open on malformed input by design, so the founder's own main thread is never
  blocked by a broken guard. `docs/enforcement.md` says exactly what they do and
  do not contain. A finding that a hook can be bypassed by a process the founder
  is already running as themselves is a documented boundary, not a bug — but the
  gateway is fail-closed regardless of the hook, and a way past *that* is.
- **The founder can write their own files.** They are the CEO and it is their
  machine. The ownership map binds agents, not the human.
- **A local overlay (`_local/`) can grant a local agent shell access.** The
  founder wrote it; `founder-os-doctor` reports it; the package does not stop it.

## Non-security trust questions

Anything about what the package does with data, where state lives, or what
reaches the model host is public and belongs in
[Discussions](https://github.com/msolecki/founder-os/discussions) or a
[bug report](https://github.com/msolecki/founder-os/issues/new?template=bug.yml).
The [trust center](https://msolecki.github.io/founder-os/trust.html) answers most
of them first.
