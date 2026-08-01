# Founder OS Audit Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close all twelve audit findings with capability-scoped workspace access, a compliant MCP lifecycle, durable bounded state, safe cross-host cadences, accurate documentation, and executable regression coverage.

**Architecture:** Keep the stdlib-only gateway and assign each behavior to its existing boundary: workspace authority in `workspaces.py`, role authority and retention in `sessions.py`, state mechanics in `safe_io.py`, transport lifecycle in `protocol.py`, and host scheduling in one new focused script. Add one portfolio-only MCP tool rather than widening ordinary reads, then verify the installed package on Claude Code and Codex.

**Tech Stack:** Python 3.9 standard library, `unittest`, JSON-RPC 2.0/MCP over stdio, Markdown/YAML package metadata, Node's built-in test runner.

## Global Constraints

- Python 3.9 remains the minimum interpreter; add no third-party runtime dependency.
- Preserve stable domain error codes and fail-closed actions.
- Keep business reads and all writes bound to one resolved workspace.
- Permit cross-business reads only through `read_portfolio_inputs`, for active businesses and the three fixed sections in the approved design.
- Require one explicit founder confirmation before scheduler mutation and write no scheduler artifact into `FOUNDER_OS_HOME`.
- Do not modify or restore the user's staged deletion of `docs/design/2026-07-31-decision-first-activation-design.md`.
- Use `apply_patch`; run each RED command before production edits.
- Canonical design: `docs/superpowers/specs/2026-08-01-founder-os-audit-remediation-design.md`.

## File Responsibility Map

- `founder-os/mcp/workspaces.py`: typed bindings, disjoint roots, registry revalidation, bounded business lookup.
- `founder-os/mcp/sessions.py`: role/workflow authority, capability retention, journal rotation.
- `founder-os/mcp/safe_io.py`: fixed-section reads, pagination, durable atomic writes.
- `founder-os/mcp/gateway.py`: eight closed MCP schemas and dispatch.
- `founder-os/mcp/protocol.py`: JSON-RPC validation and MCP lifecycle.
- `founder-os/hooks/ownership-guard.py`, `record-agent.py`: defense in depth and bounded hook data.
- `founder-os/scripts/cadence_manager.py`: deterministic preview, backup, exact merge, apply, removal, and smoke commands.
- `tests/`: behavior at the real module, stdio, hook, documentation, and installed-package boundaries.

---

### Task 1: Typed, Disjoint, Current Workspace Bindings

**Files:**
- Modify: `founder-os/mcp/workspaces.py`
- Modify: `founder-os/mcp/gateway.py`
- Test: `tests/test_state_gateway_reads.py`

**Interfaces:**
- Consumes: current registry keys `businesses`, `default`, and `portfolio`.
- Produces: `WorkspaceBinding.workspace_kind: str`, `WorkspaceResolver.validate_binding(binding) -> WorkspaceBinding`, `WorkspaceResolver.portfolio_business_root(binding, business_slug) -> Path`.

- [ ] **Step 1: Write failing kind and collision tests**

Add literal assertions to `WorkspaceResolverReadTests`:

```python
def test_bindings_report_all_workspace_kinds(self) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        project = root / "project"
        project.mkdir()
        single = WorkspaceResolver(env={}, home=root / "single-home").resolve(project)
        self.assertEqual("single-business", single.workspace_kind)

        alpha = root / "alpha"
        portfolio = root / "portfolio"
        alpha.mkdir()
        portfolio.mkdir()
        home = root / "home"
        write_registry(home, "\n".join((
            "businesses:",
            "  alpha:",
            "    home: " + alpha.as_posix(),
            "    status: active",
            "portfolio: " + portfolio.as_posix(),
        )))
        resolver = WorkspaceResolver(env={}, home=home)
        self.assertEqual("business", resolver.resolve(project, "alpha").workspace_kind)
        self.assertEqual("portfolio", resolver.resolve(project, "portfolio").workspace_kind)

def test_registry_rejects_equal_parent_and_child_roots(self) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        project = root / "project"
        project.mkdir()
        for name, alpha, beta in (
            ("equal", root / "shared", root / "shared"),
            ("nested", root / "shared", root / "shared" / "child"),
        ):
            with self.subTest(name=name):
                home = root / ("home-" + name)
                write_registry(home, "\n".join((
                    "businesses:",
                    "  alpha:",
                    "    home: " + alpha.as_posix(),
                    "    status: active",
                    "  beta:",
                    "    home: " + beta.as_posix(),
                    "    status: paused",
                )))
                self.assert_unresolved(
                    lambda home=home: WorkspaceResolver(env={}, home=home).resolve(project, "alpha")
                )
```

