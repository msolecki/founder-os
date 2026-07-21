# Enforcement Test Net Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the five-item P1 batch `TEST-001`, `TEST-002`, `TEST-003`, `TEST-004`, and `PERF-001` without changing Founder OS enforcement semantics.

**Architecture:** Keep the runtime guard fail-open while replacing its eager PyYAML import with one memoized lazy-loader seam that remains patchable as `guard.yaml = None`. Add contract tests around both no-PyYAML paths and around the validator's existing exception containment and outbound-tool set; test-only changes use mutation checks to prove they detect regressions.

**Tech Stack:** Python 3.9+, stdlib `unittest`, PyYAML, project scripts under `scripts/`.

## Global Constraints

- Work directly on `main`; the user explicitly selected this option on 2026-07-21.
- Preserve the guard's documented fail-open posture, main-thread-always-allowed behavior, and outbound-tool behavior.
- Preserve the intentional `OUTBOUND_TOOLS` divergence between `founder-os/hooks/ownership-guard.py` and `scripts/validate_package.py`.
- Do not add dependencies; this package remains Python stdlib + PyYAML, with no npm/package.json.
- Every production-code change follows RED → GREEN; test-only coverage tasks require a temporary mutation that makes the new test fail, followed by restoration and a passing run.
- Do not modify authentication or middleware.
- Do not edit `feature_list.json` except changing the matching five `passes` values from `false` to `true`, and only after their listed end-to-end checks pass.
- Use the commands documented in `TODO.md`: `python3 scripts/validate_package.py founder-os`, `python3 scripts/generate_commands.py founder-os --check`, and `python3 -m unittest discover -s tests`; task-scoped unittests and `python3 -m py_compile` are the Implementator quick checks.

---

### Task 1: Lazy PyYAML loading and no-PyYAML guard coverage (`PERF-001`, `TEST-001`, `TEST-002`)

**Files:**
- Modify: `founder-os/hooks/ownership-guard.py:55-63,159-240`
- Modify: `tests/test_ownership_guard.py:271-379`

**Interfaces:**
- Consumes: the module-level `yaml` seam, `load_ownership()`, `_registry_roots()`, `workspace_roots(hook_cwd)`, and the real `founder-os/references/ownership.yaml`.
- Produces: `_get_yaml()` returning the memoized PyYAML module or `None`; loading the guard module performs no `yaml` import; tests can force fallback behavior with `mock.patch.object(guard, "yaml", None)`.

- [x] **Step 1: Write the failing lazy-import test**

Add `import builtins` and `from unittest import mock` at module scope in `tests/test_ownership_guard.py`, then add:

```python
class TestLazyYamlImport(unittest.TestCase):
    def test_loading_guard_does_not_import_yaml(self):
        imported = []
        real_import = builtins.__import__

        def tracked_import(name, *args, **kwargs):
            if name == "yaml" or name.startswith("yaml."):
                imported.append(name)
            return real_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=tracked_import):
            load_guard()

        self.assertEqual(imported, [])
```

- [x] **Step 2: Run the lazy-import test and verify RED**

Run: `python3 -m unittest tests.test_ownership_guard.TestLazyYamlImport -v`

Expected: FAIL because importing `ownership-guard.py` currently imports `yaml` immediately.

- [x] **Step 3: Implement the memoized lazy loader**

Replace the top-level `try: import yaml` block in `founder-os/hooks/ownership-guard.py` with:

```python
_YAML_UNSET = object()
yaml = _YAML_UNSET


def _get_yaml():
    """Import PyYAML only on paths that need to parse YAML."""
    global yaml
    if yaml is _YAML_UNSET:
        try:
            import yaml as yaml_module
        except ImportError:  # PyYAML is optional on strangers' machines.
            yaml_module = None
        yaml = yaml_module
    return yaml
```

At the start of each YAML-using parse block in `load_ownership()` and `_registry_roots()`, bind `yaml_module = _get_yaml()`. Replace `yaml.safe_load`, `yaml.YAMLError`, and `if yaml is not None` with their `yaml_module` equivalents. Do not call `_get_yaml()` from `main()` before the main-thread and outbound early exits.

- [x] **Step 4: Run the lazy-import test and guard suite and verify GREEN**

Run: `python3 -m unittest tests.test_ownership_guard.TestLazyYamlImport -v`

Expected: PASS.

Run: `python3 -m unittest tests.test_ownership_guard -v`

Expected: PASS with no changed allow/deny decisions.

- [x] **Step 5: Add the no-PyYAML registry fallback test**

In `TestRegistryRoots`, add a test using `_home_with_registry` and absolute temporary paths:

