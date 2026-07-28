"""Contract tests for the dependency-free command generator."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_commands.py"


class GenerateCommandsTest(unittest.TestCase):
    def test_missing_skills_directory_is_clean_failure(self):
        with tempfile.TemporaryDirectory() as td:
            plugin = Path(td) / "plugin"
            plugin.mkdir()
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(plugin)],
                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL:", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_frontmatter_shapes_are_clean_failures(self):
        for yaml_root in ("[]", "false", "1", "not-a-mapping"):
            with self.subTest(yaml_root=yaml_root):
                with tempfile.TemporaryDirectory() as td:
                    plugin = Path(td) / "plugin"
                    (plugin / "agents").mkdir(parents=True)
                    (plugin / "skills").mkdir()
                    (plugin / "agents" / "broken.md").write_text(
                        "---\n%s\n---\nbody\n" % yaml_root,
                        encoding="utf-8",
                    )
                    result = subprocess.run(
                        [sys.executable, str(SCRIPT), str(plugin)],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                self.assertEqual(result.returncode, 1)
                self.assertIn("FAIL:", result.stdout)
                self.assertIn("mapping or null", result.stdout)
                self.assertNotIn("Traceback", result.stderr)
