#!/usr/bin/env python3
"""Exercise Founder OS from a temporary installed marketplace copy."""
import json
import hashlib
import os
import select
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PLUGIN = REPO_ROOT / "founder-os"
SESSION_SOURCES = ("startup", "resume", "clear", "compact")
CONTEXT_PREFIX = "Founder OS canonical guidance (shared with Claude Code):\n\n"


class SmokeFailure(AssertionError):
    """An installed-copy contract did not hold."""


def tree_fingerprint(root):
    """Hash a source tree without treating interpreter caches as source."""
    root = Path(root)
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if "__pycache__" in relative.parts or path.suffix in (".pyc", ".pyo"):
            continue
        if path.is_symlink():
            payload = os.readlink(path).encode("utf-8", errors="surrogateescape")
            kind = b"link"
        elif path.is_file():
            payload = path.read_bytes()
            kind = b"file"
        else:
            continue
        digest.update(kind + b"\0" + relative.as_posix().encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(payload).digest())
    return digest.hexdigest()


def assert_tree_unchanged(root, expected_fingerprint):
    """Fail when an installed-copy probe mutates the repository package."""
    if tree_fingerprint(root) != expected_fingerprint:
        raise SmokeFailure("source package changed during installed-copy smoke")


def create_installed_copy(source_plugin, marketplace_root):
    """Copy the package into a marketplace-like root and make it identifiable."""
    source_plugin = Path(source_plugin)
    installed_plugin = Path(marketplace_root) / "founder-os"
    installed_plugin.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_plugin, installed_plugin)

    guidance_path = installed_plugin / "CLAUDE.md"
    marker = "<!-- installed-copy-smoke:%s -->" % installed_plugin
    guidance = guidance_path.read_text(encoding="utf-8")
    guidance_path.write_text(
        guidance.rstrip() + "\n\n" + marker + "\n", encoding="utf-8"
    )
    return installed_plugin


def _hook_environment(plugin_root, **overrides):
    env = os.environ.copy()
    env.pop("PLUGIN_ROOT", None)
    env["CLAUDE_PLUGIN_ROOT"] = str(plugin_root)
    env.update({key: str(value) for key, value in overrides.items()})
    return env


def _run_hook(hook_path, payload, env, cwd, label):
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
        timeout=30,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        raise SmokeFailure("%s exited %d: %s" % (
            label, result.returncode, detail
        ))
    return result


def _json_output(result, label):
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SmokeFailure("%s did not emit valid JSON: %s" % (
            label, exc
        )) from exc


def check_session_context(installed_plugin, cwd, hook_plugin_root=None):
    """Exercise every SessionStart source against the copied hook and guidance."""
    installed_plugin = Path(installed_plugin)
    runtime_root = Path(hook_plugin_root or installed_plugin)
    hook_path = installed_plugin / "hooks" / "session-context.py"
    installed_guidance = (installed_plugin / "CLAUDE.md").read_text(
        encoding="utf-8"
    )
    expected_context = CONTEXT_PREFIX + installed_guidance
    env = _hook_environment(runtime_root)
    results = {}

    for source in SESSION_SOURCES:
        payload = {
            "session_id": "installed-copy-%s" % source,
            "transcript_path": str(Path(cwd) / (source + ".jsonl")),
            "cwd": str(cwd),
            "hook_event_name": "SessionStart",
            "source": source,
        }
        label = "SessionStart/%s" % source
        process = _run_hook(hook_path, payload, env, cwd, label)
        output = _json_output(process, label)
        hook_output = output.get("hookSpecificOutput", {})
        if hook_output.get("hookEventName") != "SessionStart":
            raise SmokeFailure("%s omitted the SessionStart event" % label)
        if hook_output.get("additionalContext") != expected_context:
            raise SmokeFailure(
                "%s did not return installed-copy guidance" % label
            )
        results[source] = {
            "output": output,
            "installed_guidance": installed_guidance,
        }

    return results


