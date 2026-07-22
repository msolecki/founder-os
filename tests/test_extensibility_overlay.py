"""Contract tests for the local overlay (references/extensibility.md).

The overlay is the one part of this package whose validation cannot run in CI:
`scripts/validate_package.py` checks the package, and a founder's `_local/`
directory does not exist when it runs. So what CI *can* pin is the contract
itself — that the reference states the rules, that the guard implements them,
that `skill-forge` carries the refusals, and that `founder-os-doctor` is where
the late-binding validation actually lives. A rule stated in one of those four
places and missing from the others is how the overlay quietly becomes advisory.
"""
import importlib.util
import sys
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import yaml  # noqa: E402

from _package import (  # noqa: E402
    STANDALONE_SKILLS,
    SYSTEM_SKILLS,
    parse_frontmatter,
)

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "founder-os"
REFERENCE = PLUGIN_ROOT / "references" / "extensibility.md"
FORGE = PLUGIN_ROOT / "skills" / "skill-forge" / "SKILL.md"
DOCTOR = PLUGIN_ROOT / "skills" / "founder-os-doctor" / "SKILL.md"
GUARD = PLUGIN_ROOT / "hooks" / "ownership-guard.py"


def norm(text):
    """Prose wraps; contracts do not. Compare on one line."""
    return " ".join(text.split())


