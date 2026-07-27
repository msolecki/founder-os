# Founder OS Full Host Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship Founder OS 2.5.0 with one tested local state gateway, identical role behavior on Claude Code and Codex, one-level sibling orchestration, and every P1/P2 audit defect closed.

**Architecture:** A Python 3.9+ stdlib-first stdio MCP server owns workspace resolution, bounded reads, role capabilities, ownership enforcement, optimistic concurrency, atomic writes, and metadata-only journaling. Claude Code and Codex use host adapters that point to that same server; hooks provide defense in depth, while the main thread only orchestrates sibling roles and never substitutes for a specialist's state write.

**Tech Stack:** Python 3.9+ standard library with optional PyYAML compatibility, JSON-RPC/MCP over stdio, Markdown/YAML/JSON, static HTML/CSS/CommonJS, `unittest`, and Node's built-in test runner.

## Global Constraints

- The approved design is `docs/superpowers/specs/2026-07-27-founder-os-full-host-parity-design.md`; implementation may clarify mechanics but may not weaken its contracts.
- Package version stays exactly `2.5.0`; there is no `v2.5.0` tag yet.
- No dependency installation, `npm install`, remote service, authentication integration, telemetry, network call, delete tool, arbitrary filesystem browser, or shell proxy.
- Do not modify authentication or middleware and do not delete tests.
- All thirteen packaged roles read and write state themselves through the local `founder-os-state` gateway; the controller performs technical orchestration only.
- Subagents are siblings. No role or workflow may spawn another subagent, and Codex parity may not rely solely on undocumented discovery of `agents/*.md`.
- Native-role and generic-agent fallback execution use the same packaged role file, active workflow, bounded handoff, and capability-bound ownership contract.
- Gateway writes fail closed for unknown roles, malformed ownership, missing ownership, invalid or expired capabilities, unsafe paths, stale hashes, bad structure, and I/O failures.
- Gateway failures use only `WORKSPACE_UNRESOLVED`, `ROLE_SESSION_INVALID`, `PATH_OUTSIDE_WORKSPACE`, `ROLE_NOT_OWNER`, `STALE_WRITE`, `INVALID_DOCUMENT_STRUCTURE`, and `STATE_IO_ERROR`, each with the concise recovery action from the approved design.
- Every production behavior follows RED → GREEN → REFACTOR. Reports must record the failing command/output and the passing command/output.
- After every task, run focused tests, package validation, generated-command check, the full Python suite, and relevant Node behavior tests before committing.
- Every commit uses `--no-gpg-sign`, an explicit `--only` pathspec, and only files owned by that task.
- After each task's independent review is clean, the controller marks that task's checkboxes, appends its commit/review evidence to the Progress Log, and commits only this plan before dispatching the next task.
- Never stage, restore, edit, commit, or otherwise alter `docs/superpowers/specs/2026-07-22-founder-os-evaluation-codex-design.md`; its pre-existing staged deletion must remain staged.
- Do not tag, push, publish, send, pay, sign, invoice, or cancel anything.
- The package must remain deployable after every task.

## File and Interface Map

- `founder-os/mcp/founder_os_state.py`: executable stdio entry point; protocol stdout only, diagnostics stderr only.
- `founder-os/mcp/protocol.py`: MCP JSON-RPC framing, initialize, notifications, `tools/list`, and `tools/call` dispatch.
- `founder-os/mcp/workspaces.py`: single/multi-business resolution and opaque server-side workspace bindings.
- `founder-os/mcp/safe_io.py`: bounded relative path validation, symlink containment, Markdown listing, UTF-8 reads, SHA-256, and atomic replacement.
- `founder-os/mcp/ownership.py`: dependency-light canonical ownership/section schema loader and longest-prefix member ownership.
- `founder-os/mcp/sessions.py`: short-lived role capabilities, persisted hashes/metadata, close/expiry, and metadata-only journal.
- `founder-os/mcp/gateway.py`: seven public tool handlers and the stable error contract.
- `founder-os/.mcp.json`: Claude Code adapter using `${CLAUDE_PLUGIN_ROOT}`.
- `founder-os/.codex-plugin/plugin.json`: Codex adapter with an inline `mcpServers` object using `${CODEX_PLUGIN_ROOT}`.
- `founder-os/references/orchestration.md`: portable native-role/generic-agent sibling execution contract.
- `scripts/check_local_links.py`: tracked Markdown/HTML local target and anchor validator.
- `scripts/probe_installed_hosts.py`: isolated Claude/Codex installed-plugin discovery and role-I/O probes.

