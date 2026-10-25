"""Contracts for founder-os/scripts/skill_usage.py: what it counts, what it
deduplicates, and that it prints names and dates — never transcript text."""
import datetime
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "founder-os" / "scripts" / "skill_usage.py"

spec = importlib.util.spec_from_file_location("skill_usage", SCRIPT)
U = importlib.util.module_from_spec(spec)
spec.loader.exec_module(U)


def tool_use(uuid, day, name, **tool_input):
    return {"type": "assistant", "uuid": uuid, "timestamp": day + "T10:00:00Z",
            "message": {"content": [{"type": "tool_use", "name": name,
                                     "input": tool_input}]}}


class TestSkillUsage(unittest.TestCase):
    def setUp(self):
        self.config = Path(tempfile.mkdtemp())
        self.today = datetime.date(2026, 7, 20)
        recent = (self.today - datetime.timedelta(days=2)).isoformat()
        old = (self.today - datetime.timedelta(days=90)).isoformat()
        records = [
            tool_use("u1", recent, "Skill", skill="founder-os:daily-brief"),
            tool_use("u2", old, "Skill", skill="founder-os:daily-brief"),
            tool_use("u3", recent, "Agent", subagent_type="founder-os:cfo",
                     prompt="SECRET revenue 9000"),
            tool_use("u4", recent, "Skill", skill="developer-os:spec"),
            tool_use("u5", recent, "Skill",
                     skill="founder-os:SECRET free text"),
            tool_use("u6", recent, "Skill", skill="founder-os:retired-flow"),
            {"type": "user", "uuid": "u7", "timestamp": old + "T09:00:00Z",
             "message": {"content":
                         "<command-name>/founder-os:triage</command-name>"}},
        ]
        project = self.config / "projects" / "-Users-x-secret-client"
        project.mkdir(parents=True)
        body = "\n".join(json.dumps(r, separators=(",", ":"))
                         for r in records) + "\nnot json founder-os:\n"
        (project / "a.jsonl").write_text(body, encoding="utf-8")
        # A resumed session repeats u1; it must not count twice.
        (project / "sub").mkdir()
        (project / "sub" / "b.jsonl").write_text(
            json.dumps(records[0]) + "\n", encoding="utf-8")
        self.recent, self.old = recent, old

    def tearDown(self):
        shutil.rmtree(self.config, ignore_errors=True)

    def test_scan_counts_skills_agents_and_typed_commands_once(self):
        used = U.scan(self.config / "projects")
        self.assertEqual(sorted(used["daily-brief"]), [self.old, self.recent])
        self.assertEqual(used["cfo"], [self.recent])
        self.assertEqual(used["triage"], [self.old])
        self.assertNotIn("spec", used)
        self.assertFalse(any("SECRET" in name for name in used))

    def test_records_without_a_uuid_are_each_counted(self):
        project = self.config / "projects" / "-Users-x-other"
        project.mkdir(parents=True)
        lines = [tool_use(None, self.recent, "Skill", skill="founder-os:capture")
                 for _ in range(2)]
        for line in lines:
            del line["uuid"]
        (project / "c.jsonl").write_text(
            "\n".join(json.dumps(r) for r in lines) + "\n", encoding="utf-8")
        self.assertEqual(U.scan(self.config / "projects")["capture"],
                         [self.recent, self.recent])

    def test_report_rows_never_used_and_gone(self):
        used = U.scan(self.config / "projects")
        text = U.report(used, {"daily-brief", "triage", "capture"}, {"cfo"},
                        self.today)
        lines = text.splitlines()
        self.assertEqual(lines[0], "kind | name | calls 30d | last used")
        self.assertIn("workflow | daily-brief | 1 | %s" % self.recent, lines)
        self.assertIn("role | cfo | 1 | %s" % self.recent, lines)
        self.assertIn("workflow | triage | 0 | %s" % self.old, lines)
        self.assertIn("Never used (1): capture", lines)
        self.assertIn("Seen in history, no longer packaged: retired-flow",
                      lines)

    def test_cli_honors_config_dir_and_prints_no_content(self):
        env = {**os.environ, "CLAUDE_CONFIG_DIR": str(self.config)}
        # The CLI counts against its own clock; a far-future call stays in
        # its 30-day window whatever the date.
        project = self.config / "projects" / "-Users-x-future"
        project.mkdir(parents=True)
        (project / "d.jsonl").write_text(json.dumps(tool_use(
            "u9", "2999-01-01", "Skill", skill="founder-os:capture")) + "\n",
            encoding="utf-8")
        result = subprocess.run([sys.executable, str(SCRIPT)], env=env,
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("workflow | capture | 1 | 2999-01-01", result.stdout)
        self.assertTrue(any(
            line.startswith("workflow | daily-brief | ")
            and line.endswith(" | %s" % self.recent)
            for line in result.stdout.splitlines()), result.stdout)
        self.assertIn("Never used (", result.stdout)
        for leaked in ("SECRET", "9000", "secret-client", str(self.config)):
            self.assertNotIn(leaked, result.stdout)

    def test_missing_history_is_not_an_error(self):
        env = {**os.environ, "CLAUDE_CONFIG_DIR": str(self.config / "none")}
        result = subprocess.run([sys.executable, str(SCRIPT)], env=env,
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Never used (", result.stdout)


if __name__ == "__main__":
    unittest.main()
