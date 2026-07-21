# Product Hunt Activation Launch — Implementation Plan

> **For the implementer:** use `superpowers:executing-plans` in a fresh session
> and update this file after every task. Use test-driven development for every
> behavior change. A fresh agent that did not author the change must perform the
> final code review before release.

**Goal:** ship Founder OS `2.4.0` with one resumable path from public install to
a useful, persisted first daily brief, then launch it on Product Hunt with
activation—not rank—as the primary outcome.

**Design source:**
[`docs/superpowers/specs/2026-07-21-product-hunt-activation-design.md`](../specs/2026-07-21-product-hunt-activation-design.md)

**Architecture:** keep Founder OS as a static Claude Code/Codex plugin. The
Chief of Staff orchestrates onboarding, but Positioning Advisor, Strategist and
CFO remain the only writers of their owned state. Activation is derived from a
valid daily-review file in the resolved workspace; no cloud service, hidden
state tracker or telemetry is added.

**Tech stack:** Markdown plugin skills and agents, Python 3.11 validator/hooks
and `unittest`, dependency-free browser JavaScript tested with Node 20, static
GitHub Pages HTML/CSS/assets.

## Global constraints

- Work from the current HEAD, not the design snapshot. At implementation start,
  record HEAD and re-run the audit because other work was active on 2026-07-21.
- Preserve unrelated and staged user changes. Never include them in a task
  commit.
- Keep `founder-os` as the marketplace, plugin and namespace id.
- Do not modify authentication or middleware.
- Do not add product telemetry, outbound tools, integrations, agents or skills.
- Do not install npm dependencies without the founder's explicit approval. The
  package has no `package.json`; Node tests use the standard library.
- Preserve the enforcement semantics: explicit agent allowlists, fail-open
  runtime guard, build-time outbound denial and one owner per file.
- Preserve user-facing data honesty. An unknown stays unknown and is queued;
  onboarding must not fabricate a full close, evidence-backed ICP or historical
  trend.
- The repository must remain installable and deployable after every task.
- Every production behavior change follows RED → GREEN. A test-only task uses a
  temporary mutation to prove the new test detects its target regression.
- Run focused tests after each task and the complete gate before every task
  commit that changes package behavior.
- Do not flip any `feature_list.json` item until its listed end-to-end behavior
  passes. Do not recreate retired `TODO.md`/`TODO-done.md` files unless current
  HEAD still tracks and requires them.
- Before a task commit, inspect `git status` and `git diff`; commit only that
  task's paths.

## Canonical verification commands

```bash
python3 scripts/validate_package.py founder-os
python3 scripts/generate_commands.py founder-os --check
python3 -m unittest discover -s tests
node --test tests/*.behavior.test.js
claude plugin validate .
claude plugin validate founder-os
```

Passing logs stay concise; report only failures and the final pass counts.

---

## Task 1 — Pin the activation contract (M)

- [x] **What:** add executable contract coverage for first-run stage order,
  completion, failure and resume behavior before changing the onboarding prose.
- **Where:** create `tests/test_onboarding_activation.py`; modify
  `tests/test_validate_package.py` and `scripts/validate_package.py` only if a
  reusable structural check belongs in the package validator.
- **How:**
  1. Parse frontmatter and named Markdown headings instead of asserting exact
     sentences.
  2. Assert that init declares preflight, four progress stages, owner-safe
     delegation, minimum-state validation, daily-brief invocation, persisted
     completion and resume behavior.
  3. Assert that `Activation complete` is downstream of a successful write to
     `reviews/daily/`, never merely downstream of scaffolding.
  4. Assert that the downstream skills named by init exist and are held by the
     expected agent; derive owners from `ownership.yaml` instead of creating a
     second ownership map.
  5. Assert that completion and validation resolve against the same
     `FOUNDER_OS_HOME`/business slug.
  6. Keep prose-quality judgments for review; machine-check only structural
     contracts.
