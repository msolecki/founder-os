# Platform and Launch Readiness Batch

**Goal:** close `ARCH-001` and `A11Y-001` from `TODO.md` without changing runtime enforcement behavior.

## Task 1 — ARCH-001

- **What:** pin Node 20 in CI, document Node as a test requirement, and skip the browser behavior test cleanly when Node is unavailable.
- **Where:** `.github/workflows/ci.yml`, `docs/getting-started.md`, `tests/test_site_workflows.py`.
- **How:** add setup-node before tests; add the requirement row; guard the subprocess test with `shutil.which("node")`.
- **Test:** run the site workflow tests with Node and run the full Python suite.

## Task 2 — A11Y-001

- **What:** add Open Graph, Twitter Card, and canonical metadata to the launch page.
- **Where:** `docs/index.html` head.
- **How:** use the repository's public GitHub Pages URL and a stable 1200×630 social image URL; add a regression test for required metadata if the existing site tests support HTML assertions.
- **Test:** parse the head metadata with the existing site test tooling and run the full suite.

## Validation and review

- Run package validation, command generation check, Python compile, and all unit tests.
- Obtain a fresh read-only review before committing.
- Update `TODO.md`, `TODO-done.md`, and `feature_list.json` only after end-to-end checks pass.

## Evidence

- ARCH-001 focused test passed with Node and skipped cleanly under `PATH=/tmp`; full suite passed with 94 tests.
- A11Y-001 metadata contract passed; `docs/og-image.svg` is 1200×630 and referenced by absolute public URL.
- Validator reported 13 agents / 49 skills / 0 errors; generated commands are current; fresh review found no critical or important issues.
