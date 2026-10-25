#!/usr/bin/env python3
"""Probe copied Founder OS installs through an isolated Claude Code root."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

import smoke_installed_copy as installed_smoke
import validate_package as package_validator


VERSION = "3.1.0"
PLUGIN_ID = "founder-os@founder-os"


class ProbeFailure(AssertionError):
    """An installed host did not satisfy the release contract."""


def isolated_environment(root, inherited=None):
    """Return a host environment whose writable discovery state is temporary."""
    root = Path(root).resolve()
    environment = dict(os.environ if inherited is None else inherited)
    for key in (
        "CLAUDE_CONFIG_DIR",
        "CLAUDE_PLUGIN_DATA",
        "CLAUDE_PLUGIN_ROOT",
        "FOUNDER_OS_HOME",
        "PLUGIN_DATA",
        "PLUGIN_ROOT",
    ):
        environment.pop(key, None)

    home = root / "home"
    xdg = root / "xdg"
    temporary = root / "tmp"
    for directory in (home, xdg, temporary):
        directory.mkdir(parents=True, exist_ok=True)
    environment["HOME"] = str(home)
    environment["XDG_CONFIG_HOME"] = str(xdg)
    environment["TMPDIR"] = str(temporary)
    config = root / "claude"
    config.mkdir(parents=True, exist_ok=True)
    environment["CLAUDE_CONFIG_DIR"] = str(config)
    return environment


def require_cli(which=shutil.which):
    """Resolve the Claude CLI; absence is never a skip."""
    path = which("claude")
    if not path:
        raise ProbeFailure("claude CLI is unavailable")
    return os.path.abspath(path)


def installation_commands(repo_root, binary):
    """Build the local-only marketplace, install, and discovery commands."""
    source = str(Path(repo_root).resolve())
    return [
        [binary, "plugin", "marketplace", "add", source, "--scope", "user"],
        [binary, "plugin", "install", PLUGIN_ID, "--scope", "user"],
        [binary, "plugin", "list", "--json"],
        [binary, "plugin", "details", PLUGIN_ID],
    ]


def _run_command(command, environment, cwd, label, timeout=90):
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd),
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProbeFailure("%s could not run: %s" % (label, exc)) from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        raise ProbeFailure("%s exited %d: %s" % (label, result.returncode, detail))
    return result


def _inside(path, root, label):
    path = Path(path).resolve()
    root = Path(root).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ProbeFailure("%s escaped the isolated host root" % label) from exc
    return path


def _discover_install(results, isolated_root):
    listing = installed_smoke._json_output(results[2], "claude plugin list")
    matches = [
        item
        for item in listing
        if isinstance(item, dict) and item.get("id") == PLUGIN_ID
    ] if isinstance(listing, list) else []
    if len(matches) != 1:
        raise ProbeFailure("Claude did not discover exactly one Founder OS install")
    installed = matches[0]
    install_path = installed.get("installPath")
    cli_version = installed.get("version")
    enabled = installed.get("enabled")
    details = results[3].stdout

    if not isinstance(install_path, str):
        raise ProbeFailure("Claude discovery omitted its installed path")
    plugin_root = _inside(install_path, isolated_root, "Claude install")
    if not plugin_root.is_dir():
        raise ProbeFailure("Claude discovered install does not exist")
    if cli_version != VERSION or enabled is not True:
        raise ProbeFailure("Claude discovered the wrong or disabled release")

    manifest_path = plugin_root / ".claude-plugin" / "plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError) as exc:
        raise ProbeFailure("Claude installed manifest is unreadable") from exc
    if manifest.get("name") != "founder-os" or manifest.get("version") != VERSION:
        raise ProbeFailure("Claude installed manifest identity drifted")
    return plugin_root, details


def _execution_envelope(plugin_root):
    role_path = Path(plugin_root) / "agents" / "cfo.md"
    return {
        "role": "cfo",
        "role_file": "agents/cfo.md",
        "role_instructions": role_path.read_bytes(),
        "workflow": "revenue-review",
        "handoff": "Verify the isolated installed-host state cycle.",
        "capability": "installed-host-probe-capability",
    }


def execution_envelopes(plugin_root):
    """Build native and generic envelopes through independent file reads."""
    return _execution_envelope(plugin_root), _execution_envelope(plugin_root)


def check_cadence_preview(plugin_root, binary, workspace_root):
    """Render an installed host command without invoking a model or scheduler."""
    script = Path(plugin_root) / "scripts" / "cadence_manager.py"
    spec = importlib.util.spec_from_file_location(
        "founder_os_installed_cadence_manager", script
    )
    if spec is None or spec.loader is None:
        raise ProbeFailure("installed cadence manager is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        workspace_root = Path(workspace_root).resolve()
        config = module.CadenceConfig(
            binary=Path(binary).resolve(),
            workspace=workspace_root / "founder-os",
            workdir=workspace_root,
            log_root=workspace_root / "logs",
            slug=None,
        )
        argv = module.host_argv(config, "daily-brief")
    except Exception as exc:
        raise ProbeFailure("cadence preview failed: %s" % exc) from exc
    required = {
        "dontAsk",
        "--allowedTools",
        "--no-session-persistence",
        "mcp__plugin_founder-os_founder-os-state__*",
    }
    if not required.issubset(set(argv)):
        raise ProbeFailure("cadence preview drifted")
    return tuple(argv)


def check_scheduled_dispatch(argv, environment, workspace_root, isolated_root):
    """Run the scheduled daily-brief argv once; a role session must write it.

    Spends one real model run and needs credentials the isolated config can
    use (for example ANTHROPIC_API_KEY), so it runs only with --live-cadence.
    Under ``dontAsk`` the argv allows only the gateway tools; this proves the
    host still dispatches the owning role, whose capability the gateway
    journals, rather than the brief going unwritten.
    """
    workspace_root = Path(workspace_root).resolve()
    workspace = workspace_root / "founder-os"
    workspace.mkdir(parents=True, exist_ok=True)
    _run_command(
        list(argv),
        dict(environment, FOUNDER_OS_HOME=str(workspace)),
        workspace_root,
        "scheduled daily-brief",
        timeout=900,
    )
    writes = []
    for journal in Path(isolated_root).rglob("operations.jsonl"):
        for line in journal.read_text(encoding="utf-8").splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if (
                isinstance(event, dict)
                and event.get("result") == "OK"
                and str(event.get("path", "")).startswith("reviews/daily/")
            ):
                writes.append(event)
    if not writes:
        raise ProbeFailure("scheduled daily-brief wrote no daily review")
    if any(event.get("role") != "chief-of-staff" for event in writes):
        raise ProbeFailure("scheduled daily-brief was written by the wrong role")
    if not any((workspace / event["path"]).is_file() for event in writes):
        raise ProbeFailure("scheduled daily-brief journal does not match disk")
    return "PASS"


def _check_orchestration(plugin_root, details, guard_report, required):
    agents = package_validator.load_agents(plugin_root)
    native, fallback = execution_envelopes(plugin_root)
    errors = package_validator.execution_envelope_errors(
        plugin_root, agents, native, fallback
    )
    if errors:
        raise ProbeFailure("fallback envelope failed: %s" % "; ".join(errors))

    native_status = "not-exposed"
    if (
        "Agents (13)" in details
        and "cfo" in details
        and guard_report.get("native_allowed") is None
    ):
        native_status = "PASS"
    elif required:
        raise ProbeFailure("Claude did not expose its thirteen native roles")
    fallback_status = (
        "PASS" if guard_report.get("fallback_allowed") is None else "FAIL"
    )
    if required and fallback_status != "PASS":
        raise ProbeFailure("generic fallback was not exercised")
    return native_status, fallback_status


def probe_host(repo_root, isolated_root, require_native_and_fallback, live_cadence):
    """Install Claude Code locally, discover it, and run installed role I/O."""
    binary = require_cli()
    isolated_root = Path(isolated_root).resolve()
    environment = isolated_environment(isolated_root)
    run_root = isolated_root / "run"
    run_root.mkdir(parents=True, exist_ok=True)
    results = [
        _run_command(
            command,
            environment,
            run_root,
            "claude install step %d" % index,
        )
        for index, command in enumerate(
            installation_commands(repo_root, binary), start=1
        )
    ]
    plugin_root, details = _discover_install(results, isolated_root)
    cadence_root = run_root / "claude-cadence-workspace"
    argv = check_cadence_preview(plugin_root, binary, cadence_root)
    installed_smoke.check_session_context(plugin_root, run_root)
    installed_smoke.check_session_context_warning(plugin_root, run_root)
    guard_report = installed_smoke.check_ownership_guard(
        plugin_root, run_root / "claude-guard-workspace"
    )
    report = installed_smoke.check_mcp_lifecycle(
        plugin_root, run_root / "claude-workspace"
    )
    native, fallback = _check_orchestration(
        plugin_root,
        details,
        guard_report,
        require_native_and_fallback,
    )
    report.update(native=native, fallback=fallback, scheduled="skipped")
    if live_cadence:
        report["scheduled"] = check_scheduled_dispatch(
            argv, environment, cadence_root, isolated_root
        )
    return report


def format_pass_record(report):
    """Return a content-free release record with only result metadata."""
    return (
        "installed-host probe: claude PASS version={version} role_io=PASS "
        "initial_sha256={initial} persisted_sha256={persisted} "
        "native={native} fallback={fallback} scheduled={scheduled}"
    ).format(
        version=report["version"],
        initial=report["initial_sha256"],
        persisted=report["persisted_sha256"],
        native=report["native"],
        fallback=report["fallback"],
        scheduled=report.get("scheduled", "skipped"),
    )


def _parser():
    parser = argparse.ArgumentParser(
        description="Probe isolated local Founder OS installs on real host CLIs."
    )
    parser.add_argument(
        "--claude",
        action="store_true",
        help="accepted for compatibility; Claude Code is the only host",
    )
    parser.add_argument(
        "--require-native-and-fallback",
        action="store_true",
        help="require native discovery where exposed and byte-identical fallback",
    )
    parser.add_argument(
        "--live-cadence",
        action="store_true",
        help="also run the scheduled daily-brief argv once (spends a model run)"
        " and require the chief-of-staff role session to write the brief",
    )
    return parser


def main(argv=None):
    parser = _parser()
    arguments = parser.parse_args(argv)
    try:
        with tempfile.TemporaryDirectory(prefix="founder-os-host-probes-") as temp_dir:
            report = probe_host(
                REPO_ROOT,
                Path(temp_dir) / "claude",
                arguments.require_native_and_fallback,
                arguments.live_cadence,
            )
        print(format_pass_record(report))
    except (ProbeFailure, installed_smoke.SmokeFailure, OSError) as exc:
        print("installed-host probe: FAIL: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