def check_session_context_warning(installed_plugin, cwd):
    """Prove a broken installed guidance path is visible to the model."""
    installed_plugin = Path(installed_plugin)
    missing_root = Path(cwd) / "missing-installed-plugin"
    hook_path = installed_plugin / "hooks" / "session-context.py"
    env = _hook_environment(missing_root)
    payload = {
        "session_id": "installed-copy-warning",
        "transcript_path": str(Path(cwd) / "warning.jsonl"),
        "cwd": str(cwd),
        "hook_event_name": "SessionStart",
        "source": "startup",
    }
    process = _run_hook(
        hook_path, payload, env, cwd, "SessionStart/missing-guidance"
    )
    output = _json_output(process, "SessionStart/missing-guidance")
    context = output.get("hookSpecificOutput", {}).get("additionalContext")
    stderr = process.stderr.rstrip("\n")
    if not isinstance(context, str) or context != stderr:
        raise SmokeFailure(
            "SessionStart warning was not identical in model context and stderr"
        )
    if "missing" not in context or "Do not give Founder OS advice" not in context:
        raise SmokeFailure("SessionStart warning omitted its fail-visible instruction")
    return {"output": output, "stderr": stderr}


def _empty_allow_output(result, label):
    if result.stdout.strip():
        raise SmokeFailure("%s should allow silently, got: %s" % (
            label, result.stdout.strip()
        ))
    return None


def _issue_installed_capability(installed_plugin, data_root, role):
    """Create a real role session from the installed copy in isolation."""
    code = (
        "import sys,time\n"
        "from pathlib import Path\n"
        "from mcp.sessions import RoleSessionStore\n"
        "store=RoleSessionStore(Path(sys.argv[2]),Path(sys.argv[1]),time.time,300)\n"
        "print(store.open('installed-workspace',sys.argv[3],'installed-smoke',"
        "'revenue-review','business'))\n"
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(installed_plugin)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            code,
            str(installed_plugin),
            str(data_root / "state-gateway"),
            role,
        ],
        capture_output=True,
        text=True,
        cwd=str(data_root.parent),
        env=env,
        timeout=30,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise SmokeFailure(
            "installed role session could not be created: %s"
            % (result.stderr.strip() or "no capability")
        )
    return result.stdout.strip()


