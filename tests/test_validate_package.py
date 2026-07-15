import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import validate_package as V


# The four headings every agent body must carry, in order.
AGENT_TAIL = ("---\n\n## What triggers you\nx\n## What you do\nx\n"
              "## What you produce\nx\n## Who you hand off to\nx\n")
UNIVERSALS = "  - guardrails\n  - state-integrity\n  - ingestion-gate\n"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def minimal_package(root: Path) -> None:
    """Smallest package that must validate clean: 2 agents, 1 team, 1 task."""
    write(root / "COMPANY.md", (
        "---\n"
        "name: Founder OS\n"
        "description: Test company\n"
        "slug: founder-os\n"
        "schema: agentcompanies/v1\n"
        "version: 1.0.0\n"
        "license: MIT\n"
        "authors:\n"
        "  - name: Mateusz Solecki\n"
        "goals:\n"
        "  - Ship\n"
        "---\n\nBody.\n"
    ))
    for slug in ("guardrails", "state-integrity", "ingestion-gate", "daily-brief"):
        write(root / "skills" / slug / "SKILL.md",
              "---\nname: %s\ndescription: d\n---\n\n## Beliefs\n\n- A.\n- B.\n- C.\n\n## Steps\n\n1. Go.\n" % slug)
    write(root / "agents" / "chief-of-staff" / "AGENTS.md",
          "---\nname: Chief of Staff\ntitle: Chief of Staff\nreportsTo: null\n"
          "skills:\n  - daily-brief\n" + UNIVERSALS + AGENT_TAIL)
    write(root / "agents" / "cfo" / "AGENTS.md",
          "---\nname: CFO\ntitle: CFO\nreportsTo: chief-of-staff\n"
          "skills:\n" + UNIVERSALS + AGENT_TAIL)
    write(root / "teams" / "board" / "TEAM.md", (
        "---\nname: Board\ndescription: d\nslug: board\n"
        "manager: ../../agents/chief-of-staff/AGENTS.md\n"
        "includes:\n  - ../../agents/cfo/AGENTS.md\n---\n\nBody.\n"
    ))
    write(root / "tasks" / "daily-brief" / "TASK.md", (
        "---\nname: Daily Brief\nassignee: chief-of-staff\n"
        "metadata:\n  skill: daily-brief\n---\n\nBody.\n"
    ))
    write(root / "references" / "ownership.yaml", (
        "workspace_files:\n  - goals.md\n"
        "owns:\n  chief-of-staff:\n    - goals.md\n"
        "sections:\n  goals.md:\n    - \"## Bets\"\n"
    ))


def all_errors(root: Path):
    agents = V.load_agents(root)
    return (V.check_company(root) + V.check_agents(root, agents)
            + V.check_role_skill_exclusivity(agents) + V.check_orphans(root, agents)
            + V.check_teams(root) + V.check_tasks(root, agents)
            + V.check_ownership(root, agents) + V.check_skill_writes(root, agents)
            + V.check_sections(root, agents) + V.check_routines(root, agents)
            + V.check_beliefs(root, agents) + V.check_agent_headings(root, agents))


