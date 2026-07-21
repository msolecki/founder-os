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
