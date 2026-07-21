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


def operative_markdown(body: str) -> str:
    """Remove fenced examples and blockquotes while preserving line offsets."""
    operative_lines = []
    fence = None
    for line in body.splitlines(keepends=True):
        stripped = line.lstrip()
        marker = stripped[:3]
        if marker in {"```", "~~~"}:
            fence = None if fence == marker else marker if fence is None else fence
            operative_lines.append("\n" if line.endswith("\n") else "")
        elif fence is not None or stripped.startswith(">"):
            operative_lines.append("\n" if line.endswith("\n") else "")
        else:
            operative_lines.append(line)
    return "".join(operative_lines)


def markdown_sections(body: str, level: int) -> list[tuple[str, str, int]]:
    """Return operative sections at one heading level."""
    body = operative_markdown(body)
    marker = "#" * level
    matches = list(
        re.finditer(rf"(?m)^{re.escape(marker)}[ \t]+(.+?)[ \t]*$", body)
    )
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


def h2_sections(body: str) -> list[tuple[str, str, int]]:
    return markdown_sections(body, 2)


def section_matching(
    body: str, pattern: str, level: int = 2
) -> tuple[str, str, int]:
    matches = [
        section
        for section in markdown_sections(body, level)
        if re.search(pattern, section[0], re.IGNORECASE)
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"expected one H{level} matching {pattern!r}, found {len(matches)}"
        )
    return matches[0]


def structured_actions(body: str) -> dict[str, tuple[str, int]]:
    """Return unique `- **Action:** contract` entries from operative prose."""
    actions = {}
    pattern = re.compile(
        r"(?m)^[ \t]*(?:[-*+]|\d+\.)[ \t]+\*\*([^*\n]+):\*\*[ \t]*(.+)$"
    )
    for match in pattern.finditer(operative_markdown(body)):
        label = match.group(1).strip().lower()
        if label in actions:
            raise AssertionError(f"duplicate structured action {label!r}")
        actions[label] = (match.group(2).strip(), match.start())
    return actions


def markdown_table_rows(body: str) -> list[list[str]]:
    rows = []
    for line in operative_markdown(body).splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


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


