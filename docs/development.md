# Development guide

For working *on* the package. The repo is both the plugin marketplace and the
source repo. This page covers the checks, how to add a skill or an agent, the
tests, CI, and releasing.

## Before you open a PR

```bash
pip install pyyaml
python3 scripts/validate_package.py founder-os     # 13 agent(s), 49 skill(s), 0 error(s)
python3 scripts/generate_commands.py founder-os    # regenerate COMMANDS.md if frontmatter changed
python3 -m unittest discover -s tests              # OK
```

CI runs all three on every push and PR (`.github/workflows/ci.yml`). A red build
is a no from the machine before it is a review comment from a human.

## What the validator checks

`scripts/validate_package.py` runs these checks (each named function). They
enforce *structure*; they cannot read prose.

| Check | Fails when… |
|---|---|
| `check_plugin` | `.claude-plugin/plugin.json` is missing/invalid, or `name` ≠ `founder-os`. |
| `check_agents` | An agent lacks `name`/`description`/`skills`, its `name` ≠ filename, it lists a skill with no `SKILL.md`, or it omits a universal skill (`guardrails`, `state-integrity`, `ingestion-gate`). |
| `check_agent_tools` | An agent has no `tools:` (omitting it inherits everything), holds an outbound tool (`Bash`, `WebFetch`, `WebSearch`, `NotebookEdit`, `Task`), or names an unknown tool. Allowed: `Read, Write, Edit, Glob, Grep, Skill, Agent`. |
| `check_agent_graph` | An `Agent(...)` target isn't a real agent, or an agent tries to summon itself. |
| `check_role_skill_exclusivity` | A non-system skill is held by two agents. |
| `check_orphans` | A skill directory is held by no agent and not declared standalone. |
| `check_agent_headings` | An agent is missing one of the four mandated headings or has them out of order (`## What triggers you` → `## What you do` → `## What you produce` → `## Who you hand off to`). |
| `check_ownership` | `ownership.yaml` names a non-agent owner, a file owned twice, or a `workspace_files:`/`portfolio_files:` entry nobody owns. |
| `check_workspace_files_complete` | A path in `owns:` is not in `workspace_files:`/`portfolio_files:` — so `founder-os-init` would never scaffold it. |
| `check_skill_writes` | A skill's `metadata.writes` names a path no agent owns, or a path owned by an agent other than the one holding the skill. |
| `check_sections` | `sections:` declares a path nobody owns, or a skill writes a path `ownership.yaml` declares no sections for. |
| `check_beliefs` | A role skill has no `## Beliefs`, has it *after* `## Steps`, or has fewer than 3 bullets. |
| `check_hooks` | `hooks.json` is missing/invalid, the `PreToolUse` matcher doesn't cover `Write/Edit/NotebookEdit/Bash/WebFetch/mcp__*`, or `ownership-guard.py` doesn't compile. |
| `check_readme_counts` | The README "What's inside" table's Agents/Skills/Cadences counts don't match the package. |

The **system skills** (`founder-os-init`, `founder-os-doctor`, `context-load`,
`guardrails`, `state-integrity`, `ingestion-gate`) are exempt from the
writes/beliefs checks — they are cross-cutting and write no workspace file of
their own. `setup-cadences` is **standalone** (belongs to no agent by design).
Both sets are defined at the top of `validate_package.py`, and that code — not
any prose — is the authority on which skills are exempt.

## What the validator cannot check (review holds the bar)

Three things the machine can't read, from
[`CONTRIBUTING.md`](../CONTRIBUTING.md):

1. **One agent = one decision no other agent can make.** A new agent that shares
   a decision with an existing one is a merge, not an addition.
2. **Beliefs must be contestable.** The count and placement are machine-checked;
   whether the three principles are *actual* beliefs rather than platitudes with
   a heading over them is what review is for. The bar: "at least 3 principles a
   competent generic advisor would NOT say."
3. **House rule 0 is not negotiable.** No PR that loosens an allowlist to add an
   outbound tool will be merged.

## Adding a skill

1. Create `founder-os/skills/<name>/SKILL.md` from
   [`references/skill-template.md`](../founder-os/references/skill-template.md).
   Fill in `name`, `description` (verb-first, says when to use it), and
   `metadata.writes` — every path it writes, copied *verbatim* from
   `ownership.yaml`.
2. Write the body: `## When to use`, `## Inputs`, `## Beliefs` (≥3 contestable
   principles, before `## Steps`), `## Steps`, `## Output` (exact file, exact
   section, exact format), `## Guardrails`. Optionally `## Named failure modes`.
3. Add `<name>` to the owning agent's `skills:` in `agents/<agent>.md`. That agent
   must own every path in `metadata.writes`.
4. If it writes a *new* section of a file, add that heading to `sections:` in
   `ownership.yaml` **in the same PR**.
5. For Codex parity, add `skills/<name>/agents/openai.yaml` (a small interface:
   `display_name`, `short_description`, `default_prompt`).
6. Regenerate: `python3 scripts/generate_commands.py founder-os`.
7. Validate and test.

A skill that writes nothing (every board-member skill) omits `metadata` entirely.
Declaring a write you don't make is worse than declaring none — it asserts an
ownership claim the agent doesn't have.

## Adding an agent

1. Create `founder-os/agents/<slug>.md`. Frontmatter: `name` (= filename),
   `description`, `skills:` (must include the three universal ones), `tools:` (an
   explicit allowlist — never omit it, and never an outbound tool).
2. Body: the four mandated headings, in order.
3. If it owns files, add them under `owns:` in `ownership.yaml`, ensure each is in
   `workspace_files:` (or `portfolio_files:`), and declare its `sections:`.
4. Wire `Agent(...)` edges only if it is a manager that legitimately summons
   reports. Nobody summons themselves; targets must be real agents.
5. Update the README counts (or let `check_readme_counts` tell you).

Owning nothing must be a *decision* (as the board can defend), not an omission.

## Generated and derived files — never hand-edit

- `founder-os/COMMANDS.md` — regenerated by `generate_commands.py`; CI's `--check`
  fails when it is stale.
- README's counts — checked by `check_readme_counts`.

A hand edit to either is a second map, and second maps go stale silently.

## Tests

Under `tests/`:

- `test_validate_package.py` — the validator's own behavior.
- `test_ownership_guard.py` — the write-time hook (subprocess tests: main-thread
  allow, subagent ownership deny, outbound deny, fail-open paths).
- `test_docs_workflows.py` / `docs_workflows.behavior.test.js` — the landing
  site's workflow content.

Run: `python3 -m unittest discover -s tests`.

## Releasing

1. Bump the version in `founder-os/.claude-plugin/plugin.json` (mirror it in
   `.codex-plugin/plugin.json`).
2. Add a `CHANGELOG.md` entry (SemVer, dated).
3. Ensure validator, `--check`, and tests are green.
4. Tag / publish. The repo *is* the marketplace, so a merge to the default branch
   ships it.

The `solkova-core:release` skill can build a SemVer release from Conventional
Commits if you use it.

## Dual-host notes

- Claude Code reads `.claude-plugin/plugin.json` + `agents/*.md` + `skills/*/SKILL.md`.
- Codex reads `.codex-plugin/plugin.json` + `skills/<name>/agents/openai.yaml`;
  `AGENTS.md` at the repo root points it at `founder-os/CLAUDE.md`.
- The `SessionStart` and guard hooks handle both hosts: Claude supplies
  `agent_type` directly; Codex supplies `turn_id`, resolved through
  `record-agent.py`. Keep both manifests' `version` in sync.
