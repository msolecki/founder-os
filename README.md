# Founder OS

A [Claude Code](https://code.claude.com/docs) plugin that gives a company of one an executive
team: **12 agents, 48 skills, 9 scheduled cadences** — strategy, offer, pipeline,
delivery, money and focus, with a markdown workspace as shared state and a
write-time ownership guard keeping twelve agents from corrupting it.

This repository is both the **plugin marketplace** (install straight from it)
and the **source repo** (validator, tests, design docs).

> Product philosophy, the org chart, and what the plugin refuses to do:
> [`founder-os/README.md`](founder-os/README.md). This file covers how the
> machine works and how to develop against it.

## Install

In Claude Code:

```
/plugin marketplace add msolecki/founder-os
/plugin install founder-os@founder-os
```

Then, once:

```
/founder-os-init      # ~20 min onboarding, ends with your first brief
/setup-cadences       # optional: cron entries so it runs without being asked
```

Requirements: a recent Claude Code; `python3` with PyYAML for the ownership
hook (the hook degrades gracefully without PyYAML — see below); `cron` only if
you schedule the cadences.

## How it works

### The moving parts

| Piece | Where | What it does |
|---|---|---|
| Agents | `founder-os/agents/*.md` | 12 role definitions. Frontmatter: `name`, `description`, `skills[]`, `tools:` allowlist (+ `Agent(...)` edges for managers). Body: four mandated headings. |
| Skills | `founder-os/skills/*/SKILL.md` | 48 procedures. Role skills follow `references/skill-template.md` exactly; each declares its writes in `metadata.writes`. |
| Ownership map | `founder-os/references/ownership.yaml` | The single source of truth: `workspace_files:` (what init scaffolds), `owns:` (one owner per file), `sections:` (the headings each file may contain). |
| Write-time guard | `founder-os/hooks/ownership-guard.py` | A `PreToolUse` hook. Denies a subagent writing a file it doesn't own, and denies subagents any outbound-capable tool (`Bash`, `WebFetch`, `mcp__*`). Fails **open**, main thread always allowed. |
| Validator | `scripts/validate_package.py` | 14 build-time checks (below). CI runs it on every push. |
| Cadences | `founder-os/skills/setup-cadences/SKILL.md` | 9 cron lines on *your* machine calling skills headless — a plugin cannot ship a schedule, so this writes one, with your consent, once. |

### The contract, in one paragraph

Every workspace file has exactly one owning agent (`owns:`); every skill
declares which paths it writes (`metadata.writes`), and the validator fails the
build if a skill writes a path its agent doesn't own. What's *inside* a file is
pinned too: `sections:` lists the allowed `##` headings per path, init
scaffolds exactly those, and `founder-os-doctor` reports drift in a live
workspace. Claims entering the workspace are tiered (FACT / VALIDATE /
DISREGARD, `references/ingestion-gate.md`) and stamped with provenance inline;
entities shared across files are `[[slug]]` links (`references/linking.md`),
so `Acme` and `Acme Corp` can never silently become two companies. The seven
house rules (`references/house-rules.md`) sit above all of it — rule 0: **no
agent ever sends or pays anything**; agents draft, the founder presses the
button.

### Enforcement is layered, deliberately

1. **Build time** — `scripts/validate_package.py`: plugin manifest; agent
   frontmatter, headings, tool allowlists (nothing outbound), `Agent()` graph
   sanity; role-skill exclusivity; no orphan skills; ownership map coherence in
   both directions; skill-writes vs ownership join; sections coverage; ≥3
   beliefs per role skill placed before steps; hooks load and cover the right
   tools; README counts match the package.
2. **Write time** — `hooks/ownership-guard.py`, scoped to subagents only.
   **Not a security boundary** (the file says so at length): it's operational
   policy behind the real boundary, which is each agent's `tools:` allowlist.
   Unknown states fail open and log to stderr — a guard that denies because it
   lost its own config protects nobody after the uninstall.
3. **Run time, weeks later** — `founder-os-doctor`: 13 checks against a real
   workspace (missing files, section drift, stale metrics, broken links,
   undrained inbox, rotting queue, briefs nobody acts on, …).

## Repository layout

```
.claude-plugin/marketplace.json   # this repo *is* the marketplace
founder-os/                       # the plugin (what gets installed)
  .claude-plugin/plugin.json
  CLAUDE.md                       # loaded into every session; the never-miss rules
  README.md                       # the product: org, philosophy, refusals
  agents/           (12)
  skills/           (48)
  hooks/                          # hooks.json + ownership-guard.py
  references/                     # ownership.yaml, house-rules, skill-template,
                                  # ingestion-gate, linking
  images/                         # org chart (mermaid + png)
scripts/validate_package.py       # build-time validator (14 checks)
tests/                            # 75 tests: validator mutations + hook subprocess
docs/superpowers/                 # design specs and implementation plans (v2.1, v2.2)
founder-os-review.md              # full project audit, 2026-07-18
```

## Development

```bash
pip install pyyaml
python3 scripts/validate_package.py founder-os   # expect: 12 agent(s), 48 skill(s), 0 error(s)
python3 -m unittest discover -s tests            # expect: 75 tests, OK
```

CI (`.github/workflows/ci.yml`) runs both on every push and PR.

### Adding a skill

1. Copy the shape from `references/skill-template.md` — headings are not
   suggestions, the validator reads the frontmatter.
2. Declare every path you write in `metadata.writes`, spelled **verbatim** from
   `ownership.yaml` `owns:` — and make sure the agent whose `skills[]` will
   list your skill owns those paths.
3. New file or heading? Add it to `workspace_files:`/`owns:`/`sections:` in the
   same change — init scaffolds from the map, and a heading the map doesn't
   declare is drift the doctor will report on someone's real workspace.
4. Write `## Beliefs`: at least 3 principles a competent generic advisor would
   *not* say. The count and placement are machine-checked; the bar is held by
   review.
5. Run the validator and the tests.

### Adding an agent

One agent = one decision no other agent can make — that's the test every
existing agent had to pass. Explicit `tools:` allowlist (never omit it: omitting
inherits everything, including Bash), the four mandated headings, the three
universal skills (`guardrails`, `state-integrity`, `ingestion-gate`), and an
entry in `ownership.yaml` if it owns anything. Owning nothing must be a
decision, not an omission — the board-member is the worked example.

## Porting the pattern

The ownership map + write-time hook + build validator are domain-agnostic:
`ownership-guard.py` enforces *any* `owns:` map over *any* workspace directory,
and the validator's core checks (frontmatter, allowlists, ownership joins,
sections) carry over with renames. What you rewrite is the map and the agent
content — that's the product. One caveat for code repos: the outbound guard
denies subagents `Bash`, which engineering subagents need; scope
`check_outbound` to mapped agents, or drop it and keep the ownership half.

## License

MIT — see [`founder-os/LICENSE`](founder-os/LICENSE).