def _record_installed_turn(installed_plugin, data_root, workspace_root, turn_id, role):
    """Run the copied SubagentStart hook instead of injecting agent_type."""
    hook_path = Path(installed_plugin) / "hooks" / "record-agent.py"
    env = _hook_environment(installed_plugin, PLUGIN_DATA=data_root)
    result = _run_hook(
        hook_path,
        {
            "hook_event_name": "SubagentStart",
            "turn_id": turn_id,
            "agent_type": role,
        },
        env,
        workspace_root,
        "SubagentStart/%s" % role,
    )
    _empty_allow_output(result, "SubagentStart/%s" % role)
    mapping = Path(data_root) / "agent-types" / (turn_id + ".json")
    try:
        recorded = json.loads(mapping.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SmokeFailure("SubagentStart/%s did not persist turn mapping" % role) from exc
    if (
        not isinstance(recorded, dict)
        or set(recorded) != {"agent_type", "recorded_at"}
        or recorded.get("agent_type") != role
        or not isinstance(recorded.get("recorded_at"), (int, float))
    ):
        raise SmokeFailure("SubagentStart/%s persisted the wrong role" % role)


def check_ownership_guard(installed_plugin, workspace_root):
    """Check gateway allow, direct/elevation/mismatch deny, and main allow."""
    installed_plugin = Path(installed_plugin)
    workspace_root = Path(workspace_root)
    workspace_root.mkdir(parents=True, exist_ok=True)
    data_root = workspace_root / ".plugin-data"
    data_root.mkdir()
    turns = {"cfo": "installed-cfo-turn", "strategist": "installed-strategist-turn"}
    for role, turn_id in turns.items():
        _record_installed_turn(
            installed_plugin, data_root, workspace_root, turn_id, role
        )
    capability = _issue_installed_capability(
        installed_plugin, data_root, "cfo"
    )
    target = workspace_root / "metrics.md"
    guard_path = installed_plugin / "hooks" / "ownership-guard.py"
    env = _hook_environment(
        installed_plugin,
        FOUNDER_OS_HOME=workspace_root,
        PLUGIN_DATA=data_root,
    )
    direct_payload = {
        "tool_name": "Write",
        "cwd": str(workspace_root),
        "tool_input": {"file_path": str(target)},
    }

    gateway_allowed = _run_hook(
        guard_path,
        {
            "turn_id": turns["cfo"],
            "tool_name": "mcp__founder-os-state__read_state",
            "cwd": str(workspace_root),
            "tool_input": {
                "capability": capability,
                "paths": ["metrics.md"],
            },
        },
        env,
        workspace_root,
        "gateway/allowed-role",
    )
    native_allowed = _run_hook(
        guard_path,
        {
            "agent_type": "cfo",
            "tool_name": "mcp__founder-os-state__read_state",
            "cwd": str(workspace_root),
            "tool_input": {
                "capability": capability,
                "paths": ["metrics.md"],
            },
        },
        env,
        workspace_root,
        "gateway/native-role",
    )
    fallback_allowed = _run_hook(
        guard_path,
        {
            "agent_type": "default",
            "tool_name": "mcp__founder-os-state__read_state",
            "cwd": str(workspace_root),
            "tool_input": {
                "capability": capability,
                "paths": ["metrics.md"],
            },
        },
        env,
        workspace_root,
        "gateway/generic-fallback",
    )
    direct_denied = _run_hook(
        guard_path,
        {**direct_payload, "turn_id": turns["cfo"]},
        env,
        workspace_root,
        "gateway/direct-file-denied",
    )
    fallback_direct_denied = _run_hook(
        guard_path,
        {**direct_payload, "agent_type": "default"},
        env,
        workspace_root,
        "gateway/fallback-direct-file-denied",
    )
    wrong_role = _run_hook(
        guard_path,
        {
            "turn_id": turns["strategist"],
            "tool_name": "mcp__founder-os-state__read_state",
            "cwd": str(workspace_root),
            "tool_input": {
                "capability": capability,
                "paths": ["metrics.md"],
            },
        },
        env,
        workspace_root,
        "gateway/wrong-role",
    )
    elevation = _run_hook(
        guard_path,
        {
            "turn_id": turns["cfo"],
            "tool_name": "mcp__founder-os-state__open_role_session",
            "cwd": str(workspace_root),
            "tool_input": {"role": "cfo"},
        },
        env,
        workspace_root,
        "gateway/elevation",
    )
    main_thread = _run_hook(
        guard_path,
        direct_payload,
        env,
        workspace_root,
        "gateway/main-thread",
    )
    # Claude Code runtime shapes: the host namespaces the subagent identity
    # (`founder-os:cfo`) and wraps the plugin server's tool names
    # (`mcp__plugin_founder-os_founder-os-state__*`). The installed guard must
    # speak both, and must not lock a non-role subagent out of reading.
    claude_namespaced_gateway = _run_hook(
        guard_path,
        {
            "agent_type": "founder-os:cfo",
            "tool_name": "mcp__plugin_founder-os_founder-os-state__read_state",
            "cwd": str(workspace_root),
            "tool_input": {
                "capability": capability,
                "paths": ["metrics.md"],
            },
        },
        env,
        workspace_root,
        "gateway/claude-namespaced-role",
    )
    claude_namespaced_direct_denied = _run_hook(
        guard_path,
        {**direct_payload, "agent_type": "founder-os:cfo"},
        env,
        workspace_root,
        "gateway/claude-namespaced-direct-file-denied",
    )
    claude_reviewer_read_allowed = _run_hook(
        guard_path,
        {
            "agent_type": "general-purpose",
            "tool_name": "Read",
            "cwd": str(workspace_root),
            "tool_input": {"file_path": str(target)},
        },
        env,
        workspace_root,
        "gateway/claude-reviewer-read",
    )
    # Self-elevation under the host-registered name. A subagent that opens its
    # own role session picks its own capability and every other gateway check
    # becomes advisory, so this deny has to hold in the shape Claude Code
    # actually sends — not only under the packaged one tested above.
    claude_namespaced_elevation = _run_hook(
        guard_path,
        {
            "agent_type": "founder-os:cfo",
            "tool_name":
            "mcp__plugin_founder-os_founder-os-state__open_role_session",
            "cwd": str(workspace_root),
            "tool_input": {"role": "cfo"},
        },
        env,
        workspace_root,
        "gateway/claude-namespaced-elevation",
    )

    denied = {}
    for label, result in (
        ("direct_file", direct_denied),
        ("fallback_direct_denied", fallback_direct_denied),
        ("claude_namespaced_direct_denied", claude_namespaced_direct_denied),
        ("claude_namespaced_elevation", claude_namespaced_elevation),
        ("wrong_role", wrong_role),
        ("elevation", elevation),
    ):
        output = _json_output(result, "gateway/" + label)
        if output.get("hookSpecificOutput", {}).get(
            "permissionDecision"
        ) != "deny":
            raise SmokeFailure("%s was not denied" % label)
        denied[label] = output

    return {
        "gateway_allowed": _empty_allow_output(
            gateway_allowed, "gateway/allowed-role"
        ),
        "native_allowed": _empty_allow_output(
            native_allowed, "gateway/native-role"
        ),
        "fallback_allowed": _empty_allow_output(
            fallback_allowed, "gateway/generic-fallback"
        ),
        "claude_namespaced_gateway": _empty_allow_output(
            claude_namespaced_gateway, "gateway/claude-namespaced-role"
        ),
        "claude_reviewer_read": _empty_allow_output(
            claude_reviewer_read_allowed, "gateway/claude-reviewer-read"
        ),
        **denied,
        "main_thread": _empty_allow_output(
            main_thread, "gateway/main-thread"
        ),
        "recorded_turns": set(turns),
    }


class _McpClient:
    """Small synchronous JSON-RPC client for the copied stdio server."""

    def __init__(self, command, cwd, env, label):
        self.label = label
        self.next_id = 1
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=str(cwd),
            env=env,
        )

    def request(self, method, params=None):
        request_id = self.next_id
        self.next_id += 1
        message = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            message["params"] = params
        self._send(message)
        ready, _, _ = select.select([self.process.stdout], [], [], 30)
        if not ready:
            self._abort("timed out waiting for JSON-RPC response")
        raw = self.process.stdout.readline()
        if not raw:
            self._abort("closed stdout before a JSON-RPC response")
        try:
            response = json.loads(raw)
        except ValueError as exc:
            self._abort("emitted invalid JSON-RPC: %s" % exc)
        if response.get("id") != request_id:
            self._abort("returned a mismatched JSON-RPC id")
        return response

    def notify(self, method, params=None):
        message = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        self._send(message)

    def _send(self, message):
        if self.process.stdin is None:
            self._abort("has no stdin")
        try:
            self.process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            self._abort("could not send JSON-RPC: %s" % exc)

    def _abort(self, reason):
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        diagnostic = ""
        if self.process.stderr is not None:
            diagnostic = self.process.stderr.read().strip()
        if self.process.stdin is not None and not self.process.stdin.closed:
            self.process.stdin.close()
        if self.process.stdout is not None:
            self.process.stdout.close()
        if self.process.stderr is not None:
            self.process.stderr.close()
        suffix = ": %s" % diagnostic if diagnostic else ""
        raise SmokeFailure("%s %s%s" % (self.label, reason, suffix))

    def close(self):
        if self.process.stdin is not None and not self.process.stdin.closed:
            self.process.stdin.close()
        try:
            returncode = self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._abort("did not exit after stdin closed")
        diagnostic = ""
        if self.process.stderr is not None:
            diagnostic = self.process.stderr.read().strip()
        if self.process.stdout is not None:
            self.process.stdout.close()
        if self.process.stderr is not None:
            self.process.stderr.close()
        if returncode != 0 or diagnostic:
            raise SmokeFailure(
                "%s exited %d%s"
                % (
                    self.label,
                    returncode,
                    ": " + diagnostic if diagnostic else "",
                )
            )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, _exc, _traceback):
        if exc_type is None:
            self.close()
        elif self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        if exc_type is not None:
            if self.process.stdin is not None and not self.process.stdin.closed:
                self.process.stdin.close()
            if self.process.stdout is not None:
                self.process.stdout.close()
            if self.process.stderr is not None:
                self.process.stderr.close()
        return False


