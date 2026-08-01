# Founder OS

<a href="https://www.producthunt.com/products/founder-os?embed=true&amp;utm_source=badge-featured&amp;utm_medium=badge&amp;utm_campaign=badge-founder-os" target="_blank" rel="noopener noreferrer"><img alt="Founder OS - Know what matters today — before opening your inbox | Product Hunt" width="250" height="54" src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1202964&amp;theme=light&amp;t=1784745192561"></a>

## Know what matters today

Founder OS is for a solo service founder already using Claude Code or Codex.
When company decisions disappear into chats and disconnected notes, it turns
current business state into one source-linked decision, saves it to local
Markdown, and produces a valid first brief in less than fifteen minutes.

Start with the situation, not the command list: say **“I do not know what
matters today”** or run `/situation-review`. The Chief of Staff selects one
owner, one workflow, and the state destination. It previews that route and its
missing state first; the specialist starts only after you choose **Continue**,
while **Stop** ends without running it. Founder OS never sends, pays, signs,
cancels, or publishes; the founder remains the CEO.

**Local Markdown · No automatic sending · Explicit ownership · No hidden
actions**

It is a plugin for [Claude Code](https://code.claude.com/docs) and
[Codex](https://developers.openai.com/codex/plugins/build) for a company of one
— or a founder running several. Behind the daily decision are **13 agents, 53
skills, 10 scheduled cadences** and one Markdown workspace per business. The
roles own separate decisions; a local state gateway keeps their state from
silently crossing those boundaries on either host.

**Free and MIT-licensed.** Founder OS runs inside your existing Claude Code or
Codex environment and adds no account or subscription of its own.

[Getting started](docs/getting-started.md) ·
[Example workspace](examples/studio-north/README.md) ·
[All 53 workflows](founder-os/COMMANDS.md) ·
[Product philosophy](founder-os/README.md)

This repository is both the **plugin marketplace** (install straight from it)
and the **source repo** (validator, tests, design docs).

> Product philosophy, the org chart, and what the plugin refuses to do:
> [`founder-os/README.md`](founder-os/README.md). This file covers how the
> machine works and how to develop against it.

## Install

Before installing:

| Requirement | Purpose |
|---|---|
| Recent [Claude Code](https://code.claude.com/docs) or [Codex](https://developers.openai.com/codex/plugins/build) | Founder OS is a plugin, not a standalone app. |
| Python 3.9+ | Runs the local state gateway and host hooks. |
| PyYAML *(development only)* | Runs the full package validator; installed runtime parsers remain dependency-light. |
| A user scheduler *(optional)* | `launchd`, user `systemd`, or cron runs cadences. Manual workflows need none. |

The 13 agents are specialized roles invoked when needed, not 13 autonomous
processes running all day. Founder OS knows only what is recorded in its local
Markdown workspace or supplied in the current session; it does not
automatically sync a calendar, CRM, inbox, or bank account. Workspace files stay
on your machine. Prompts and context sent through Claude Code or Codex remain
governed by that environment's data-handling terms.

In Claude Code:

```
/plugin marketplace add msolecki/founder-os
/plugin install founder-os@founder-os
```

In Codex:

```
codex plugin marketplace add msolecki/founder-os
codex plugin add founder-os@founder-os
```

Then run the two workflows once. Claude Code uses namespaced slash commands:

```
/founder-os:founder-os-init      # one resumable flow to a persisted first brief
/founder-os:setup-cadences       # optional local scheduling
```

Codex invokes the same skills with dollar syntax:

```
$founder-os:founder-os-init
$founder-os:setup-cadences
```

The flow targets a ten-minute median and stops at fifteen minutes. Activation
means a valid `reviews/daily/YYYY-MM-DD.md`, not an installed plugin or an empty
folder. A valid brief has all four required headings from `ownership.yaml` —
`## The one thing`, `## Rotting`, `## The trade`, and `## Triage` — with
non-empty `## The one thing` and `## The trade`. If onboarding stops, repeat
the host-specific init command above; it preserves populated sections and
resumes from the first missing owner output.

After preflight, onboarding asks the optional **“What made you install Founder
OS today?”** and records a supplied answer as founder-stated context, not
business evidence. Its validated receipt reads **You came with:**, **Your first
decision:**, **Based on:**, **Saved to:**, **Founder OS will remember:**, and
**Recommended next move:**. Only after activation, `/situation-review` may
preview the owner, workflow, required state, and expected persistence for that
reason. You choose **Continue** or **Stop**; the specialist workflow runs only
after **Continue**. At the fifteen-minute hard stop, the flow prints a copyable
command instead of opening another role session.

Cron jobs run only while that machine and cron are running; launchd and
persistent user systemd timers catch up after sleep.
See the complete
[`docs/getting-started.md`](docs/getting-started.md) guide before installing if
you want the requirements, data boundary, and first-week workflow in one place.

To see the output first, open the fictional but contract-shaped
[`daily brief`](examples/studio-north/reviews/daily/2026-07-20.md), then follow
`q-0720a` through the complete
[`examples/studio-north/`](examples/studio-north/README.md) workspace into the
queue, quarterly bet, week, and review.

## What every completed workflow shows

Founder OS ends each successful workflow with one receipt:

- **Decision:** the verdict or result.
- **Evidence:** workspace paths and source dates used.
- **Changed:** only paths re-read and verified after the role returned.
- **Gaps:** missing or stale state that constrained the answer, or `none`.
- **Returns:** the cadence or date that revisits the decision, or `none`.
- **Your move:** exactly one human action, or `none`.

A read-only workflow reports **Changed:** `none`. A failed or uncertain write
produces an error receipt, never a success claim. Freshness is explicit:
`current` and `stale` require a named workflow or doctor threshold; `unknown`
means a required value is absent. When no threshold exists, the receipt shows
the source date without inventing a freshness label.

## Your first five actions

1. Run `/daily-brief` before opening email.
2. Run `/capture Call Anna about the Acme scope` to save one unclassified line.
3. Run `/pipeline-review` so each deal has a dated next move.
4. Run `/weekly-review` before Friday's memory becomes the record.
5. Ask the **Chief of Staff** to route an uncategorized decision.

## Update, repair, or uninstall

Update with `/plugin marketplace update founder-os`, then
`/plugin update founder-os@founder-os` and `/reload-plugins`. Diagnose a live
workspace with `/founder-os-doctor`; it reports before proposing repairs.
For Codex, refresh with `codex plugin marketplace upgrade founder-os`, replace
the cached install with `codex plugin remove founder-os@founder-os` followed by
`codex plugin add founder-os@founder-os`, then start a new conversation.
Uninstall with the host's corresponding `plugin uninstall`/`plugin remove`
command. Your Markdown workspace is separate from the plugin and remains yours.
The full recovery branches are in
[`docs/getting-started.md`](docs/getting-started.md#update-repair-or-uninstall).

## How it works

### The moving parts

| Piece | Where | What it does |
|---|---|---|
| Agents | `founder-os/agents/*.md` | 13 role definitions. Every role exposes the same bounded state-gateway tool surface and four mandated headings. |
| Skills | `founder-os/skills/*/SKILL.md` | 53 procedures. Role skills follow `references/skill-template.md` exactly; each declares its writes in `metadata.writes`. |
| Ownership map | `founder-os/references/ownership.yaml` | The single source of truth: `workspace_files:` (what init scaffolds), `owns:` (one owner per file), `sections:` (the headings each file may contain). |
| State gateway | `founder-os/mcp/` | The local `founder-os-state` stdio server. A role capability binds one role, workspace, workflow, and run; reads are bounded and writes are owner-checked, hash-guarded, structure-validated, atomic, and fail closed. |
| Host guard | `founder-os/hooks/ownership-guard.py` | Defense in depth. Maps Claude `agent_type` or Codex `turn_id`, denies role direct-file/outbound access and unknown MCP, and permits only capability-consistent calls to the local gateway. |
| Validator | `scripts/validate_package.py` | 17 build-time checks (below). CI runs it on every push. |
| Cadences | `founder-os/scripts/cadence_manager.py` | Previews, snapshots, and safely applies nine jobs per business plus one conditional portfolio job through cron, launchd, or persistent user systemd. Exact identities prevent sibling schedules from being overwritten. |
| Local overlay | `founder-os/references/extensibility.md` | Per-business extension without a fork: `$FOUNDER_OS_HOME/_local/` may **add** a file, skill or agent and can never reassign or remove one the package ships. Merged into the guard's map per workspace; validated by `founder-os-doctor`, because a build-time validator cannot see a stranger's workspace. Forged by `/skill-forge`, whose commonest correct answer is "a packaged agent already owns this decision". |
| Multi-business | `founder-os/references/multi-business.md` | One workspace per business + a registry (`~/.founder-os/businesses.yaml`) + a portfolio workspace. The hook resolves all registered roots; `context-load` step 0 picks the business before any file opens. |
| Commands doc | `founder-os/COMMANDS.md` | Generated by `scripts/generate_commands.py` from the skills' own frontmatter — the user-facing catalogue, machine-derived so it cannot drift. CI fails if it is stale. |

### The contract, in one paragraph

Every workspace file has exactly one owning agent (`owns:`); every skill
declares which paths it writes (`metadata.writes`), and the validator fails the
build if a skill writes a path its agent doesn't own. At run time, that owner
uses a role capability to read through and persist through `founder-os-state`;
the main thread orchestrates sibling roles but never substitutes its own write.
What's *inside* a file is pinned too: `sections:` lists the allowed `##`
headings per path, init scaffolds exactly those, and `founder-os-doctor` reports drift in a live
workspace. Claims entering the workspace are tiered (FACT / VALIDATE /
DISREGARD, `references/ingestion-gate.md`) and stamped with provenance inline;
entities shared across files are `[[slug]]` links (`references/linking.md`),
so `Acme` and `Acme Corp` can never silently become two companies. The seven
house rules (`references/house-rules.md`) sit above all of it — rule 0: **no
agent ever sends or pays anything**; agents draft, the founder presses the
button.

### Enforcement is layered, deliberately

1. **Build time** — `scripts/validate_package.py`: 17 build-time checks cover
   both manifests/adapters, strict frontmatter and tools, one-level sibling
   orchestration, ownership/section joins, beliefs, hooks, and public counts.
2. **State access** — the local `founder-os-state` gateway is the authoritative
   write boundary. Role reads require a live role capability; write uncertainty
   fails closed with one of seven stable error codes, and successful writes use
   optimistic SHA-256 checks plus atomic replacement.
3. **Host tool time** — `hooks/ownership-guard.py` is defense in depth, not a
   security sandbox. A known role cannot use direct file tools, shell, web, an
   unknown MCP server, or a capability belonging to another role. Malformed
   non-role hook traffic does not grant role state authority.
4. **Run time, weeks later** — `founder-os-doctor`: 20 checks against a real
   workspace (missing files, section drift, stale metrics, broken links,
   undrained inbox, rotting queue, briefs nobody acts on, …).

## Repository layout

```
.claude-plugin/marketplace.json   # this repo *is* the marketplace
docs/index.html                   # GitHub Pages marketing landing page
docs/README.md                    # documentation hub for the complete docs set
docs/getting-started.md           # external-user requirements and first run
examples/studio-north/            # fictional, contract-shaped workspace tour
founder-os/                       # the plugin (what gets installed)
  .claude-plugin/plugin.json
  CLAUDE.md                       # loaded into every session; the never-miss rules
  README.md                       # the product: org, philosophy, refusals
  COMMANDS.md                     # generated catalogue: every command, owner, schedule
  agents/           (13)
  skills/           (53)
  mcp/                            # one eight-tool local state gateway
  scripts/cadence_manager.py      # safe scheduler preview/snapshot/apply
  hooks/                          # hooks.json + ownership-guard.py
  references/                     # ownership.yaml, house-rules, skill-template,
                                  # ingestion-gate, linking, multi-business
  images/                         # org chart (mermaid + png)
scripts/validate_package.py       # build-time validator (17 checks)
scripts/generate_commands.py      # derives COMMANDS.md from the package; CI checks it
tests/                            # validator mutations + hook subprocess + registry roots
CHANGELOG.md                      # what shipped in each version
```

GitHub Pages serves `docs/index.html` as the public landing page. The remaining
Markdown files under `docs/` are the linked documentation hub and are not a
second landing-page index.

## Development

```bash
pip install pyyaml
python3 scripts/validate_package.py founder-os   # expect: 13 agent(s), 53 skill(s), 0 error(s)
python3 scripts/generate_commands.py founder-os  # regenerate COMMANDS.md (CI checks it)
python3 scripts/smoke_installed_copy.py          # clean installed-copy lifecycle
python3 -m unittest discover -s tests            # expect: OK
node --test tests/*.behavior.test.js              # landing behavior
python3 scripts/check_local_links.py              # docs files + anchors
```

CI (`.github/workflows/ci.yml`) runs all six on every push and PR.

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
existing agent had to pass. The exact role-callable `founder-os-state` allowlist,
the shared sibling/delegation contract, the four mandated headings, the three
universal skills (`guardrails`, `state-integrity`, `ingestion-gate`), and an
entry in `ownership.yaml` if it owns anything. Owning nothing must be a
decision, not an omission — the board-member is the worked example.

## Porting the pattern

The ownership map + local state gateway + host guard + build validator are
domain-agnostic: the gateway enforces any `owns:`/`sections:` map over a bounded
workspace, and the validator's core checks (frontmatter, capability allowlists,
ownership joins, sections) carry over with renames. What you rewrite is the map
and the agent content — that's the product. A code-repository port would need a
different bounded tool contract; Founder OS intentionally exposes no shell
proxy or arbitrary filesystem browser to roles.

## Contributing & history

[`CONTRIBUTING.md`](CONTRIBUTING.md) is the short version; the sections above
are the long one. [`CHANGELOG.md`](CHANGELOG.md) records what shipped in each
version.

## License

MIT — see [`LICENSE`](LICENSE).
