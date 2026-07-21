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