def _adapter_command(installed_plugin, host):
    installed_plugin = Path(installed_plugin).resolve()
    if host == "claude":
        manifest_path = installed_plugin / ".mcp.json"
        root_variable = "${CLAUDE_PLUGIN_ROOT}"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            server = manifest["mcpServers"]["founder-os-state"]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise SmokeFailure("Claude installed adapter is unreadable") from exc
    elif host == "codex":
        manifest_path = installed_plugin / ".codex-plugin" / "plugin.json"
        root_variable = None
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            server = manifest["mcpServers"]["founder-os-state"]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise SmokeFailure("Codex installed adapter is unreadable") from exc
    else:
        raise SmokeFailure("unknown installed adapter: %s" % host)

    if (
        not isinstance(server, dict)
        or server.get("command") != "python3"
        or not isinstance(server.get("args"), list)
        or len(server["args"]) != 1
        or not isinstance(server["args"][0], str)
    ):
        raise SmokeFailure("%s installed adapter has an invalid command" % host)
    argument = server["args"][0]
    if host == "claude":
        argument = argument.replace(root_variable, str(installed_plugin))
        if root_variable in argument:
            raise SmokeFailure("Claude installed adapter root did not expand")
        entry = Path(argument).resolve()
    else:
        if server.get("cwd") != ".":
            raise SmokeFailure("Codex installed adapter must use plugin cwd")
        entry = (installed_plugin / argument).resolve()
    try:
        entry.relative_to(installed_plugin)
    except ValueError as exc:
        raise SmokeFailure("%s installed adapter escapes the plugin" % host) from exc
    if not entry.is_file():
        raise SmokeFailure("%s installed adapter entry does not exist" % host)
    return [server["command"], str(entry)]


