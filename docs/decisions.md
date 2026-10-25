---
title: "Decisions"
status: current
owner: Mateusz Solecki
last-verified: 2026-10-25
---

# Decisions

The project's decision log: how this repository is built and shipped. It is
not the founder-facing `decision-log` workflow, which writes a business's
`decisions/` folder.

Each entry: date, decision, why, and the commit or file that holds the
evidence. The "why" is quoted or summarized from commit messages, code
comments and `CHANGELOG.md`; where none of them records it, the entry says so.
Never renumber. When a decision is replaced, mark it superseded and add a new
entry. Deliberate settings that follow from these are in
[`pitfalls.md`](pitfalls.md).

## D1. A Claude Code plugin, not a package for another runtime

- **Date:** 2026-07-15 · **Commit:** `2b418f2`
- **Decision:** Founder OS is a Claude Code plugin. The paperclip/companies.sh
  format (`COMPANY.md`, `.paperclip.yaml`, `teams/`, `tasks/`) is removed.
- **Why:** the commit says the earlier target was a misreading of the brief:
  companies.sh was a pattern to model, not a dependency. The skills, house
  rules, ownership map and workspace were runtime-agnostic and carried over.

## D2. Agents get no tool that reaches the outside world

- **Date:** 2026-07-15 · **Commit:** `2b418f2`; today `OUTBOUND_TOOLS` and
  `check_agent_tools` in `scripts/validate_package.py`
- **Decision:** house rule 0 ("never outbound, never money") is enforced as a
  tool allowlist. No agent holds `Bash`, `WebFetch`, `WebSearch` or an outside
  MCP tool, and the build fails if one is added.
- **Why:** "An agent cannot send because it has nothing to send with — the
  rule stopped being a request" (`2b418f2`).

## D3. One owner per file; `ownership.yaml` is the only map

- **Date:** 2026-07-15 (the map is in the first commit, `48543cb`; it became a
  write-time hook in `2b418f2`)
- **Decision:** every workspace file has exactly one owning agent, recorded in
  `founder-os/references/ownership.yaml`. Agents read anything and write only
  what they own. No other file restates the map; where prose and the map
  disagree, the map wins (`founder-os/references/guidance.md`). Counts and
  lists derived from it are checked, not retyped.
- **Why:** the map's own comment block gives the reason for not restating it:
  "A count of a set that grows is a second map with one field in it, and
  second maps go stale silently". The first commit that introduced the map
  records no reason for one owner per file.

## D4. The state gateway is the authoritative write boundary

- **Date:** 2026-07-27 · **Commits:** `da7e0d5`, `9a5b79c`, `48c323a`;
  released in 2.5.0
- **Decision:** role reads and writes go through the local `founder-os-state`
  MCP server: a short-lived role capability, owner-checked, hash-guarded,
  atomic writes that fail closed. The `PreToolUse` hook stays as defense in
  depth.
