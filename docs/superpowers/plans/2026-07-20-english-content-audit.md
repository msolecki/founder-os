# Founder OS — English content audit

Status: complete
Date: 2026-07-20

## Goal

Make English the only language used by Founder OS product content,
documentation, examples, plans, and user-facing source text.

## Decisions

- Audit the entire tracked repository, not only the public landing page.
- Translate Polish prose without changing product behavior or historical facts.
- Keep commands, paths, identifiers, and technical terms unchanged.
- Exclude the repository-local `AGENTS.md`: it is untracked operator guidance
  supplied by the user, not Founder OS product content.
- Preserve unrelated working-tree changes in hooks, tests, plugin metadata, and
  generated agent files.

## Step 1 — inventory [S]

**What:** Find Polish text across all tracked text-based product files.

**Where:** Markdown, HTML, JSON, YAML, Python, shell, and TOML files.

**How:** Scan for Polish diacritics and a second set of common Polish words
that can appear without diacritics; inspect every match in context.

**Test:** Every match is classified as Polish prose, an intentional literal,
or a false positive from English text.

## Step 2 — translation [M]

**What:** Replace every confirmed Polish fragment with natural English.

**Where:** The files identified in step 1.

**How:** Preserve the original meaning, status, dates, commands, constraints,
and review limitations. Do not turn a translation into a product change.

**Test:** The translated files contain no Polish diacritics or confirmed Polish
phrases and remain structurally equivalent to their originals.

## Step 3 — validation and review [M]

**What:** Prove the repository is English-only and the package still works.

**Where:** Entire changed set and the tracked repository.

**How:** Re-run both language scans, check the diff, run the package validator
and unit tests, then commit only files from this task.

**Test:** Zero Polish-language matches, zero diff whitespace errors, package
validator reports zero errors, and all unit tests pass.

## Invariant

The landing layout, plugin runtime, ownership contract, commands, and workflow
behavior do not change. Existing unrelated working-tree changes stay untouched.

## Next step

Push the resulting commit when ready; no implementation work remains.

## Progress

- Audited 98 tracked product text files plus current untracked product files.
- Confirmed Polish prose in one historical implementation plan and one example
  banned phrase in the onboarding skill; translated both into natural English.
- Re-ran the diacritic scan and the common-word scan with zero confirmed Polish
  matches. English uses of `data` were inspected as false positives.
- Package validation passes with 13 agents, 49 skills, and zero errors. All 80
  unit tests pass.