- **Test:**
  - RED: run `python3 -m unittest tests.test_onboarding_activation -v`; the
    current “hand off and stop” flow must fail.
  - Mutation: temporarily move the completion statement before the daily-review
    write; the test must fail, then restore it.
  - GREEN comes in Tasks 2–3; the rest of the existing suite must remain green
    while the new contract is red for the known reason.
- **Deployability:** test-only change; no runtime behavior changes.
- **Commit:** `test(onboarding): pin activation and resume contract`

## Task 2 — Make `/founder-os-init` resumable and outcome-complete (L)

- [x] **What:** replace the contradictory stop-and-handoff behavior with one
  preflighted, resumable orchestration ending in the first brief.
- **Where:** modify
  `founder-os/skills/founder-os-init/SKILL.md`,
  `founder-os/skills/founder-os-init/agents/openai.yaml`, and, only if routing
  needs clarification, `founder-os/agents/chief-of-staff.md`.
- **How:**
  1. Add Stage 0 read-only preflight: package files, target resolution,
     writability, registry resolution, canonical context and activation state.
  2. Classify state as `new`, `incomplete` or `activated`. An activated
     workspace routes to `founder-os-doctor`; an incomplete one resumes.
  3. Replace the single hard “charter exists” abort with preservation rules:
     never overwrite a populated section, never re-scaffold destructively and
     continue from the first missing owned output.
  4. Present interview progress `1/4`–`4/4`. Add hours and cash capacity to the
     90-day question because the first bet must be sized.
  5. Reduce the hard onboarding stop from twenty to fifteen minutes and move
     unused questions to post-activation setup.
  6. Delegate carried answers through the agent allowlist to Positioning
     Advisor, Strategist and CFO. Chief of Staff writes only charter, queue and
     daily review state it already owns.
  7. Validate minimum state before invoking `daily-brief`.
  8. Print `Activation complete` only after validating the review file in the
     same resolved workspace.
  9. On failure, print completed stages, the missing stage and
     `/founder-os-init` as the resume command.
- **Test:** run the focused contract from Task 1. Add cases for new, interrupted
  and already-activated workspaces. Verify that a simulated populated charter is
  preserved byte-for-byte and no failure branch contains a success receipt.
- **Deployability:** existing active workspaces keep their state and are routed
  to the doctor; the existing command name is unchanged.
- **Commit:** `feat(onboarding): continue init through first brief`

## Task 3 — Add truthful first-run branches to the owner skills (L)

- [x] **What:** let each owner consume the carried onboarding answer without
  pretending that a ten-minute setup is a full operating review.
- **Where:** modify
  `founder-os/skills/icp-definition/SKILL.md`,
  `founder-os/skills/quarterly-planning/SKILL.md`,
  `founder-os/skills/revenue-review/SKILL.md`,
  `founder-os/skills/runway-forecast/SKILL.md`,
  `founder-os/skills/daily-brief/SKILL.md`, and tests in
  `tests/test_onboarding_activation.py`.
- **How:**
  1. ICP first run writes a dated hypothesis when `clients/` lacks evidence,
     names the real examples supplied by the founder and queues missing
     validation instead of filling evidence slots.
  2. Quarterly first run writes one partial-quarter bet, numeric outcome, kill
     condition, capacity/cash cap and first move. It keeps the existing rule
     that future quarter plans require verdicts and red-team review.
  3. Revenue first run writes only supplied/computable values, marks unavailable
     close inputs explicitly and must not infer booked revenue, hours, rate or
     receivables.
  4. Runway first run uses cash and real burn when both exist. If either is
     unknown, it writes the gap and queues it; it never guesses a reserve or
     pipeline.
  5. Daily brief accepts truthful thin day-one state, selects the first move or
     the blocking cash unknown and never fabricates rotting history.
  6. Keep every write inside the existing ownership and section vocabulary.
     Change `ownership.yaml` only if an unavoidable new section is approved;
     the preferred implementation uses existing sections.