Add a third test: resolve `alpha`, rewrite its registry root, and assert
`validate_binding(binding)` raises `WORKSPACE_UNRESOLVED`.

- [ ] **Step 2: Verify RED**

Run:

```bash
python3 -m unittest tests.test_state_gateway_reads.WorkspaceResolverReadTests -v
```

Expected: no `workspace_kind`; equal/nested roots and changed bindings are accepted.

- [ ] **Step 3: Implement the minimal workspace contract**

Use this dataclass shape:

```python
@dataclass(frozen=True)
class WorkspaceBinding:
    workspace_id: str
    business_slug: Optional[str]
    display_path: str
    root: Path
    workspace_kind: str
```

Resolve every business and portfolio root during registry validation. For each
pair, reject equality and ancestry in either direction. Return
`single-business`, `business`, or `portfolio` from selection. Implement
`validate_binding` by reloading the current registry and matching slug, root,
and kind exactly. Implement `portfolio_business_root` by validating a portfolio
binding and returning only one explicitly named active registered business
root; accept no path argument.

Return `workspace_kind` from `resolve_workspace`. In `_session_workspace`, call
`validate_binding` before any I/O.

- [ ] **Step 4: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_state_gateway_reads.WorkspaceResolverReadTests -v
git add founder-os/mcp/workspaces.py founder-os/mcp/gateway.py tests/test_state_gateway_reads.py
git -c commit.gpgsign=false commit --only -m "fix(state): enforce disjoint workspace kinds" -- founder-os/mcp/workspaces.py founder-os/mcp/gateway.py tests/test_state_gateway_reads.py
```

---

### Task 2: Role-Owned Workflows and Portfolio-Only Inputs

**Files:**
- Modify: `founder-os/mcp/sessions.py`
- Modify: `founder-os/mcp/safe_io.py`
- Modify: `founder-os/mcp/gateway.py`
- Modify: `founder-os/hooks/ownership-guard.py`
- Modify: `founder-os/agents/portfolio-manager.md`
- Modify: `founder-os/skills/portfolio-review/SKILL.md`
- Test: `tests/test_state_gateway_reads.py`
- Test: `tests/test_state_gateway_writes.py`
- Test: `tests/test_ownership_guard.py`
- Test: `tests/test_host_adapters.py`
- Test: `tests/test_session_context.py`
- Test: `tests/test_onboarding_activation.py`

**Interfaces:**
- Consumes: Task 1's workspace kinds and portfolio lookup.
- Produces: required `workflow`; `RoleSessionStore.open(workspace_id, role, correlation_id, workflow, workspace_kind)`; `RoleSessionMetadata.workspace_kind: str`; `SafeStateIO.read_fixed_sections(spec) -> dict`; MCP tool `read_portfolio_inputs`.

- [ ] **Step 1: Make test agents express real ownership**

Replace header-only fixture agents with minimal frontmatter using this
independently defined map and create every named fixture skill:

```python
ROLE_WORKFLOWS = {
    "board-member": ("red-team",),
    "brand-editor": ("content-plan",),
    "cfo": ("revenue-review",),
    "chief-of-staff": ("daily-brief",),
    "delivery-lead": ("capacity-check",),
    "focus-coach": ("week-plan",),
    "network-manager": ("follow-up-sweep",),
    "ops-engineer": ("automation-audit",),
    "pipeline-coach": ("pipeline-review",),
    "portfolio-manager": ("portfolio-review",),
    "positioning-advisor": ("offer-design",),
    "skills-mentor": ("skill-gap",),
    "strategist": ("quarterly-planning",),
}
```

Update direct store calls to pass a listed workflow and explicit kind.
Update every gateway `open_role_session` fixture outside the focused read tests
to pass its role-owned workflow; preserve one explicit missing-workflow case as
the regression that proves the new requirement.

- [ ] **Step 2: Write failing authorization tests**

Assert these calls raise `ROLE_SESSION_INVALID`:

```python
self.store.open("workspace-1", "chief-of-staff", "corr-missing", None, "business")
self.store.open("workspace-1", "chief-of-staff", "corr-wrong", "week-plan", "business")
self.store.open("workspace-1", "portfolio-manager", "corr-business", "portfolio-review", "business")
self.store.open("workspace-1", "chief-of-staff", "corr-portfolio", "daily-brief", "portfolio")
```

Add successful focus-coach/business and portfolio-manager/portfolio cases.

- [ ] **Step 3: Write failing bounded portfolio tests**

Create active business files with allowed headings and private content under
other headings. Open a portfolio-review session and assert:

```python
payload = self.payload(self.gateway.call(
    "read_portfolio_inputs",
    {"capability": capability, "business_slug": "alpha"},
))
self.assertEqual("alpha", payload["business_slug"])
self.assertEqual(
    [
        ("goals.md", "Bets", "Alpha bet\n"),
        ("metrics.md", "Close", "100 collected\n"),
        ("metrics.md", "Runway", "6 months\n"),
    ],
    [(item["path"], item["heading"], item["content"]) for item in payload["sections"]],
)
self.assertNotIn("PRIVATE PIPELINE", json.dumps(payload))
self.assertEqual([], payload["missing"])
```

Separately assert absent Runway returns `metrics.md#Runway` in `missing`, a
paused slug returns `WORKSPACE_UNRESOLVED`, another role returns
`ROLE_SESSION_INVALID`, and extra input property `paths` is rejected.