class TestValidator(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "founder-os"
        minimal_package(self.root)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_minimal_package_is_clean(self):
        self.assertEqual(all_errors(self.root), [])

    def test_missing_company_field_is_caught(self):
        write(self.root / "COMPANY.md",
              "---\nname: Founder OS\nslug: founder-os\nschema: agentcompanies/v1\n---\n\nB.\n")
        self.assertTrue(any("description" in e for e in V.check_company(self.root)))

    def test_dangling_skill_reference_is_caught(self):
        write(self.root / "agents" / "cfo" / "AGENTS.md", (
            "---\nname: CFO\ntitle: CFO\nreportsTo: chief-of-staff\n"
            "skills:\n  - no-such-skill\n  - guardrails\n  - state-integrity\n  - ingestion-gate\n---\n\n## What triggers you\nx\n## What you do\nx\n## What you produce\nx\n## Who you hand off to\nx\n"
        ))
        errs = V.check_agents(self.root, V.load_agents(self.root))
        self.assertTrue(any("no-such-skill" in e for e in errs))

    def test_dangling_reports_to_is_caught(self):
        write(self.root / "agents" / "cfo" / "AGENTS.md", (
            "---\nname: CFO\ntitle: CFO\nreportsTo: ghost\n"
            "skills:\n  - guardrails\n  - state-integrity\n  - ingestion-gate\n---\n\n## What triggers you\nx\n## What you do\nx\n## What you produce\nx\n## Who you hand off to\nx\n"
        ))
        errs = V.check_agents(self.root, V.load_agents(self.root))
        self.assertTrue(any("ghost" in e for e in errs))

    def test_missing_universal_skill_is_caught(self):
        write(self.root / "agents" / "cfo" / "AGENTS.md",
              "---\nname: CFO\ntitle: CFO\nreportsTo: chief-of-staff\nskills:\n  - guardrails\n---\n\nB.\n")
        errs = V.check_agents(self.root, V.load_agents(self.root))
        self.assertTrue(any("state-integrity" in e for e in errs))

    def test_role_skill_owned_by_two_agents_is_caught(self):
        write(self.root / "agents" / "cfo" / "AGENTS.md", (
            "---\nname: CFO\ntitle: CFO\nreportsTo: chief-of-staff\n"
            "skills:\n  - daily-brief\n  - guardrails\n  - state-integrity\n  - ingestion-gate\n---\n\n## What triggers you\nx\n## What you do\nx\n## What you produce\nx\n## Who you hand off to\nx\n"
        ))
        errs = V.check_role_skill_exclusivity(V.load_agents(self.root))
        self.assertTrue(any("daily-brief" in e for e in errs))

    def test_universal_skills_are_exempt_from_exclusivity(self):
        self.assertEqual(V.check_role_skill_exclusivity(V.load_agents(self.root)), [])

    def test_orphan_skill_is_caught(self):
        write(self.root / "skills" / "lonely" / "SKILL.md", "---\nname: lonely\ndescription: d\n---\n\nB.\n")
        errs = V.check_orphans(self.root, V.load_agents(self.root))
        self.assertTrue(any("lonely" in e for e in errs))

    def test_unresolvable_team_path_is_caught(self):
        write(self.root / "teams" / "board" / "TEAM.md", (
            "---\nname: Board\ndescription: d\nslug: board\n"
            "manager: ../../agents/ghost/AGENTS.md\nincludes: []\n---\n\nB.\n"
        ))
        self.assertTrue(any("ghost" in e for e in V.check_teams(self.root)))

    def test_null_manager_is_clean(self):
        # A board has no manager: the founder chairs it and the founder is not an
        # agent. Requiring a truthy manager forced teams/board to name the very
        # agent its reviewer exists to attack.
        write(self.root / "teams" / "board" / "TEAM.md", (
            "---\nname: Board\ndescription: d\nslug: board\nmanager: null\n"
            "includes:\n  - ../../agents/cfo/AGENTS.md\n---\n\nB.\n"
        ))
        self.assertEqual(V.check_teams(self.root), [])

    def test_missing_manager_key_is_caught(self):
        # Absent and null are different claims: absent is an omission, null is a
        # decision. Only the omission is an error.
        write(self.root / "teams" / "board" / "TEAM.md", (
            "---\nname: Board\ndescription: d\nslug: board\n"
            "includes:\n  - ../../agents/cfo/AGENTS.md\n---\n\nB.\n"
        ))
        errs = V.check_teams(self.root)
        self.assertTrue(any("manager" in e for e in errs))

    def test_skill_writing_a_path_with_no_declared_sections_is_caught(self):
        write(self.root / "references" / "ownership.yaml", (
            "workspace_files:\n  - goals.md\n"
            "owns:\n  chief-of-staff:\n    - goals.md\n"
        ))
        write(self.root / "skills" / "daily-brief" / "SKILL.md", (
            "---\nname: daily-brief\ndescription: d\n"
            "metadata:\n  writes:\n    - goals.md\n---\n\nBody.\n"
        ))
        errs = V.check_sections(self.root, V.load_agents(self.root))
        self.assertTrue(any("goals.md" in e and "sections" in e for e in errs))

    def test_sections_declared_for_unowned_path_is_caught(self):
        write(self.root / "references" / "ownership.yaml", (
            "workspace_files:\n  - goals.md\n"
            "owns:\n  chief-of-staff:\n    - goals.md\n"
            "sections:\n  goals.md:\n    - \"## Bets\"\n"
            "  ghost.md:\n    - \"## Nowhere\"\n"
        ))
        errs = V.check_sections(self.root, V.load_agents(self.root))
        self.assertTrue(any("ghost.md" in e for e in errs))

    def test_skill_writing_a_path_with_declared_sections_is_clean(self):
        write(self.root / "skills" / "daily-brief" / "SKILL.md", (
            "---\nname: daily-brief\ndescription: d\n"
            "metadata:\n  writes:\n    - goals.md\n---\n\nBody.\n"
        ))
        self.assertEqual(V.check_sections(self.root, V.load_agents(self.root)), [])

    def test_task_skill_not_held_by_assignee_is_caught(self):
        write(self.root / "tasks" / "daily-brief" / "TASK.md", (
            "---\nname: Daily Brief\nassignee: cfo\nmetadata:\n  skill: daily-brief\n---\n\nB.\n"
        ))
        errs = V.check_tasks(self.root, V.load_agents(self.root))
        self.assertTrue(any("daily-brief" in e for e in errs))

    def test_file_with_two_owners_is_caught(self):
        write(self.root / "references" / "ownership.yaml", (
            "workspace_files:\n  - goals.md\n"
            "owns:\n  chief-of-staff:\n    - goals.md\n  cfo:\n    - goals.md\n"
        ))
        errs = V.check_ownership(self.root, V.load_agents(self.root))
        self.assertTrue(any("goals.md" in e for e in errs))

    def test_skill_writing_a_file_its_holder_does_not_own_is_caught(self):
        # This is the real bug found in Task 3: chief-of-staff held monthly-review
        # while cfo owned reviews/monthly/. Every other check passed.
        write(self.root / "references" / "ownership.yaml", (
            "workspace_files:\n  - goals.md\n  - metrics.md\n"
            "owns:\n  chief-of-staff:\n    - goals.md\n  cfo:\n    - metrics.md\n"
        ))
        write(self.root / "skills" / "daily-brief" / "SKILL.md", (
            "---\nname: daily-brief\ndescription: d\n"
            "metadata:\n  writes:\n    - metrics.md\n---\n\nBody.\n"
        ))
        errs = V.check_skill_writes(self.root, V.load_agents(self.root))
        self.assertTrue(any("metrics.md" in e and "chief-of-staff" in e for e in errs))

    def test_skill_writing_a_file_its_holder_owns_is_clean(self):
        write(self.root / "skills" / "daily-brief" / "SKILL.md", (
            "---\nname: daily-brief\ndescription: d\n"
            "metadata:\n  writes:\n    - goals.md\n---\n\nBody.\n"
        ))
        self.assertEqual(V.check_skill_writes(self.root, V.load_agents(self.root)), [])

    def test_skill_writing_unknown_path_is_caught(self):
        write(self.root / "skills" / "daily-brief" / "SKILL.md", (
            "---\nname: daily-brief\ndescription: d\n"
            "metadata:\n  writes:\n    - nowhere.md\n---\n\nBody.\n"
        ))
        errs = V.check_skill_writes(self.root, V.load_agents(self.root))
        self.assertTrue(any("nowhere.md" in e for e in errs))

    def _make_recurring(self, task_fm, paperclip):
        write(self.root / "tasks" / "daily-brief" / "TASK.md", task_fm)
        write(self.root / ".paperclip.yaml", paperclip)

    GOOD_PC = (
        "routines:\n  daily-brief:\n    catchUpPolicy: enqueue_missed_with_cap\n"
        "    concurrencyPolicy: coalesce_if_active\n    triggers:\n"
        "      - kind: schedule\n        enabled: true\n"
        "        cronExpression: \"0 8 * * 1-5\"\n        timezone: UTC\n"
    )
    GOOD_TASK = ("---\nname: Daily Brief\nassignee: chief-of-staff\nrecurring: true\n"
                 "metadata:\n  skill: daily-brief\n---\n\nBody.\n")

    def test_recurring_task_with_routine_is_clean(self):
        self._make_recurring(self.GOOD_TASK, self.GOOD_PC)
        self.assertEqual(V.check_routines(self.root, V.load_agents(self.root)), [])

    def test_legacy_schedule_block_is_caught(self):
        # The exact shape we shipped: the importer parses this as legacyRecurrence.
        self._make_recurring(
            "---\nname: Daily Brief\nassignee: chief-of-staff\n"
            "metadata:\n  skill: daily-brief\n"
            "schedule:\n  timezone: UTC\n  recurrence:\n    frequency: monthly\n"
            "    interval: 3\n---\n\nBody.\n", self.GOOD_PC)
        errs = V.check_routines(self.root, V.load_agents(self.root))
        self.assertTrue(any("legacy" in e for e in errs))

    def test_recurring_task_without_routine_never_fires(self):
        self._make_recurring(self.GOOD_TASK, "routines: {}\n")
        errs = V.check_routines(self.root, V.load_agents(self.root))
        self.assertTrue(any("never fire" in e for e in errs))

    def test_missing_catch_up_policy_is_caught(self):
        # Default skip_missed silently drops a cadence when the laptop was closed.
        self._make_recurring(self.GOOD_TASK, (
            "routines:\n  daily-brief:\n    triggers:\n      - kind: schedule\n"
            "        cronExpression: \"0 8 * * 1-5\"\n        timezone: UTC\n"))
        errs = V.check_routines(self.root, V.load_agents(self.root))
        self.assertTrue(any("catchUpPolicy" in e for e in errs))

    def test_malformed_cron_is_caught(self):
        self._make_recurring(self.GOOD_TASK, self.GOOD_PC.replace('"0 8 * * 1-5"', '"0 8 * *"'))
        errs = V.check_routines(self.root, V.load_agents(self.root))
        self.assertTrue(any("5-field" in e for e in errs))

    def test_orphan_routine_is_caught(self):
        self._make_recurring(self.GOOD_TASK, self.GOOD_PC + (
            "  ghost-routine:\n    catchUpPolicy: skip_missed\n    triggers:\n"
            "      - kind: schedule\n        cronExpression: \"0 9 * * 1\"\n"
            "        timezone: UTC\n"))
        errs = V.check_routines(self.root, V.load_agents(self.root))
        self.assertTrue(any("ghost-routine" in e for e in errs))

    def _role_skill(self, body):
        # daily-brief is a role skill (held by chief-of-staff), so it needs Beliefs.
        write(self.root / "skills" / "daily-brief" / "SKILL.md",
              "---\nname: daily-brief\ndescription: d\n---\n\n" + body)

    BELIEFS_OK = ("## Beliefs\n\n- One a generic advisor would not say.\n"
                  "- Two, contestable.\n- Three, the one they resist.\n\n## Steps\n\n1. Go.\n")

    def test_role_skill_with_three_beliefs_is_clean(self):
        self._role_skill(self.BELIEFS_OK)
        self.assertEqual(V.check_beliefs(self.root, V.load_agents(self.root)), [])

    def test_role_skill_without_beliefs_is_caught(self):
        self._role_skill("## Steps\n\n1. Go.\n")
        errs = V.check_beliefs(self.root, V.load_agents(self.root))
        self.assertTrue(any("missing '## Beliefs'" in e for e in errs))

    def test_too_few_beliefs_is_caught(self):
        self._role_skill("## Beliefs\n\n- Only one.\n\n## Steps\n\n1. Go.\n")
        errs = V.check_beliefs(self.root, V.load_agents(self.root))
        self.assertTrue(any("the bar is 3" in e for e in errs))

    def test_beliefs_after_steps_is_caught(self):
        self._role_skill("## Steps\n\n1. Go.\n\n## Beliefs\n\n- A.\n- B.\n- C.\n")
        errs = V.check_beliefs(self.root, V.load_agents(self.root))
        self.assertTrue(any("before '## Steps'" in e for e in errs))

    def test_system_skills_are_exempt_from_beliefs(self):
        # guardrails is a refusal rule; it does not get opinions about itself.
        write(self.root / "skills" / "guardrails" / "SKILL.md",
              "---\nname: guardrails\ndescription: d\n---\n\n## Steps\n\n1. Refuse.\n")
        errs = V.check_beliefs(self.root, V.load_agents(self.root))
        self.assertFalse(any("guardrails" in e for e in errs))

    def test_unowned_workspace_file_is_caught(self):
        write(self.root / "references" / "ownership.yaml", (
            "workspace_files:\n  - goals.md\n  - metrics.md\n"
            "owns:\n  chief-of-staff:\n    - goals.md\n"
        ))
        errs = V.check_ownership(self.root, V.load_agents(self.root))
        self.assertTrue(any("metrics.md" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