- **Test:**
  - add table-driven contract cases for complete inputs and each unknown;
  - assert hypothesis/unknown labels and dates survive into output contracts;
  - assert each modified skill's declared writes still match its holder;
  - run `python3 scripts/validate_package.py founder-os` and the full unit suite.
- **Deployability:** recurring ICP, quarterly, revenue, runway and daily flows
  retain their current branches; only an empty first-run workspace takes the new
  branch.
- **Commit:** `feat(onboarding): add owner-safe first-run branches`

## Task 4 — Prove installed-package context and clean-copy behavior (M)

- [x] **What:** close the gap between source-tree tests and an installed plugin
  layout without invoking an LLM or sending data.
- **Where:** create `tests/test_session_context.py` and
  `scripts/smoke_installed_copy.py`; modify `.github/workflows/ci.yml` and
  `docs/development.md`.
- **How:**
  1. Build a temporary marketplace copy using stdlib `tempfile`/`shutil`.
  2. Set `CLAUDE_PLUGIN_ROOT` and send realistic `startup`, `resume`, `clear`
     and `compact` hook fixtures.
  3. Assert valid JSON, `hookEventName: SessionStart` and the canonical guidance
     content from the installed copy.
  4. Exercise the installed copy's ownership hook with one allowed owner write,
     one denied wrong-owner write and one main-thread path.
  5. Run internal package validation and command-generation checks against the
     copied plugin.
  6. Add the smoke to CI without external network calls.
- **Test:** mutation-check by pointing the hook at the repository root instead
  of the copied plugin; the installed-copy assertion must fail. Restore and run
  the smoke, hook tests and full unit suite.
- **Deployability:** source package is unchanged until tests prove installed
  path resolution.
- **Commit:** `test(packaging): exercise session context from installed copy`

## Task 5 — Close the remaining landing controller test debt (M)

- [x] **What:** close `TEST-010` if it remains false on current HEAD by testing
  exported controller behavior instead of slicing and evaluating inline HTML.
- **Where:** create `docs/workflow-library.js` and `docs/demo-tabs.js`; modify
  `docs/index.html`, `tests/docs_workflows.behavior.test.js`,
  `tests/test_docs_workflows.py`, and `feature_list.json` only after proof.
- **How:**
  1. Extract each controller into a small UMD/CommonJS-compatible module with no
     dependency and an explicit initializer.
  2. Keep progressive enhancement: all catalogue content remains available when
     JavaScript fails.
  3. Load scripts through same-origin `<script src>` tags and update CSP to avoid
     widening it.
  4. Require the modules directly from the Node test and test user-visible
     behavior with the existing fake DOM.
  5. Remove `extractController`, literal start/end markers and `eval`.
  6. Flip `TEST-010` only after the behavior command listed in
     `feature_list.json` passes.
- **Test:** RED by requiring the not-yet-created modules; GREEN with
  `node --test tests/*.behavior.test.js` and the full Python suite. Temporarily
  rename an internal local variable to confirm tests remain green, proving they
  pin behavior rather than source text.
- **Deployability:** HTML retains no-JS content and same-origin scripts; no new
  runtime dependency.
- **Commit:** `refactor(landing): extract testable workflow controllers [TEST-010]`

## Task 6 — Rebuild the landing and onboarding documentation around activation (L)

- [ ] **What:** make the first screen and getting-started path sell and deliver
  the first brief rather than the agent count.
- **Where:** modify `docs/index.html`, `docs/getting-started.md`,
  `docs/troubleshooting.md`, `docs/architecture.md`, `docs/commands.md`,
  `README.md`, `founder-os/README.md`, and the landing tests. Regenerate
  `founder-os/COMMANDS.md`; do not hand-edit it.