def _tool_call(client, name, arguments):
    response = client.request(
        "tools/call", {"name": name, "arguments": arguments}
    )
    if "error" in response:
        raise SmokeFailure("%s returned a protocol error" % name)
    result = response.get("result")
    if not isinstance(result, dict):
        raise SmokeFailure("%s omitted its MCP result" % name)
    return result


def _success_payload(result, label):
    if result.get("isError") is not False:
        raise SmokeFailure("%s unexpectedly failed" % label)
    payload = result.get("structuredContent")
    if not isinstance(payload, dict):
        raise SmokeFailure("%s omitted structuredContent" % label)
    return payload


def _error_code(result, label):
    if result.get("isError") is not True:
        raise SmokeFailure("%s unexpectedly succeeded" % label)
    try:
        code = result["structuredContent"]["error"]["code"]
    except (KeyError, TypeError) as exc:
        raise SmokeFailure("%s omitted its stable error code" % label) from exc
    if not isinstance(code, str):
        raise SmokeFailure("%s emitted a non-string error code" % label)
    return code


def check_mcp_lifecycle(installed_plugin, workspace_root, host):
    """Run initialize/list/call and a complete role I/O cycle via one adapter."""
    installed_plugin = Path(installed_plugin).resolve()
    workspace_root = Path(workspace_root).resolve()
    workspace_root.mkdir(parents=True, exist_ok=True)
    initial_content = (
        "## Close\nInitial probe\n\n"
        "## Runway\nUnknown\n\n"
        "## Profitability\nUnknown\n\n"
        "## Rate\nUnknown\n"
    )
    updated_content = initial_content.replace("Initial probe", "Persisted probe")
    metrics_path = workspace_root / "metrics.md"
    metrics_path.write_text(initial_content, encoding="utf-8")

    runtime_root = workspace_root.parent / ("." + host + "-runtime")
    home_root = runtime_root / "home"
    home_root.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["HOME"] = str(home_root)
    env["FOUNDER_OS_HOME"] = str(workspace_root)
    env["PLUGIN_DATA"] = str(runtime_root / "plugin-data")
    env.pop("CLAUDE_PLUGIN_DATA", None)
    command = _adapter_command(installed_plugin, host)

    with _McpClient(command, workspace_root.parent, env, host + "/MCP") as client:
        initialized = client.request(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "installed-host-probe", "version": "1"},
            },
        )
        try:
            server = initialized["result"]["serverInfo"]
        except (KeyError, TypeError) as exc:
            raise SmokeFailure("%s initialize omitted serverInfo" % host) from exc
        if server.get("name") != "founder-os-state":
            raise SmokeFailure("%s initialized the wrong server" % host)
        client.notify("notifications/initialized")
        ping = client.request("ping")
        if ping.get("result") != {}:
            raise SmokeFailure("%s MCP ping failed" % host)
        listed_tools = client.request("tools/list").get("result", {}).get("tools")
        if not isinstance(listed_tools, list) or len(listed_tools) != 8:
            raise SmokeFailure("%s did not discover all eight tools" % host)

        resolved = _success_payload(
            _tool_call(
                client,
                "resolve_workspace",
                {"project_dir": str(workspace_root.parent)},
            ),
            host + "/resolve",
        )
        workspace_id = resolved.get("workspace_id")
        if not isinstance(workspace_id, str) or not workspace_id:
            raise SmokeFailure("%s resolve omitted workspace_id" % host)

        cfo = _success_payload(
            _tool_call(
                client,
                "open_role_session",
                {
                    "workspace_id": workspace_id,
                    "role": "cfo",
                    "correlation_id": host + "-cfo-probe",
                    "workflow": "revenue-review",
                },
            ),
            host + "/open-cfo",
        )["capability"]
        strategist = _success_payload(
            _tool_call(
                client,
                "open_role_session",
                {
                    "workspace_id": workspace_id,
                    "role": "strategist",
                    "correlation_id": host + "-strategist-probe",
                    "workflow": "quarterly-planning",
                },
            ),
            host + "/open-strategist",
        )["capability"]

        paths = _success_payload(
            _tool_call(
                client, "list_state", {"capability": cfo, "pattern": "*.md"}
            ),
            host + "/list",
        )["paths"]
        if "metrics.md" not in paths:
            raise SmokeFailure("%s list did not include metrics.md" % host)
        read = _success_payload(
            _tool_call(
                client,
                "read_state",
                {"capability": cfo, "paths": ["metrics.md"]},
            ),
            host + "/read",
        )["files"][0]
        initial_sha256 = read["sha256"]
        _success_payload(
            _tool_call(
                client,
                "read_reference",
                {
                    "capability": cfo,
                    "path": "skills/revenue-review/SKILL.md",
                },
            ),
            host + "/read-reference",
        )

        wrong_owner = _error_code(
            _tool_call(
                client,
                "write_owned_state",
                {
                    "capability": strategist,
                    "path": "metrics.md",
                    "content": updated_content,
                    "expected_sha256": initial_sha256,
                },
            ),
            host + "/wrong-owner",
        )
        written = _success_payload(
            _tool_call(
                client,
                "write_owned_state",
                {
                    "capability": cfo,
                    "path": "metrics.md",
                    "content": updated_content,
                    "expected_sha256": initial_sha256,
                },
            ),
            host + "/write",
        )
        persisted_sha256 = written["after_sha256"]
        stale_write = _error_code(
            _tool_call(
                client,
                "write_owned_state",
                {
                    "capability": cfo,
                    "path": "metrics.md",
                    "content": updated_content,
                    "expected_sha256": initial_sha256,
                },
            ),
            host + "/stale-write",
        )
        bad_structure = _error_code(
            _tool_call(
                client,
                "write_owned_state",
                {
                    "capability": cfo,
                    "path": "metrics.md",
                    "content": "# invalid\n",
                    "expected_sha256": persisted_sha256,
                },
            ),
            host + "/bad-structure",
        )
        _success_payload(
            _tool_call(
                client,
                "close_role_session",
                {"capability": strategist, "final_status": "denied"},
            ),
            host + "/close-strategist",
        )
        _success_payload(
            _tool_call(
                client,
                "close_role_session",
                {"capability": cfo, "final_status": "completed"},
            ),
            host + "/close-cfo",
        )
        closed_reuse = _error_code(
            _tool_call(
                client,
                "read_state",
                {"capability": cfo, "paths": ["metrics.md"]},
            ),
            host + "/closed-reuse",
        )

    landed_sha256 = hashlib.sha256(metrics_path.read_bytes()).hexdigest()
    if landed_sha256 != persisted_sha256:
        raise SmokeFailure("%s persisted hash did not match disk" % host)
    expected_codes = {
        "wrong_owner": (wrong_owner, "ROLE_NOT_OWNER"),
        "stale_write": (stale_write, "STALE_WRITE"),
        "bad_structure": (bad_structure, "INVALID_DOCUMENT_STRUCTURE"),
        "closed_reuse": (closed_reuse, "ROLE_SESSION_INVALID"),
    }
    for label, (actual, expected) in expected_codes.items():
        if actual != expected:
            raise SmokeFailure(
                "%s %s returned %s instead of %s"
                % (host, label, actual, expected)
            )
    return {
        "version": server.get("version"),
        "tool_count": len(listed_tools),
        "initial_sha256": initial_sha256,
        "persisted_sha256": persisted_sha256,
        "wrong_owner": wrong_owner,
        "stale_write": stale_write,
        "bad_structure": bad_structure,
        "closed_reuse": closed_reuse,
    }


