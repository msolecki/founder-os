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


def check_ownership_guard(installed_plugin, workspace_root):
    """Check owner allow, wrong-owner deny, and main-thread allow paths."""
    installed_plugin = Path(installed_plugin)
    workspace_root = Path(workspace_root)
    workspace_root.mkdir(parents=True, exist_ok=True)
    target = workspace_root / "metrics.md"
    guard_path = installed_plugin / "hooks" / "ownership-guard.py"
    env = _hook_environment(
        installed_plugin, FOUNDER_OS_HOME=workspace_root
    )
    base_payload = {
        "tool_name": "Write",
        "cwd": str(workspace_root),
        "tool_input": {"file_path": str(target)},
    }

    allowed = _run_hook(
        guard_path,
        {**base_payload, "agent_type": "cfo"},
        env,
        workspace_root,
        "ownership/allowed-owner",
    )
    wrong_owner = _run_hook(
        guard_path,
        {**base_payload, "agent_type": "strategist"},
        env,
        workspace_root,
        "ownership/wrong-owner",
    )
    main_thread = _run_hook(
        guard_path,
        base_payload,
        env,
        workspace_root,
        "ownership/main-thread",
    )

    denied = _json_output(wrong_owner, "ownership/wrong-owner")
    deny_output = denied.get("hookSpecificOutput", {})
    if deny_output.get("permissionDecision") != "deny":
        raise SmokeFailure("wrong-owner write was not denied")
    if "cfo" not in deny_output.get("permissionDecisionReason", ""):
        raise SmokeFailure("wrong-owner denial did not name the cfo owner")

    return {
        "allowed_owner": _empty_allow_output(
            allowed, "ownership/allowed-owner"
        ),
        "wrong_owner": denied,
        "main_thread": _empty_allow_output(
            main_thread, "ownership/main-thread"
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