- **How:**
  1. Implement the approved hero, support line, CTAs and proof line.
  2. Put a real, source-linked daily brief and the empty-folder-to-brief flow
     before the organization chart.
  3. Explain local workspace storage accurately and link to environment data
     handling without claiming offline operation or zero data transmission.
  4. Update all onboarding claims to one continuous flow and remove obsolete
     manual handoff instructions.
  5. Add “first five things,” update, repair and uninstall sections.
  6. Keep canonical command names consistent with the founder-approved
     `founder-os` identity; document qualified forms where collision handling
     matters.
  7. Update the fictional workspace only where the new activation contract
     requires it; all example claims must remain traceable across files.
  8. Preserve current accessibility, reduced-motion, CSP, metadata, favicon and
     responsive contracts.
- **Test:**
  - add copy-contract assertions for the hero, CTA, proof line and prohibited
    claims;
  - run the five-second test with five people and record exact answers;
  - 4/5 must describe the result as choosing what matters today;
  - run behavior tests, HTML reference checks and the full package gate.
- **Deployability:** the existing install commands remain visible and functional
  throughout; deploy the copy only after the clean-copy smoke passes.
- **Commit:** `feat(landing): lead Founder OS with daily activation`

## Task 7 — Build the Product Hunt launch kit (M)

- [ ] **What:** produce every submission asset and the complete maker copy before
  scheduling the launch.
- **Where:** create `docs/product-hunt/README.md`,
  `docs/product-hunt/listing.md`, `docs/product-hunt/maker-comment.md`,
  `docs/product-hunt/demo-script.md`, `docs/product-hunt/activation-study.md`,
  `docs/product-hunt/thumbnail-240.png`, and at least four
  `docs/product-hunt/gallery-*.png` assets at `1270×760`.
- **How:**
  1. Use the approved name and tagline; keep description within 500 characters
     and tagline within 60.
  2. Gallery sequence: outcome, four-stage onboarding, trust/provenance, daily
     and weekly operating loop.
  3. Capture assets from the real static page/example workspace or generate
     them from a reviewed visual source; do not present a mocked activation as a
     successful live run.
  4. Write a 45–60 second recording script with the public install commands and
     no hidden cuts across a failure.
  5. Draft the maker comment without an upvote request, paid hunter or engagement
     manipulation.
  6. Add alt text, source paths, exact dimensions and a submission checklist.
  7. The activation-study sheet records consented participant id, success,
     elapsed time, first confusion, outcome usefulness and seven-day return; no
     workspace contents.
- **Test:** add a stdlib image-dimension/required-file check to
  `tests/test_docs_workflows.py`; proofread character limits programmatically;
  open every image at target resolution and review legibility at 50% scale.
- **Deployability:** launch assets are additive and do not affect package
  runtime.
- **Commit:** `docs(launch): add Product Hunt activation kit`

## Task 8 — Add release gates and prepare `2.4.0` (M)

- [ ] **What:** remove manifest warnings, align version metadata and make release
  validation reproducible without prematurely tagging the release.
- **Where:** modify `.claude-plugin/marketplace.json`,
  `founder-os/.claude-plugin/plugin.json`, the Codex manifest used by current
  HEAD, `CHANGELOG.md`, `.github/workflows/ci.yml`, and `docs/development.md`.
- **How:**
  1. Add the missing marketplace-level description using activation-led copy.
  2. Set all package manifests and marketplace entry to `2.4.0` in one change.
  3. Add a dated changelog section covering activation, trust, tests and launch
     assets without claiming untested Codex parity.
  4. Run both official `claude plugin validate` targets locally.
  5. Propose a pinned official Claude CLI validation step for CI. Because this
     downloads an npm package, obtain explicit founder approval before adding or
     executing it. If approval is denied, keep official validation as a blocking
     documented release gate and do not describe it as CI coverage.
  6. Keep the internal installed-copy smoke in CI regardless of that decision.
  7. Do not create the git tag in this task.
- **Test:** manifest parity tests, internal validator, generated-command check,
  full unit/behavior suites, installed-copy smoke and official local plugin
  validation. No unaddressed warning may remain.
- **Deployability:** version metadata changes only after activation and docs are
  green; no tag means the candidate is still reversible.
- **Commit:** `chore(release): prepare Founder OS 2.4.0`

## Task 9 — Fresh review and five-person activation gate (L, operational)

