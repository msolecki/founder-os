import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import validate_package as V


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
    for slug in ("guardrails", "state-integrity", "daily-brief"):
        write(root / "skills" / slug / "SKILL.md",
              "---\nname: %s\ndescription: d\n---\n\nBody.\n" % slug)
    write(root / "agents" / "chief-of-staff" / "AGENTS.md", (
        "---\nname: Chief of Staff\ntitle: Chief of Staff\nreportsTo: null\n"
        "skills:\n  - daily-brief\n  - guardrails\n  - state-integrity\n---\n\nBody.\n"
    ))
    write(root / "agents" / "cfo" / "AGENTS.md", (
        "---\nname: CFO\ntitle: CFO\nreportsTo: chief-of-staff\n"
        "skills:\n  - guardrails\n  - state-integrity\n---\n\nBody.\n"
    ))
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
        "workspace_files:\n  - goals.md\nowns:\n  chief-of-staff:\n    - goals.md\n"
    ))


def all_errors(root: Path):
    agents = V.load_agents(root)
    return (V.check_company(root) + V.check_agents(root, agents)
            + V.check_role_skill_exclusivity(agents) + V.check_orphans(root, agents)
            + V.check_teams(root) + V.check_tasks(root, agents)
            + V.check_ownership(root, agents) + V.check_skill_writes(root, agents))


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
            "skills:\n  - no-such-skill\n  - guardrails\n  - state-integrity\n---\n\nB.\n"
        ))
        errs = V.check_agents(self.root, V.load_agents(self.root))
        self.assertTrue(any("no-such-skill" in e for e in errs))

    def test_dangling_reports_to_is_caught(self):
        write(self.root / "agents" / "cfo" / "AGENTS.md", (
            "---\nname: CFO\ntitle: CFO\nreportsTo: ghost\n"
            "skills:\n  - guardrails\n  - state-integrity\n---\n\nB.\n"
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
            "skills:\n  - daily-brief\n  - guardrails\n  - state-integrity\n---\n\nB.\n"
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

    def test_unowned_workspace_file_is_caught(self):
        write(self.root / "references" / "ownership.yaml", (
            "workspace_files:\n  - goals.md\n  - metrics.md\n"
            "owns:\n  chief-of-staff:\n    - goals.md\n"
        ))
        errs = V.check_ownership(self.root, V.load_agents(self.root))
        self.assertTrue(any("metrics.md" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
