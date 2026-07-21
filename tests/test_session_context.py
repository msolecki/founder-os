"""Installed-copy smoke-test contracts."""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE_SCRIPT = REPO_ROOT / "scripts" / "smoke_installed_copy.py"
SOURCE_PLUGIN = REPO_ROOT / "founder-os"


def load_smoke_module():
    spec = importlib.util.spec_from_file_location(
        "smoke_installed_copy", SMOKE_SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestInstalledCopySmokeContract(unittest.TestCase):
    def test_smoke_script_exists(self):
        self.assertTrue(
            SMOKE_SCRIPT.is_file(),
            "Task 4 requires a reusable installed-copy smoke harness",
        )

    def test_all_session_sources_load_guidance_from_installed_copy(self):
        smoke = load_smoke_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            installed = smoke.create_installed_copy(
                SOURCE_PLUGIN, temp_root / "marketplace"
            )
            results = smoke.check_session_context(installed, temp_root)

        self.assertEqual(set(results), set(smoke.SESSION_SOURCES))
        expected_context = (
            smoke.CONTEXT_PREFIX
            + next(iter(results.values()))["installed_guidance"]
        )
        for result in results.values():
            output = result["output"]
            self.assertEqual(
                output["hookSpecificOutput"]["hookEventName"],
                "SessionStart",
            )
            self.assertEqual(
                output["hookSpecificOutput"]["additionalContext"],
                expected_context,
            )

    def test_repository_root_mutation_is_detected(self):
        smoke = load_smoke_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            installed = smoke.create_installed_copy(
                SOURCE_PLUGIN, temp_root / "marketplace"
            )
            with self.assertRaisesRegex(
                smoke.SmokeFailure, "installed-copy guidance"
            ):
                smoke.check_session_context(
                    installed,
                    temp_root,
                    hook_plugin_root=SOURCE_PLUGIN,
                )

    def test_installed_ownership_guard_covers_three_authority_paths(self):
        smoke = load_smoke_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            installed = smoke.create_installed_copy(
                SOURCE_PLUGIN, temp_root / "marketplace"
            )
            outcomes = smoke.check_ownership_guard(
                installed, temp_root / "workspace"
            )

        self.assertIsNone(outcomes["allowed_owner"])
        self.assertIsNone(outcomes["main_thread"])
        denied = outcomes["wrong_owner"]["hookSpecificOutput"]
        self.assertEqual(denied["permissionDecision"], "deny")
        self.assertIn("cfo", denied["permissionDecisionReason"])

    def test_package_tools_accept_installed_copy(self):
        smoke = load_smoke_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            installed = smoke.create_installed_copy(
                SOURCE_PLUGIN, temp_root / "marketplace"
            )
            results = smoke.check_package_tools(REPO_ROOT, installed)

        self.assertEqual(set(results), {"validator", "commands"})
        self.assertTrue(all(result.returncode == 0 for result in results.values()))

    def test_command_line_smoke_passes(self):
        result = subprocess.run(
            [sys.executable, str(SMOKE_SCRIPT)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("installed-copy smoke: PASS", result.stdout)


class TestInstalledCopySmokeWiring(unittest.TestCase):
    def test_ci_runs_smoke(self):
        workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("python3 scripts/smoke_installed_copy.py", workflow)

    def test_development_guide_documents_smoke(self):
        guide = (REPO_ROOT / "docs" / "development.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("python3 scripts/smoke_installed_copy.py", guide)


if __name__ == "__main__":
    unittest.main()