---

### Task 1: MCP Protocol Shell and Tool Catalogue

**What:** Add a dependency-light stdio MCP process that implements initialization, notifications, tool discovery, tool-call dispatch, and clean JSON-RPC errors for all seven gateway tools.

**Where:** Create `founder-os/mcp/founder_os_state.py`, `founder-os/mcp/protocol.py`, `founder-os/mcp/gateway.py`, `founder-os/mcp/__init__.py`, and `tests/test_state_gateway_protocol.py`.

**How:** Keep line-oriented JSON-RPC in `protocol.py`; inject a `Gateway` instance so protocol tests use real dispatch without a subprocess and installed-copy tests can use the executable. Advertise protocol version `2025-06-18`, server name `founder-os-state`, and exactly `resolve_workspace`, `open_role_session`, `list_state`, `read_state`, `read_reference`, `write_owned_state`, and `close_role_session`. Treat notifications as no-response messages. Serialize responses only to stdout and send diagnostics only to stderr.

**Test:** `python3 -m unittest tests.test_state_gateway_protocol -v` must first fail because the entry point and handlers do not exist, then pass for initialize, notification silence, tool schemas, valid dispatch, unknown tool, malformed JSON, stdout framing, and stderr diagnostics.

**Size:** M

- [x] Write protocol tests that start the real subprocess and assert literal JSON-RPC response shapes, including no stdout frame for `notifications/initialized`.
- [x] Run `python3 -m unittest tests.test_state_gateway_protocol -v`; record the expected missing-module/entry-point RED failure.
- [x] Implement `ProtocolServer.handle_message(message: dict) -> dict | None` and `ProtocolServer.serve(stdin, stdout, stderr) -> int`, with `Gateway.call(name, arguments)` as the only tool boundary.
- [x] Re-run the focused tests and the repository Python suite; record GREEN output.
- [x] Run `python3 scripts/validate_package.py founder-os`, `python3 scripts/generate_commands.py founder-os --check`, and `git diff --check`.
- [x] Commit with `git commit --only --no-gpg-sign -m "feat: add Founder OS MCP protocol shell" -- founder-os/mcp/__init__.py founder-os/mcp/founder_os_state.py founder-os/mcp/protocol.py founder-os/mcp/gateway.py tests/test_state_gateway_protocol.py`.

### Task 2: Workspace Resolution, Role Sessions, and Safe Read Surface

**What:** Implement opaque workspace bindings, short-lived role sessions, and safe `resolve_workspace`, `open_role_session`, `list_state`, `read_state`, `read_reference`, and `close_role_session` behavior for single- and multi-business installs.

**Where:** Create `founder-os/mcp/workspaces.py`, `founder-os/mcp/safe_io.py`, `founder-os/mcp/sessions.py`, and `tests/test_state_gateway_reads.py`; modify `founder-os/mcp/gateway.py`.

**How:** `WorkspaceResolver.resolve(project_dir: Path, business_slug: str | None) -> WorkspaceBinding` applies `FOUNDER_OS_HOME` and `~/.founder-os/businesses.yaml`, refuses ambiguity, stores the canonical root under a random opaque identifier, and never accepts a later caller path. `RoleSessionStore.open(workspace_id, role, correlation_id, workflow=None) -> capability` uses `secrets.token_urlsafe`, persists only `sha256(capability)` plus validated role/workspace/run/workflow/expiry metadata under plugin data, and invalidates on close/expiry; `workflow` is optional for the base tool contract and, when present, must be a packaged workflow slug. `SafeStateIO` rejects absolute paths, `..`, NUL, unsupported glob syntax, directories, special files, and escaping symlinks; lists regular `.md` files only and enforces explicit result/per-file/total byte caps. `read_reference` permits only `CLAUDE.md`, the session-bound file under `agents/{role}.md`, the session-bound file under `skills/{workflow}/SKILL.md`, `references/ownership.yaml`, `references/house-rules.md`, `references/multi-business.md`, and `references/orchestration.md`; role and workflow values come from role-session metadata, never caller-supplied paths.

