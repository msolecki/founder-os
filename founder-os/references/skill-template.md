# SKILL.md template

Every skill in this package uses exactly this shape. Copy it literally; the
headings are not suggestions, and `scripts/validate_package.py` reads the
frontmatter.

```markdown
---
name: <skill-slug>
description: <one line, starts with a verb, says when to use it>
metadata:
  writes:
    - <path, copied exactly from references/ownership.yaml>
---

# <Human Title>

<One paragraph: what decision this skill serves and why it exists.>

## When to use

<Concrete triggers.>

## Inputs

<Which workspace files to read first. House rule 1: no advice without state.>

## Steps

1. <numbered, concrete>

## Output

<Exact file written, exact section, exact format.>

## Guardrails

<What this skill refuses to do. Omit only if genuinely nothing.>
```

## `metadata.writes`

**Role skills must declare every workspace path they write.** Each path must
appear **verbatim** as an entry under `owns:` in `references/ownership.yaml`,
and must be owned by the agent whose `skills[]` lists this skill.
`check_skill_writes` in `scripts/validate_package.py` fails the build otherwise.
This catches the one class of bug no other check sees: an agent running a skill
whose output belongs to somebody else — `agent -> skill` and `file -> owner` can
both be valid while `skill -> file` is not.

Use the `ownership.yaml` spelling exactly. Directory entries keep their trailing
slash and are not expanded to a filename:

```yaml
metadata:
  writes:
    - reviews/daily/          # correct
    - reviews/daily/2026-07-15.md   # WRONG — not an entry in ownership.yaml
```

**A skill that writes nothing omits `metadata` entirely.** This is correct for
every `board-member` skill: a board advises, it does not write company state.
Its findings reach the workspace only if the founder logs them via
`decision-log`. Declaring a write you do not make is worse than declaring none —
it asserts an ownership claim the agent does not have.

Owning nothing must be a decision, not an omission. `focus-coach` owns
`week.md` precisely because the alternative failed that test: it had a
scheduled Monday `week-plan` task with nowhere to write, and a `calendar-audit`
skill with no baseline to compare against. If you add an agent that owns
nothing, be able to say why — as the board can.

**The five system skills are exempt** — `founder-os-init`, `founder-os-doctor`,
`context-load`, `guardrails`, `state-integrity`. They are cross-cutting, and
`founder-os-init` scaffolds the entire workspace regardless of owner. Do not add
`metadata.writes` to them; the validator skips them by design.

## The quality bar

Every skill contains at least one of:

- a specific question the founder is avoiding,
- a named failure mode, or
- a decision rule with a threshold.

If a competent founder already knows everything in the file, the file is filler.
"Review your pipeline regularly and follow up with prospects" is filler. Forty
skills of filler is what makes a package worthless — and it is the default
outcome, not the unlucky one.

No motivational language. State the cost of the thing the founder is avoiding
and stop.
