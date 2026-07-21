# TODO — Completed audit items

## 2026-07-21 — enforcement test net batch

### [TEST-001] `_registry_roots` no-PyYAML fallback parser is untested
- **File**: `founder-os/hooks/ownership-guard.py:226-239`
- **Severity**: HIGH (P1)
- **Problem**: Only the PyYAML branch of `_registry_roots` is exercised. On a PyYAML-less multi-business machine (the module's own "most of them"), the hand-rolled `home:`/`portfolio:` scanner is what guards the portfolio workspace, and nothing tests it.
- **Evidence**: `TestRegistryRoots` (tests/test_ownership_guard.py:292-379) never sets `yaml=None`.
- **Fix**: Add a test that patches `guard.yaml = None`, points `HOME` at a temp registry with absolute `home:`/`portfolio:` paths, and asserts both roots are returned (matching the PyYAML result).
- **Validation**: `python3 -m unittest tests.test_ownership_guard.TestRegistryRoots -v`
- **Completed**: Added the fallback test; focused suite and full `93`-test suite pass. Commit `c49873d`.

### [TEST-002] `load_ownership()` PyYAML-missing integration path is untested
- **File**: `founder-os/hooks/ownership-guard.py:186-192`
- **Severity**: HIGH (P1)
- **Problem**: `_parse_owns_without_yaml` is unit-tested directly, but nothing confirms `load_ownership()` routes to it when `yaml is None` and produces the same `by_path` map as the PyYAML branch — the integration the fallback exists for.
- **Evidence**: `TestFallbackParser` (tests/test_ownership_guard.py:271-289) calls the parser, never `load_ownership`.
- **Fix**: Patch `guard.yaml = None`, call `load_ownership()`, and assert it equals the `{path: agent}` map derived from PyYAML on the real `ownership.yaml`.
- **Validation**: `python3 -m unittest tests.test_ownership_guard.TestFallbackParser -v`
- **Completed**: Added the integration test and lazy-loader seam; focused suite and full `93`-test suite pass. Commit `c49873d`.

### [TEST-003] `run_checks` per-check exception containment is untested
- **File**: `scripts/validate_package.py:462-467`
- **Severity**: HIGH (P1)
- **Problem**: The inner per-check `try/except` (stops a bad `ownership.yaml` from killing every later check) is never triggered; only the outer `load_agents` failure is tested.
- **Evidence**: `TestRunChecksContainment` (tests/test_validate_package.py:557-576) only tests a malformed agent file.
- **Fix**: Write a malformed `ownership.yaml` and assert the errors contain `"check_ownership' aborted at first bad file"` while other checks still ran.
- **Validation**: `python3 -m unittest tests.test_validate_package.TestRunChecksContainment -v`
- **Completed**: Added malformed-ownership containment coverage; validator-focused tests and full `93`-test suite pass. Commit `76bf04e`.

### [TEST-004] `check_agent_tools` never tests WebSearch / NotebookEdit / Task
- **File**: `scripts/validate_package.py:30,118-121`
- **Severity**: HIGH (P1)
- **Problem**: The build-time `OUTBOUND_TOOLS` is deliberately wider than the runtime hook's (`{Bash, WebFetch, WebSearch, NotebookEdit, Task}`). Tests only assert Bash/WebFetch, so dropping the other three — loosening house rule 0 enforcement — passes every test.
- **Evidence**: `TestAgentTools` asserts only Bash and WebFetch.
- **Fix**: Parametrize the outbound test over `WebSearch`, `NotebookEdit`, `Task` and assert each is caught as "outside world".
- **Validation**: `python3 -m unittest tests.test_validate_package.TestAgentTools -v`
- **Completed**: Added subtests for all three tools; validator-focused tests and full `93`-test suite pass. Commit `76bf04e`.

### [PERF-001] `import yaml` runs on every tool call, including the main-thread majority
- **File**: `founder-os/hooks/ownership-guard.py:60-63`
- **Severity**: HIGH (P1)
- **Problem**: PyYAML (a heavy pure-Python package) is imported at module top on every invocation, but the dominant paths — main-thread calls (exit at :462-464) and outbound denials (:480) — never parse YAML. The founder pays the import on every tool call.
- **Evidence**: top-level `try: import yaml except ImportError: yaml = None`.
- **Fix**: Defer the import into `load_ownership` and `_registry_roots` via a memoized `_get_yaml()` sentinel; keep every `if yaml is not None` branch. Fail-open semantics unchanged.
- **Validation**: `python3 -X importtime ... < main_thread_payload.json | grep -c yaml` → 0 for main-thread/outbound; `python3 -m unittest tests.test_ownership_guard` stays green.
- **Completed**: Added memoized lazy import; importtime output contained no `yaml` module and full `93`-test suite passed. Commit `c49873d`.

## 2026-07-21 — platform and launch readiness batch

### [ARCH-001] Hidden, unpinned `node` dependency for the test suite
- **Completed**: CI now pins Node 20, getting-started documents the development dependency, and the behavior test skips cleanly when Node is absent. Full suite passed with 94 tests.

### [A11Y-001] No Open Graph / Twitter Card / canonical meta on a launch page
- **Completed**: Added OG/Twitter/canonical metadata and a 1200×630 `og-image.svg`, plus a metadata contract test. Full suite passed with 94 tests.

## 2026-07-21 — hook coverage batch

### [TEST-005] Symlink / `..` resolution in `relative_to_workspace` is untested
- **Completed**: Added an end-to-end symlink fixture proving an outside link to an owned file is denied to the wrong agent. Full suite passed with 95 tests.

### [BUG-001] `check_hooks` never asserts the matcher covers `apply_patch`
- **Completed**: Validator coverage now includes `apply_patch`; fixture and regression test pin the matcher contract. Full suite passed with 95 tests.

## 2026-07-21 — ownership hot-path batch

### [PERF-002] `workspace_roots()` + registry read + all `realpath`s recomputed per path
- **Completed**: `check_ownership` computes roots once per invocation and reuses them for each touched path; a multi-path call-count test pins the optimization. Full suite passed with 97 tests.

### [BUG-002] Fallback `owns:` parser rejects valid same-indent YAML list style
- **Completed**: Fallback accepts same-indent sequences and has a focused parser contract test. Full suite passed with 97 tests.

## 2026-07-21 — parser portability batch

### [BUG-003] `parse_frontmatter` hardcodes `\n`, so a CRLF checkout breaks all validation & generation
- **Completed**: Central parser normalizes CRLF before parsing; a CRLF fixture test passes in the full 98-test suite.

### [ARCH-002] `SYSTEM_SKILLS` / `STANDALONE_SKILLS` / `parse_frontmatter` copy-pasted across both scripts
- **Completed**: Shared `scripts/_package.py` now owns the constants and parser; both scripts import it and command generation remains current.

## 2026-07-21 — generator robustness batch

### [BUG-004] `generate_commands.load` tracebacks when `skills/` is absent
- **Completed**: Missing `skills/` now produces a clean `FAIL:` with exit 1; regression test passes. Full suite reached 99 tests.

## 2026-07-21 — documentation drift batch

### [ARCH-003] Hardcoded "13 / 49 / 10" counts drift across docs & the Codex manifest
- **Completed**: `check_readme_counts` now scans the documentation surfaces and Codex long description; a stale docs fixture fails validation. Full suite passed with 100 tests.

## 2026-07-21 — manifest parity batch

### [ARCH-004] Claude and Codex plugin manifests disagree, and nothing validates agreement
- **Completed**: Claude and Codex identity fields are synchronized; `check_plugin` now rejects name/version/description drift. Full suite passed with 101 tests.