- [ ] **Step 4: Verify RED**

```bash
python3 -m unittest tests.test_state_gateway_reads tests.test_state_gateway_writes tests.test_ownership_guard tests.test_host_adapters tests.test_session_context tests.test_onboarding_activation -v
```

Expected: workflow mismatches succeed and the portfolio tool is unknown.

- [ ] **Step 5: Implement frontmatter and workspace enforcement**

Parse only the `skills:` list inside agent frontmatter; reject malformed or
duplicate entries and any package that does not yield thirteen role maps.
Require `workflow` in the open-tool schema and persist `workspace_kind`.
Enforce exactly:

```python
if workflow not in self._role_workflows().get(role, frozenset()):
    raise RoleSessionError()
if role == "portfolio-manager":
    if workspace_kind != "portfolio" or workflow != "portfolio-review":
        raise RoleSessionError()
elif workspace_kind == "portfolio":
    raise RoleSessionError()
elif workspace_kind not in {"single-business", "business"}:
    raise RoleSessionError()
```

Extend the ownership guard's exact open-session `SESSION_FIELDS` set with
`workspace_kind`, so defense in depth reads the new live record shape instead
of silently rejecting every valid capability.

- [ ] **Step 6: Implement fixed-section reads and the eighth tool**

Use the internal constant:

```python
PORTFOLIO_INPUTS = {
    "goals.md": ("Bets",),
    "metrics.md": ("Close", "Runway"),
}
```

Recognize exact H2 headings outside fenced code. Return body, path, heading,
full-file SHA-256, and mtime. Only missing files/headings become fixed
`path#Heading` gaps; unsafe files remain `STATE_IO_ERROR`.

Add a closed `read_portfolio_inputs` schema. Require portfolio-manager,
portfolio-review, and portfolio kind; resolve the active slug through Task 1;
accept no model-supplied paths/headings. Add the tool to the ownership guard
and portfolio-manager frontmatter only; update portfolio-review usage text.

