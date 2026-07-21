"""Release metadata and reproducible gate contracts for Founder OS."""

import json
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE_PATH = REPO_ROOT / ".claude-plugin" / "marketplace.json"
CLAUDE_MANIFEST_PATH = (
    REPO_ROOT / "founder-os" / ".claude-plugin" / "plugin.json"
)
CODEX_MANIFEST_PATH = REPO_ROOT / "founder-os" / ".codex-plugin" / "plugin.json"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"
CI_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"
DEVELOPMENT_PATH = REPO_ROOT / "docs" / "development.md"

RELEASE_VERSION = "2.4.0"
ACTIVATION_DESCRIPTION = (
    "Know what matters today with one source-linked daily decision from your "
    "goals, cash, pipeline, and commitments."
)


class ReleaseMetadataContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.marketplace = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))
        cls.claude_manifest = json.loads(
            CLAUDE_MANIFEST_PATH.read_text(encoding="utf-8")
        )
        cls.codex_manifest = json.loads(
            CODEX_MANIFEST_PATH.read_text(encoding="utf-8")
        )
        cls.changelog = CHANGELOG_PATH.read_text(encoding="utf-8")
        cls.ci = CI_PATH.read_text(encoding="utf-8")
        cls.development = DEVELOPMENT_PATH.read_text(encoding="utf-8")

    def test_all_release_versions_match_2_4_0(self):
        versions = {
            "marketplace": self.marketplace["plugins"][0]["version"],
            "claude": self.claude_manifest["version"],
            "codex": self.codex_manifest["version"],
        }
        self.assertEqual(set(versions.values()), {RELEASE_VERSION}, versions)

    def test_marketplace_and_plugin_descriptions_lead_with_activation(self):
        descriptions = {
            "marketplace": self.marketplace.get("description"),
            "marketplace entry": self.marketplace["plugins"][0]["description"],
            "claude": self.claude_manifest["description"],
            "codex": self.codex_manifest["description"],
        }
        self.assertEqual(
            set(descriptions.values()), {ACTIVATION_DESCRIPTION}, descriptions
        )

    def test_changelog_records_activation_trust_tests_and_launch_assets(self):
        release_heading = "## 2.4.0 — 2026-07-22"
        self.assertIn(release_heading, self.changelog)
        release = self.changelog.split(release_heading, 1)[1].split(
            "\n## 2.3.0", 1
        )[0]
        for marker in (
            "**Activation.**",
            "**Trust.**",
            "**Verification.**",
            "**Launch assets.**",
            "Codex remains beta/manual",
            "not tagged",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, release)
        self.assertNotIn("Codex parity", release)

    def test_ci_keeps_internal_smoke_without_unapproved_cli_download(self):
        workflow = yaml.safe_load(self.ci)
        job = workflow["jobs"]["validate-and-test"]
        self.assertNotIn("if", job)
        self.assertFalse(job.get("continue-on-error", False))

        steps = job["steps"]
        named_steps = {step.get("name"): step for step in steps if "name" in step}

        expected_commands = {
            "Smoke-test an installed copy": (
                "python3 scripts/smoke_installed_copy.py"
            ),
            "Run landing behavior tests": (
                "node --test tests/*.behavior.test.js"
            ),
        }
        for name, command in expected_commands.items():
            with self.subTest(step=name):
                step = named_steps[name]
                self.assertEqual(step.get("run"), command)
                self.assertNotIn("if", step)
                self.assertFalse(step.get("continue-on-error", False))

        self.assertNotIn("npx", self.ci)
        self.assertNotIn("npm install", self.ci)
        self.assertNotIn("npm exec", self.ci)

    def test_development_guide_documents_both_official_local_gates(self):
        normalized = " ".join(self.development.split())
        for marker in (
            "claude plugin validate .",
            "claude plugin validate founder-os",
            "The package currently emits one addressed warning for "
            "`founder-os/CLAUDE.md`",
            "the `SessionStart` hook injects that canonical guidance",
            "tests/test_session_context.py",
            "Any new or different warning blocks the release.",
            "explicit founder approval",
            "a release gate, not CI coverage",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, normalized)


if __name__ == "__main__":
    unittest.main()