- [ ] **What:** obtain independent code review and real first-run evidence before
  scheduling Product Hunt.
- **Where:** update this plan's evidence section and
  `docs/product-hunt/activation-study.md`; code fixes return to their owning
  files and tests.
- **How:**
  1. Spawn a fresh reviewer that did not inherit the author's implementation
     context. Provide objective, changed file list, constraints and expected
     severity-ranked findings—not debugging history.
  2. Compare `git status`, `git diff` and commits after reviewer work; never
     trust a green uncommitted tree.
  3. Resolve every P0/P1 finding using TDD and request a second read of the fix.
  4. Recruit five people who have not worked on the repository. Observe a clean
     install without rescuing them.
  5. Run one deliberate interruption at each onboarding boundary across the
     cohort and verify resume/preservation.
  6. Run Claude Code clean installs for all five. Run a separate Codex test; if
     it fails, label Codex beta/manual everywhere before launch.
  7. Re-test `weekly-review` seven days later.
- **Test / go-no-go:**
  - at least 4/5 first briefs persisted;
  - P50 ≤10 minutes and target P90 ≤15 minutes;
  - 0 overwrites, ownership breaches or false completions;
  - 3/5 return for weekly review;
  - all reviewer P0/P1 findings closed.
  If any threshold fails, do not schedule the launch. Return to the failing task
  and repeat the cohort with new participants for changed steps.
- **Deployability:** no public release occurs in this task; failed evidence stops
  the process safely.
- **Commit:** commit only fixes and evidence that contain no participant or
  workspace-sensitive data.

## Task 10 — Release, launch and seven-day activation review (M, operational)

- [ ] **What:** publish the verified release, run the Product Hunt day and judge
  it against activation.
- **Where:** git tag `v2.4.0`, Product Hunt submission, GitHub Pages, and the
  evidence section of this plan. The plugin itself makes no outbound write.
- **How:**
  1. D-7: freeze feature scope; accept only installation, activation, data-loss,
     security, packaging and material copy-accuracy blockers.
  2. D-2: schedule Product Hunt only after Task 9 passes; prefer Saturday only
     if the tester cohort can participate.
  3. D-1: install from the public repo, run the complete gate, verify Pages and
     every asset, then tag `v2.4.0` using the release workflow.
  4. D0: publish around `00:01 PT`, post the maker comment first, respond to
     substantive questions and never ask for upvotes.
  5. Invite a named, consented cohort to test the full activation and report the
     first break. The founder sends invitations; Founder OS only drafts them.
  6. Patch only release blockers. Every hotfix gets a regression test and the
     full gate before publication.
  7. D+7: record confirmed activations, cohort conversion, P50/P90, weekly return,
     blockers and supporting Product Hunt/repository indicators.
  8. Write a verdict: continue the current funnel, revise the activation flow or
     stop promotion until the failed condition is fixed.
- **Test / launch success:**
  - ten voluntary confirmed activations in seven days;
  - at least 60% activation in the consented launch cohort;
  - P50 ≤10 minutes and P90 ≤15 minutes;
  - at least 3 of the first 5 activated users return for weekly review;
  - Product Hunt rank and upvotes are recorded only as secondary context.
- **Deployability:** tag only the exact commit that passed the final gate. If a
  blocker appears after tag, ship the smallest tested patch release; do not edit
  the tag.

---

## Final release checklist

- [ ] Current HEAD and worktree ownership recorded.
- [ ] All relevant `feature_list.json` entries true with end-to-end evidence.
- [ ] Package validator: 0 errors.
- [ ] `COMMANDS.md` current.
- [ ] Python unit suite green.
- [ ] Node behavior suite green.
- [ ] Installed-copy smoke green.
- [ ] Official root and plugin validation green without unaddressed warnings.
- [ ] Fresh-agent review has no open P0/P1.
- [ ] Five-person activation gate passed.
- [ ] Landing five-second test passed.
- [ ] Product Hunt dimensions, character limits, links and alt text verified.
- [ ] `2.4.0` versions and changelog agree.
- [ ] Public install retested immediately before tagging.
- [ ] Product Hunt page asks for testing/feedback, never votes.

