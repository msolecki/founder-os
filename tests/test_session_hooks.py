"""Contracts for the version-notice (SessionStart) and decision-nudge (Stop)
hooks: what each prints, when it stays silent, and that it fails open.

Both run as Claude Code runs them — a subprocess, JSON on stdin — against a
temporary plugin-data directory, so no marker leaks between cases.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "founder-os"
NOTICE = PLUGIN_ROOT / "hooks" / "version-notice.py"
NUDGE = PLUGIN_ROOT / "hooks" / "decision-nudge.py"
VERSION = json.loads((PLUGIN_ROOT / ".claude-plugin" / "plugin.json")
                     .read_text(encoding="utf-8"))["version"]


class HookCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.data = self.tmp / "data"
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith(("FOUNDER_OS_", "CLAUDE_"))}
        self.env["CLAUDE_PLUGIN_DATA"] = str(self.data)
        self.env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_hook(self, hook, payload, **env):
        result = subprocess.run(
            [sys.executable, str(hook)],
            input=payload if isinstance(payload, str) else json.dumps(payload),
            capture_output=True, text=True, env={**self.env, **env},
            check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout) if result.stdout else None


class TestVersionNotice(HookCase):
    def test_first_install_then_silent(self):
        out = self.run_hook(NOTICE, {"source": "startup"})
        msg = out["systemMessage"]
        self.assertEqual(
            msg, "Founder OS %s is installed. What's new: "
            "https://msolecki.github.io/founder-os/changelog.html" % VERSION)
        hook = out["hookSpecificOutput"]
        self.assertEqual(hook["hookEventName"], "SessionStart")
        self.assertTrue(hook["additionalContext"].endswith("\n" + msg))
        self.assertIsNone(self.run_hook(NOTICE, {"source": "startup"}))

    def test_update_names_both_versions(self):
        marker = self.data / "notices" / "version"
        marker.parent.mkdir(parents=True)
        marker.write_text("0.0.1\n", encoding="utf-8")
        out = self.run_hook(NOTICE, {"source": "startup"})
        self.assertIn("Founder OS updated 0.0.1 -> %s." % VERSION,
                      out["systemMessage"])
        self.assertEqual(marker.read_text(encoding="utf-8"), VERSION + "\n")

    def test_silent_cases(self):
        cases = {
            "resume": ({"source": "resume"}, {}),
            "kill-switch": ({"source": "startup"},
                            {"FOUNDER_OS_NOTICES": "off"}),
            "headless": ({"source": "startup"},
                         {"CLAUDE_CODE_ENTRYPOINT": "sdk-cli"}),
            "bad stdin": ("not json", {"CLAUDE_PLUGIN_ROOT": str(self.tmp)}),
        }
        for name, (payload, env) in cases.items():
            with self.subTest(case=name):
                self.assertIsNone(self.run_hook(NOTICE, payload, **env))
        self.assertFalse((self.data / "notices" / "version").exists())

    def test_symlinked_marker_dir_fails_open(self):
        self.data.mkdir()
        (self.tmp / "elsewhere").mkdir()
        os.symlink(self.tmp / "elsewhere", self.data / "notices")
        self.assertIsNone(self.run_hook(NOTICE, {"source": "startup"}))
        self.assertEqual(list((self.tmp / "elsewhere").iterdir()), [])


class TestDecisionNudge(HookCase):
    def transcript(self, calls, founder_os=True, secret="SECRET-LINE"):
        path = self.tmp / "t.jsonl"
        lines = []
        for i in range(calls):
            name = ("mcp__plugin_founder-os_founder-os-state__read_state"
                    if founder_os and i == 0 else "Read")
            lines.append(json.dumps({"type": "assistant", "message": {
                "content": [{"type": "tool_use", "name": name,
                             "input": {"note": secret}}]}},
                separators=(",", ":")))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def payload(self, path, **extra):
        return {"session_id": "s1", "transcript_path": str(path), **extra}

    def test_nudges_once_after_threshold(self):
        path = self.transcript(30)
        out = self.run_hook(NUDGE, self.payload(path))
        msg = out["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "Stop")
        self.assertIn("30 tool calls", msg)
        self.assertIn("decisions/", msg)
        self.assertIn("founder-os:decision-log", msg)
        self.assertIn("founder-os:capture", msg)
        self.assertNotIn("SECRET-LINE", json.dumps(out))
        self.assertIsNone(self.run_hook(NUDGE, self.payload(path)))

    def test_repeat_stops_resume_from_the_last_offset(self):
        path = self.transcript(20)
        self.assertIsNone(self.run_hook(NUDGE, self.payload(path)))
        state = json.loads((self.data / "stop-nudge" / "s1.scan").read_text())
        self.assertEqual(
            {"offset": path.stat().st_size, "n": 20, "in_use": True}, state)
        with path.open("a", encoding="utf-8") as f:
            for _ in range(10):
                f.write('{"type":"assistant","message":{"content":'
                        '[{"type":"tool_use","name":"Read"}]}}\n')
        out = self.run_hook(NUDGE, self.payload(path))
        self.assertIn("30 tool calls",
                      out["hookSpecificOutput"]["additionalContext"])

    def test_a_partial_last_line_counts_but_is_rescanned(self):
        path = self.transcript(29)
        with path.open("a", encoding="utf-8") as f:
            f.write('{"type":"assistant","message":{"content":'
                    '[{"type":"tool_use","name":"Read"}]}}')
        size = path.stat().st_size
        # A nudge ends the session's scanning and drops its state, so the
        # state is read from a Stop that stays below the threshold.
        self.assertIsNone(self.run_hook(
            NUDGE, self.payload(path), FOUNDER_OS_STOP_NUDGE_MIN="31"))
        state = json.loads((self.data / "stop-nudge" / "s1.scan").read_text())
        self.assertLess(state["offset"], size)
        self.assertEqual(29, state["n"])
        out = self.run_hook(NUDGE, self.payload(path))
        self.assertIn("30 tool calls",
                      out["hookSpecificOutput"]["additionalContext"])

    def test_a_rewritten_transcript_is_rescanned_from_the_start(self):
        stop_nudge = self.data / "stop-nudge"
        stop_nudge.mkdir(parents=True)
        (stop_nudge / "s1.scan").write_text(
            json.dumps({"offset": 10 ** 9, "n": 0, "in_use": False}))
        path = self.transcript(30)
        self.assertIsNotNone(self.run_hook(NUDGE, self.payload(path)))

    def test_stale_state_is_swept_without_a_nudge_and_scan_dropped_on_one(self):
        stop_nudge = self.data / "stop-nudge"
        stop_nudge.mkdir(parents=True)
        old = time.time() - 9 * 86400
        for name in ("s9", "s9.scan", "s9.scan.tmp"):
            (stop_nudge / name).write_text("{}")
            os.utime(stop_nudge / name, (old, old))
        (stop_nudge / "s8.scan").write_text("{}")
        self.assertIsNone(self.run_hook(NUDGE, self.payload(self.transcript(5))))
        self.assertEqual({".swept", "s1.scan", "s8.scan"},
                         {p.name for p in stop_nudge.iterdir()})
        self.assertIsNotNone(
            self.run_hook(NUDGE, self.payload(self.transcript(30))))
        self.assertTrue((stop_nudge / "s1").exists())
        self.assertFalse((stop_nudge / "s1.scan").exists())

    def test_a_live_session_keeps_its_marker_past_the_sweep(self):
        path = self.transcript(30)
        self.assertIsNotNone(self.run_hook(NUDGE, self.payload(path)))
        stop_nudge = self.data / "stop-nudge"
        old = time.time() - 9 * 86400
        os.utime(stop_nudge / "s1", (old, old))
        os.utime(stop_nudge / ".swept", (old, old))
        # The next Stop refreshes the marker; the sweep then leaves it.
        self.assertIsNone(self.run_hook(NUDGE, self.payload(path)))
        self.assertIsNone(self.run_hook(NUDGE, self.payload(path)))
        self.assertTrue((stop_nudge / "s1").exists())

    def test_threshold_is_configurable(self):
        path = self.transcript(5)
        self.assertIsNone(self.run_hook(NUDGE, self.payload(path)))
        self.assertIsNotNone(self.run_hook(
            NUDGE, self.payload(path), FOUNDER_OS_STOP_NUDGE_MIN="5"))

    def test_silent_cases(self):
        path = self.transcript(40)
        cases = {
            "stop_hook_active": (self.payload(path, stop_hook_active=True), {}),
            "subagent": (self.payload(path, agent_id="a1"), {}),
            "kill-switch": (self.payload(path),
                            {"FOUNDER_OS_STOP_NUDGE": "off"}),
            "headless": (self.payload(path),
                         {"CLAUDE_CODE_ENTRYPOINT": "sdk-cli"}),
            "bad session id": ({"session_id": "../x",
                                "transcript_path": str(path)}, {}),
            "missing transcript": (self.payload(self.tmp / "nope"), {}),
            "not json": ("{{{", {}),
        }
        for name, (payload, env) in cases.items():
            with self.subTest(case=name):
                self.assertIsNone(self.run_hook(NUDGE, payload, **env))

    def test_session_without_founder_os_is_silent(self):
        path = self.transcript(40, founder_os=False)
        self.assertIsNone(self.run_hook(NUDGE, self.payload(path)))

    def test_typed_command_counts_as_founder_os_in_use(self):
        path = self.transcript(40, founder_os=False)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"type": "user", "message": {"content":
                "<command-name>/founder-os:daily-brief</command-name>"}},
                separators=(",", ":")) + "\n")
        self.assertIsNotNone(self.run_hook(NUDGE, self.payload(path)))


if __name__ == "__main__":
    unittest.main()
