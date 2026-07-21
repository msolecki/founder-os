# Ownership Hot-Path Batch

## Goal

Complete `PERF-002` and `BUG-002` without changing ownership decisions.

- **PERF-002:** compute workspace roots once per ownership check and pass them through each path resolution; add a call-count contract test.
- **BUG-002:** accept valid same-indent YAML sequences in the PyYAML fallback and pin the behavior with a focused test.

## Validation

Run focused tests and compile checks after each change, then package validation, command generation, and the full unit suite. Obtain fresh review before commit and update the feature/backlog ledgers only after all checks pass.

## Evidence

- Focused fallback and hot-path tests passed; the multi-path mock confirms one `workspace_roots` call.
- Full validation passed: 13 agents / 49 skills / 0 errors, compile OK, 97 tests OK, generated commands current.
- Fresh review requested; no implementation changes remain outside the two scoped tasks.