**Test:** `python3 -m unittest tests.test_state_gateway_reads -v` covers default/single/multi/ambiguous resolution, forged IDs, session creation/expiry/close/reuse, wrong workspace/role, traversal, absolute/NUL/glob attacks, special files, escaping symlinks, UTF-8 errors, missing state, size caps, SHA-256, and reference allowlist denial.

**Size:** L

- [x] Write table-driven tests with literal expected codes `WORKSPACE_UNRESOLVED`, `PATH_OUTSIDE_WORKSPACE`, and `STATE_IO_ERROR`; include a registry with two businesses and a separate portfolio root.
- [x] Run the focused suite and record RED failures for missing resolver and safe-I/O interfaces.
- [x] Implement `WorkspaceBinding`, `WorkspaceResolver`, `RoleSessionStore`, `SafeStateIO.list_markdown()`, `SafeStateIO.read_many()`, and `SafeStateIO.read_reference()` with real filesystem fixtures.
- [x] Connect resolve/open/list/read/reference/close handlers to `Gateway.call()` and return concise human actions with every stable code.
- [x] Re-run focused tests, protocol tests, full Python tests, package validation, generated-command check, and `git diff --check`.
- [x] Commit only Task 2 files with an explicit `--only` pathspec and message `feat: add safe Founder OS state reads`.

### Task 3: Ownership, Atomic Writes, and Journal

**What:** Add fail-closed `write_owned_state` on the Task 2 role capabilities, including canonical ownership, required headings, optimistic SHA-256 concurrency, atomic replacement, and metadata-only audit records.

**Where:** Create `founder-os/mcp/ownership.py` and `tests/test_state_gateway_writes.py`; modify `founder-os/mcp/gateway.py`, `founder-os/mcp/safe_io.py`, `founder-os/mcp/sessions.py`, and the enforcement comment at the top of `founder-os/references/ownership.yaml`.

**How:** `OwnershipSchema.load(path)` validates top-level, `owns`, `sections`, workspace/portfolio collections, role names, non-empty string lists, and directory-member longest-prefix ownership without depending on PyYAML availability. `write_owned_state` resolves the Task 2 capability binding, requires either `expected_sha256` for replacement or `create_only: true`, rejects `_local/`, validates headings in canonical order, flushes and `fsync`s a temp file in the destination directory, calls `os.replace`, cleans up failures, and journals timestamp/correlation/role/workspace/path/operation/result/before-hash/after-hash without content or prompt.

**Test:** `python3 -m unittest tests.test_state_gateway_writes -v` covers invalid/wrong-role/wrong-workspace capabilities, all ownership entry types, CFO success, Strategist `ROLE_NOT_OWNER`, `_local/`, structure failures, create-only, `STALE_WRITE`, atomic failure preservation/cleanup, and journal redaction.

**Size:** L

- [ ] Write real-filesystem and controllable-clock tests; name the mutation each test catches and assert literal before/after hashes independently.
- [ ] Run focused tests and record RED failures for missing role/session/write behavior.
- [ ] Implement `OwnershipSchema`, add metadata-only journal append/final-status support to `RoleSessionStore`, implement `SafeStateIO.atomic_replace()`, and connect `write_owned_state` to the gateway.
- [ ] Re-run focused tests; then run Tasks 1–3 suites together and confirm protocol stdout contains no diagnostic or journal text.
- [ ] Run full Python tests, package validation, generated-command check, and `git diff --check`.
- [ ] Commit only Task 3 files with an explicit `--only` pathspec and message `feat: enforce role-owned atomic state writes`.

