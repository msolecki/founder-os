from __future__ import annotations

import base64
import importlib.util
import json
import os
import plistlib
from pathlib import Path
import shlex
import sys
import tempfile
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "founder-os" / "scripts" / "cadence_manager.py"


def load_manager():
    spec = importlib.util.spec_from_file_location("cadence_manager", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class Result:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class CronRunner:
    def __init__(self, current):
        self.current = current
        self.installed = None
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append((tuple(argv), kwargs))
        if list(argv) == ["crontab", "-l"]:
            return Result(stdout=self.current.decode("utf-8"))
        if len(argv) == 2 and argv[0] == "crontab":
            self.installed = Path(argv[1]).read_bytes()
            self.current = self.installed
            return Result()
        raise AssertionError("unexpected argv: %r" % (argv,))


def stat_mode(path):
    return os.stat(path).st_mode & 0o777


class CadenceManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = load_manager()

    def config(self, host="claude", slug="a"):
        return self.manager.CadenceConfig(
            host=host,
            binary=Path("/opt/%s App/bin/%s" % (host.title(), host)),
            workspace=Path("/Users/Test Founder/work $;(tree)/founder-os"),
            workdir=Path("/Users/Test Founder/work $;(tree)"),
            log_root=Path("/Users/Test Founder/.founder-os/logs/'quoted'"),
            slug=slug,
        )

    def test_host_argv_matches_supported_claude_and_codex_contracts(self):
        claude = self.config("claude")
        self.assertEqual(
            self.manager.host_argv(claude, "daily-brief"),
            (
                "/opt/Claude App/bin/claude",
                "-p",
                "/founder-os:daily-brief",
                "--permission-mode",
                "dontAsk",
                "--allowedTools",
                "mcp__plugin_founder-os_founder-os-state__*",
                "--max-turns",
                "50",
                "--no-session-persistence",
            ),
        )
        codex = self.config("codex")
        self.assertEqual(
            self.manager.host_argv(codex, "daily-brief"),
            (
                "/opt/Codex App/bin/codex",
                "-a",
                "never",
                "exec",
                "--sandbox",
                "workspace-write",
                "--ephemeral",
                "-C",
                "/Users/Test Founder/work $;(tree)",
                "$founder-os:daily-brief",
            ),
        )

    def test_cron_quoting_roundtrips_metacharacters_without_shell_fragments(self):
        config = self.config("codex")
        block = self.manager.render_cron_blocks(config, "2026-08-01")
        line = next(line for line in block.splitlines() if "daily-brief" in line)
        command = line.split(None, 5)[5].split(" >> ", 1)[0]
        tokens = shlex.split(command)
        self.assertEqual(tokens[:3], ["cd", str(config.workdir), "&&"])
        self.assertEqual(tokens[3:6], ["umask", "077", "&&"])
        self.assertEqual(
            tokens[6],
            "PATH=" + str(config.binary.parent) + ":/usr/bin:/bin",
        )
        self.assertEqual(tokens[7], "FOUNDER_OS_HOME=" + str(config.workspace))
        self.assertEqual(
            tuple(tokens[8:]), self.manager.host_argv(config, "daily-brief")
        )
        self.assertNotIn("/bin/sh -c", block)

    def test_exact_fence_merge_is_idempotent_and_preserves_siblings(self):
        current = (
            "MAILTO=founder@example.com\n"
            "# BEGIN founder-os:a — old\nold-a\n# END founder-os:a\n"
            "# BEGIN founder-os:acme — old\nold-acme\n# END founder-os:acme\n"
            "# BEGIN founder-os:portfolio — old\nold-p\n# END founder-os:portfolio\n"
        ).encode("utf-8")
        block = self.manager.render_cron_blocks(self.config(slug="a"), "2026-08-01")
        merged = self.manager.merge_crontab(current, block.encode("utf-8"), "a")
        self.assertIn(b"MAILTO=founder@example.com\n", merged)
        self.assertIn(b"old-acme", merged)
        self.assertIn(b"old-p", merged)
        self.assertNotIn(b"\nold-a\n", merged)
        self.assertEqual(merged, self.manager.merge_crontab(merged, block.encode(), "a"))

    def test_registry_migration_removes_only_legacy_and_malformed_fences_fail(self):
        current = (
            "# BEGIN founder-os — old\nlegacy\n# END founder-os\n"
            "# BEGIN founder-os:acme — old\nsibling\n# END founder-os:acme\n"
        ).encode()
        block = self.manager.render_cron_blocks(self.config(slug="a"), "2026-08-01")
        merged = self.manager.merge_crontab(
            current, block.encode(), "a", migrate_legacy=True
        )
        self.assertNotIn(b"legacy", merged)
        self.assertIn(b"sibling", merged)
        with self.assertRaises(self.manager.CadenceError):
            self.manager.merge_crontab(
                b"# BEGIN founder-os:a\nbroken\n", block.encode(), "a"
            )

    def test_percent_is_escaped_for_cron_before_the_shell_sees_it(self):
        config = self.manager.CadenceConfig(
            host="claude",
            binary=Path("/opt/Claude%20App/bin/claude"),
            workspace=Path("/Users/founder/100%real/founder-os"),
            workdir=Path("/Users/founder/100%real"),
            log_root=Path("/Users/founder/.founder-os/logs"),
            slug="percent",
        )
        block = self.manager.render_cron_blocks(config, "2026-08-01")
        self.assertIn(r"\%", block)
        self.assertNotIn("100%real", block)

    def test_launchd_and_systemd_are_shell_free_and_persistent(self):
        config = self.config("codex")
        launchd = self.manager.render_launchd(config)
        quarterly_name = next(name for name in launchd if "quarterly-planning" in name)
        quarterly = plistlib.loads(launchd[quarterly_name])
        self.assertEqual(
            quarterly["ProgramArguments"],
            list(self.manager.host_argv(config, "quarterly-planning")),
        )
        self.assertEqual(
            quarterly["EnvironmentVariables"]["FOUNDER_OS_HOME"],
            str(config.workspace),
        )
        self.assertEqual(
            quarterly["EnvironmentVariables"]["PATH"],
            str(config.binary.parent) + ":/usr/bin:/bin:/usr/sbin:/sbin",
        )
        self.assertEqual(quarterly["Umask"], 0o077)
        self.assertEqual(
            [item["Month"] for item in quarterly["StartCalendarInterval"]],
            [1, 4, 7, 10],
        )

        systemd = self.manager.render_systemd(config)
        timer = next(
            body for name, body in systemd.items()
            if name.endswith("quarterly-planning.timer")
        ).decode()
        service = next(
            body for name, body in systemd.items()
            if name.endswith("quarterly-planning.service")
        ).decode()
        self.assertIn("Persistent=true", timer)
        self.assertNotIn("/bin/sh", service)
        self.assertIn("ExecStart=", service)
        self.assertIn("UMask=0077", service)
        self.assertIn(
            'Environment="PATH=/opt/Codex App/bin:/usr/bin:/bin"',
            service,
        )
        self.assertIn(
            'WorkingDirectory="/Users/Test Founder/work $;(tree)"',
            service,
        )
        self.assertIn(
            'Environment="FOUNDER_OS_HOME=/Users/Test Founder/'
            'work $;(tree)/founder-os"',
            service,
        )

    def test_launchd_weekdays_match_cron_weekdays(self):
        self.assertEqual(
            [1, 2, 3, 4, 5],
            [
                item["Weekday"]
                for item in self.manager._launchd_calendar("daily-brief")
            ],
        )
        expected = {
            "week-plan": 1,
            "weekly-review": 5,
            "pipeline-review": 4,
            "follow-up-sweep": 5,
            "content-plan": 3,
            "calendar-audit": 5,
            "portfolio-review": 1,
        }
        for workflow, weekday in expected.items():
            with self.subTest(workflow=workflow):
                self.assertEqual(
                    weekday,
                    self.manager._launchd_calendar(workflow)["Weekday"],
                )

    def test_log_directories_are_private(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            log_root = root / "logs"
            log_root.mkdir(mode=0o755)
            config = self.manager.CadenceConfig(
                host="claude",
                binary=root / "claude",
                workspace=root / "work" / "founder-os",
                workdir=root / "work",
                log_root=log_root,
                slug="private",
            )
            self.manager._ensure_log_directories(config)
            log_directory = log_root / "private"
            self.assertEqual(stat_mode(log_directory), 0o700)

    def test_snapshot_never_overwrites_an_existing_backup(self):
        original = b"MAILTO=founder@example.com\n"
        runner = CronRunner(original)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self.manager.CadenceConfig(
                host="claude",
                binary=root / "claude",
                workspace=root / "work" / "founder-os",
                workdir=root / "work",
                log_root=root / "logs",
                slug="a",
            )
            first = self.manager.snapshot(
                config,
                "cron",
                root / "backups",
                runner=runner,
                timestamp="20260801-120000",
            )
            backup = Path(first["backup_path"])
            with self.assertRaises(self.manager.CadenceError):
                self.manager.snapshot(
                    config,
                    "cron",
                    root / "backups",
                    runner=runner,
                    timestamp="20260801-120000",
                )
            self.assertEqual(original, backup.read_bytes())

    def test_apply_rejects_unexpected_file_scheduler_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scheduler_directory = root / "LaunchAgents"
            config = self.manager.CadenceConfig(
                host="claude",
                binary=root / "claude",
                workspace=root / "work" / "founder-os",
                workdir=root / "work",
                log_root=root / "logs",
                slug="a",
            )
            with mock.patch.object(
                self.manager,
                "_scheduler_directory",
                return_value=scheduler_directory,
            ):
                manifest = self.manager.preview(config, "launchd")
                snapshot = self.manager.snapshot(
                    config,
                    "launchd",
                    root / "backups",
                    timestamp="20260801-120000",
                )
                forged = json.loads(json.dumps(manifest))
                forged["artifacts"]["unexpected.plist"] = base64.b64encode(
                    b"not a Founder OS job"
                ).decode("ascii")
                forged.pop("manifest_sha256")
                forged = self.manager._seal(forged)

                with self.assertRaises(self.manager.CadenceError):
                    self.manager.apply(
                        forged,
                        snapshot,
                        runner=lambda *args, **kwargs: Result(),
                    )
            self.assertFalse((scheduler_directory / "unexpected.plist").exists())
            self.assertFalse(config.log_root.exists())

    def test_apply_rejects_symlinked_or_workspace_local_backups(self):
        original = b"MAILTO=founder@example.com\n"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self.manager.CadenceConfig(
                host="claude",
                binary=root / "claude",
                workspace=root / "work" / "founder-os",
                workdir=root / "work",
                log_root=root / "logs",
                slug="a",
            )
            config.workspace.mkdir(parents=True)
            runner = CronRunner(original)
            manifest = self.manager.preview(
                config, "cron", runner=runner, date="2026-08-01"
            )
            snapshot = self.manager.snapshot(
                config,
                "cron",
                root / "backups",
                runner=runner,
                timestamp="20260801-120000",
            )

            backup = Path(snapshot["backup_path"])
            target = root / "target.txt"
            target.write_bytes(original)
            backup.unlink()
            backup.symlink_to(target)
            with self.assertRaises(self.manager.CadenceError):
                self.manager.apply(manifest, snapshot, runner=runner)

            local_backup = config.workspace / "backup.txt"
            local_backup.write_bytes(original)
            forged_snapshot = dict(snapshot)
            forged_snapshot["backup_path"] = str(local_backup)
            forged_snapshot.pop("manifest_sha256")
            forged_snapshot = self.manager._seal(forged_snapshot)
            with self.assertRaises(self.manager.CadenceError):
                self.manager.apply(manifest, forged_snapshot, runner=runner)

    def test_apply_recomputes_expected_artifacts_instead_of_trusting_a_seal(self):
        original = b"MAILTO=founder@example.com\n"
        runner = CronRunner(original)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self.manager.CadenceConfig(
                host="claude",
                binary=root / "claude",
                workspace=root / "work" / "founder-os",
                workdir=root / "work",
                log_root=root / "logs",
                slug="a",
            )
            manifest = self.manager.preview(
                config, "cron", runner=runner, date="2026-08-01"
            )
            snapshot = self.manager.snapshot(
                config,
                "cron",
                root / "backups",
                runner=runner,
                timestamp="20260801-120000",
            )
            forged = dict(manifest)
            forged["artifacts"] = {
                "crontab": base64.b64encode(
                    b"* * * * * /usr/bin/false\n"
                ).decode("ascii")
            }
            forged.pop("manifest_sha256")
            forged = self.manager._seal(forged)

            with self.assertRaises(self.manager.CadenceError):
                self.manager.apply(forged, snapshot, runner=runner)
            self.assertIsNone(runner.installed)

    def test_manifest_outputs_are_outside_workspace_and_create_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            with self.assertRaises(self.manager.CadenceError):
                self.manager._write_json(
                    workspace / "preview.json",
                    {"value": 1},
                    forbidden_root=workspace,
                )

            output = root / "manifests" / "preview.json"
            self.manager._write_json(
                output, {"value": 1}, forbidden_root=workspace
            )
            with self.assertRaises(self.manager.CadenceError):
                self.manager._write_json(
                    output, {"value": 2}, forbidden_root=workspace
                )
            self.assertEqual({"value": 1}, json.loads(output.read_text()))

    def test_remove_installs_crontab_once(self):
        current = (
            "# BEGIN founder-os:a — old\nold\n# END founder-os:a\n"
        ).encode()
        runner = CronRunner(current)
        self.manager.remove(self.config(slug="a"), "cron", "a", runner=runner)
        installs = [
            call
            for call in runner.calls
            if (
                call[0][0] == "crontab"
                and len(call[0]) == 2
                and call[0][1] != "-l"
            )
        ]
        self.assertEqual(1, len(installs))

    def test_systemd_remove_stops_before_deleting_when_disable_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / "systemd"
            directory.mkdir()
            config = self.manager.CadenceConfig(
                host="claude",
                binary=root / "claude",
                workspace=root / "work" / "founder-os",
                workdir=root / "work",
                log_root=root / "logs",
                slug="a",
            )
            names = self.manager._selected_names(config, "systemd")
            for name in names:
                (directory / name).write_text("unit")

            def runner(argv, **kwargs):
                if "disable" in argv:
                    return Result(returncode=1)
                return Result()

            with mock.patch.object(
                self.manager, "_scheduler_directory", return_value=directory
            ):
                with self.assertRaises(self.manager.CadenceError):
                    self.manager.remove(
                        config, "systemd", "a", runner=runner
                    )
            self.assertTrue(all((directory / name).exists() for name in names))

    def test_malformed_manifest_seals_fail_as_cadence_errors(self):
        with self.assertRaises(self.manager.CadenceError):
            self.manager._verify_seal(
                {"manifest_sha256": "invalid", "not_json": {1, 2}}
            )

    def test_preview_snapshot_and_apply_abort_on_stale_crontab(self):
        original = b"MAILTO=founder@example.com\n"
        runner = CronRunner(original)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self.manager.CadenceConfig(
                host="claude",
                binary=root / "Claude App" / "claude",
                workspace=root / "work tree" / "founder-os",
                workdir=root / "work tree",
                log_root=root / "logs",
                slug="a",
            )
            manifest = self.manager.preview(
                config, "cron", runner=runner, date="2026-08-01"
            )
            snapshot = self.manager.snapshot(
                config,
                "cron",
                root,
                runner=runner,
                timestamp="20260801-120000",
            )
            self.assertEqual(original, Path(snapshot["backup_path"]).read_bytes())

            runner.current = b"MAILTO=changed@example.com\n"
            with self.assertRaises(self.manager.CadenceError):
                self.manager.apply(manifest, snapshot, runner=runner)
            self.assertIsNone(runner.installed)

            runner.current = original
            self.manager.apply(manifest, snapshot, runner=runner)
            self.assertEqual(
                self.manager.decode_artifact(manifest, "crontab"),
                runner.installed,
            )
            self.assertEqual(
                manifest,
                json.loads(self.manager.serialize_manifest(manifest)),
            )


if __name__ == "__main__":
    unittest.main()