- [ ] **Step 7: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_state_gateway_reads tests.test_state_gateway_writes tests.test_ownership_guard tests.test_host_adapters tests.test_session_context tests.test_onboarding_activation -v
git add founder-os/mcp/sessions.py founder-os/mcp/safe_io.py founder-os/mcp/gateway.py founder-os/hooks/ownership-guard.py founder-os/agents/portfolio-manager.md founder-os/skills/portfolio-review/SKILL.md tests/test_state_gateway_reads.py tests/test_state_gateway_writes.py tests/test_ownership_guard.py tests/test_host_adapters.py tests/test_session_context.py tests/test_onboarding_activation.py
git -c commit.gpgsign=false commit --only -m "fix(state): bind workflows and portfolio reads" -- founder-os/mcp/sessions.py founder-os/mcp/safe_io.py founder-os/mcp/gateway.py founder-os/hooks/ownership-guard.py founder-os/agents/portfolio-manager.md founder-os/skills/portfolio-review/SKILL.md tests/test_state_gateway_reads.py tests/test_state_gateway_writes.py tests/test_ownership_guard.py tests/test_host_adapters.py tests/test_session_context.py tests/test_onboarding_activation.py
```

---

### Task 3: MCP Lifecycle and JSON-RPC Validation

**Files:**
- Modify: `founder-os/mcp/protocol.py`
- Test: `tests/test_state_gateway_protocol.py`

**Interfaces:**
- Consumes: Task 2's eight-tool `Gateway`.
- Produces: states `new -> initializing -> ready`; protocol versions `2025-11-25` and `2025-06-18`; `ping`.

- [ ] **Step 1: Write failing lifecycle tests**

Initialize direct-server tool tests with this helper:

```python
def ready(server) -> None:
    response = server.handle_message(_request(
        1,
        "initialize",
        {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {"name": "contract-test", "version": "1.0"},
        },
    ))
    assert response["result"]["protocolVersion"] == "2025-11-25"
    assert server.handle_message({
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
    }) is None
```

Add literal cases for missing/wrong `jsonrpc`, null/bool IDs, malformed
initialize params, tools before ready, duplicate initialize, initialized in the
wrong state, both supported versions, unsupported-version fallback, ping in
every state, unknown valid notifications, and structurally invalid
notifications. Require `-32600`, `-32602`, `-32601`, or `-32002` exactly as
specified by the design.

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_state_gateway_protocol -v
```

Expected: tools work before initialize, ping is unknown, and bad envelopes pass.

- [ ] **Step 3: Implement validation and state**

Define:

```python
SUPPORTED_PROTOCOL_VERSIONS = ("2025-11-25", "2025-06-18")
NOT_INITIALIZED = -32002
```

Validate `jsonrpc`, method, notification/request shape, and finite string or
numeric IDs excluding bool/null before dispatch. Validate initialize's
non-empty `protocolVersion`, mapping `capabilities`, and `clientInfo` with
non-empty name/version. Permit ping in every state; initialize only in `new`;
initialized notification only advances `initializing`; tools require `ready`.
Valid notifications return no response. Keep the stdio parse and internal-error
guards.

- [ ] **Step 4: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_state_gateway_protocol -v
git add founder-os/mcp/protocol.py tests/test_state_gateway_protocol.py
git -c commit.gpgsign=false commit --only -m "fix(mcp): enforce protocol lifecycle" -- founder-os/mcp/protocol.py tests/test_state_gateway_protocol.py
```

---

### Task 4: Deterministic Paginated State Discovery

**Files:**
- Modify: `founder-os/mcp/safe_io.py`
- Modify: `founder-os/mcp/gateway.py`
- Test: `tests/test_state_gateway_reads.py`

**Interfaces:**
- Consumes: existing pattern/path rules and capability-bound gateway reads.
- Produces: `SafeStateIO.list_markdown_page(pattern, limit=100, cursor=None) -> Dict[str, object]`; optional `limit`/`cursor` for `list_state`.

- [ ] **Step 1: Write failing pagination tests**

Create 205 real files and traverse them:

```python
seen = []
cursor = None
while True:
    page = self.io(max_results=100).list_markdown_page(
        "reviews/daily/*.md", limit=37, cursor=cursor
    )
    seen.extend(page["paths"])
    cursor = page["next_cursor"]
    if cursor is None:
        break
self.assertEqual(
    ["reviews/daily/{:03d}.md".format(index) for index in range(205)],
    seen,
)
```

Add cases for limits `0`, `101`, bool, string; malformed base64; cursor reused
with another pattern; and deletion of the cursor-boundary file. The
last case must resume after its encoded lexical path without duplication.

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_state_gateway_reads.SafeStateIOTests tests.test_state_gateway_reads.GatewayIntegrationTests -v
```

Expected: page method missing; gateway rejects limit/cursor.

- [ ] **Step 3: Implement pattern-bound cursors and pages**

Encode strict compact JSON as URL-safe base64:

```python
payload = {
    "v": 1,
    "pattern_sha256": hashlib.sha256(pattern.encode("utf-8")).hexdigest(),
    "after": last_path,
}
```

Reject unknown fields, invalid UTF-8/JSON/types, pattern mismatch, and unsafe
`after`. Traverse eligible Markdown paths lexically, skip `<= after`, retain
only `limit + 1`, and use the extra record only to make `next_cursor`.