```python
def test_registry_roots_without_pyyaml_match_yaml_result(self):
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        acme = tmp / "acme" / "founder-os"
        portfolio = tmp / "portfolio"
        acme.mkdir(parents=True)
        portfolio.mkdir(parents=True)
        home = self._home_with_registry(tmp, (
            "businesses:\n"
            "  acme:\n"
            "    home: %s\n"
            "portfolio: %s\n" % (acme, portfolio)))
        guard = load_guard()
        with mock.patch.object(guard, "yaml", None), \
                mock.patch.dict(os.environ, {"HOME": str(home)}):
            roots = guard._registry_roots()
        self.assertEqual(roots, [str(acme), str(portfolio)])
```

- [x] **Step 6: Add the no-PyYAML `load_ownership()` integration test**

In `TestFallbackParser`, add:

```python
def test_load_ownership_without_pyyaml_matches_pyyaml_map(self):
    import yaml
    owns = yaml.safe_load(self.text)["owns"]
    expected = {
        path.strip(): agent
        for agent, paths in owns.items()
        for path in paths
        if isinstance(path, str) and path.strip()
    }
    with mock.patch.object(self.guard, "yaml", None):
        got = self.guard.load_ownership()
    self.assertEqual(got, expected)
```

- [x] **Step 7: Prove the fallback tests detect regressions**

Temporarily change the `yaml_module is None` branch of `_registry_roots()` to `return []`, run:

`python3 -m unittest tests.test_ownership_guard.TestRegistryRoots.test_registry_roots_without_pyyaml_match_yaml_result -v`

Expected: FAIL because both roots are missing. Restore the production code immediately.

Temporarily change the `yaml_module is None` branch of `load_ownership()` to `owns = None`, run:

`python3 -m unittest tests.test_ownership_guard.TestFallbackParser.test_load_ownership_without_pyyaml_matches_pyyaml_map -v`

Expected: FAIL because the fallback map is missing. Restore the production code immediately.

- [x] **Step 8: Run the task checks**

Run: `python3 -m unittest tests.test_ownership_guard.TestLazyYamlImport tests.test_ownership_guard.TestRegistryRoots tests.test_ownership_guard.TestFallbackParser -v`

Expected: all tests PASS.

Run: `python3 -m py_compile founder-os/hooks/ownership-guard.py tests/test_ownership_guard.py`

Expected: exit 0.

- [x] **Step 9: Commit Task 1 files only**

```bash
git add founder-os/hooks/ownership-guard.py tests/test_ownership_guard.py
git commit -m "perf(hooks): defer PyYAML import and test fallbacks [PERF-001, TEST-001, TEST-002]"
```

**Task 1 evidence (2026-07-21):** lazy-import RED observed `yaml` and `yaml._yaml`; GREEN passed. Both fallback tests failed under their specified temporary mutations and passed after restoration. Focused checks passed 8/8, the subsequent full batch suite passed 93/93, validator reported 13 agents / 49 skills / 0 errors, generator was current, and fresh review approved the task without findings. Commit: `c49873d`.

---

### Task 2: Validator enforcement coverage (`TEST-003`, `TEST-004`)

**Files:**
- Modify: `tests/test_validate_package.py:220-258,557-577`

**Interfaces:**
- Consumes: `validate_package.OUTBOUND_TOOLS`, `check_agent_tools(root, agents)`, `run_checks(root)`, and the real `check_ownership`/`check_hooks` entries in `CHECKS`.
- Produces: one subtest per `WebSearch`, `NotebookEdit`, and `Task`; one integration test proving malformed ownership aborts its check while a later hook check still reports its own error.

- [x] **Step 1: Add the three outbound-tool contract cases**

In `TestAgentTools`, add:

```python
def test_additional_outbound_tools_are_caught(self):
    for tool in ("WebSearch", "NotebookEdit", "Task"):
        with self.subTest(tool=tool):
            self.write_agent("cfo", skills=list(UNIVERSALS),
                             tools=DEFAULT_TOOLS + ", " + tool)
            self.assertIn(
                "agents/cfo.md: tool '%s' can reach the outside world — "
                "house rule 0 says agents draft and the founder sends" % tool,
                self.check(V.check_agent_tools))
```

- [x] **Step 2: Mutation-check the outbound-tool cases**

Temporarily remove `WebSearch`, `NotebookEdit`, and `Task` from `scripts/validate_package.py::OUTBOUND_TOOLS`, then run:

`python3 -m unittest tests.test_validate_package.TestAgentTools.test_additional_outbound_tools_are_caught -v`

Expected: FAIL for all three subtests. Restore `OUTBOUND_TOOLS` immediately and rerun the command; expected PASS.

- [x] **Step 3: Add the per-check exception-containment integration test**

In `TestRunChecksContainment`, add:

