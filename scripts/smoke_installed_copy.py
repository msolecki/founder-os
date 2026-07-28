#!/usr/bin/env python3
"""Exercise Founder OS from a temporary installed marketplace copy."""
import json
import os
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
        "print(store.open('installed-workspace',sys.argv[3],'installed-smoke'))\n"
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


def check_ownership_guard(installed_plugin, workspace_root):
    """Check gateway allow, direct/elevation/mismatch deny, and main allow."""
    installed_plugin = Path(installed_plugin)
    workspace_root = Path(workspace_root)
    workspace_root.mkdir(parents=True, exist_ok=True)
    data_root = workspace_root / ".plugin-data"
    data_root.mkdir()
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
        "gateway/allowed-role",
    )
    direct_denied = _run_hook(
        guard_path,
        {**direct_payload, "agent_type": "cfo"},
        env,
        workspace_root,
        "gateway/direct-file-denied",
    )
    wrong_role = _run_hook(
        guard_path,
        {
            "agent_type": "strategist",
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
            "agent_type": "cfo",
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

    denied = {}
    for label, result in (
        ("direct_file", direct_denied),
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
        **denied,
        "main_thread": _empty_allow_output(
            main_thread, "gateway/main-thread"
        ),
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
    with tempfile.TemporaryDirectory(prefix="founder-os-installed-") as temp_dir:
        temp_root = Path(temp_dir)
        installed = create_installed_copy(
            repo_root / "founder-os", temp_root / "marketplace"
        )
        check_session_context(
            installed, temp_root, hook_plugin_root=hook_plugin_root
        )
        check_ownership_guard(installed, temp_root / "workspace")
        check_package_tools(repo_root, installed)


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
