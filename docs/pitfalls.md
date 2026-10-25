---
title: "Pitfalls"
status: current
owner: Mateusz Solecki
last-verified: 2026-10-25
---

# Pitfalls

Settings in this repository that look like defects and are deliberate. Each
one is written down in the code it describes; this page collects them so
nobody "fixes" one in passing. Changing one breaks the package or a promise it
makes. Project decisions behind several of them are in
[`decisions.md`](decisions.md).

## The PreToolUse guard runs on every tool (`matcher: ".*"`)

- **Where:** `founder-os/hooks/hooks.json`, `founder-os/hooks/ownership-guard.py`
- **Looks like:** a hook that spawns a Python process on every tool call,
  including tools it has no opinion on.
- **Why it is deliberate:** a known role may hold only the gateway tools and
  `ToolSearch`/`TodoWrite`. The guard denies a role any tool it does not
  recognize ("A role holds only the gateway tools"), so a file tool a host adds
  later is denied instead of waved through. That only works if the guard sees
  every tool. The list matcher it replaced (`^(Read|Write|Edit|…|mcp__.*)$`)
  was widened to `.*` in `90df46d` ("Roles now deny any tool outside the
  gateway and the PreToolUse matcher covers every tool").
- **Breaks if changed:** a narrower matcher lets a role call any tool the list
  forgot, without the guard running at all. `check_hooks` in
  `scripts/validate_package.py` fails the build if the matcher stops covering
  the file, shell, web and `mcp__` tools.

## The guard is silent when it allows

- **Where:** `allow()` in `founder-os/hooks/ownership-guard.py`
- **Looks like:** a guard that never says "allow".
- **Why it is deliberate:** emitting `permissionDecision: "allow"` would bypass
  Claude Code's normal permission system and hand out approvals the founder
  never gave. Exiting 0 with no output means "no opinion", and the usual
  permission flow runs.
- **Breaks if changed:** every tool call the guard has no opinion on would be
  auto-approved.

## The guard fails open on the main thread and closed for a role

- **Where:** `main()` and the `__main__` block of
  `founder-os/hooks/ownership-guard.py`
- **Looks like:** inconsistent error handling — some failures allow, some deny.
- **Why it is deliberate:** the hook runs in every session. Unreadable stdin,
  input that is not JSON or not an object, a call with no subagent identity
  (the founder's own main thread), and an unexpected exception all allow, so a
  hook bug never blocks the founder. Once a call is identified as one of the
  thirteen roles, the posture flips: a present but invalid `agent_type` is
  denied, a tool the guard does not recognize is denied, and a generic agent
  bound to a role whose binding cannot be persisted or read is denied
  (`_bind_generic_role`). The module docstring says it: "defense in depth, not
  a security sandbox".
- **Breaks if changed:** failing closed everywhere blocks the founder on any
  malformed hook input; failing open for roles lets a role reach a shell or a
  file tool. One known gap is tracked in [`backlog.md`](backlog.md): an
  unexpected exception exits 0 even on a role path.

## Missing PyYAML or an unreadable overlay means less coverage, not a deny

- **Where:** `_parse_owns_without_yaml`, `_derived_from_text`,
  `local_ownership` and `_registry_roots` in
  `founder-os/hooks/ownership-guard.py`
- **Looks like:** a guard that quietly guards less when a file is broken.
- **Why it is deliberate:** PyYAML is not in the standard library, so the
  guard carries a minimal parser for the one shape `ownership.yaml` has and
  returns "no map" on anything else rather than guessing. An overlay
  (`_local/ownership.yaml`) or a business registry it cannot read costs
  coverage; a false deny costs the founder a write. The code comments say so
  ("Failing open is a decision; failing open invisibly forever because of an
  import is an accident").
- **Breaks if changed:** a broken overlay or registry would block writes
  machine-wide. The one exception is `derived_files:`: the derived deny still
  runs when `owns:` cannot be parsed.

## A non-role subagent's shell is not inspected

- **Where:** module docstring and `PATH_NAMING_TOOLS` in
  `founder-os/hooks/ownership-guard.py`
- **Looks like:** a hole — a reviewer subagent with `Bash` can write any file
  its own permissions allow.
- **Why it is deliberate:** the ownership checks bind tools that name a path
  (`Write`, `Edit`, `NotebookEdit`). Denying every unrecognized subagent every
  tool "locked reviewers and Explore passes out of unrelated repositories
  machine-wide". Roles are different: they hold no shell at all.
- **Breaks if changed:** every non-Founder-OS subagent on the machine loses
  its tools.

## Cadences run headless with only the gateway tools

- **Where:** `host_argv` in `founder-os/scripts/cadence_manager.py`;
  [`cadences.md`](cadences.md)
- **Looks like:** `--permission-mode dontAsk` reads like "skip every prompt".
- **Why it is deliberate:** the argv is
  `claude -p /founder-os:<workflow> --permission-mode dontAsk --allowedTools 'mcp__plugin_founder-os_founder-os-state__*' --max-turns 50 --no-session-persistence`.
  `dontAsk` with that allowlist means an unattended run can use the local state
  gateway and nothing else: no shell, no web, so an injected instruction cannot
  reach the network. `--no-session-persistence` keeps recurring transcripts out
  of the host's history; the workspace holds the durable record. The cron line
  sets `umask 077`, so logs are readable only by the founder.
- **Breaks if changed:** widening `--allowedTools` gives an unattended run the
  host's whole tool surface. `--max-turns` is accepted by Claude Code 2.1.x but
  missing from its `--help`; dropping it because help does not list it removes
  the 50-turn bound (`founder-os/skills/setup-cadences/SKILL.md`, step 1, warns
  against exactly this).

## Traffic history lives on an orphan `metrics` branch

- **Where:** `.github/workflows/traffic-snapshot.yml`;
  [`development.md`](development.md)
- **Looks like:** analytics data missing from `main`, and a branch with no
  shared history.
- **Why it is deliberate:** this repository is also the plugin marketplace.
  Every commit on `main` reaches every installed copy at the next
  `/plugin marketplace update`, and a weekly analytics commit is bandwidth the
  founder's users pay for. The workflow creates the orphan branch on its first
  run and never merges it.
- **Breaks if changed:** merging `metrics` into `main`, or writing the series
  there, ships analytics inside the product package.

## Count checks skip the landing page

- **Where:** `check_readme_counts` in `scripts/validate_package.py`
- **Looks like:** `docs/index.html` is missing from the pages whose counts are
  checked.
- **Why it is deliberate:** its catalogue carries a per-category "9 workflows"
  on every group heading, which the count patterns cannot tell from a package
  count. `tests/test_docs_workflows.py` holds that page instead.
- **Breaks if changed:** adding it to `_counted_docs` fails the build on
  correct per-category counts.

## A published changelog entry is never rewritten

- **Where:** `RECORDS` in `scripts/bump_version.py`;
  `test_a_published_release_entry_is_never_rewritten` in
  `tests/test_release_metadata.py`
- **Looks like:** stale counts in older `CHANGELOG.md` sections (the 2.9.1
  entry says 21 build-time checks).
- **Why it is deliberate:** a tagged entry is a record of what shipped. The
  moving counts belong to `## Unreleased`, which
  `test_the_topmost_written_entry_carries_the_counts_we_ship_now` checks.
- **Breaks if changed:** an edited release entry describes a package the tag
  does not contain.

## The site has no theme

- **Where:** `theme: null` in `docs/_config.yml`
- **Looks like:** a GitHub Pages site with no theme; the guides are styled by
  `docs/_layouts/default.html` (inline CSS, no script) instead.
- **Why it is deliberate:** the GitHub Pages default theme (primer) loads
  `anchor-js` from `cdnjs.cloudflare.com` on every page, and
  [`trust.md`](trust.md) promises that the site loads no script from another
  origin. Of the other GitHub themes checked, minimal references `html5shiv`
  on cdnjs and cayman loads Google Fonts.
  The own layout carries the same `Content-Security-Policy` as the Trust Center.
- **Breaks if changed:** setting a theme puts a third-party request on every
  guide page and makes the Trust Center's website section false; a script or
  an external font added to the layout does the same.

## `trust.md` is published as `trust-notes.html`

- **Where:** `permalink: /trust-notes.html` in `docs/trust.md`
- **Looks like:** an odd URL for the Trust Center's long form.
- **Why it is deliberate:** Jekyll would render `trust.md` to `trust.html`, the
  path of the hand-written Trust Center, and one would overwrite the other.
- **Breaks if changed:** removing the permalink replaces the Trust Center or
  its notes, depending on build order.

## The link checker accepts `.html` links that are not in the repository

- **Where:** `SITE_SOURCES` and `_site_source` in
  `scripts/check_local_links.py`; tests in `tests/test_local_links.py`
- **Looks like:** an exception in a checker whose job is to find missing
  targets.
- **Why it is deliberate:** the landing page and the Trust Center link to pages
  Jekyll builds (`getting-started.html`, `changelog.html`, …). A missing
  top-level `docs/X.html` resolves to its source `docs/X.md`, and anchors are
  checked against that source. Two pages have a source that is not a
  same-named sibling and are listed by name: `changelog.html` (copied from
  `CHANGELOG.md` by `.github/workflows/pages.yml`) and `trust-notes.html`
  (`docs/trust.md`'s permalink). Nothing else is exempt; a nested or unknown
  `.html` target still fails.
- **Breaks if changed:** removing the rule fails CI on every built-page link;
  widening it to any `.html` hides real missing pages.

## `changelog.html` exists only on the built site

- **Where:** the copy step in `.github/workflows/pages.yml`
- **Looks like:** a footer link to a page that is not in `docs/`.
- **Why it is deliberate:** `CHANGELOG.md` stays at the repository root, where
  release tooling and tests read it, and is copied into the site at build time
  with front matter added. Jekyll renders Liquid in every page with front
  matter, so a Liquid marker (two opening curly braces, or an opening curly
  brace followed by a percent sign) written into `CHANGELOG.md` or a
  `docs/*.md` page is interpreted, not printed. An unterminated one fails the
  site build. This page spells them out in words for that reason.
- **Breaks if changed:** moving the changelog into `docs/` breaks
  `scripts/bump_version.py` and the release tests.

## `robots.txt` sits under `/founder-os/`

- **Where:** `docs/robots.txt`
- **Looks like:** a robots file at a path crawlers do not read; they read only
  `https://msolecki.github.io/robots.txt`.
- **Why it is deliberate:** the site is a project page and cannot publish at
  the host root. The file still names the sitemap for any tool that looks for
  it next to the site.
- **Breaks if changed:** nothing breaks. It is listed so nobody expects it to
  steer crawlers.
