"""The reporting channels, pinned to the package they report on.

Thirty-seven machines cloned this repo in a fortnight and not one of them had
anywhere to say anything: no issue templates, Discussions off, and a
CONTRIBUTING.md that never used the word "issue". These tests pin the channels
that fixed that, and one property that would otherwise rot silently — the
workflow dropdown is a copy of the package's skill list, and a copy of a growing
set is a second map.
"""
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = REPO_ROOT / ".github" / "ISSUE_TEMPLATE"
SKILLS = REPO_ROOT / "founder-os" / "skills"
DISCUSSIONS = "https://github.com/msolecki/founder-os/discussions"


def load(name):
    return yaml.safe_load((TEMPLATES / name).read_text(encoding="utf-8"))


def dropdown_options(template, field_id):
    for block in template["body"]:
        if block.get("id") == field_id:
            return block["attributes"]["options"]
    raise AssertionError("no field %r in template" % field_id)


class TestIssueTemplates(unittest.TestCase):
    def test_every_declared_template_exists_and_parses(self):
        for name in ("bug.yml", "workflow-feedback.yml", "idea.yml",
                     "config.yml"):
            with self.subTest(template=name):
                self.assertTrue((TEMPLATES / name).is_file(), name)
                self.assertIsInstance(load(name), dict)

    def test_workflow_dropdowns_are_the_package_skill_list(self):
        packaged = sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md"))
        for name in ("bug.yml", "workflow-feedback.yml"):
            with self.subTest(template=name):
                self.assertEqual(
                    dropdown_options(load(name), "workflow"),
                    packaged,
                    "%s lists a different set of workflows than the package "
                    "ships — a dropdown that drifts is a second map" % name,
                )

    def test_both_report_forms_ask_for_host_and_version(self):
        for name in ("bug.yml", "workflow-feedback.yml"):
            ids = {block.get("id") for block in load(name)["body"]}
            with self.subTest(template=name):
                self.assertIn("host", ids)
                self.assertIn("version", ids)

    def test_bug_report_requires_the_doctor_output(self):
        doctor = next(
            block for block in load("bug.yml")["body"]
            if block.get("id") == "doctor"
        )
        self.assertTrue(doctor["validations"]["required"])

    def test_idea_requires_the_decision_it_improves(self):
        """An idea with no decision behind it is the failure mode, not the form."""
        decision = next(
            block for block in load("idea.yml")["body"]
            if block.get("id") == "decision"
        )
        self.assertTrue(decision["validations"]["required"])

    def test_report_forms_warn_against_pasting_workspace_contents(self):
        for name in ("bug.yml", "workflow-feedback.yml"):
            markdown = " ".join(
                block["attributes"]["value"]
                for block in load(name)["body"]
                if block.get("type") == "markdown"
            ).lower()
            with self.subTest(template=name):
                self.assertIn("do not paste", markdown)

    def test_blank_issues_are_closed_and_discussions_are_offered(self):
        config = load("config.yml")
        self.assertFalse(config["blank_issues_enabled"])
        self.assertIn(
            DISCUSSIONS,
            [link["url"] for link in config["contact_links"]],
        )


class TestFeedbackIsReachable(unittest.TestCase):
    """A channel nobody is pointed at is a channel that stays empty."""

    def test_contributing_names_the_reporting_route(self):
        text = (REPO_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        self.assertIn("ISSUE_TEMPLATE", text)
        self.assertIn(DISCUSSIONS, text)

    def test_readme_links_feedback_from_the_top(self):
        text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("/issues/new/choose", text)

    def test_the_website_footer_offers_a_way_back(self):
        text = (REPO_ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        footer = text[text.index('<footer class="site-footer">'):]
        self.assertIn("/issues/new/choose", footer)


class TestFeedbackSkillTargetsARealTemplate(unittest.TestCase):
    def test_prefilled_url_names_a_template_that_exists(self):
        skill = (SKILLS / "founder-os-feedback" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        for name in ("workflow-feedback.yml", "bug.yml", "idea.yml"):
            with self.subTest(template=name):
                self.assertIn("template=%s" % name, skill)
                self.assertTrue((TEMPLATES / name).is_file())

    def test_the_prefill_uses_field_ids_and_never_a_body_parameter(self):
        """A YAML issue form ignores `body=`; it prefills by each field's id.

        The plan this came from specified the `body=` shape, which opens an
        empty form. The failure is invisible until someone clicks the link, so
        it is pinned here instead.
        """
        skill = (SKILLS / "founder-os-feedback" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        output = skill[skill.index("## Output"):]
        self.assertNotIn("&body=", output)

        ids = {
            block["id"]
            for block in load("workflow-feedback.yml")["body"]
            if block.get("id")
        }
        for field in sorted(ids):
            with self.subTest(field=field):
                self.assertIn("&%s=" % field, output)

    def test_the_skill_refuses_to_quote_workspace_values(self):
        """The rule lives in Beliefs so it survives a step-level refactor."""
        skill = (SKILLS / "founder-os-feedback" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        beliefs = skill[skill.index("## Beliefs"):skill.index("## Steps")]
        self.assertIn("never", beliefs.lower())
        self.assertIn("workspace", beliefs.lower())


if __name__ == "__main__":
    unittest.main()