### Task 4: Claude/Codex MCP Adapters and Hook Identity Roundtrip

**What:** Wire the shared gateway into both hosts and harden PreToolUse/SubagentStart so only capability-consistent local gateway access is allowed to role subagents.

**Where:** Create `founder-os/.mcp.json` and `tests/test_host_adapters.py`; modify `founder-os/.codex-plugin/plugin.json`, `founder-os/hooks/hooks.json`, `founder-os/hooks/record-agent.py`, `founder-os/hooks/ownership-guard.py`, `scripts/validate_package.py`, and `tests/test_ownership_guard.py`.

**How:** Both adapters declare `founder-os-state` as a local stdio Python command pointing at the same entry script, differing only by `${CLAUDE_PLUGIN_ROOT}` versus `${CODEX_PLUGIN_ROOT}`. Claude reads the plugin-root `.mcp.json`; Codex reads the inline `mcpServers` object in `.codex-plugin/plugin.json`, which is an officially validated manifest shape and avoids relying on native `agents/*.md` discovery. `record-agent.py` atomically records the real SubagentStart `turn_id → agent_type`; the guard resolves Claude `agent_type` directly or Codex `turn_id`, allows only the seven known gateway tools, denies subagent `open_role_session`, checks native role/capability agreement for role-bound calls, and denies every other MCP, Bash, WebFetch, WebSearch, direct Write/Edit/NotebookEdit/apply_patch, and arbitrary local file access by roles.

**Test:** `python3 -m unittest tests.test_host_adapters tests.test_ownership_guard -v` and `python3 scripts/smoke_installed_copy.py` cover manifest paths, shared entry point, Claude identity, real Codex SubagentStart/turn_id roundtrip, gateway allow, elevation denial, role mismatch, and outbound/direct-file denial.

**Size:** L

- [ ] Add adapter/config validation and subprocess hook tests, including one payload that omits `agent_type` after recording a real `turn_id`.
- [ ] Run focused tests and record RED failures for missing configs, missing roundtrip, and overly broad/incorrect guard decisions.
- [ ] Add both host configs, manifest reference, normalized hook matching, atomic role mapping, and capability-aware guard decisions.
- [ ] Extend package validation to compile/validate the MCP entry and both adapter shapes without assuming Codex native role discovery.
- [ ] Re-run focused suites, installed-copy smoke, full Python/Node suites, package validation, generated-command check, plugin-creator validation, and `git diff --check`.
- [ ] Commit only Task 4 files using an explicit `--only` pathspec and message `feat: wire state gateway into Claude and Codex`.

### Task 5: Portable Sibling Orchestration and Generic-Agent Fallback

**What:** Replace every nested-agent edge with one documented main-thread sibling protocol and a generic-agent fallback that preserves the exact packaged role identity.

**Where:** Create `founder-os/references/orchestration.md` and `tests/test_orchestration_contract.py`; modify all `founder-os/agents/*.md`, `founder-os/references/house-rules.md`, `scripts/validate_package.py`, and `tests/test_validate_package.py`.

**How:** Role frontmatter exposes only the bounded Founder OS gateway tools needed to resolve/read/write/close; no `Agent(...)` edge survives. Managers return a structured delegation request containing `role`, `workflow`, `workspace_id`, `correlation_id`, `handoff`, and `expected_persistence`, rather than spawning. The orchestrator opens the session, invokes a named native role when documented, otherwise invokes a generic agent carrying exactly one unchanged role file, one active workflow, one bounded handoff, and one capability, then re-reads persisted state before close/advance. Validator logic rejects any future `Agent(...)`, `Task`, nested-spawn claim, unknown gateway tool, or role without the shared state contract.

**Test:** `python3 -m unittest tests.test_orchestration_contract tests.test_validate_package -v` proves all 13 roles share the same I/O contract, native and fallback inputs resolve to byte-identical role instructions, manager requests are structured, and nested edges are rejected.

**Size:** L