Keep `list_markdown` as a compatibility wrapper: request `max_results`, then
raise `STATE_IO_ERROR` when a next cursor exists. Add optional integer limit
(1–100, excluding bool) and string cursor to the closed gateway schema; return
both `paths` and `next_cursor`.

- [ ] **Step 4: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_state_gateway_reads -v
git add founder-os/mcp/safe_io.py founder-os/mcp/gateway.py tests/test_state_gateway_reads.py
git -c commit.gpgsign=false commit --only -m "fix(state): paginate bounded listings" -- founder-os/mcp/safe_io.py founder-os/mcp/gateway.py tests/test_state_gateway_reads.py
```

---

### Task 5: Durable Renames and Bounded Runtime Data

**Files:**
- Modify: `founder-os/mcp/safe_io.py`
- Modify: `founder-os/mcp/sessions.py`
- Modify: `founder-os/hooks/record-agent.py`
- Test: `tests/test_state_gateway_writes.py`
- Test: `tests/test_ownership_guard.py`

**Interfaces:**
- Consumes: Task 2's session record including `workspace_kind`.
- Produces: directory sync after replace; `closed_at`/`expired_at`; seven-day session retention; 24-hour mapping retention; 5 MiB journal rotation with three archives.

- [ ] **Step 1: Write failing directory-durability tests**

Patch module-local OS boundaries only to observe syscall order. Assert a
directory `fsync` occurs after `replace` for state, session, and hook mapping
writes. Make the final directory sync raise `OSError` and assert the component
returns `STATE_IO_ERROR` or `ROLE_SESSION_INVALID` rather than success.

- [ ] **Step 2: Verify durability RED**

```bash
python3 -m unittest tests.test_state_gateway_writes tests.test_ownership_guard -v
```

Expected: no parent directory is synced after current replaces.

- [ ] **Step 3: Implement the durable sequence**

After each replace, `fsync` the already-open trusted parent descriptor. For
path-based session/hook directories, open the exact directory with
`O_RDONLY | O_DIRECTORY | O_CLOEXEC` where available, verify `fstat` is a
directory, sync, close, and map failure to the component's existing error. Do
not retry a replace.

- [ ] **Step 4: Write failing retention tests**

With injected clocks, create fresh/stale closed, expired, and abandoned open
records. Assert lifecycle cleanup deletes only records older than
`7 * 24 * 60 * 60` and examines at most 256 candidates. Run `record-agent.py`
against fresh and >24-hour mapping files; only the old regular file may vanish.

- [ ] **Step 5: Write failing rotation tests**

Use a test-only constructor threshold of 128 bytes, append complete events, and
assert:

```python
self.assertTrue((self.data_root / "operations.jsonl").is_file())
self.assertTrue((self.data_root / "operations.jsonl.1").is_file())
self.assertLessEqual(
    len([path for path in (
        self.data_root / "operations.jsonl.1",
        self.data_root / "operations.jsonl.2",
        self.data_root / "operations.jsonl.3",
    ) if path.exists()]),
    3,
)
for path in (
    self.data_root / "operations.jsonl",
    self.data_root / "operations.jsonl.1",
):
    for line in path.read_text(encoding="utf-8").splitlines():
        self.assertIsInstance(json.loads(line), dict)
```

Add symlink/non-regular rejection and two concurrent preflights guarded by an
exclusive lock.

- [ ] **Step 6: Verify retention/rotation RED**

Run the Step 2 command. Expected: stale files remain and journal never rotates.

- [ ] **Step 7: Implement bounded cleanup and rotation**

Persist `closed_at` and `expired_at`. Before new sessions, scan at most 256
regular non-symlink records and unlink only beyond seven days, syncing after a
batch. Apply the same bounded algorithm to agent mappings using a 24-hour mtime
cutoff.

Before journal append, lock a dedicated regular lock file. At
`5 * 1024 * 1024` bytes rotate `.2 -> .3`, `.1 -> .2`, current -> `.1`, sync
the directory, then reopen current. Reject unexpected file types and retain
three archives. Test overrides change thresholds only, never production
defaults.

- [ ] **Step 8: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_state_gateway_writes tests.test_ownership_guard -v
git add founder-os/mcp/safe_io.py founder-os/mcp/sessions.py founder-os/hooks/record-agent.py tests/test_state_gateway_writes.py tests/test_ownership_guard.py
git -c commit.gpgsign=false commit --only -m "fix(runtime): sync and bound plugin data" -- founder-os/mcp/safe_io.py founder-os/mcp/sessions.py founder-os/hooks/record-agent.py tests/test_state_gateway_writes.py tests/test_ownership_guard.py
```

