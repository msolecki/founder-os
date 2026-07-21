# Hook Coverage Batch

## Goal

Complete `TEST-005` and `BUG-001` from the audit backlog while preserving the guard's documented fail-open semantics.

## Task 1 — TEST-005

- **What:** prove a symlink outside a workspace resolves to the owned target and is denied to a non-owner.
- **Where:** `tests/test_ownership_guard.py`.
- **How:** add a temporary workspace fixture, create a symlink to an owned file, and exercise the existing ownership decision path.
- **Test:** focused ownership suite and a temporary mutation of `realpath`/resolution that makes the new assertion fail.

## Task 2 — BUG-001

- **What:** make validator coverage assert that `hooks.json` routes `apply_patch` through the ownership guard.
- **Where:** `tests/test_validate_package.py` only, unless the current matcher is genuinely missing coverage.
- **How:** add the matcher to the existing coverage cases and mutation-check by removing `apply_patch` from the fixture.
- **Test:** focused hook validator tests and full package validation.

## Batch validation

Run package validation, command generation check, Python compilation, and all unit tests; obtain fresh review before commit; update backlog/feature ledger only after these checks pass.

## Evidence

- Symlink integration test passes and reports the real owner (`strategist`) on deny.
- `apply_patch` mutation was red before adding coverage; restored validator and fixture pass.
- Validator: 13 agents / 49 skills / 0 errors; compile OK; 95 tests OK; generated commands current.
- Fresh review found no critical or important issues; platform-sensitivity is limited to symlink-capable environments.
