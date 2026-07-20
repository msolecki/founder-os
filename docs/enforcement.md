# Ownership and enforcement

"Every file has exactly one owner" and "no agent sends" are not promises the
prose makes — they are enforced by a triad of a **map**, a **write-time hook**,
and a **build-time validator**. This page explains how the three fit together and,
just as importantly, what they are *not*.

## The three layers

| Layer | File | When | Catches |
|---|---|---|---|
| The map | `references/ownership.yaml` | — | The single source of truth: who owns each file, what sections it has. |
| The build validator | `scripts/validate_package.py` | CI / before merge | A package whose *structure* is incoherent — an agent with an outbound tool, a skill writing a file it doesn't own, a missing belief. |
| The write-time guard | `hooks/ownership-guard.py` | Every subagent tool call | A running agent that decides *mid-flow* to write someone else's file or reach outside. |

The validator checks the map is coherent and no skill *declares* a write it
doesn't own. The guard is the runtime half: it checks the *actual* write. Before
the guard existed, an agent that decided mid-flow to fix a number in someone
else's file just did it.

## What the guard does

`ownership-guard.py` runs on `PreToolUse` for
`Write|Edit|NotebookEdit|apply_patch|Bash|WebFetch|mcp__*`. Two guards, both
**scoped to subagents**:

1. **Ownership** — a subagent writing a workspace path it does not own is denied
   and told who owns it (house rule 4). Matching is longest-prefix (a nested
   entry beats a broader one), case-folded (APFS is case-insensitive), and
   resolves symlinks and `..` walks on both sides so the map can't be dodged.
2. **Outbound** — a subagent reaching for `Bash`, `WebFetch`, or any `mcp__*`
   tool is denied (house rule 0). These three are the ones that can reach the
   outside world in one call: an agent with `Bash` can curl, one with `WebFetch`
   can POST, one with a mail MCP can send.

**Main-thread calls are always allowed.** Claude marks subagent calls with
`agent_type`; Codex supplies `turn_id`, resolved from the mapping written by
`record-agent.py` at `SubagentStart`. The founder is the CEO — this rule is about
agents, not about them.

## The fail-open posture (read this before you rely on it)

Every unknown **fails open**: no ownership map, no PyYAML, unparseable stdin, a
path it can't resolve, an unpredicted exception — the guard *allows*, logs to
stderr, and moves on.

This is deliberate and it is the whole product decision. A guard that denies
because it lost its own config is not "safe," it is broken: the founder hits it
on their own work, uninstalls it that afternoon, and then it protects nobody. A
false deny costs more than a miss — because a miss is caught by the build-time
validator, and a false deny is caught by the user's patience. The guard even
ships a minimal `owns:` parser for machines without PyYAML, so it degrades to
best-effort rather than a silent no-op.

## What this is NOT: a security boundary

Say this plainly, because the Claude Code docs do too: **hooks are not a security
boundary, and this hook is not one either.** It is operational policy — it keeps
an org of agents from corrupting each other's state during honest work. It does
not contain an adversary:

- A subagent that can shell out routes around the `Write` matcher entirely —
  `Bash(echo ... > goals.md)` never touches a Write hook. Guard 2 (the outbound
  ban) is the only reason that isn't trivial, and guard 2 is itself just another
  matcher.
- Matchers are string patterns. A tool this file doesn't name is a tool it
  doesn't see.
- Anything running outside the tool layer is invisible to it.

**The real boundary is the `tools:` allowlist on each agent**, enforced at build
time. No agent's allowlist may contain an outbound tool, so no agent has a shell,
a browser, or an MCP tool to route around anything. The board-member cannot even
write. The guard is defence in depth *behind* that allowlist: it fires only when
someone has loosened an agent — which is exactly the moment you want a second
opinion. **Treat a deny from the guard as a bug report about the allowlist, not
as "the system held."**

## Two allowlists, slightly different on purpose

The set of "outbound" tools is defined in two places, and they differ:

| Set | Where | Members |
|---|---|---|
| Build-time ban | `OUTBOUND_TOOLS` in `validate_package.py` | `Bash`, `WebFetch`, `WebSearch`, `NotebookEdit`, `Task` |
| Write-time deny | `OUTBOUND_TOOLS` in `ownership-guard.py` (+ `mcp__*`) | `Bash`, `WebFetch` |

The build check is deliberately *tighter*: an allowlist should be conservative,
so it also bars `WebSearch` and `Task`. The runtime deny is deliberately
*narrower*: neither `WebSearch` nor `Task` is a *send*, and denying a live agent
mid-run over a `WebSearch` would be a false deny for no gain. `NotebookEdit`
writes files, so at runtime it goes through the **ownership** check like `Write`
and `Edit`, not through the outbound set.

The tools an agent *may* hold: `Read, Write, Edit, Glob, Grep, Skill, Agent`
(`ALLOWED_AGENT_TOOLS`). Anything else fails the build.

## Multi-business coverage

On a multi-business install a session routinely writes a workspace other than the
one `FOUNDER_OS_HOME` names — the portfolio-manager writing `portfolio.md` is the
everyday case. The guard reads `~/.founder-os/businesses.yaml` and resolves every
registered business workspace root plus the portfolio workspace, so a
cross-business write is checked against the map rather than being invisible. The
same fail-open posture applies to the registry: unreadable YAML costs *coverage*,
never a write.