---

### Task 6: Safe Claude and Codex Cadence Manager

**Files:**
- Create: `founder-os/scripts/cadence_manager.py`
- Create: `tests/test_cadence_manager.py`
- Modify: `founder-os/skills/setup-cadences/SKILL.md`
- Modify: `founder-os/references/multi-business.md`

**Interfaces:**
- Consumes: absolute host binary/workspace/workdir/log root, optional slug, scheduler, date.
- Produces: `CadenceConfig`, `host_argv`, `render_cron_blocks`, `merge_crontab`, `render_launchd`, `render_systemd`; CLI `preview`, `snapshot`, `apply`, `remove`, `smoke`.

- [ ] **Step 1: Write failing exact host-command tests**

Load the new script as a module and assert:

```python
self.assertEqual(
    cadence.host_argv(config_for("claude"), "daily-brief"),
    (
        "/opt/Claude Code/bin/claude", "-p", "/founder-os:daily-brief",
        "--permission-mode", "dontAsk", "--allowedTools",
        "mcp__plugin_founder-os_founder-os-state__*",
        "--max-turns", "50",
    ),
)
self.assertEqual(
    cadence.host_argv(config_for("codex"), "daily-brief"),
    (
        "/opt/Codex App/bin/codex", "-a", "never", "exec",
        "--sandbox", "workspace-write", "--ephemeral", "-C",
        "/Users/Test Founder/work tree", "$founder-os:daily-brief",
    ),
)
```

Use fixture paths containing spaces, a single quote, `$`, `;`, and parentheses.

- [ ] **Step 2: Write failing quoting/fence/snapshot tests**

Use `shlex.split` to prove a rendered cron command reconstructs intended
arguments without executing metacharacters. Merge crontabs containing unrelated
bytes and fences `a`, `acme`, `portfolio`, legacy. Updating `a` must preserve
`acme`; a second merge must be byte-identical; migration removes only legacy;
malformed fences raise `CadenceError`.

With an argv-recording fake runner, snapshot current crontab, preview a
manifest, mutate current state, and assert apply stops before install. With
unchanged state, installed bytes must equal preview and backup bytes the exact
original.

- [ ] **Step 3: Write failing launchd/systemd tests**

Parse LaunchAgent bytes with `plistlib.loads`; require array
`ProgramArguments`, absolute `FOUNDER_OS_HOME`, and four quarterly month
dictionaries. Require `Persistent=true` in systemd timers and no `/bin/sh -c`
in services.

- [ ] **Step 4: Verify RED**

```bash
python3 -m unittest tests.test_cadence_manager -v
```

Expected: module import fails because the script is absent.

- [ ] **Step 5: Implement the pure model and renderers**

Use immutable dataclasses:

```python
@dataclass(frozen=True)
class Cadence:
    workflow: str
    cron: str

@dataclass(frozen=True)
class CadenceConfig:
    host: str
    binary: Path
    workspace: Path
    workdir: Path
    log_root: Path
    slug: Optional[str]
```

Create the package directory with `mkdir -p founder-os/scripts`, then add the
script itself with `apply_patch` after the RED run.

Keep nine business rows plus the Monday portfolio row as literals. Build cron
fields only with `shlex.quote`, launchd with `plistlib`, and systemd argument
tokens without a shell wrapper.

- [ ] **Step 6: Implement preview, snapshot, apply, removal, smoke**

Serialize sorted compact JSON manifests and hash exact bytes. Accept `crontab
-l` return codes 0/1 only. Snapshot before confirmation. Apply only when
manifest checksum and current-state digest match; preserve unrelated bytes;
install via private temp file and argv-only `subprocess.run`. Removal accepts
one exact identity or literal `all`; never prefix regex. Use file and directory
sync for manager-owned artifacts; never `shell=True`.