```python
def test_malformed_ownership_aborts_only_its_check(self):
    write(self.root / "references" / "ownership.yaml", "owns: [unclosed\n")
    agents, errs = V.run_checks(self.root)
    self.assertEqual(agents, {})
    self.assertTrue(any(
        "check 'check_ownership' aborted at first bad file" in err
        for err in errs), errs)
    self.assertTrue(any("hooks.json" in err for err in errs), errs)
```

The missing `hooks/hooks.json` error is emitted by `check_hooks`, which appears after `check_ownership` in `CHECKS`; seeing both messages proves the loop continued.

- [x] **Step 4: Mutation-check exception containment**

Temporarily replace the inner `try/except` in `run_checks()` with a direct `errs += fn(root, agents)`, then run:

`python3 -m unittest tests.test_validate_package.TestRunChecksContainment.test_malformed_ownership_aborts_only_its_check -v`

Expected: ERROR with a PyYAML parser exception instead of a returned error list. Restore `run_checks()` immediately and rerun the command; expected PASS.

- [x] **Step 5: Run the task checks**

Run: `python3 -m unittest tests.test_validate_package.TestAgentTools tests.test_validate_package.TestRunChecksContainment -v`

Expected: all tests PASS.

Run: `python3 -m py_compile tests/test_validate_package.py`

Expected: exit 0.

- [x] **Step 6: Commit Task 2 file only**

```bash
git add tests/test_validate_package.py
git commit -m "test(validator): pin enforcement containment [TEST-003, TEST-004]"
```

**Task 2 evidence (2026-07-21):** all three outbound-tool subtests failed when the tools were temporarily removed from `OUTBOUND_TOOLS`; containment failed with a parser traceback when the inner `try/except` was temporarily removed. Restored code passed 9 focused tests, py_compile, full 93-test suite, and fresh review; the test name was tightened after the review's Minor finding. Commit: `76bf04e`.

---

### Task 3: Full validation, feature ledger, and backlog bookkeeping

**Files:**
- Modify: `feature_list.json` (`passes` only for the five completed IDs)
- Modify: `TODO.md`
- Create or modify: `TODO-done.md`
- Modify: `docs/superpowers/plans/2026-07-21-enforcement-test-net.md`

**Interfaces:**
- Consumes: verified Task 1 and Task 2 commits.
- Produces: a clean batch validation record, five `passes: true` values, a small active backlog with completed entries moved intact to `TODO-done.md`, and a recorded next batch.

- [x] **Step 1: Run full validation in mandated order**

Run: `python3 scripts/validate_package.py founder-os`

Expected: `13 agent(s), 49 skill(s), 0 error(s)`.

Run: `python3 -m py_compile founder-os/hooks/ownership-guard.py scripts/validate_package.py tests/test_ownership_guard.py tests/test_validate_package.py`

Expected: exit 0.

Run: `python3 -m unittest discover -s tests`

Expected: `OK`, with the test count greater than the 88-test baseline.

Run: `python3 scripts/generate_commands.py founder-os --check`

Expected: `founder-os/COMMANDS.md is current`.

- [x] **Step 2: Verify the performance acceptance check**

Pipe a JSON main-thread payload into:

`python3 -X importtime founder-os/hooks/ownership-guard.py`

Capture stderr and assert there is no import-time line whose module column is `yaml` or starts with `yaml.`. Do not count occurrences in file paths or comments.

- [x] **Step 3: Update `feature_list.json` only after E2E verification**

Change only the `passes` field from `false` to `true` for descriptions beginning `[TEST-001]`, `[TEST-002]`, `[TEST-003]`, `[TEST-004]`, and `[PERF-001]`. Do not reformat the file or edit descriptions/steps.

- [x] **Step 4: Move completed backlog entries intact**

Remove the five completed item sections from `TODO.md` and append them under a dated heading in `TODO-done.md`, preserving their original text and adding only a one-line completion note with the validating command or commit.

- [x] **Step 5: Update this plan**

Check completed steps, record the exact validation evidence, list any review findings, and set the next action to the highest-priority remaining coherent batch.

- [x] **Step 6: Obtain fresh review before the bookkeeping commit**

Give a fresh reviewer the full batch diff and the five original TODO requirements. Fix CRITICAL/HIGH findings before proceeding; add MEDIUM/LOW findings to `TODO.md` with evidence.

**Review evidence (2026-07-21):** fresh whole-batch review approved the implementation with no critical, important, or actionable minor findings. The only noted scope observation—malformed registry YAML handling—is outside TEST-003, which specifically covers malformed ownership YAML.

- [ ] **Step 7: Commit bookkeeping files only**

```bash
git add feature_list.json TODO.md TODO-done.md docs/superpowers/plans/2026-07-21-enforcement-test-net.md
git commit -m "chore(backlog): close enforcement test batch [TEST-001, TEST-002, TEST-003, TEST-004, PERF-001]"
```
