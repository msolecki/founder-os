"""Executable contract for Founder OS first-run activation.

The product is a Markdown plugin, so these tests pin observable orchestration
structure rather than exact copy. Ownership and skill holders are always read
from the package manifests; this file deliberately carries no second owner map.
"""

import re
import sys
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "founder-os"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from _package import parse_frontmatter  # noqa: E402


def h2_sections(body: str) -> list[tuple[str, str, int]]:
    """Return H2 title, body and source offset without pinning prose."""
    matches = list(re.finditer(r"(?m)^##[ \t]+(.+?)[ \t]*$", body))
    return [
        (
            match.group(1),
            body[match.end() : matches[index + 1].start()]
            if index + 1 < len(matches)
            else body[match.end() :],
            match.start(),
        )
        for index, match in enumerate(matches)
    ]


def section_matching(body: str, pattern: str) -> tuple[str, str, int]:
    for section in h2_sections(body):
        if re.search(pattern, section[0], re.IGNORECASE):
            return section
    raise AssertionError(f"missing H2 matching {pattern!r}")


def owner_for(path: str, ownership: dict) -> str:
    matches = []
    for agent, owned_paths in ownership["owns"].items():
        for owned_path in owned_paths:
            if path == owned_path or (
                owned_path.endswith("/") and path.startswith(owned_path)
            ):
                matches.append(agent)
    if len(matches) != 1:
        raise AssertionError(f"{path!r} has {len(matches)} owners: {matches}")
    return matches[0]


def skill_holders(skill_name: str) -> list[str]:
    holders = []
    for agent_path in sorted((PLUGIN_ROOT / "agents").glob("*.md")):
        frontmatter, _ = parse_frontmatter(agent_path)
        if skill_name in frontmatter.get("skills", []):
            holders.append(frontmatter["name"])
    return holders


def receipt_markers(text: str) -> dict[str, int]:
    patterns = {
        "minimum state validation": r"minimum[- ]state validation",
        "daily brief invocation": r"(?:invoke|run)[^\n]{0,80}/daily-brief",
        "persisted daily review": (
            r"(?:successful|validated)[^\n]{0,100}"
            r"(?:write|persist)[^\n]{0,100}reviews/daily/"
        ),
        "activation receipt": r"Activation complete",
    }
    positions = {}
    for label, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match is None:
            raise AssertionError(f"missing {label}: /{pattern}/")
        positions[label] = match.start()
    return positions


def assert_receipt_order(testcase: unittest.TestCase, text: str) -> None:
    positions = receipt_markers(text)
    testcase.assertLess(
        positions["minimum state validation"],
        positions["daily brief invocation"],
    )
    testcase.assertLess(
        positions["daily brief invocation"],
        positions["persisted daily review"],
    )
    testcase.assertLess(
        positions["persisted daily review"],
        positions["activation receipt"],
        "Activation complete must follow the persisted daily review",
    )


class OnboardingActivationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.init_frontmatter, cls.init_body = parse_frontmatter(
            PLUGIN_ROOT / "skills" / "founder-os-init" / "SKILL.md"
        )
        cls.ownership = yaml.safe_load(
            (PLUGIN_ROOT / "references" / "ownership.yaml").read_text(
                encoding="utf-8"
            )
        )

    def test_init_declares_ordered_activation_stages(self):
        self.assertEqual(self.init_frontmatter["name"], "founder-os-init")
        headings = [title for title, _, _ in h2_sections(self.init_body)]
        required = [
            r"Stage 0.*Preflight",
            r"Stage 1/4.*Business",
            r"Stage 2/4.*Customer",
            r"Stage 3/4.*Quarter",
            r"Stage 4/4.*Money",
            r"Stage 5.*Owner-safe delegation",
            r"Stage 6.*First brief",
            r"Stage 7.*Activation receipt",
            r"Resume and failure",
        ]
        positions = []
        for pattern in required:
            position = next(
                (index for index, heading in enumerate(headings)
                 if re.search(pattern, heading, re.IGNORECASE)),
                None,
            )
            self.assertIsNotNone(position, f"missing H2 /{pattern}/")
            positions.append(position)
        self.assertEqual(positions, sorted(positions), positions)

    def test_preflight_classifies_new_incomplete_and_activated_workspaces(self):
        _, preflight, _ = section_matching(
            self.init_body, r"Stage 0.*Preflight"
        )
        for required in (
            "read-only",
            "FOUNDER_OS_HOME",
            "business slug",
            "writable",
            "registry",
            "canonical context",
            "new",
            "incomplete",
            "activated",
        ):
            self.assertRegex(preflight, rf"(?i){re.escape(required)}")
        self.assertRegex(preflight, r"(?is)activated.*?/founder-os-doctor")
        self.assertRegex(preflight, r"(?is)incomplete.*?resume")

    def test_delegated_skills_follow_live_agent_and_ownership_manifests(self):
        _, delegation, _ = section_matching(
            self.init_body, r"Stage 5.*Owner-safe delegation"
        )
        chief_frontmatter, _ = parse_frontmatter(
            PLUGIN_ROOT / "agents" / "chief-of-staff.md"
        )
        allowlist = chief_frontmatter.get("tools", "")

        for skill_name in (
            "icp-definition",
            "quarterly-planning",
            "revenue-review",
            "runway-forecast",
        ):
            with self.subTest(skill=skill_name):
                skill_path = PLUGIN_ROOT / "skills" / skill_name / "SKILL.md"
                self.assertTrue(skill_path.is_file(), skill_path)
                skill_frontmatter, _ = parse_frontmatter(skill_path)
                writes = skill_frontmatter.get("metadata", {}).get("writes", [])
                self.assertTrue(writes, f"{skill_name} declares no writes")

                holders = skill_holders(skill_name)
                self.assertEqual(len(holders), 1, (skill_name, holders))
                holder = holders[0]
                for write_path in writes:
                    self.assertEqual(
                        holder,
                        owner_for(write_path, self.ownership),
                        (skill_name, write_path),
                    )

                self.assertRegex(delegation, rf"(?i)/{re.escape(skill_name)}\b")
                self.assertRegex(
                    delegation,
                    rf"(?i)\b{re.escape(holder)}\b",
                )
                self.assertRegex(
                    allowlist,
                    rf"(?i)\b{re.escape(holder)}\b",
                )

    def test_minimum_state_daily_brief_persistence_and_receipt_are_ordered(self):
        _, first_brief, first_brief_offset = section_matching(
            self.init_body, r"Stage 6.*First brief"
        )
        _, receipt, receipt_offset = section_matching(
            self.init_body, r"Stage 7.*Activation receipt"
        )
        self.assertLess(first_brief_offset, receipt_offset)
        assert_receipt_order(self, first_brief + receipt)

    def test_completion_reuses_the_preflight_resolved_workspace(self):
        _, preflight, _ = section_matching(
            self.init_body, r"Stage 0.*Preflight"
        )
        _, receipt, _ = section_matching(
            self.init_body, r"Stage 7.*Activation receipt"
        )
        for token in ("FOUNDER_OS_HOME", "business slug", "resolved workspace"):
            with self.subTest(token=token):
                self.assertRegex(preflight, rf"(?i){re.escape(token)}")
                self.assertRegex(receipt, rf"(?i){re.escape(token)}")
        self.assertRegex(receipt, r"(?i)same resolved workspace")

    def test_failure_reports_resume_state_without_a_success_receipt(self):
        _, failure, _ = section_matching(self.init_body, r"Resume and failure")
        for required in ("completed stages", "missing stage", "/founder-os-init"):
            self.assertRegex(failure, rf"(?i){re.escape(required)}")
        self.assertNotIn("Activation complete", failure)

    def test_receipt_order_check_detects_completion_moved_before_write(self):
        compliant = """
## Stage 6 — First brief
Perform minimum-state validation.
Invoke /daily-brief.
Require a successful persisted write to reviews/daily/YYYY-MM-DD.md.
## Stage 7 — Activation receipt
Print Activation complete.
"""
        assert_receipt_order(self, compliant)

        mutated = compliant.replace(
            "Require a successful persisted write to reviews/daily/YYYY-MM-DD.md.\n"
            "## Stage 7 — Activation receipt\n"
            "Print Activation complete.",
            "Print Activation complete.\n"
            "Require a successful persisted write to reviews/daily/YYYY-MM-DD.md.",
        )
        with self.assertRaisesRegex(
            AssertionError,
            "Activation complete must follow the persisted daily review",
        ):
            assert_receipt_order(self, mutated)


if __name__ == "__main__":
    unittest.main()
