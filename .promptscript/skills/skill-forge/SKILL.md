---
name: skill-forge
description: Add a workflow, file, or role this package does not ship — run when the founder's business needs something the thirteen agents have no lane for, and refuse when one of them already does
references:
  - agents/openai.yaml
---

# Skill Forge

Thirteen agents and fifty workflows are the shape of a company of one in
general. Nobody runs a company in general. Somewhere in this founder's week
there is a recurring decision the package has no lane for — a licensing
partner, a production rhythm, a regulator, a second product with its own
clock — and until this skill existed their only option was to fork, which
trades a missing file for an `ownership.yaml` frozen on the day they forked.

This is the other option, and most of the time the right answer is still no.
Read `references/extensibility.md` before you write anything: it is the
contract, and the refusals below are half of it.

## When to use

- The founder names a decision they make repeatedly and no packaged workflow
  covers it — not "I wish this were faster", a decision, with an outcome.
- The workspace needs a file the map does not declare, and the founder can say
  which agent should own it.
- `founder-os-doctor` reported an overlay finding: the source is theirs to fix
  and this is where the fix happens.

**Not for**: a one-off task (do the task), a preference about how an existing
workflow behaves (that is a change to the packaged skill, upstream), or a
capability the founder wants because a tool exists.

## Inputs

- `references/extensibility.md` — the overlay contract, the merge rules, the
  refusals. Read it first; everything below assumes it.
- `references/skill-template.md` — the shape every skill has, including the
  ones the founder writes. The template does not relax because the author
  changed.
- `references/ownership.yaml` — the packaged map. You are checking against it,
  never editing it.
- `$FOUNDER_OS_HOME/_local/` — the current overlay, if there is one.
- `charter.md` and `goals.md` — house rule 1. A workflow for a decision that
  serves no bet is a workflow the founder will run twice.

## The refusals

These come before the steps because refusing is most of this skill's job, and
the first one is most of the refusing.

**A decision a packaged agent already owns.** Name the agent, name the workflow,
and stop. One agent, one decision, is the test all thirteen had to pass, and it
does not lapse because the founder is the author — a second `/pipeline-review`
called `/local-deals` does not add a capability, it adds a second answer to a
question that already had one, and the founder now has to remember which of the
two they trust. This is the most common outcome of running this skill and it
should be. Being told "the Pipeline Coach already does this, here is the
command" is a better result than a new file.

**Anything inside the plugin directory.** The overlay lives in the workspace.
A skill written into `founder-os/skills/` is deleted by the next
`/plugin update` and takes the founder's work with it.

**A path the packaged map already owns.** The overlay is additive. If the real
need is that a packaged file has the wrong owner, that is a conversation about
the packaged map — open an issue, do not shadow it locally where it reads as
active and is silently dropped by the guard.

**Any tool no packaged agent holds.** No `Bash`, no `WebFetch`, no `WebSearch`,
no `mcp__*`, no `Agent`. House rule 0 is not a default the founder's own file
may override, and the guard denies these regardless of what any map says — so
granting one produces a skill that fails mid-run rather than a skill that works.

**Beliefs you wrote yourself.** See step 5. A belief the founder did not say is
a platitude with their name on it, and they will not defend it when the skill
tells them something they do not want to hear — which is the only moment the
beliefs matter.

## Steps

1. **Resolve the business first.** `context-load` step 0. The overlay is per
   workspace, and forging into the wrong one files a licensing partner under
   the company that does not have one.

2. **Make them state the decision in one sentence.** "What do you decide when
   you run this, and what changes because you decided it?" If it takes a
   paragraph, there is more than one decision in it — split it, or stop. A
   workflow whose decision cannot be stated cannot be refused either, which is
   how a skill ends up being run for anything vaguely nearby.

3. **Run the one-decision test out loud.** Walk the thirteen agents and say
   which one is closest and why it is not this. If a packaged agent owns the
   decision, refuse (above). If a packaged agent owns the *lane* but has no
   workflow for this decision, that is the good case: the skill is local, the
   owner is packaged.