## Evidence log

Update after each task with:

```text
Task 1 — 2026-07-21
Commit: 938bd11..259e095
Focused test: python3 -m unittest tests.test_onboarding_activation -v — 6 expected contract RED, 2 parser/mutation tests green
Full gate: 122 pre-existing Python tests, validator, generated-command check and 2 Node behavior tests green
Review: fresh task reviewer approved; no Critical, Important or Minor findings open
Decision / next action: continuous RED → GREEN batch approved; implement Task 2 without handing back the red state
```

```text
Task 2 — 2026-07-21
Commit: d203803, 7042f3b, 7178d57
Focused test: python3 -m unittest tests.test_onboarding_activation — 21/21 green, including resume-target and independent-CFO-marker mutations
Full gate: 143 Python tests, validator, generated-command check, 2 Node behavior tests and both official plugin validations green
Review: fresh task reviewer approved after two correction rounds; no Critical, Important or Minor findings open
Decision / next action: implement Task 3 owner-safe first-run branches, pressure-test the day-one scenario, then restore the complete green gate
```

```text
Task 3 — 2026-07-21
Commit: 002c446, bdefd48
Focused test: python3 -m unittest tests.test_onboarding_activation — 31/31 green, including fabrication, boundary and composed-transition mutations
Full gate: 153 Python tests, validator, generated-command check, 2 Node behavior tests and both official plugin validations green
Review: fresh task and batch reviewers approved after correction; no Critical, Important or Minor findings open
Decision / next action: begin Task 4 from this green deployable checkpoint
```

```text
Task 4 — 2026-07-22
Commit: f7b0ec1
Focused test: python3 -m unittest tests.test_session_context -v — 8/8 green; source-root mutation rejected while the restored installed root passed
Full gate: installed-copy smoke, 161 Python tests, validator, generated-command check, 2 Node behavior tests and both official plugin validations green
Review: fresh artifact reviewer approved; no Critical, Important or Minor findings open
Decision / next action: implement Task 5's exported landing controllers from this clean-copy checkpoint
```

```text
Task 5 — 2026-07-22
Commit: ad2c9f8
Focused test: node --test tests/*.behavior.test.js — 2/2 green; local-variable rename resilience mutation also stayed 2/2
Full gate: 163 Python tests, installed-copy smoke, validator, generated-command check, 2 Node behavior tests and both official plugin validations green
Review: fresh artifact reviewer approved; no Critical, Important or Minor findings open
Decision / next action: implement Task 6's activation-led landing and onboarding documentation; hold completion for the required five-person test
```

```text
Task 6 machine checkpoint — 2026-07-22
Commit: bb5b54d
Focused test: python3 -m unittest tests.test_docs_workflows.ActivationCopyContractTest — 11/11 green after the validity contract first failed across all six activation documents
Full gate: 174 Python tests, installed-copy smoke, validator, generated-command check, 2 Node behavior tests and both official plugin validations green with two known warnings reserved for Task 8
Review: fresh artifact reviewer approved the corrected validity and example-trace contracts; no Critical, Important or Minor findings open
Decision / next action: keep Task 6 unchecked until five real five-second-test answers are recorded and at least 4/5 describe choosing what matters today
```

```text
Task N — YYYY-MM-DD
Commit: <sha>
Focused test: <command and concise result>
Full gate: <command and concise result>
Review: <reviewer and verdict>
Decision / next action: <one line>
```

## Next action

Tasks 1–5 and Task 6's machine artifact are committed and fresh-review approved,
with the complete gate green through `bb5b54d`. Run the five-second test with
five people who have not worked on the repository: show the first screen, ask
“What does this product help you do?”, and record each answer verbatim. Keep Task
6 unchecked until at least 4/5 describe choosing what matters today, and keep the
staged user deletion of `TODO-done.md` outside every task commit.
