# Development guide

For working *on* the package. The repo is both the plugin marketplace and the
source repo. This page covers the checks, how to add a skill or an agent, the
tests, CI, and releasing.

## Before you open a PR

```bash
pip install pyyaml
python3 scripts/validate_package.py founder-os     # 13 agent(s), 56 skill(s), 0 error(s)
python3 scripts/generate_commands.py founder-os    # regenerate COMMANDS.md if frontmatter changed
python3 scripts/smoke_installed_copy.py            # installed-copy smoke: PASS
python3 -m unittest discover -s tests              # OK
node --test tests/*.behavior.test.js               # landing behavior: pass
python3 scripts/check_local_links.py                # local links: PASS
```

CI runs all six on every push and PR (`.github/workflows/ci.yml`). A red build
is a no from the machine before it is a review comment from a human.

## What the validator checks

`scripts/validate_package.py` runs 17 build-time checks (each named function).
They enforce *structure*; they cannot decide whether business advice is good.

| Check | Fails when… |
|---|---|
| `check_plugin` | Claude/Codex manifests are missing or invalid, identities/descriptions disagree, or the plugin name is not `founder-os`. |
| `check_host_adapters` | The Claude `.mcp.json` or Codex `mcpServers` adapter is missing, malformed, or does not point at the one shared local gateway entry. |
| `check_codex_skill_interfaces` | A shared `skills/<name>/SKILL.md` has no Codex `agents/openai.yaml`, malformed interface YAML, missing presentation fields, or a default prompt that does not name the same `$<name>` skill. |
| `check_agents` | An agent lacks `name`/`description`/`skills`, its `name` ≠ filename, it lists a skill with no `SKILL.md`, or it omits a universal skill (`guardrails`, `state-integrity`, `ingestion-gate`). |
| `check_agent_tools` | An agent has no `tools:`, names a direct/outbound/unknown tool, or differs from the bounded `founder-os-state` gateway allowlist. |
| `check_one_level_orchestration` | A role lacks the shared state/delegation contract, names a nested-agent edge, carries an unbounded handoff, or uses an invalid gateway tool. |
| `check_role_skill_exclusivity` | A non-system skill is held by two agents. |
| `check_orphans` | A skill directory is held by no agent and not declared standalone. |
| `check_agent_headings` | An agent is missing one of the four mandated headings or has them out of order (`## What triggers you` → `## What you do` → `## What you produce` → `## Who you hand off to`). |
| `check_ownership` | `ownership.yaml` names a non-agent owner, a file owned twice, or a `workspace_files:`/`portfolio_files:` entry nobody owns. |
| `check_workspace_files_complete` | A path in `owns:` is not in `workspace_files:`/`portfolio_files:` — so `founder-os-init` would never scaffold it. |
| `check_skill_writes` | A skill's `metadata.writes` names a path no agent owns, or a path owned by an agent other than the one holding the skill. |
| `check_sections` | `sections:` declares a path nobody owns, or a skill writes a path `ownership.yaml` declares no sections for. |
| `check_capture_contract` | `capture` is missing, is held by an agent other than `chief-of-staff`, writes anything but `inbox.md`, or drops a phrase of its bounded input contract — the single nonblank line, the 2048-byte limit, the rejected control characters, the safe `- ` list prefix, the observed-SHA precondition, the post-write re-read, or the uncertain-persistence rule. |
| `check_beliefs` | A role skill has no `## Beliefs`, has it *after* `## Steps`, or has fewer than 3 bullets. |
| `check_hooks` | Hook config or matchers are invalid/incomplete, or the guard, recorder, or gateway entry does not compile. |
| `check_readme_counts` | The README "What's inside" table's Agents/Skills/Cadences counts don't match the package. |

The **system skills** (`founder-os-init`, `founder-os-doctor`, `context-load`,
`guardrails`, `state-integrity`, `ingestion-gate`) are exempt from the
writes/beliefs checks — they are cross-cutting and write no workspace file of
their own. `setup-cadences` and `skill-forge` are **standalone** (belong to no
agent by design). Both sets are defined in `scripts/_package.py`, and that code
— not any prose — is the authority on which skills are exempt.

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
4. Give it the same bounded state-gateway tools and shared sibling contract as
   every other role. If it routes work, it returns the canonical six-field
   delegation request; it never invokes another agent itself.
5. Update the README counts (or let `check_readme_counts` tell you).

Owning nothing must be a *decision* (as the board can defend), not an omission.

## Documentation consistency contract

Public documentation is derived from executable package state, not copied from
an internal release plan. Use these sources of truth:

| Public claim | Authority |
|---|---|
| Current version | `.claude-plugin/marketplace.json` and both package manifests; all three must match. |
| Agent and workflow totals | `founder-os/agents/*.md` and `founder-os/skills/*/SKILL.md`. |
| Cadence total | The command table in `founder-os/skills/setup-cadences/SKILL.md`. |
| Host install and update commands | Commands exercised by the current Claude and Codex CLIs and pinned in release tests. |
| Runtime dependencies | Imports and subprocess entry points used by the installed gateway and hooks; development-only tooling is labeled separately. |
| Gateway, ownership, and orchestration behavior | `founder-os/mcp/`, `founder-os/hooks/`, `founder-os/references/ownership.yaml`, and `founder-os/references/orchestration.md`. |

The public site has two HTML surfaces. `docs/index.html` is one concise landing
page containing the user-facing product contract, both host installation paths,
current counts and version, and links to deeper Markdown guides. `docs/trust.html`
is the separate Trust Center navigation destination for data, host, ownership,
hook, installed-copy, and human-authority boundaries. Do not add another HTML
page for release or technical details that belong in the one-page landing or an
existing Markdown guide.