- [ ] Add contract tests that enumerate all role files and mutate a fixture with `Agent(cfo)`, `Task`, a direct write tool, a changed fallback role body, and a malformed delegation request.
- [ ] Run focused tests and record RED failures against current manager edges and file-tool allowlists.
- [ ] Write the orchestration reference and migrate all 13 role contracts without changing their business decision ownership.
- [ ] Replace `check_agent_graph` with fail-closed one-level orchestration validation and update validator fixtures.
- [ ] Re-run focused tests, full suites, package validation, generated-command check, and `git diff --check`.
- [ ] Commit the reference, all role files, validator, and tests only, using explicit paths and message `refactor: orchestrate Founder OS roles as siblings`.

### Task 6: Onboarding, Strategic Evaluation, and Manager Workflow Migration

**What:** Convert onboarding, strategic evaluation, situation routing, and manager-owned workflows to persisted sibling checkpoints executed by the controller without business judgment.

**Where:** Modify `founder-os/skills/founder-os-init/SKILL.md`, `founder-os/skills/strategic-evaluation/SKILL.md`, `founder-os/skills/situation-review/SKILL.md`, `founder-os/skills/kill-or-continue/SKILL.md`, `tests/test_onboarding_activation.py`, and `tests/test_orchestration_contract.py`.

**How:** Onboarding executes Chief of Staff → Positioning Advisor → Strategist → CFO revenue review → CFO runway forecast → Chief of Staff daily brief, validating each independently persisted checkpoint before advancing. Strategic evaluation executes Chief of Staff routing, two or three attributed read-only sibling perspectives, Board Member, then a final Chief of Staff persistence pass; it never calls a perspective independent when it received another result. Manager workflows emit delegation requests and carried answers only; each specialist opens/uses/closes its own role session and writes its own owned file.

**Test:** `python3 -m unittest tests.test_onboarding_activation tests.test_orchestration_contract -v` covers ordered sibling sequences, persisted checkpoint gates, interrupted resume, owner-specific writes, attributed perspectives, native/fallback equivalence, and no controller-authored specialist output.

**Size:** L

- [ ] Add failing semantic contract tests for exact ordered roles, checkpoint re-reads, session closure, carried-answer bounds, and final evaluation ownership.
- [ ] Run focused tests and record RED failures from current direct invocation/delegation wording.
- [ ] Migrate `founder-os-init`, `strategic-evaluation`, `situation-review`, and `kill-or-continue` to the shared delegation-request format.
- [ ] Re-run focused tests, all workflow/validator tests, generated-command check, package validation, and `git diff --check`.
- [ ] Commit only migrated workflows and tests with explicit paths and message `refactor: persist sibling workflow checkpoints`.

### Task 7: Visible SessionStart Failures and YAML Type Hardening

**What:** Close audit items ERR-001, TYPE-001, TYPE-002, and TYPE-003 with model-visible context warnings and collected validator/generator errors for every invalid YAML container shape.

**Where:** Modify `founder-os/hooks/session-context.py`, `scripts/_package.py`, `scripts/generate_commands.py`, `scripts/validate_package.py`, `tests/test_session_context.py`, `tests/test_generate_commands.py`, and `tests/test_validate_package.py`.

**How:** SessionStart emits valid hook JSON containing a warning and writes the same diagnostic to stderr when installed `CLAUDE.md` is missing, unreadable, or invalid UTF-8; the warning includes the resolved plugin path and tells the model not to give Founder OS advice until restored, while the hook itself does not crash the host. `parse_frontmatter` accepts only mapping/null YAML; `_tool_names` accepts only string or list-of-strings; one validated ownership loader supplies every ownership/sections check and rejects scalar/list roots, scalar `owns`, non-list path collections, and mixed element types through controlled `ValueError` findings.

**Test:** `python3 -m unittest tests.test_session_context tests.test_generate_commands tests.test_validate_package -v` covers mapping, list, scalar, null, false, empty list, mixed tools, scalar owns, and non-list owned paths without traceback.

**Size:** M