def assert_receipt_order(testcase: unittest.TestCase, text: str) -> None:
    actions = structured_actions(text)
    required = (
        "minimum-state validation",
        "daily-brief invocation",
        "persisted completion",
        "activation receipt",
    )
    for label in required:
        testcase.assertIn(label, actions)
    positions = {label: actions[label][1] for label in required}
    testcase.assertRegex(
        actions["daily-brief invocation"][0], r"(?i)(?:invoke|run).*?/daily-brief"
    )
    testcase.assertRegex(
        actions["persisted completion"][0],
        r"(?i)(?:successful|validated).*(?:write|persist).*reviews/daily/",
    )
    testcase.assertRegex(
        actions["activation receipt"][0],
        r"(?i)\bActivation complete\b.*\bonly after\b.*"
        r"(?:successful|validated).*(?:write|persist)",
    )
    testcase.assertLess(
        positions["minimum-state validation"],
        positions["daily-brief invocation"],
    )
    testcase.assertLess(
        positions["daily-brief invocation"],
        positions["persisted completion"],
    )
    testcase.assertLess(
        positions["persisted completion"], positions["activation receipt"],
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
            matches = [
                index
                for index, heading in enumerate(headings)
                if re.search(pattern, heading, re.IGNORECASE)
            ]
            self.assertEqual(len(matches), 1, (pattern, matches))
            positions.append(matches[0])
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
        rows = markdown_table_rows(delegation)
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

                matching_rows = [
                    row
                    for row in rows
                    if any(
                        re.fullmatch(rf"`?/{re.escape(skill_name)}`?", cell)
                        for cell in row
                    )
                ]
                self.assertEqual(len(matching_rows), 1, (skill_name, rows))
                row_text = " | ".join(matching_rows[0])
                self.assertRegex(row_text, rf"(?i)\b{re.escape(holder)}\b")
                for write_path in writes:
                    self.assertIn(write_path, row_text)
                self.assertRegex(
                    allowlist,
                    rf"(?i)\b{re.escape(holder)}\b",
                )

        _, first_brief, _ = section_matching(
            self.init_body, r"Stage 6.*First brief"
        )
        daily_path = PLUGIN_ROOT / "skills" / "daily-brief" / "SKILL.md"
        self.assertTrue(daily_path.is_file(), daily_path)
        daily_frontmatter, _ = parse_frontmatter(daily_path)
        self.assertEqual(daily_frontmatter["name"], "daily-brief")
        daily_holders = skill_holders("daily-brief")
        self.assertEqual(len(daily_holders), 1, daily_holders)
        daily_holder = daily_holders[0]
        daily_writes = daily_frontmatter.get("metadata", {}).get("writes", [])
        self.assertTrue(daily_writes, "daily-brief declares no writes")
        for write_path in daily_writes:
            self.assertEqual(daily_holder, owner_for(write_path, self.ownership))
        self.assertEqual(
            daily_holder, owner_for("reviews/daily/", self.ownership)
        )
        self.assertRegex(first_brief, r"(?i)/daily-brief\b")

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
        _, validation, _ = section_matching(
            self.init_body, r"Stage 6.*First brief"
        )
        _, receipt, _ = section_matching(
            self.init_body, r"Stage 7.*Activation receipt"
        )
        for token in ("FOUNDER_OS_HOME", "business slug", "resolved workspace"):
            with self.subTest(token=token):
                self.assertRegex(preflight, rf"(?i){re.escape(token)}")
                self.assertRegex(validation, rf"(?i){re.escape(token)}")
                self.assertRegex(receipt, rf"(?i){re.escape(token)}")
        for section in (validation, receipt):
            self.assertRegex(section, r"(?i)same resolved workspace")

    def test_failure_reports_resume_state_without_a_success_receipt(self):
        _, failure, _ = section_matching(self.init_body, r"Resume and failure")
        _, halt, halt_offset = section_matching(failure, r"Failure", level=3)
        _, resume, resume_offset = section_matching(failure, r"Resume", level=3)
        self.assertLess(halt_offset, resume_offset)
        for required in (
            "completed stages",
            "missing stage",
            "/founder-os-init",
            "halt",
            "Stage 7",
        ):
            self.assertRegex(halt, rf"(?i){re.escape(required)}")
        self.assertNotIn("Activation complete", halt)
        for required in (
            "first missing stage",
            "completed stages",
            "preserve",
            "byte-for-byte",
        ):
            self.assertRegex(resume, rf"(?i){re.escape(required)}")

    def test_receipt_order_check_detects_completion_moved_before_write(self):
        compliant = """
## Stage 6 — First brief
- **Minimum-state validation:** validate the resolved target.
- **Daily-brief invocation:** invoke /daily-brief.
- **Persisted completion:** require a successful persisted write to reviews/daily/YYYY-MM-DD.md.
## Stage 7 — Activation receipt
- **Activation receipt:** print Activation complete only after the successful persisted write.
"""
        assert_receipt_order(self, compliant)

        mutated = compliant.replace(
            "- **Persisted completion:** require a successful persisted write to reviews/daily/YYYY-MM-DD.md.\n"
            "## Stage 7 — Activation receipt\n"
            "- **Activation receipt:** print Activation complete only after the successful persisted write.",
            "- **Activation receipt:** print Activation complete only after the successful persisted write.\n"
            "- **Persisted completion:** require a successful persisted write to reviews/daily/YYYY-MM-DD.md.",
        )
        with self.assertRaisesRegex(
            AssertionError,
            "Activation complete must follow the persisted daily review",
        ):
            assert_receipt_order(self, mutated)

    def test_contract_parser_ignores_examples_and_quotations(self):
        examples_only = """
```markdown
## Stage 0 — Preflight
- **Activation receipt:** print Activation complete only after a successful write.
```
> ## Stage 6 — First brief
> - **Daily-brief invocation:** invoke /daily-brief.
"""
        self.assertEqual(h2_sections(examples_only), [])
        self.assertEqual(structured_actions(examples_only), {})


if __name__ == "__main__":
    unittest.main()
