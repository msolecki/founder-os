# The Local Overlay

Thirteen agents and fifty-three skills are the shape of a company of one in
general. No founder runs a company in general. One of them has a licensing
partner and needs `partners.md`; one runs a podcast and needs a workflow no
consultant would ever want; one has a rhythm nobody upstream has heard of.

Until this file existed, every one of them had exactly one option: fork the
package. A fork stops receiving updates on the day it is made, which means the
founder trades a missing file for a frozen `ownership.yaml` — and they find out
which was the worse trade about four months later.

This is the other option. `references/ownership.yaml` stays the package's map.
The overlay is the founder's, it lives in their workspace, and it can only add.

## Where it lives

`$FOUNDER_OS_HOME/_local/` — inside the workspace, not inside the plugin.

```
$FOUNDER_OS_HOME/
  _local/
    ownership.yaml        # additive map: workspace_files, owns, sections
    skills/<slug>/SKILL.md
    agents/<slug>.md
```

In the workspace for three reasons, and the third is the one that decided it:

1. It survives `/plugin update` and `/plugin uninstall`. Anything the founder
   authored that a package manager can delete was in the wrong place.
2. It is per business. On a multi-business install each workspace carries its
   own, which is the point — a licensing partner belongs to the business that
   has one.
3. A shared extension directory would be a cross-business claim filed under no
   business's name. `ownership.yaml` already makes this argument about
   `portfolio_files:`, and it is the same argument.

`_local/` is deliberately **not** in `workspace_files:`. Init scaffolds from
that list, and an empty `_local/` in every new workspace would advertise
extension as step one. It is not step one. Most workspaces should never have
one.

## The three rules

### 1. Additive only

The overlay may declare a **new** path, its sections, a new skill and a new
agent. It may not reassign, remove, or re-section anything the package ships.

This is the rule the whole design exists to make structurally true rather than
merely stated. A rule the build cannot check is a rule that gets broken, and
the breaking case here is quiet and total: `metrics.md` reassigned away from
the CFO, in one founder's workspace, on a machine nobody upstream will ever
see. Every skill that reads `metrics.md` still reads it. Nothing errors. The
number is just written by somebody who does not close the month.

So the merge does not resolve that conflict in the packaged map's favour as a
matter of precedence — precedence would mean the overlay tried and lost, which
is a thing the founder is entitled to be told about. It **ignores the entry and
logs it**, and `founder-os-doctor` reports it as a finding against the overlay.

### 2. A conflict is a finding, never an override

A path present in both maps is not a merge with a winner. It is a bug in the
overlay, and it stays a bug until the founder removes it. Same for two local
agents claiming one local path: the contract is one owner per file, and the
overlay does not get a weaker version of it.

### 3. The overlay cannot widen the tool allowlist

A local agent gets a `tools:` allowlist that is a **subset** of what packaged
agents hold, and no overlay may grant `Bash`, `WebFetch`, `WebSearch`, an MCP
tool, or `Agent`.

**This rule is a contract, not something the guard enforces for you.**
`check_outbound` in `hooks/ownership-guard.py` denies the outbound tools to the
*thirteen packaged roles*, and a local agent is by definition not one of them —
`_role_of` returns None for it, the role lockdown never applies, and the guard
reaches `check_outbound` at all only on the role path. A local agent that names
`Bash` gets whatever the founder's own permission settings allow. The gateway
still refuses it: a local agent holds no role capability, so every
`founder-os-state` call is denied.

So `founder-os-doctor` is not an early warning about a tool that would be
denied mid-run. It is the only thing that reads this rule, and a finding it
reports is a capability the founder actually granted themselves. House rule 0
still binds every packaged role; the overlay simply cannot be handed the job of
enforcing it on agents the founder writes.

## Merge, precisely

`load_ownership()` reads the packaged map. `local_ownership(root)` reads
`<root>/_local/ownership.yaml` for the root a write actually resolved into, and
`merged_ownership()` joins them:

- Packaged entries are taken as-is.
- A local entry whose path is not in the packaged map is added.
- A local entry whose path **is** in the packaged map (compared case-folded,
  same as `owner_of`) is dropped with a log line.
- An unreadable, unparseable, or wrongly-shaped overlay is ignored entirely
  and logged. It never produces a deny.