For launchd, snapshot the selected existing plist files, write only
`~/Library/LaunchAgents/com.founder-os.<identity>.<workflow>.plist`, and invoke
`launchctl bootstrap`/`bootout` with argument arrays after stale-state checks.
For systemd, snapshot only matching files under `~/.config/systemd/user`, write
the selected `.service`/`.timer` pairs, then invoke `systemctl --user
daemon-reload` and `enable --now` by argv. Both paths use the same preview
checksum and exact-identity removal rules as cron.

- [ ] **Step 7: Replace scheduling prose with executable flow**

Detect both hosts and ask which when both exist. Select cron/launchd/systemd by
sleep behavior. Run preview and snapshot, show exact artifacts and backup path,
ask once, then apply those checksums. Document Claude `dontAsk` plus narrow MCP
`--allowedTools`, Codex `-a never exec --sandbox workspace-write`, and manager
removal instead of BSD/GNU-dependent sed.

- [ ] **Step 8: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_cadence_manager -v
git add founder-os/scripts/cadence_manager.py tests/test_cadence_manager.py founder-os/skills/setup-cadences/SKILL.md founder-os/references/multi-business.md
git -c commit.gpgsign=false commit --only -m "fix(cadences): support safe Claude and Codex jobs" -- founder-os/scripts/cadence_manager.py tests/test_cadence_manager.py founder-os/skills/setup-cadences/SKILL.md founder-os/references/multi-business.md
```

---

### Task 7: Documentation, Validators, and Installed Host Probes

**Files:**
- Modify: `README.md`
- Modify: `founder-os/README.md`
- Modify: `founder-os/CLAUDE.md`
- Modify: `docs/README.md`
- Modify: `docs/getting-started.md`
- Modify: `docs/cadences.md`
- Modify: `docs/commands.md`
- Modify: `docs/concepts.md`
- Modify: `docs/architecture.md`
- Modify: `docs/multi-business.md`
- Modify: `docs/trust.md`
- Modify: `docs/troubleshooting.md`
- Modify: `docs/index.html`
- Modify: `founder-os/references/extensibility.md`
- Modify: `founder-os/references/orchestration.md`
- Modify: `founder-os/skills/skill-forge/SKILL.md`
- Modify: `scripts/validate_package.py`
- Modify: `tests/test_validate_package.py`
- Modify: `tests/test_release_metadata.py`
- Modify: `tests/test_docs_workflows.py`
- Modify: `tests/docs_workflows.behavior.test.js`
- Modify: `tests/test_installed_host_probes.py`

**Interfaces:**
- Consumes: Task 2's eight-tool surface, Task 6's host commands, 53 packaged workflows.
- Produces: host-specific copy/invocation behavior and validators that reject count/tool/command drift.

- [ ] **Step 1: Write failing documentation behavior tests**

Require both host sections independently:

```python
self.assertIn("/founder-os:founder-os-init", claude_section)
self.assertIn("/founder-os:setup-cadences", claude_section)
self.assertIn("$founder-os:founder-os-init", codex_section)
self.assertIn("$founder-os:setup-cadences", codex_section)
```

In JavaScript, click Claude and Codex onboarding/cadence copy buttons
separately and assert the clipboard receives the matching slash or dollar
syntax. Add validator fixtures that mutate each canonical count from 53 to 52
and require a count-drift error.

- [ ] **Step 2: Extend installed probes before documentation changes**

Make isolated probes send initialize, then initialized notification, then
tools/list and ping. Assert eight tools. Run cadence-manager preview for Claude
and Codex without a model or scheduler mutation; assert MCP allowlist in Claude
and workspace-write plus dollar skill syntax in Codex.

- [ ] **Step 3: Verify RED**

```bash
python3 -m unittest tests.test_validate_package tests.test_release_metadata tests.test_docs_workflows tests.test_installed_host_probes -v
node --test tests/docs_workflows.behavior.test.js
```

Expected: slash-only Codex examples, seven-tool expectations, stale counts,
and pre-initialize probes fail.

- [ ] **Step 4: Update host-facing documentation**

Use namespaced slash commands for Claude Code and dollar-prefixed skills for
Codex. Describe nine business schedules and a tenth only for qualifying
multi-business portfolios. Explain cron no-catch-up, launchd/systemd
persistence, MCP permission flags, backup, logs, smoke, and exact removal.
Update visible HTML and copy data together.

Describe seven common role tools plus one portfolio-only tool. Change intended
workflow-count prose to 53. Preserve unrelated examples such as "fifty files"
in linking documentation.

- [ ] **Step 5: Update validator contracts**

Derive the skill-directory count; require canonical 53-count statements;
require eight gateway schemas; require `read_portfolio_inputs` only for
portfolio-manager. Replace phrase-based `seven-tool` tests with actual common
and portfolio-only set assertions.

- [ ] **Step 6: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_validate_package tests.test_release_metadata tests.test_docs_workflows tests.test_installed_host_probes -v
node --test tests/docs_workflows.behavior.test.js
git add README.md founder-os/README.md founder-os/CLAUDE.md docs/README.md docs/getting-started.md docs/cadences.md docs/commands.md docs/concepts.md docs/architecture.md docs/multi-business.md docs/trust.md docs/troubleshooting.md docs/index.html founder-os/references/extensibility.md founder-os/references/orchestration.md founder-os/skills/skill-forge/SKILL.md scripts/validate_package.py tests/test_validate_package.py tests/test_release_metadata.py tests/test_docs_workflows.py tests/docs_workflows.behavior.test.js tests/test_installed_host_probes.py
git -c commit.gpgsign=false commit --only -m "docs: align hosts and runtime contracts" -- README.md founder-os/README.md founder-os/CLAUDE.md docs/README.md docs/getting-started.md docs/cadences.md docs/commands.md docs/concepts.md docs/architecture.md docs/multi-business.md docs/trust.md docs/troubleshooting.md docs/index.html founder-os/references/extensibility.md founder-os/references/orchestration.md founder-os/skills/skill-forge/SKILL.md scripts/validate_package.py tests/test_validate_package.py tests/test_release_metadata.py tests/test_docs_workflows.py tests/docs_workflows.behavior.test.js tests/test_installed_host_probes.py
```

