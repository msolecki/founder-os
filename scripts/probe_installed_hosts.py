#!/usr/bin/env python3
"""Probe copied Founder OS installs through isolated Claude and Codex roots."""

from __future__ import annotations

import argparse
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


VERSION = "2.5.0"
PLUGIN_ID = "founder-os@founder-os"


class ProbeFailure(AssertionError):
    """An installed host did not satisfy the release contract."""


def isolated_environment(root, host, inherited=None):
    """Return a host environment whose writable discovery state is temporary."""
    root = Path(root).resolve()
    environment = dict(os.environ if inherited is None else inherited)
    for key in (
        "CLAUDE_CONFIG_DIR",
        "CLAUDE_PLUGIN_DATA",
        "CLAUDE_PLUGIN_ROOT",
        "CODEX_HOME",
        "CODEX_PLUGIN_ROOT",
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
    if host == "claude":
        config = root / "claude"
        config.mkdir(parents=True, exist_ok=True)
        environment["CLAUDE_CONFIG_DIR"] = str(config)
    elif host == "codex":
        config = root / "codex"
        config.mkdir(parents=True, exist_ok=True)
        environment["CODEX_HOME"] = str(config)
    else:
        raise ProbeFailure("unknown host: %s" % host)
    return environment


def require_cli(host, which=shutil.which):
    """Resolve a required release CLI; absence is never a skip."""
    path = which(host)
    if not path:
        raise ProbeFailure("%s CLI is unavailable" % host)
    return os.path.abspath(path)


def installation_commands(host, repo_root, binary):
    """Build the local-only marketplace, install, and discovery commands."""
    source = str(Path(repo_root).resolve())
    if host == "claude":
        return [
            [binary, "plugin", "marketplace", "add", source, "--scope", "user"],
            [binary, "plugin", "install", PLUGIN_ID, "--scope", "user"],
            [binary, "plugin", "list", "--json"],
            [binary, "plugin", "details", PLUGIN_ID],
        ]
    if host == "codex":
        return [
            [binary, "plugin", "marketplace", "add", source, "--json"],
            [binary, "plugin", "add", PLUGIN_ID, "--json"],
            [binary, "plugin", "list", "--json"],
        ]
    raise ProbeFailure("unknown host: %s" % host)


def _run_command(command, environment, cwd, label):
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd),
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=90,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProbeFailure("%s could not run: %s" % (label, exc)) from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        raise ProbeFailure("%s exited %d: %s" % (label, result.returncode, detail))
    return result


def _json_output(source, label):
    try:
        return json.loads(source)
    except (TypeError, ValueError) as exc:
        raise ProbeFailure("%s did not emit JSON discovery data" % label) from exc


def _inside(path, root, label):
    path = Path(path).resolve()
    root = Path(root).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ProbeFailure("%s escaped the isolated host root" % label) from exc
    return path


def _discover_install(host, results, isolated_root):
    if host == "claude":
        listing = _json_output(results[2].stdout, "claude plugin list")
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
    else:
        install_result = _json_output(results[1].stdout, "codex plugin add")
        listing = _json_output(results[2].stdout, "codex plugin list")
        installed_items = listing.get("installed", []) if isinstance(listing, dict) else []
        matches = [
            item
            for item in installed_items
            if isinstance(item, dict) and item.get("pluginId") == PLUGIN_ID
        ]
        if len(matches) != 1:
            raise ProbeFailure("Codex did not discover exactly one Founder OS install")
        installed = matches[0]
        install_path = install_result.get("installedPath")
        cli_version = installed.get("version")
        enabled = installed.get("enabled")
        details = ""

    if not isinstance(install_path, str):
        raise ProbeFailure("%s discovery omitted its installed path" % host)
    plugin_root = _inside(install_path, isolated_root, host + " install")
    if not plugin_root.is_dir():
        raise ProbeFailure("%s discovered install does not exist" % host)
    if cli_version != VERSION or enabled is not True:
        raise ProbeFailure("%s discovered the wrong or disabled release" % host)

    manifest_name = ".claude-plugin/plugin.json" if host == "claude" else ".codex-plugin/plugin.json"
    manifest_path = plugin_root / manifest_name
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError) as exc:
        raise ProbeFailure("%s installed manifest is unreadable" % host) from exc
    if manifest.get("name") != "founder-os" or manifest.get("version") != VERSION:
        raise ProbeFailure("%s installed manifest identity drifted" % host)
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