Release tests must derive totals and versions from their authorities and reject
stale public copy. Landing tests must exercise both Claude and Codex installation
paths, dependency wording, local-state boundaries, and every interactive
controller. The repository link checker remains the final local target and
anchor gate.

## Generated and derived files — never hand-edit

- `founder-os/COMMANDS.md` — regenerated by `generate_commands.py`; CI's `--check`
  fails when it is stale.
- README's counts — checked by `check_readme_counts`.

A hand edit to either is a second map, and second maps go stale silently.

## Tests

Under `tests/`:

- `test_validate_package.py` — the validator's own behavior.
- `test_state_gateway_*.py` — protocol framing, workspace/session reads,
  ownership, optimistic concurrency, atomic writes, and journal redaction.
- `test_ownership_guard.py` — host defense in depth: native/Codex identity,
  capability agreement, direct/outbound denial, and malformed-hook paths.
- `test_session_context.py` — copies the plugin into a temporary marketplace,
  checks every `SessionStart` source and exercises ownership from that copy.
- `test_release_metadata.py` — pins release versions, activation-led metadata,
  changelog sections and the reproducible release-gate contract.
- `test_docs_workflows.py` / `docs_workflows.behavior.test.js` — the landing
  site's workflow content, and the trust center's claim that no third-party
  script runs on it.
- `test_feedback_channels.py` — the issue templates, and the pin that keeps
  their workflow dropdown equal to the skills directory.
- `test_traffic_snapshot.py` — the traffic series' dedup and its
  automation rule, and the snapshot workflow's branch and permission contract.

Run `python3 scripts/smoke_installed_copy.py` for the clean-copy lifecycle and
`python3 -m unittest discover -s tests` for the complete Python suite. The smoke
starts the copied gateway over stdio and uses local subprocesses only; it does
not invoke an LLM or make network calls.

## Repository traffic — the `metrics` branch

The GitHub Traffic API keeps fourteen days and then the data is gone.
`.github/workflows/traffic-snapshot.yml` runs weekly and on
`workflow_dispatch`, and turns that sliding window into a series.

**The series is not on `main`, and that is the whole design constraint.** This
repository is also the plugin marketplace, so every commit on the default branch
reaches every installed copy at the next `/plugin marketplace update`. Fifty-two
commits a year of analytics inside the product package is bandwidth the founder's
users pay for. The workflow writes to an orphan branch called `metrics`, which
shares no history with `main` and never merges into it. **It creates the branch
itself on the first run**, so there is nothing to set up by hand.

- `metrics/traffic.csv` — one row per day, keyed by date. Reading the same day
  twice updates the row; the API's most recent day is always partial, so today's
  numbers are corrected by tomorrow's run rather than duplicated.
- `metrics/referrers-YYYY-MM-DD.csv`, `metrics/paths-YYYY-MM-DD.csv` — whole
  snapshots. They describe overlapping fourteen-day windows with no way to
  subtract one from another, so they are photographs and not a series.

To read it:

```bash
git fetch origin metrics && git switch metrics
python3 scripts/traffic_report.py metrics/traffic.csv
```

**Report unique cloners, never `count`.** A clone count includes
`actions/checkout` on this repo's own CI and a re-clone from every
`/plugin marketplace update`. The measured case: 2026-08-12 recorded 41 clones
and zero unique views. `automation_suspected` flags exactly that shape — no
unique viewer, more than ten clones — and `traffic_report.py` drops those days
from the trend rather than zeroing them, because zero would claim a quiet day
and the truth is that we do not know. None of these numbers are users. They are
machines that cloned a repository, and some of them are ours.

## Releasing

1. Bump the version in `.claude-plugin/marketplace.json` and both package
   manifests: `founder-os/.claude-plugin/plugin.json` and
   `founder-os/.codex-plugin/plugin.json`.
2. Add a `CHANGELOG.md` entry (SemVer, dated).
3. Run every command from **Before you open a PR**, then run both official local
   Claude gates and the Codex plugin validator below.
4. Tag / publish only after the release plan's remaining gates are complete.
   The repo *is* the marketplace, so a merge to the default branch ships it.

The `solkova-core:release` skill can build a SemVer release from Conventional
Commits if you use it.

## Official Claude validation

Run the installed Claude CLI against both distribution boundaries before a
release:

```bash
claude plugin validate .
claude plugin validate founder-os
```

The marketplace must pass without warnings. The package currently emits one
addressed warning for `founder-os/CLAUDE.md`: plugin roots are not loaded as
project context by Claude, so the `SessionStart` hook injects that canonical
guidance. `tests/test_session_context.py` and the installed-copy smoke pin the
actual delivery path. Any new or different warning blocks the release.

These local official commands are a release gate, not CI coverage. Adding a
pinned Claude CLI package to CI would download and execute an npm dependency;
that requires explicit founder approval before the workflow may change.

Validate the Codex package shape from the plugin-creator tooling Codex installs
in its own home (`$CODEX_HOME`, default `~/.codex`):

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/plugin-creator/scripts/validate_plugin.py" founder-os
```

If that path does not exist, the local Codex install does not ship the
plugin-creator skill; skip this gate rather than substituting another script.

## Dual-host notes

- Claude Code reads `.claude-plugin/plugin.json` + `.mcp.json` + the shared role
  and workflow files.
- Codex reads `.codex-plugin/plugin.json` + `skills/<name>/agents/openai.yaml`;
  the manifest's inline `mcpServers` points at the same Python gateway.
- The `SessionStart` and guard hooks handle both hosts: Claude supplies
  `agent_type` directly; Codex supplies `turn_id`, resolved through
  `record-agent.py`. Named native roles and the generic fallback receive the
  same packaged role bytes and role capability. Keep both manifests' `version`
  in sync.