- [ ] Add subprocess SessionStart cases and table-driven YAML-shape mutations; assert model-visible JSON, matching stderr, controlled exit behavior, and `FAIL:` output.
- [ ] Run focused suites and record RED failures for silent context loss and uncaught/incorrect YAML shapes.
- [ ] Implement warning output, strict frontmatter/tools validation, and the single ownership-schema loader used by all validator checks.
- [ ] Re-run focused tests, installed-copy smoke, full Python suite, package validation, generated-command check, and `git diff --check`.
- [ ] Commit only Task 7 files with an explicit pathspec and message `fix: surface context and YAML contract failures`.

### Task 8: Trust Center and Local Link/Anchor Validation

**What:** Ship the missing deployable Trust Center page and a repository-wide validator for every tracked local Markdown/HTML target and anchor.

**Where:** Create `docs/trust.html`, `scripts/check_local_links.py`, `tests/test_local_links.py`; modify `tests/test_docs_workflows.py`, `docs/trust.md`, `docs/index.html`, and `.github/workflows/ci.yml` to pin the shared claims and run the new check.

**How:** `trust.html` is a complete static page at the manifest/landing URL and carries the required claims from `trust.md`: one shared product, local state gateway/no network or telemetry, role ownership, no outbound/no money, host data-handling boundary, installed-copy behavior, and non-security-sandbox hook caveat. The link checker parses tracked Markdown links and HTML `href`/`src`, decodes relative targets, ignores approved external/mail/fragmentless schemes, indexes Markdown headings and HTML `id`/`name`, and fails for missing files, duplicate/missing anchors, or repository escape.

**Test:** `python3 -m unittest tests.test_local_links tests.test_docs_workflows -v` plus `python3 scripts/check_local_links.py` begins RED on missing `trust.html` and any fixture-broken target/anchor, then passes on the real repository.

**Size:** M

- [ ] Write trust-claim parity and temporary-tree link/anchor tests with literal expected diagnostics.
- [ ] Run focused tests and record RED failures for the missing page and checker.
- [ ] Create the accessible static Trust Center, implement the parser/checker, and wire it into CI.
- [ ] Run focused tests, the real local-link command, Node behavior tests, full Python tests, package validation, and `git diff --check`.
- [ ] Commit only Task 8 files with explicit paths and message `docs: ship and validate the Trust Center`.

### Task 9: Website Focus Transfer and Truthful Clipboard Fallback

**What:** Close A11Y-006 and A11Y-007 so in-panel navigation never hides focus and clipboard fallback never announces an unconfirmed copy.

**Where:** Create `docs/workspace-demo.js`; modify `docs/index.html` and `tests/docs_workflows.behavior.test.js`.

**How:** Export `openWorkspaceFile(name)` and `copyInstallCommand(button)` from `workspace-demo.js` through the existing browser/CommonJS pattern and load the file with a same-origin script element. `openWorkspaceFile` returns the active panel. Only `.sample-next` controls inside the panel being hidden move focus to the new panel's first heading after setting `tabIndex = -1`; initial render and persistent sidebar activation do not steal focus. Clipboard fallback records `document.activeElement`, inserts/selects a temporary textarea, treats `execCommand('copy') === false` as failure, removes the textarea and restores focus in `finally`, shows `✓`/success live text only after confirmed copy, and otherwise announces a truthful manual-copy instruction.

**Test:** `node --test tests/*.behavior.test.js` covers keyboard activation, in-panel focus transfer, no initial/sidebar focus theft, native clipboard success, fallback success, false fallback, thrown fallback, cleanup, focus restoration, and live-region text.

**Size:** M

- [ ] Add behavior tests against real exported controller functions and DOM fakes; assert the exact visible/focused panel and absence of temporary textareas.
- [ ] Run Node tests and record RED failures for hidden focus and false/exception copy paths.
- [ ] Move the existing workspace and clipboard controllers into the same-origin CommonJS-compatible module and implement the minimal focus/copy fixes there.
- [ ] Re-run Node tests, Python docs/link tests, package validation, and `git diff --check`.
- [ ] Commit only Task 9 files with explicit paths and message `fix: preserve website focus and clipboard truth`.

