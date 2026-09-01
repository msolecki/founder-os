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
ADVISORIES = "https://github.com/msolecki/founder-os/security/advisories/new"


def load(name):
    return yaml.safe_load((TEMPLATES / name).read_text(encoding="utf-8"))


def dropdown_options(template, field_id):
    for block in template["body"]:
        if block.get("id") == field_id:
            return block["attributes"]["options"]
    raise AssertionError("no field %r in template" % field_id)


class TestIssueTemplates(unittest.TestCase):
    def test_every_declared_template_exists_and_parses(self):
        for name in ("report.yml", "idea.yml", "config.yml"):
            with self.subTest(template=name):
                self.assertTrue((TEMPLATES / name).is_file(), name)
                self.assertIsInstance(load(name), dict)

    def test_the_workflow_dropdown_is_the_package_skill_list(self):
        packaged = sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md"))
        self.assertEqual(
            dropdown_options(load("report.yml"), "workflow"),
            packaged,
            "report.yml lists a different set of workflows than the package "
            "ships — a dropdown that drifts is a second map",
        )

    def test_the_report_form_asks_for_host_and_version(self):
        ids = {block.get("id") for block in load("report.yml")["body"]}
        self.assertIn("host", ids)
        self.assertIn("version", ids)

    def test_the_doctor_output_is_offered_and_never_required(self):
        """An install broken enough to be worth reporting may not run doctor.

        Requiring it turned the worst bugs into no report at all, which is the
        opposite of what the field was added for.
        """
        doctor = next(
            block for block in load("report.yml")["body"]
            if block.get("id") == "doctor"
        )
        self.assertFalse(doctor.get("validations", {}).get("required", False))

    def test_the_split_that_used_to_be_two_forms_is_one_question(self):
        """Two forms asked the reporter to classify their own bug from
        descriptions that overlapped. The dropdown asks the one thing that
        actually separates them: did it finish?"""
        options = dropdown_options(load("report.yml"), "kind")
        self.assertEqual(2, len(options))
        joined = " ".join(options).lower()
        self.assertIn("errored", joined)
        self.assertIn("completed", joined)

    def test_idea_requires_the_decision_it_improves(self):
        """An idea with no decision behind it is the failure mode, not the form."""
        decision = next(
            block for block in load("idea.yml")["body"]
            if block.get("id") == "decision"
        )
        self.assertTrue(decision["validations"]["required"])

    def test_the_report_form_warns_against_pasting_workspace_contents(self):
        markdown = " ".join(
            block["attributes"]["value"]
            for block in load("report.yml")["body"]
            if block.get("type") == "markdown"
        ).lower()
        self.assertIn("do not paste", markdown)

    def test_no_form_hardcodes_a_version_that_will_go_stale(self):
        """The old placeholder read `2.6.0` and nothing checked it.

        It was correct on the day it was written and wrong at the next bump,
        which the release right after this one performs — the same drift the
        workflow dropdown is pinned against, one field along.
        """
        for name in ("report.yml", "idea.yml"):
            for block in load(name)["body"]:
                attributes = block.get("attributes", {})
                with self.subTest(template=name, field=block.get("id")):
                    self.assertNotRegex(
                        str(attributes.get("placeholder", "")),
                        r"^\d+\.\d+\.\d+$",
                        "a version placeholder is a copy of the manifest, and "
                        "a copy of a moving number is a second map",
                    )

    def test_blank_issues_are_closed_and_discussions_are_offered(self):
        config = load("config.yml")
        self.assertFalse(config["blank_issues_enabled"])
        self.assertIn(
            DISCUSSIONS,
            [link["url"] for link in config["contact_links"]],
        )

    def test_the_security_route_is_private_and_lands_somewhere_real(self):
        """The contact link promised "privately first" and pointed at a page
        with no security section, whose only reporting advice was the public
        tracker. A private route has to be a private form, named in every place
        that sends someone to it."""
        urls = [link["url"] for link in load("config.yml")["contact_links"]]
        self.assertIn(ADVISORIES, urls)

        policy = REPO_ROOT / "SECURITY.md"
        self.assertTrue(policy.is_file(), "SECURITY.md is the scope document")
        self.assertIn(ADVISORIES, policy.read_text(encoding="utf-8"))

        for page in ("trust.md", "trust.html"):
            with self.subTest(page=page):
                text = (REPO_ROOT / "docs" / page).read_text(encoding="utf-8")
                self.assertIn(ADVISORIES, text)

    def test_the_trust_center_carries_every_section_the_markdown_does(self):
        """The two are one page in two formats; a section in only one of them
        is a promise the other half of the audience never reads."""
        html = (REPO_ROOT / "docs" / "trust.html").read_text(encoding="utf-8")
        for anchor_id in ("website", "security"):
            with self.subTest(section=anchor_id):
                self.assertIn('id="%s"' % anchor_id, html)
                self.assertIn('href="#%s"' % anchor_id, html)



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
        for name in ("report.yml", "idea.yml"):
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

        # Every template, not just one. The pin existed to make "add a field to
        # the form and forget the skill" a build failure, and it covered one of
        # the three forms that claim to be prefilled.
        for name in ("report.yml", "idea.yml"):
            for field in sorted(
                block["id"] for block in load(name)["body"] if block.get("id")
            ):
                with self.subTest(template=name, field=field):
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