---

### Task 8: Integration, Independent Review, and Full Verification

**Files:**
- Modify: only a component and its regression test when fresh integration evidence proves a remaining defect.
- Verify: complete repository and installed-package artifacts.

**Interfaces:**
- Consumes: Tasks 1–7.
- Produces: all twelve audit reproductions passing with the unrelated staged deletion preserved.

- [ ] **Step 1: Record the implementation range and run all Python tests**

Record `git rev-parse HEAD` before Task 1 as the review base. After Task 7 run:

```bash
PYTHONPYCACHEPREFIX=/tmp/founder-os-remediation-pycache python3 -m unittest discover -s tests -v
```

Expected: zero failures/errors. For any failure, invoke
`superpowers:systematic-debugging`, reproduce the responsible boundary, and
perform a new RED/GREEN cycle before continuing.

- [ ] **Step 2: Run package and generated-artifact validation**

```bash
python3 scripts/validate_package.py founder-os
python3 scripts/generate_commands.py founder-os --check
```

Expected: 13 agents, 53 skills, zero errors, no generated-command drift.

- [ ] **Step 3: Run all JavaScript behavior tests**

```bash
node --test tests/*.behavior.test.js
```

Expected: every test passes, including distinct Claude/Codex copy commands.

- [ ] **Step 4: Run links and installed host coverage**

```bash
python3 -m unittest tests.test_local_links tests.test_installed_host_probes tests.test_host_adapters -v
```

Run the existing installed smoke and official Claude/OpenAI plugin validator
commands referenced by those tests. Both adapters must initialize, advertise
eight tools, ping, and render cadence previews.

- [ ] **Step 5: Request independent code review**

Invoke `superpowers:requesting-code-review` with the approved design, this
plan, recorded base SHA, and current HEAD. Fix all Critical and Important
findings using fresh RED/GREEN cycles; reject a finding only with code/test
evidence.

- [ ] **Step 6: Re-run the full gate after review changes**

Repeat Steps 1–4 from new processes. Earlier output is not completion evidence.

- [ ] **Step 7: Verify final diff scope**

```bash
git status --short
git diff --check
git diff --name-status 76d805b..HEAD
```

Expected: remediation files only, no whitespace error, and
`docs/design/2026-07-31-decision-first-activation-design.md` remains deleted in
the working tree exactly as before implementation.

- [ ] **Step 8: Commit only evidence-backed review corrections**

If review required a correction, use the exact affected production and test
paths from Tasks 1–7 and a `fix:` Conventional Commit. If no correction was
needed, create no empty commit.