### Task 10: Documentation, Counts, Release Metadata, and Tracked Planning

**What:** Synchronize all public/internal documentation with the executable full-host 2.5.0 contract and make the required planning system trackable.

**Where:** Modify `.gitignore`, `README.md`, `founder-os/README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `docs/README.md`, `docs/agents.md`, `docs/architecture.md`, `docs/concepts.md`, `docs/data-integrity.md`, `docs/development.md`, `docs/enforcement.md`, `docs/getting-started.md`, `docs/house-rules.md`, `docs/troubleshooting.md`, `docs/workspace-state.md`, `docs/commands.md`, `.claude-plugin/marketplace.json`, `founder-os/.claude-plugin/plugin.json`, `founder-os/.codex-plugin/plugin.json`, `feature_list.json`, `tests/test_release_metadata.py`, and count assertions in existing tests; regenerate `founder-os/COMMANDS.md` only with `scripts/generate_commands.py`.

**How:** Remove only `docs/superpowers` from `.gitignore`; leave `.superpowers/` ignored. Replace fail-open/native-file-tool/nested-manager claims with the executable gateway/capability/sibling contract, document Claude/Codex install and generic fallback truthfully, synchronize agent/workflow/cadence/validator/doctor counts from package sources, add the current 2.5.0 changelog section without rewriting historical releases, and keep every manifest at 2.5.0. Release tests assert the current full-host contract and trust URL rather than the historical 2.4.0 manual/beta wording.

**Test:** `python3 -m unittest tests.test_release_metadata tests.test_docs_workflows tests.test_validate_package -v`, generator `--check`, link checker, and package validator detect any stale count/version/architecture/doctor/troubleshooting claim.

**Size:** L

- [ ] Add failing release/count/document-contract tests that derive expected totals from agents, skills, cadence rows, validator `CHECKS`, and doctor sections.
- [ ] Run focused tests and record RED failures for current 2.4.0/full-host/count/ignore drift.
- [ ] Update metadata and docs, run `python3 scripts/generate_commands.py founder-os`, and preserve historical changelog text below the new section.
- [ ] Re-run release/docs/validator/link tests, generated-command check, all Python/Node suites, package validation, both plugin validators, and `git diff --check`.
- [ ] Commit only explicit Task 10 paths with message `docs: synchronize Founder OS 2.5.0 host parity`; verify the unrelated staged deletion remains staged.

### Task 11: Installed-Copy Lifecycle, Real Host Probes, and Release Gate

**What:** Exercise the copied package and both installed hosts through their real configuration/discovery paths, then run the complete release verification matrix and close the plan only on evidence.

**Where:** Create `scripts/probe_installed_hosts.py` and `tests/test_installed_host_probes.py`; modify `scripts/smoke_installed_copy.py`, `tests/test_session_context.py`, `.github/workflows/ci.yml`, and this plan's checkboxes/status log.

**How:** Installed-copy smoke starts the copied MCP subprocess through each adapter and performs initialize/list/call, SessionStart success/warning, real SubagentStart `turn_id` mapping, workspace resolution, role open, read, CFO write, Strategist wrong-owner denial, stale-write denial, bad-structure denial, close/reuse denial, and repository-mutation detection. The host probe uses isolated local marketplace/install roots, verifies Claude and Codex discover the copied 2.5.0 plugin, runs one role I/O cycle on each, and exercises native and generic fallback orchestration wherever the CLI exposes both. An unavailable CLI, skipped role call, or missing persistence is a failing release result, not a skip.

**Test:** Every command in the final matrix below must exit zero freshly; host probes must print explicit Claude and Codex PASS records with persisted hashes and no business content.

**Size:** L

- [ ] Add failing installed-copy/host-probe tests for config path use, MCP lifecycle, role I/O, wrong owner, stale write, structure failure, and hard-fail unavailable host behavior.
- [ ] Run focused tests and record RED failures because the current smoke injects `agent_type` and never starts the gateway or real hosts.
- [ ] Extend installed-copy smoke and implement isolated CLI probes without changing global marketplace/config files or publishing anything.
- [ ] Run the exact final matrix:

```bash
python3 scripts/validate_package.py founder-os
python3 scripts/generate_commands.py founder-os --check
python3 scripts/smoke_installed_copy.py
python3 -m unittest discover -s tests -v
node --test tests/*.behavior.test.js
claude plugin validate .
claude plugin validate founder-os
python3 /Users/msolecki/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py founder-os
python3 scripts/probe_installed_hosts.py --claude --codex --require-native-and-fallback
python3 scripts/check_local_links.py
git diff --check
git status --short --branch
```

- [ ] Verify `git status --short --branch` shows the pre-existing staged deletion plus only Task 11 implementation changes; record all command exit codes and concise output in the task report.
- [ ] Commit only `scripts/probe_installed_hosts.py`, `tests/test_installed_host_probes.py`, `scripts/smoke_installed_copy.py`, `tests/test_session_context.py`, and `.github/workflows/ci.yml` with message `test: prove installed Claude and Codex role IO`.
- [ ] Run a fresh task review, fix all Critical/Important findings through the task fix loop, and obtain both spec-compliance and quality approval.
- [ ] Dispatch a fresh whole-branch reviewer using the approved spec, this completed plan, the SDD ledger, and the full branch diff; one author/reviewer pair may not be the same agent.
- [ ] If final review finds issues, use one fresh fix agent and one scoped re-review, then re-run the entire final matrix.
- [ ] Update every task checkbox and append the final evidence/status section to this plan; commit only this plan with `--only --no-gpg-sign`.

## Coverage Matrix

| Requirement | Plan task |
|---|---:|
| Dependency-light local stdio MCP, initialize/list/call | 1 |
| Safe resolve/list/read/read-reference and role sessions | 2 |
| Ownership, sections, SHA-256, atomic write, journal | 3 |
| Claude/Codex adapters, hooks, SubagentStart/turn_id, outbound denial | 4 |
| Sibling agents and portable generic fallback | 5 |
| Onboarding, strategic evaluation, and manager migration | 6 |
| ERR-001 SessionStart visibility | 7 |
| TYPE-001/002/003 YAML shape hardening | 7 |
| Trust Center and all local links/anchors | 8 |
| A11Y-006 focus and A11Y-007 clipboard fallback | 9 |
| Counts, docs, metadata 2.5.0, `.gitignore` | 10 |
| TEST-011 real SubagentStart smoke and both host probes | 4, 11 |
| Full verification and fresh independent review | 11 |

## Progress Log

- 2026-07-27: Approved specification committed alone as `e5ec258`; unrelated staged deletion preserved.
- 2026-07-27: Implementation plan created in `fc146de`; execution began at Task 1.
- 2026-07-27: Task 1 completed in `e07c4be`. RED: 7 protocol tests produced 6 failures and 1 error because the module and entry point did not exist. GREEN: 7/7 focused tests, 231/231 full Python tests, and 2/2 Node behavior tests passed; package validation reported 13 agents, 52 skills, 0 errors; command generation and `git diff --check` were clean. Independent review found no Critical or Important issues and approved task quality; one schema-assertion coverage note was deferred to the later gateway behavior tests. The unrelated staged deletion remained staged.
- 2026-07-27: Task 2 completed in `fba8df3` with security hardening in `4da710c`. Initial REDs proved the missing resolver/session/safe-I/O interfaces; GREEN reached 38/38 Task 1–2 tests. Independent review then found three Important fail-closed gaps in registry validation, persisted-session validation, and ancestor-symlink handling. Fix-round RED reproduced all three; the scoped re-review approved the strict single registry parser, exact untrusted-record validation, and trusted-root descriptor walk with no remaining findings. Final GREEN: 45/45 focused/protocol tests, 269/269 full Python tests, and 2/2 Node tests; package validation reported 13 agents, 52 skills, 0 errors; command generation and `git diff --check` were clean. The Task 1 schema-assertion note is resolved by exact seven-schema tests, and the unrelated staged deletion remained staged.