4. **Pick the owner, and prefer a packaged agent.** A local agent is a real
   addition to the org chart and needs the same justification the thirteen
   needed — one decision no other agent can make, an explicit `tools:`
   allowlist, four headings, and an entry in the overlay's `owns:` or a stated
   reason it owns nothing. Most local skills do not need one. If the founder
   wants a local agent, make them pass the test before you write the file.

5. **Extract the beliefs; do not supply them.** At least three principles a
   competent generic advisor would not say, in the founder's words, about their
   business. Ask for the case where the obvious answer was wrong, the thing
   they have stopped explaining to people, the rule they follow that annoys
   clients. Write those down. If they cannot produce three, the skill is a
   checklist and not a decision — say so, write it as a checklist, and do not
   dress it in a `## Beliefs` heading it has not earned.

6. **Write the source of truth**, at
   `$FOUNDER_OS_HOME/_local/skills/local-<slug>/SKILL.md` and
   `agents/openai.yaml`, from
   `references/skill-template.md` verbatim: frontmatter with `name` and
   `description`, `metadata.writes` as a JSON-encoded array string containing
   every path it writes, `## Beliefs` before `## Steps`, `## Output` naming the
   exact file and heading, and `agents/openai.yaml` must name `$local-<slug>` in
   `default_prompt`; the
   `local-` prefix is not decoration — a packaged skill
   added upstream next year must not silently shadow this one.

7. **Register every new path in the same run.** New file, new directory or new
   heading goes into `$FOUNDER_OS_HOME/_local/ownership.yaml` under
   `workspace_files:`, `owns:` and `sections:` — before the skill is installed,
   never afterwards. A skill whose writes are not in the map produces a deny
   the first time a subagent runs it, and the founder reads that deny as the
   package being broken.

8. **Install, by name, with consent.** Say the exact path you are about to
   write —
   `~/.claude/skills/founder-os-local-<business>-<slug>/` and
   `~/.codex/skills/founder-os-local-<business>-<slug>/` — say that both are
   outside the workspace and plugin, and ask once. Write only on a yes — both
   destinations are written together or neither is written.
   Copy the same source directory, including `agents/openai.yaml`, to both
   destinations and report both paths. This is the `setup-cadences` rule applied
   to a file instead of scheduler state, for the same reason: a plugin cannot make
   a host load a workflow, so the founder does, knowingly.

9. **Verify against the doctor's overlay checks and show the result.** Overlay
   parses; no packaged path claimed; every local path has exactly one owner;
   the skill's `metadata.writes` is owned by its agent; beliefs present, three
   or more, before the steps; slug prefixed and not colliding; installed copy
   matches the source. A forge that reports success without running these has
   handed the founder a workflow that fails the first time it matters.

## Output

Four paths at most, and every one of them named before it is written:

- `$FOUNDER_OS_HOME/_local/skills/local-<slug>/SKILL.md` — the source of truth.
- `$FOUNDER_OS_HOME/_local/ownership.yaml` — created or extended, additive only.
- `~/.claude/skills/founder-os-local-<business>-<slug>/` and
  `~/.codex/skills/founder-os-local-<business>-<slug>/` — identical installed
  copies, only on an explicit yes, carrying a first-line comment naming the
  source path so whoever finds either copy knows which file to edit.

Optionally `$FOUNDER_OS_HOME/_local/agents/<slug>.md`, when the founder passed
the one-decision test in step 4 and not otherwise.

Then, in conversation: what was written, what it decides, who owns it, and the
command that runs it.

## Guardrails

Never write inside the plugin directory. Never install without naming the exact
path and being told yes. Never grant a tool no packaged agent holds. Never
forge a second workflow for a decision a packaged agent already owns — name it
instead. Never write a belief the founder did not say.

Never edit `references/ownership.yaml`. The packaged map is upstream's; the
overlay is the founder's; this skill only ever writes the second one, and the
guard denies every subagent that directory precisely so this stays true.

Never repair an overlay finding by relaxing the contract. If a local skill
writes a path its agent does not own, fix the ownership or fix the skill —
adding the path to a second agent is how "one owner per file" becomes a comment.