def _check_orchestration(host, plugin_root, details, guard_report, required):
    agents = package_validator.load_agents(plugin_root)
    native, fallback = execution_envelopes(plugin_root)
    errors = package_validator.execution_envelope_errors(
        plugin_root, agents, native, fallback
    )
    if errors:
        raise ProbeFailure("%s fallback envelope failed: %s" % (host, "; ".join(errors)))

    native_status = "not-exposed"
    if host == "claude":
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
        raise ProbeFailure("%s generic fallback was not exercised" % host)
    return native_status, fallback_status


def probe_host(host, repo_root, isolated_root, require_native_and_fallback=False):
    """Install one host locally, discover it, and run installed role I/O."""
    binary = require_cli(host)
    isolated_root = Path(isolated_root).resolve()
    environment = isolated_environment(isolated_root, host)
    run_root = isolated_root / "run"
    run_root.mkdir(parents=True, exist_ok=True)
    results = [
        _run_command(
            command,
            environment,
            run_root,
            "%s install step %d" % (host, index),
        )
        for index, command in enumerate(
            installation_commands(host, repo_root, binary), start=1
        )
    ]
    plugin_root, details = _discover_install(host, results, isolated_root)
    installed_smoke.check_session_context(plugin_root, run_root)
    installed_smoke.check_session_context_warning(plugin_root, run_root)
    guard_report = installed_smoke.check_ownership_guard(
        plugin_root, run_root / (host + "-guard-workspace")
    )
    report = installed_smoke.check_mcp_lifecycle(
        plugin_root, run_root / (host + "-workspace"), host
    )
    native, fallback = _check_orchestration(
        host,
        plugin_root,
        details,
        guard_report,
        require_native_and_fallback,
    )
    report.update(native=native, fallback=fallback)
    return report


def format_pass_record(host, report):
    """Return a content-free release record with only result metadata."""
    return (
        "installed-host probe: {host} PASS version={version} role_io=PASS "
        "initial_sha256={initial} persisted_sha256={persisted} "
        "native={native} fallback={fallback}"
    ).format(
        host=host,
        version=report["version"],
        initial=report["initial_sha256"],
        persisted=report["persisted_sha256"],
        native=report["native"],
        fallback=report["fallback"],
    )


def _parser():
    parser = argparse.ArgumentParser(
        description="Probe isolated local Founder OS installs on real host CLIs."
    )
    parser.add_argument("--claude", action="store_true", help="require Claude Code")
    parser.add_argument("--codex", action="store_true", help="require Codex")
    parser.add_argument(
        "--require-native-and-fallback",
        action="store_true",
        help="require native discovery where exposed and byte-identical fallback",
    )
    return parser


def main(argv=None):
    parser = _parser()
    arguments = parser.parse_args(argv)
    hosts = [
        host
        for host, enabled in (("claude", arguments.claude), ("codex", arguments.codex))
        if enabled
    ]
    if not hosts:
        parser.print_usage(sys.stderr)
        print("probe_installed_hosts.py: error: select --claude and/or --codex", file=sys.stderr)
        return 2

    try:
        with tempfile.TemporaryDirectory(prefix="founder-os-host-probes-") as temp_dir:
            root = Path(temp_dir)
            reports = {
                host: probe_host(
                    host,
                    REPO_ROOT,
                    root / host,
                    require_native_and_fallback=arguments.require_native_and_fallback,
                )
                for host in hosts
            }
        for host in hosts:
            print(format_pass_record(host, reports[host]))
    except (ProbeFailure, installed_smoke.SmokeFailure, OSError) as exc:
        print("installed-host probe: FAIL: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