def check_package_tools(repo_root, installed_plugin):
    """Run the repository's structural checks against the copied package."""
    repo_root = Path(repo_root)
    installed_plugin = Path(installed_plugin)
    commands = {
        "validator": [
            sys.executable,
            str(repo_root / "scripts" / "validate_package.py"),
            str(installed_plugin),
        ],
        "commands": [
            sys.executable,
            str(repo_root / "scripts" / "generate_commands.py"),
            str(installed_plugin),
            "--check",
        ],
    }
    results = {}
    for label, command in commands.items():
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=60,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "no output"
            raise SmokeFailure("%s failed against installed copy: %s" % (
                label, detail
            ))
        results[label] = result
    return results


def run_smoke(repo_root=REPO_ROOT, hook_plugin_root=None):
    """Run the complete smoke lifecycle in an isolated temporary directory."""
    repo_root = Path(repo_root)
    source_plugin = repo_root / "founder-os"
    source_before = tree_fingerprint(source_plugin)
    try:
        with tempfile.TemporaryDirectory(prefix="founder-os-installed-") as temp_dir:
            temp_root = Path(temp_dir)
            installed = create_installed_copy(
                source_plugin, temp_root / "marketplace"
            )
            check_session_context(
                installed, temp_root, hook_plugin_root=hook_plugin_root
            )
            check_session_context_warning(installed, temp_root)
            check_ownership_guard(installed, temp_root / "guard-workspace")
            for host in ("claude", "codex"):
                check_mcp_lifecycle(
                    installed, temp_root / (host + "-workspace"), host
                )
            check_package_tools(repo_root, installed)
    finally:
        assert_tree_unchanged(source_plugin, source_before)


def main():
    """Run the installed-copy smoke checks."""
    try:
        run_smoke()
    except SmokeFailure as exc:
        print("installed-copy smoke: FAIL: %s" % exc, file=sys.stderr)
        return 1
    print("installed-copy smoke: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