def load_guard():
    spec = importlib.util.spec_from_file_location("ownership_guard", GUARD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ReferenceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = REFERENCE.read_text(encoding="utf-8")

    def test_reference_exists_and_states_the_three_rules(self):
        for marker in (
            "Additive only",
            "A conflict is a finding, never an override",
            "The overlay cannot widen the tool allowlist",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.text)

    def test_overlay_lives_in_the_workspace_not_the_plugin(self):
        self.assertIn("$FOUNDER_OS_HOME/_local/", self.text)
        self.assertIn("_local/ownership.yaml", self.text)

    def test_the_limit_is_stated_rather_than_papered_over(self):
        """An extensibility feature that implies enforcement it lacks is worse
        than one that admits the limit — the founder builds on the implication."""
        self.assertIn("not enforced at write time", norm(self.text).lower())

    def test_local_slugs_are_namespaced_and_installed_to_user_scope(self):
        self.assertIn("local-", self.text)
        self.assertIn("~/.claude/skills/", self.text)
        self.assertIn("~/.codex/skills/", self.text)


class OwnershipMapStaysPackaged(unittest.TestCase):
    """`_local/` is the founder's, so the packaged map must not claim it."""

    @classmethod
    def setUpClass(cls):
        cls.data = yaml.safe_load(
            (PLUGIN_ROOT / "references" / "ownership.yaml").read_text(
                encoding="utf-8"))

    def test_local_is_not_scaffolded_by_init(self):
        for entry in self.data.get("workspace_files") or []:
            self.assertFalse(str(entry).startswith("_local"), entry)

    def test_no_agent_owns_anything_under_local(self):
        for agent, paths in (self.data.get("owns") or {}).items():
            for path in paths or []:
                self.assertFalse(str(path).startswith("_local"), (agent, path))

    def test_the_map_points_at_its_own_overlay_contract(self):
        text = (PLUGIN_ROOT / "references" / "ownership.yaml").read_text(
            encoding="utf-8")
        self.assertIn("references/extensibility.md", text)


class GuardImplementsTheMergeRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.guard = load_guard()

    def test_the_overlay_directory_constant_is_the_one_the_docs_name(self):
        self.assertEqual(self.guard.LOCAL_DIR, "_local/")
        self.assertEqual(self.guard.LOCAL_MAP, "_local/ownership.yaml")

    def test_merge_is_additive(self):
        packaged = {"metrics.md": "cfo"}
        with mock.patch.object(
                self.guard, "local_ownership",
                return_value={"partners.md": "network-manager"}):
            merged = self.guard.merged_ownership(packaged, "/ws")
        self.assertEqual(merged,
                         {"metrics.md": "cfo",
                          "partners.md": "network-manager"})

    def test_a_collision_leaves_the_packaged_owner_in_place(self):
        packaged = {"metrics.md": "cfo"}
        with mock.patch.object(
                self.guard, "local_ownership",
                return_value={"Metrics.md": "network-manager"}):
            merged = self.guard.merged_ownership(packaged, "/ws")
        self.assertEqual(merged, {"metrics.md": "cfo"})

    def test_no_root_means_no_overlay(self):
        packaged = {"metrics.md": "cfo"}
        self.assertEqual(self.guard.merged_ownership(packaged, None), packaged)


class SkillForgeContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frontmatter, cls.body = parse_frontmatter(FORGE)

    def test_it_belongs_to_no_agent_by_design(self):
        """Its first write is `_local/`, which the guard denies every subagent.
        A skill no agent can run is a skill no agent should hold."""
        self.assertIn("skill-forge", SYSTEM_SKILLS)
        self.assertIn("skill-forge", STANDALONE_SKILLS)

    def test_it_declares_no_writes(self):
        self.assertNotIn("metadata", self.frontmatter)

    def test_no_agent_lists_it(self):
        for path in sorted((PLUGIN_ROOT / "agents").glob("*.md")):
            frontmatter, _ = parse_frontmatter(path)
            self.assertNotIn("skill-forge", frontmatter.get("skills") or [],
                             path.name)

    def test_every_refusal_from_the_reference_is_carried(self):
        _, refusals = self.body.split("## The refusals", 1)
        refusals = norm(refusals.split("\n## Steps", 1)[0])
        for marker in ("already owns", "plugin directory", "additive",
                       "Bash", "WebFetch", "mcp__", "Beliefs"):
            with self.subTest(marker=marker):
                self.assertIn(marker, refusals)

    def test_install_is_named_first_and_consented_once(self):
        self.assertIn("~/.claude/skills/founder-os-local-", self.body)
        self.assertIn("~/.codex/skills/founder-os-local-", self.body)
        body = norm(self.body)
        self.assertRegex(body, r"(?i)ask once")
        self.assertRegex(body, r"(?i)write only on a yes")

    def test_ownership_is_registered_in_the_same_run(self):
        self.assertRegex(norm(self.body), r"(?i)never afterwards")

    def test_it_never_edits_the_packaged_map(self):
        guardrails = self.body.split("## Guardrails", 1)[1]
        self.assertIn("Never edit `references/ownership.yaml`", guardrails)


class DoctorIsWhereOverlayValidationLives(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.body = parse_frontmatter(DOCTOR)
        cls.checks = cls.body.split("## The checks", 1)[1].split("\n## Steps", 1)[0]

    def test_all_six_overlay_checks_are_declared(self):
        for check in ("Overlay unreadable",
                      "Overlay claims a packaged path",
                      "Overlay incoherent",
                      "Local agent overreaches",
                      "Local skill off template",
                      "Installed copy drift"):
            with self.subTest(check=check):
                self.assertIn("**%s**" % check, self.checks)

    def test_the_inputs_admit_this_is_the_only_validation_the_overlay_gets(self):
        inputs = norm(self.body.split("## Inputs", 1)[1].split("\n##", 1)[0])
        self.assertIn("_local/", inputs)
        self.assertIn("references/extensibility.md", inputs)
        self.assertRegex(inputs, r"(?i)only validation the overlay ever gets")

    def test_no_overlay_finding_is_repairable(self):
        repairs = norm(self.body.split("## What it may repair", 1)[1])
        self.assertRegex(repairs, r"(?i)no overlay finding is repairable")

    def test_the_shareable_report_never_carries_a_local_slug(self):
        report = self.body.split("## The shareable report", 1)[1]
        self.assertIn("| `overlay` |", report)
        self.assertRegex(norm(report), r"(?i)never a local slug")


if __name__ == "__main__":
    unittest.main()