- The overlay is read **per matched root**. Business A's overlay never applies
  to business B's workspace, and neither applies to the portfolio workspace.

The fail-open posture in the guard's docstring extends to this without
amendment: an overlay the guard cannot read costs coverage of the founder's own
local files, and coverage is not what a false deny costs.

## `_local/` is not writable by agents

The guard denies **any subagent** a write anywhere under `_local/`, whatever
the map says and whether or not an overlay exists.

An agent that can edit the map that governs it does not have a map. This is the
one place the guard is deliberately stricter than "one owner per file", and it
is cheap: the overlay is founder-authored by definition, `skill-forge` runs on
the main thread, and no packaged agent has ever had a reason to write there.

## Discovery: the source of truth and the installed copy

A `SKILL.md` under `$FOUNDER_OS_HOME/_local/skills/` is **not** discoverable.
The hosts load skills from installed plugins and their user skill scopes:
`~/.claude/skills/` for Claude Code and `~/.codex/skills/` for Codex. A file in
a Markdown workspace is a file, and
writing one and calling it a command is how a founder ends up with a workflow
that exists and never runs.

So there are two copies and they have different jobs:

| | Where | Job |
|---|---|---|
| **Source of truth** | `$FOUNDER_OS_HOME/_local/skills/<slug>/SKILL.md` | The founder's, versioned with their workspace, doctor-validated, survives uninstall. |
| **Installed copies** | `~/.claude/skills/founder-os-local-<business>-<slug>/` and `~/.codex/skills/founder-os-local-<business>-<slug>/` | What each host can actually load. The same source directory is copied to both scopes, namespaced per business, with a header naming the source. |

The install step is explicit, consented, and once — the `setup-cadences`
precedent exactly: a plugin cannot ship a schedule, so that skill writes one on
the founder's machine with their consent, names the file first, and reports
what it wrote. This does the same with a skill file. The doctor then checks the
two copies still agree, because two copies of anything is a second map and this
one is a second map on purpose.

## What the overlay does not do

**It is not enforced at write time for main-thread work.** The guard scopes to
subagents; the main thread is always allowed, because the founder is the CEO.
An installed local skill invoked as `/local-foo` runs on the main thread, so
the merged map does not constrain its writes.

This is not a regression and not a loophole introduced here — every packaged
skill has the identical property, and the guard's own docstring says at length
that it is not a security boundary. What the merged map actually buys:

- the map stays complete when a **packaged agent delegates** to a subagent that
  touches a local path,
- `founder-os-doctor` can check the whole thing statically, which is where the
  overlay's real validation lives,
- and a local path gets an owner, which is what makes handing it off possible.

Say this in the founder's terms in the docs. An extensibility feature that
implies enforcement it does not have is worse than one that admits the limit,
because the founder will build on the implication.

## Refusals

`skill-forge` refuses to:

- forge a skill whose decision a packaged agent already owns — name that agent
  and stop. One agent, one decision, is the test every packaged agent had to
  pass, and it does not lapse because the founder is the author;
- write anywhere inside the plugin directory;
- grant a tool no packaged agent holds;
- claim a path the packaged map already owns;
- install anything without naming the exact file first and being told yes.

## Decisions, and why

- **`skill-forge` belongs to no agent** — it is in both `SYSTEM_SKILLS` and
  `STANDALONE_SKILLS` in `scripts/_package.py`, the same pair as
  `setup-cadences`, and for the same reason rather than by analogy: running it
  as a subagent is denied by construction. Its first write is `_local/`, and
  the guard denies every subagent that directory. Its last write is outside the
  workspace entirely. A skill no agent can run is a skill no agent should hold.
  Making it a role skill would additionally force `_local/` into `owns:`, which
  pulls founder-authored structure into the map of company state and hands an
  agent a lane through the map that governs it.
- **Installed copies go to each host's user scope** (`~/.claude/skills/` and
  `~/.codex/skills/`), not a project's skill directory. The workspace usually
  lives outside any repository, and project scope would leak a founder's
  business workflows into a code repo they may well push.
- **Local slugs carry a `local-` prefix.** A packaged skill added upstream next
  year must not silently collide with one the founder wrote this year, and the
  founder must be able to tell, at the prompt, which of the two they are about
  to run.