- **Why:** not stated in the commit messages. The 2.5.0 changelog entry
  describes what it does ("State writes fail closed on unknown identity,
  ownership, path, structure, capability, or current-file hash"), not why a
  hook alone was not enough.

## D5. Roles are siblings; only the main thread orchestrates

- **Date:** 2026-07-28 · **Commit:** `46df6a3`; released in 2.5.0
- **Decision:** a role does not spawn other agents. The main thread invokes
  sibling roles from structured delegation requests and re-reads each
  persisted result before it continues. `check_one_level_orchestration`
  enforces it.
- **Why:** the commit message carries no rationale. The guard's comment on
  `NESTED_AGENT_TOOLS` gives the security reason it is still denied: "a role
  that can spawn a subagent escapes its own lockdown through the child".

## D6. The command catalogue is generated

- **Date:** 2026-07-19 · **Commit:** `7ffb19a` (v2.3.0)
- **Decision:** `founder-os/COMMANDS.md` is generated from the skills'
  frontmatter by `scripts/generate_commands.py`, and CI fails when it is stale.
- **Why:** the commit lists it without a reason; it is the same rule as D3
  applied to the catalogue.

## D7. Per-business extension is an additive local overlay

- **Date:** 2026-07-22 · **Commit:** `50da231`
- **Decision:** a founder adds a file, workflow or role in
  `$FOUNDER_OS_HOME/_local/`. The overlay may add a path and never reassign or
  remove one the package ships. No subagent may write under `_local/`.
- **Why:** "Two capabilities that were previously impossible without forking
  or leaking"; "An agent that can edit the map governing it does not have a
  map" (`50da231`).

## D8. Traffic history lives on an orphan `metrics` branch

- **Date:** 2026-08-25 · **Commit:** `3205088`
- **Decision:** a weekly workflow kept the GitHub Traffic API's fourteen-day
  window as a series on an orphan `metrics` branch that never merged into
  `main`.
- **Why:** the Traffic API discards data after fourteen days. Not on `main`
  because "this repository is also the marketplace, so every commit on the
  default branch reaches every installed copy at the next
  `/plugin marketplace update`".
- **Superseded 2026-10-25:** the workflow and its scripts were removed; the
  Traffic API needs an admin personal access token the founder chose not to
  keep.

## D9. The canonical guidance lives in `references/guidance.md`

- **Date:** 2026-10-16 · **Commit:** `deb6967`; released in 2.9.0
- **Decision:** the always-loaded guidance moved from `founder-os/CLAUDE.md` to
  `founder-os/references/guidance.md`, injected by the `SessionStart` hook.
- **Why:** "a plugin root's `CLAUDE.md` is never loaded as context, and the
  directory validator flags one" (`CHANGELOG.md`, 2.9.0).

## D10. Native Windows is not supported; WSL is

- **Date:** 2026-10-19 · **Commit:** `008c47c`; released in 2.9.1
- **Decision:** the state gateway and the `SessionStart` hook stop on native
  Windows with a pointer to WSL instead of crashing.
- **Why:** "The state gateway needs POSIX file locking and `dir_fd`-relative,
  symlink-safe opens, which native Windows Python does not provide"
  (`CHANGELOG.md`, 2.9.1).

## D11. Codex support is removed; Claude Code is the only host

- **Date:** 2026-10-25 · **Commit:** `cf53504` · **Breaking;** the next release
  is 3.0.0.
- **Decision:** the `.codex-plugin` manifest, the per-skill `agents/openai.yaml`
  adapters, the `record-agent.py` hook, the guard's `turn_id` and `apply_patch`
  paths, the Codex cadence argv and the `$founder-os:` syntax are removed. Codex
  users stay on 2.9.1; the Markdown workspace is unchanged.
- **Why:** not recorded in the commit message or the changelog entry, which
  describe what was removed. Codex support had been added on 2026-07-20
  (`3631f36`) and extended to full parity in 2.5.0.
- **Supersedes:** the Codex host support added in `3631f36`.

## D12. The site is built by GitHub Actions and Jekyll

- **Date:** 2026-10-25
- **Decision:** `.github/workflows/pages.yml` builds `docs/` with
  `actions/jekyll-build-pages` and deploys it with `actions/deploy-pages`.
  `docs/.nojekyll` is removed. The Markdown guides render as pages,
  `CHANGELOG.md` is copied in as `changelog.html`, and `jekyll-sitemap` adds a
  sitemap. The site has no theme; the guides use one inline-styled layout
  with no script (see [`pitfalls.md`](pitfalls.md)). Links from a guide to a
  file outside `docs/` are pointed at GitHub's file view at build time.
- **Why:** documentation and site parity with the developer-os repository,
  whose docs carry the same frontmatter and whose site is deployed by an
  Actions workflow. The landing page used to send readers to GitHub's file view
  for every guide.
- **Supersedes:** legacy Pages serving `main:/docs` as raw files behind
  `docs/.nojekyll`, added 2026-07-21 in `4a1ba55`. That commit records adding
  the file but not why Jekyll was switched off.
- **Needs:** Settings → Pages → Source set to GitHub Actions. Until then the
  legacy branch build keeps serving `main:/docs`, and now that `.nojekyll` is
  gone it runs Jekyll itself, without the changelog copy step.
