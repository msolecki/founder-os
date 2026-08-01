"""Executable package contract for the one-line /capture workflow."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "founder-os"
sys.path.insert(0, str(ROOT / "scripts"))

import validate_package as validator  # noqa: E402
from _package import parse_frontmatter  # noqa: E402


class CaptureSkillContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = PLUGIN_ROOT / "skills" / "capture" / "SKILL.md"
        cls.frontmatter, cls.body = parse_frontmatter(cls.path)

    def test_capture_is_held_only_by_the_inbox_owner(self):
        self.assertEqual(self.frontmatter["name"], "capture")
        self.assertEqual(
            self.frontmatter.get("metadata", {}).get("writes"),
            ["inbox.md"],
        )
        holders = []
        for path in (PLUGIN_ROOT / "agents").glob("*.md"):
            frontmatter, _ = parse_frontmatter(path)
            if "capture" in (frontmatter.get("skills") or []):
                holders.append(frontmatter["name"])
        self.assertEqual(holders, ["chief-of-staff"])

        ownership = yaml.safe_load(
            (PLUGIN_ROOT / "references" / "ownership.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("inbox.md", ownership["owns"]["chief-of-staff"])
        self.assertEqual(ownership["sections"]["inbox.md"], ["## Inbox"])

    def test_capture_validates_one_raw_line_before_any_write(self):
        for token in (
            "one nonblank logical line",
            "2048 UTF-8 bytes",
            "NUL",
            "newline",
            "carriage return",
            "reject",
            "before",
            "write",
            "do not trim or normalize",
            "do not split",
        ):
            with self.subTest(token=token):
                self.assertRegex(
                    self.body,
                    r"(?i)" + token.replace(" ", r"\s+"),
                )

    def test_capture_preserves_founder_bytes_inside_one_safe_list_item(self):
        for token in (
            "## Inbox",
            "- ",
            "founder's accepted bytes",
            "unchanged",
            "no ID",
            "date",
            "priority",
            "owner",
            "classification",
            "bet",
            "inferred wording",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)
        self.assertRegex(
            self.body,
            r"(?is)prefix.*?- .*prevents.*?## Urgent.*heading",
        )

    def test_capture_confirms_only_after_hash_guarded_write_and_reread(self):
        for token in (
            "read_state",
            "full `inbox.md`",
            "observed SHA-256",
            "write_owned_state",
            "expected hash",
            "re-read",
            "exact appended list item",
        ):
            with self.subTest(token=token):
                self.assertRegex(
                    self.body,
                    token.replace(" ", r"\s+"),
                )
        confirmation = (
            "Captured in `inbox.md`. The next `/daily-brief` or `/triage` "
            "will decide what it becomes."
        )
        self.assertEqual(self.body.count(confirmation), 1)
        self.assertRegex(
            self.body,
            r"(?is)validation.*gateway\s+write\s+failure.*"
            r"original.*unchanged",
        )
        self.assertRegex(
            self.body,
            r"(?is)post-write\s+re-read.*uncertain.*omit.*success",
        )

    def test_only_daily_brief_and_triage_drain_capture(self):
        self.assertRegex(
            self.body,
            r"(?is)only.*?/daily-brief.*?/triage.*drain",
        )
        interface = yaml.safe_load(
            (
                PLUGIN_ROOT
                / "skills"
                / "capture"
                / "agents"
                / "openai.yaml"
            ).read_text(encoding="utf-8")
        )["interface"]
        self.assertIn("$capture", interface["default_prompt"])
        self.assertRegex(interface["default_prompt"], r"(?i)one.*line.*inbox")


class CaptureValidatorContract(unittest.TestCase):
    def test_real_capture_contract_passes_build_validator(self):
        agents = validator.load_agents(PLUGIN_ROOT)
        self.assertEqual(validator.check_capture_contract(PLUGIN_ROOT, agents), [])

    def test_capture_contract_mutations_are_rejected(self):
        mutations = {
            "extra write": (
                "    - inbox.md\n",
                "    - inbox.md\n    - queue.md\n",
            ),
            "unsafe normalization": (
                "Do not trim or normalize",
                "Trim and normalize",
            ),
            "no reread": ("re-read", "trust the role result"),
            "wrong confirmation": (
                "Captured in `inbox.md`.",
                "Capture accepted.",
            ),
        }
        for label, (old, new) in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                copied = Path(tmp) / "founder-os"
                shutil.copytree(PLUGIN_ROOT, copied)
                path = copied / "skills" / "capture" / "SKILL.md"
                source = path.read_text(encoding="utf-8")
                self.assertIn(old, source)
                path.write_text(source.replace(old, new, 1), encoding="utf-8")
                errors = validator.check_capture_contract(
                    copied, validator.load_agents(copied)
                )
                self.assertTrue(errors, (label, errors))


class CapturePublicCountContract(unittest.TestCase):
    def test_capture_moves_the_package_to_fifty_three_workflows(self):
        self.assertEqual(
            len(list((PLUGIN_ROOT / "skills").glob("*/SKILL.md"))),
            53,
        )
        for path in (
            ROOT / "README.md",
            PLUGIN_ROOT / "README.md",
            ROOT / "docs" / "README.md",
            ROOT / "docs" / "commands.md",
            ROOT / "docs" / "index.html",
        ):
            with self.subTest(path=path):
                self.assertRegex(
                    path.read_text(encoding="utf-8"),
                    r"(?i)53 (?:skills|workflows)",
                )


if __name__ == "__main__":
    unittest.main()
