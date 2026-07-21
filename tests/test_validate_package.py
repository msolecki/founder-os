"""Tests for scripts/validate_package.py (Claude Code plugin format).

Ported from the paperclipai/agentcompanies suite. Every test that encoded a bug
we actually shipped survived the port; the ones that died are the ones whose
subject died with the old runtime (COMPANY.md, TEAM.md, TASK.md, .paperclip.yaml
routines). Their replacements are check_plugin and check_agent_graph.

Two rules this file follows, both learned the hard way:

1. Assert on the *specific* error, not on "there was an error". A test that goes
   green because something unrelated broke is worse than no test at all.
2. Frontmatter is built once, from a dict, through yaml.safe_dump. Hand-rolled
   YAML once shipped a duplicate `skills:` key here: the second silently won,
   an agent lost its skills, and four tests failed for one reason while the
   fixture looked fine on screen. A dict cannot hold a duplicate key.
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import validate_package as V


UNIVERSALS = ["guardrails", "state-integrity", "ingestion-gate"]
DEFAULT_TOOLS = "Read, Write, Edit, Glob, Grep"

# The four headings every agent body must carry, in this order.
AGENT_BODY = ("\nBody.\n\n"
              "## What triggers you\nx\n\n"
              "## What you do\nx\n\n"
              "## What you produce\nx\n\n"
              "## Who you hand off to\nx\n")

BELIEFS_OK = ("## Beliefs\n\n"
              "- One a generic advisor would not say.\n"
              "- Two, contestable.\n"
              "- Three, the one they resist.\n\n"
              "## Steps\n\n1. Go.\n")

_OMIT = object()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _frontmatter(fm: dict, body: str) -> str:
    return "---\n" + yaml.safe_dump(fm, sort_keys=False) + "---\n" + body


def agent_md(name=_OMIT, description="Does one thing.", skills=_OMIT,
             tools=DEFAULT_TOOLS, body=AGENT_BODY) -> str:
    """Build an agent file. Pass _OMIT for a field to leave the key out.

    Omitted and empty are different claims to the validator, so they must be
    different here too: `tools=_OMIT` writes no `tools:` key at all, which is
    the inherit-everything-including-Bash case.
    """
    fm = {}
    for key, value in (("name", name), ("description", description),
                       ("skills", skills), ("tools", tools)):
        if value is not _OMIT:
            fm[key] = value
    return _frontmatter(fm, body)


def skill_md(name, description="d", writes=_OMIT, body=BELIEFS_OK) -> str:
    fm = {"name": name, "description": description}
    if writes is not _OMIT:
        fm["metadata"] = {"writes": list(writes)}
    return _frontmatter(fm, "\n" + body)


def base_ownership() -> dict:
    """A fresh, mutable copy — tests mutate it, so it cannot be a constant."""
    return {
        "workspace_files": ["goals.md"],
        "owns": {"chief-of-staff": ["goals.md"]},
        "sections": {"goals.md": ["## Bets"]},
    }


def all_errors(root: Path):
    agents = V.load_agents(root)
    errs = []
    for fn in V.CHECKS:
        errs += fn(root, agents)
    return errs


class ValidatorTestCase(unittest.TestCase):
    """The minimal package that must validate clean, plus mutation helpers.

    Two agents. chief-of-staff holds the one role skill (daily-brief, which
    writes goals.md, which chief-of-staff owns) and may summon cfo. cfo holds
    only the universals.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "founder-os"
        self.write_plugin({"name": "founder-os"})
        for slug in UNIVERSALS:
            # System skills: exempt from beliefs, so no beliefs.
            self.write_skill(slug, body="## Steps\n\n1. Go.\n")
        self.write_skill("daily-brief", writes=["goals.md"])
        self.write_agent("chief-of-staff", skills=["daily-brief"] + UNIVERSALS,
                         tools=DEFAULT_TOOLS + ", Agent(cfo)")
        self.write_agent("cfo", skills=list(UNIVERSALS))
        self.write_ownership(base_ownership())
        self.write_hooks()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    # -- mutation helpers: one construction path, so a mutation is a diff ----

    def write_plugin(self, data, raw=None):
        text = raw if raw is not None else json.dumps(data)
        write(self.root / ".claude-plugin" / "plugin.json", text)

    def write_agent(self, slug, **kw):
        kw.setdefault("name", slug)
        write(self.root / "agents" / (slug + ".md"), agent_md(**kw))

    def write_skill(self, slug, **kw):
        write(self.root / "skills" / slug / "SKILL.md", skill_md(slug, **kw))

    def write_ownership(self, data):
        write(self.root / "references" / "ownership.yaml",
              yaml.safe_dump(data, sort_keys=False))

    def write_hooks(self):
        write(self.root / "hooks" / "hooks.json", json.dumps({"hooks": {
            "PreToolUse": [{"matcher":
                "^(Write|Edit|NotebookEdit|Bash|WebFetch|apply_patch|mcp__.*)$",
                "hooks": []}]}}))
        write(self.root / "hooks" / "ownership-guard.py", "x = 1\n")

    def check(self, fn):
        return fn(self.root, V.load_agents(self.root))


class TestFixture(ValidatorTestCase):
    def test_frontmatter_accepts_crlf(self):
        path = self.root / "agents" / "crlf.md"
        write(path, agent_md("crlf").replace("\n", "\r\n"))
        fm, body = V.parse_frontmatter(path)
        self.assertEqual(fm["name"], "crlf")
        self.assertIn("## What you do", body)

    def test_minimal_package_is_clean(self):
        self.assertEqual(all_errors(self.root), [])

    def test_fixture_frontmatter_is_what_we_think_it_is(self):
        # Guards the duplicate-key class of fixture bug: if the frontmatter did
        # not survive the round trip, the mutation tests below would be testing
        # a package nobody described. Assert the fixture before trusting it.
        agents = V.load_agents(self.root)
        self.assertEqual(sorted(agents), ["cfo", "chief-of-staff"])

        cos_fm, cos_body = agents["chief-of-staff"]
        self.assertEqual(cos_fm["name"], "chief-of-staff")
        self.assertEqual(cos_fm["skills"], ["daily-brief"] + UNIVERSALS)
        self.assertEqual(V._tool_names(cos_fm["tools"]),
                         ["Read", "Write", "Edit", "Glob", "Grep", "Agent"])
        self.assertEqual(V._agent_targets(cos_fm["tools"]), ["cfo"])
        for heading in V.AGENT_HEADINGS:
            self.assertIn(heading, cos_body)

        cfo_fm, _ = agents["cfo"]
        self.assertEqual(cfo_fm["skills"], UNIVERSALS)
        self.assertEqual(V._agent_targets(cfo_fm["tools"]), [])


class TestPlugin(ValidatorTestCase):
    def test_claude_and_codex_manifest_identity_must_match(self):
        write(self.root / ".codex-plugin" / "plugin.json",
              json.dumps({"name": "founder-os", "version": "0.0.1",
                          "description": "different"}))
        errs = self.check(V.check_plugin)
        self.assertTrue(any("version differs" in err for err in errs), errs)
        self.assertTrue(any("description differs" in err for err in errs), errs)

    def test_missing_plugin_json_is_caught(self):
        (self.root / ".claude-plugin" / "plugin.json").unlink()
        self.assertEqual(self.check(V.check_plugin),
                         [".claude-plugin/plugin.json: missing"])

    def test_invalid_json_is_caught(self):
        self.write_plugin(None, raw='{"name": "founder-os",}')
        errs = self.check(V.check_plugin)
        self.assertEqual(len(errs), 1)
        self.assertTrue(errs[0].startswith(
            ".claude-plugin/plugin.json: invalid JSON ("), errs)

    def test_missing_name_is_caught(self):
        self.write_plugin({"description": "no name here"})
        self.assertEqual(
            self.check(V.check_plugin),
            ["plugin.json: 'name' is the one required field and it is missing"])


class TestAgents(ValidatorTestCase):
    def test_dangling_skill_reference_is_caught(self):
        self.write_agent("cfo", skills=["no-such-skill"] + UNIVERSALS)
        self.assertIn(
            "agents/cfo.md: skill 'no-such-skill' has no skills/no-such-skill/SKILL.md",
            self.check(V.check_agents))

    def test_missing_universal_skill_is_caught(self):
        self.write_agent("cfo", skills=["guardrails", "ingestion-gate"])
        self.assertIn("agents/cfo.md: must list universal skill 'state-integrity'",
                      self.check(V.check_agents))

    def test_name_not_matching_filename_is_caught(self):
        self.write_agent("cfo", name="CFO", skills=list(UNIVERSALS))
        self.assertIn("agents/cfo.md: name 'CFO' does not match the filename",
                      self.check(V.check_agents))

    def test_missing_description_is_caught(self):
        self.write_agent("cfo", description=_OMIT, skills=list(UNIVERSALS))
        self.assertIn("agents/cfo.md: missing 'description'",
                      self.check(V.check_agents))


class TestAgentTools(ValidatorTestCase):
    """House rule 0 — never outbound, never money — enforced at the tool layer.

    The rule is that agents draft and the founder sends. An agent holding Bash
    can curl; an agent holding WebFetch can POST. Prose asking it not to is not
    the same object as the capability not existing.
    """

    def test_bash_is_caught(self):
        self.write_agent("cfo", skills=list(UNIVERSALS),
                         tools=DEFAULT_TOOLS + ", Bash")
        self.assertIn(
            "agents/cfo.md: tool 'Bash' can reach the outside world — "
            "house rule 0 says agents draft and the founder sends",
            self.check(V.check_agent_tools))

    def test_webfetch_is_caught(self):
        self.write_agent("cfo", skills=list(UNIVERSALS),
                         tools=DEFAULT_TOOLS + ", WebFetch")
        self.assertIn(
            "agents/cfo.md: tool 'WebFetch' can reach the outside world — "
            "house rule 0 says agents draft and the founder sends",
            self.check(V.check_agent_tools))

    def test_additional_outbound_tools_are_caught(self):
        for tool in ("WebSearch", "NotebookEdit", "Task"):
            with self.subTest(tool=tool):
                self.write_agent("cfo", skills=list(UNIVERSALS),
                                 tools=DEFAULT_TOOLS + ", " + tool)
                self.assertIn(
                    "agents/cfo.md: tool '%s' can reach the outside world — "
                    "house rule 0 says agents draft and the founder sends" % tool,
                    self.check(V.check_agent_tools))

    def test_omitted_tools_is_caught(self):
        # No `tools:` key inherits every tool, including Bash. Silence here is
        # the most permissive setting there is, which is why it is an error.
        self.write_agent("cfo", skills=list(UNIVERSALS), tools=_OMIT)
        self.assertIn(
            "agents/cfo.md: 'tools' must be an explicit allowlist — omitting it "
            "inherits every tool, including Bash, and an agent with Bash can send",
            self.check(V.check_agent_tools))

    def test_unknown_tool_is_caught(self):
        self.write_agent("cfo", skills=list(UNIVERSALS),
                         tools=DEFAULT_TOOLS + ", Telepathy")
        self.assertIn("agents/cfo.md: unknown tool 'Telepathy'",
                      self.check(V.check_agent_tools))

    def test_allowlist_without_outbound_tools_is_clean(self):
        self.assertEqual(self.check(V.check_agent_tools), [])


class TestAgentGraph(ValidatorTestCase):
    def test_dangling_agent_target_is_caught(self):
        self.write_agent("chief-of-staff", skills=["daily-brief"] + UNIVERSALS,
                         tools=DEFAULT_TOOLS + ", Agent(ghost)")
        self.assertIn("agents/chief-of-staff.md: Agent(ghost) is not a real agent",
                      self.check(V.check_agent_graph))

    def test_self_summon_is_caught(self):
        self.write_agent("cfo", skills=list(UNIVERSALS),
                         tools=DEFAULT_TOOLS + ", Agent(cfo)")
        self.assertIn("agents/cfo.md: may not summon itself",
                      self.check(V.check_agent_graph))

    def test_real_agent_target_is_clean(self):
        self.assertEqual(self.check(V.check_agent_graph), [])


class TestRoleSkillExclusivity(ValidatorTestCase):
    def test_role_skill_held_by_two_agents_is_caught(self):
        # One decision, one owner. Two agents holding daily-brief means two
        # answers to the same question and no way to tell which one is the org's.
        self.write_agent("cfo", skills=["daily-brief"] + UNIVERSALS)
        self.assertIn(
            "role skill 'daily-brief' is held by both 'cfo' and 'chief-of-staff'",
            self.check(V.check_role_skill_exclusivity))

    def test_universal_skills_are_exempt_from_exclusivity(self):
        # Both fixture agents hold all three universals; that is the design.
        self.assertEqual(self.check(V.check_role_skill_exclusivity), [])


class TestOrphans(ValidatorTestCase):
    def test_orphan_skill_is_caught(self):
        self.write_skill("lonely")
        self.assertIn("skills/lonely: held by no agent and not declared standalone",
                      self.check(V.check_orphans))

    def test_standalone_skill_held_by_no_agent_is_clean(self):
        # setup-cadences is in STANDALONE_SKILLS: the founder runs it directly,
        # so belonging to no agent is the point rather than an oversight.
        self.assertIn("setup-cadences", V.STANDALONE_SKILLS)
        self.write_skill("setup-cadences")
        self.assertEqual(self.check(V.check_orphans), [])


class TestAgentHeadings(ValidatorTestCase):
    def test_missing_heading_is_caught(self):
        self.write_agent("cfo", skills=list(UNIVERSALS),
                         body="\n## What triggers you\nx\n\n## What you do\nx\n\n"
                              "## What you produce\nx\n")
        self.assertIn("agents/cfo.md: missing mandated heading '## Who you hand off to'",
                      self.check(V.check_agent_headings))

    def test_headings_out_of_order_is_caught(self):
        self.write_agent("cfo", skills=list(UNIVERSALS),
                         body="\n## What triggers you\nx\n\n## What you produce\nx\n\n"
                              "## What you do\nx\n\n## Who you hand off to\nx\n")
        errs = self.check(V.check_agent_headings)
        self.assertIn("agents/cfo.md: headings out of order", errs)
        # All four are present: the only complaint should be the order.
        self.assertFalse([e for e in errs if "missing" in e], errs)


class TestOwnership(ValidatorTestCase):
    def test_file_with_two_owners_is_caught(self):
        own = base_ownership()
        own["owns"]["cfo"] = ["goals.md"]
        self.write_ownership(own)
        self.assertIn(
            "ownership.yaml: 'goals.md' is owned by both 'chief-of-staff' and 'cfo'",
            self.check(V.check_ownership))

    def test_unowned_workspace_file_is_caught(self):
        own = base_ownership()
        own["workspace_files"].append("metrics.md")
        self.write_ownership(own)
        self.assertIn("ownership.yaml: workspace file 'metrics.md' has no owner",
                      self.check(V.check_ownership))

    def test_ownership_by_a_non_agent_is_caught(self):
        own = base_ownership()
        own["owns"]["ghost"] = []
        self.write_ownership(own)
        self.assertIn("ownership.yaml: 'ghost' is not a real agent",
                      self.check(V.check_ownership))

    def test_missing_ownership_file_is_caught(self):
        (self.root / "references" / "ownership.yaml").unlink()
        self.assertEqual(self.check(V.check_ownership),
                         ["references/ownership.yaml: missing"])


class TestSkillWrites(ValidatorTestCase):
    def test_skill_writing_a_file_its_holder_does_not_own_is_caught(self):
        # The real bug, shipped and caught in Task 3: chief-of-staff held
        # monthly-review while cfo owned reviews/monthly/. Every other check
        # passed — the skill existed, the owner existed, both were spelled
        # right. Only the join between them was wrong.
        own = base_ownership()
        own["workspace_files"].append("metrics.md")
        own["owns"]["cfo"] = ["metrics.md"]
        self.write_ownership(own)
        self.write_skill("daily-brief", writes=["metrics.md"])
        self.assertIn(
            "skills/daily-brief: held by 'chief-of-staff' but writes 'metrics.md', "
            "owned by 'cfo'",
            self.check(V.check_skill_writes))

    def test_skill_writing_a_file_its_holder_owns_is_clean(self):
        self.assertEqual(self.check(V.check_skill_writes), [])

    def test_skill_writing_unknown_path_is_caught(self):
        self.write_skill("daily-brief", writes=["nowhere.md"])
        self.assertIn("skills/daily-brief: writes 'nowhere.md', which no agent owns",
                      self.check(V.check_skill_writes))


class TestSections(ValidatorTestCase):
    def test_skill_writing_a_path_with_no_declared_sections_is_caught(self):
        own = base_ownership()
        del own["sections"]
        self.write_ownership(own)
        self.assertIn(
            "skills/daily-brief: writes 'goals.md' but ownership.yaml declares no "
            "sections for it",
            self.check(V.check_sections))

    def test_sections_declared_for_unowned_path_is_caught(self):
        own = base_ownership()
        own["sections"]["ghost.md"] = ["## Nowhere"]
        self.write_ownership(own)
        self.assertIn(
            "ownership.yaml: sections declares 'ghost.md', which no agent owns",
            self.check(V.check_sections))

    def test_skill_writing_a_path_with_declared_sections_is_clean(self):
        self.assertEqual(self.check(V.check_sections), [])


class TestBeliefs(ValidatorTestCase):
    def test_role_skill_with_three_beliefs_is_clean(self):
        self.assertEqual(self.check(V.check_beliefs), [])

    def test_role_skill_without_beliefs_is_caught(self):
        self.write_skill("daily-brief", writes=["goals.md"], body="## Steps\n\n1. Go.\n")
        self.assertIn("skills/daily-brief: missing '## Beliefs'",
                      self.check(V.check_beliefs))

    def test_too_few_beliefs_is_caught(self):
        self.write_skill("daily-brief", writes=["goals.md"],
                         body="## Beliefs\n\n- Only one.\n\n## Steps\n\n1. Go.\n")
        self.assertIn("skills/daily-brief: '## Beliefs' has 1 bullet(s); the bar is 3",
                      self.check(V.check_beliefs))

    def test_beliefs_after_steps_is_caught(self):
        # Beliefs written after the steps they are supposed to govern are a
        # postscript, not a premise.
        self.write_skill("daily-brief", writes=["goals.md"],
                         body="## Steps\n\n1. Go.\n\n## Beliefs\n\n- A.\n- B.\n- C.\n")
        self.assertIn("skills/daily-brief: '## Beliefs' must come before '## Steps'",
                      self.check(V.check_beliefs))

    def test_system_skills_are_exempt_from_beliefs(self):
        # guardrails is a refusal rule; it does not get opinions about itself.
        self.write_skill("guardrails", body="## Steps\n\n1. Refuse.\n")
        self.assertFalse([e for e in self.check(V.check_beliefs) if "guardrails" in e])


class TestWorkspaceFilesComplete(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        write(self.root / ".claude-plugin" / "plugin.json",
              json.dumps({"name": "founder-os"}))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write_ownership(self, data):
        write(self.root / "references" / "ownership.yaml", yaml.safe_dump(data))

    def test_owned_path_missing_from_workspace_files_is_an_error(self):
        data = base_ownership()
        data["owns"]["chief-of-staff"].append("drafts/outreach/")
        self._write_ownership(data)
        errs = V.check_workspace_files_complete(self.root, {})
        self.assertEqual(len(errs), 1, errs)
        self.assertIn("drafts/outreach/", errs[0])
        self.assertIn("workspace_files", errs[0])

    def test_owned_path_present_in_workspace_files_is_clean(self):
        data = base_ownership()
        data["workspace_files"].append("drafts/outreach/")
        data["owns"]["chief-of-staff"].append("drafts/outreach/")
        self._write_ownership(data)
        self.assertEqual(V.check_workspace_files_complete(self.root, {}), [])

    def test_missing_ownership_file_is_not_this_checks_problem(self):
        self.assertEqual(V.check_workspace_files_complete(self.root, {}), [])


class TestCheckHooks(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        write(self.root / ".claude-plugin" / "plugin.json",
              json.dumps({"name": "founder-os"}))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_missing_hooks_json_is_an_error(self):
        errs = V.check_hooks(self.root, {})
        self.assertTrue(any("hooks.json" in e for e in errs), errs)

    def test_unparseable_hooks_json_is_an_error(self):
        write(self.root / "hooks" / "hooks.json", "{not json")
        errs = V.check_hooks(self.root, {})
        self.assertTrue(any("valid JSON" in e for e in errs), errs)

    def test_matcher_must_cover_every_guarded_tool(self):
        write(self.root / "hooks" / "hooks.json", json.dumps({"hooks": {
            "PreToolUse": [{"matcher": "^(Write|Edit)$", "hooks": []}]}}))
        write(self.root / "hooks" / "ownership-guard.py", "x = 1\n")
        errs = V.check_hooks(self.root, {})
        for tool in ("Edit", "NotebookEdit", "Bash", "WebFetch", "apply_patch", "mcp__"):
            self.assertTrue(any(tool in e for e in errs), (tool, errs))

    def test_edit_hidden_inside_notebookedit_is_detected(self):
        write(self.root / "hooks" / "hooks.json", json.dumps({"hooks": {
            "PreToolUse": [{"matcher":
                "^(Write|NotebookEdit|Bash|WebFetch|mcp__.*)$",
                "hooks": []}]}}))
        write(self.root / "hooks" / "ownership-guard.py", "x = 1\n")
        errs = V.check_hooks(self.root, {})
        self.assertTrue(any("'Edit'" in e for e in errs), errs)

    def test_guard_that_does_not_compile_is_an_error(self):
        write(self.root / "hooks" / "hooks.json", json.dumps({"hooks": {
            "PreToolUse": [{"matcher":
                "^(Write|Edit|NotebookEdit|Bash|WebFetch|mcp__.*)$",
                "hooks": []}]}}))
        write(self.root / "hooks" / "ownership-guard.py", "def broken(:\n")
        errs = V.check_hooks(self.root, {})
        self.assertTrue(any("compile" in e for e in errs), errs)

    def test_real_plugin_is_clean(self):
        real = Path(__file__).resolve().parents[1] / "founder-os"
        self.assertEqual(V.check_hooks(real, {}), [])

    def test_invalid_regex_matcher_is_an_error_not_a_crash(self):
        write(self.root / "hooks" / "hooks.json", json.dumps({"hooks": {
            "PreToolUse": [{"matcher": "([", "hooks": []}]}}))
        write(self.root / "hooks" / "ownership-guard.py", "x = 1\n")
        errs = V.check_hooks(self.root, {})
        self.assertTrue(any("not a valid regex" in e for e in errs), errs)


class TestReadmeCounts(ValidatorTestCase):
    """The README table is a count of a growing set — the exact object the
    package's own philosophy says goes stale silently. Now it fails the build
    instead."""

    README = ("# X\n\n| Content | Count |\n|---|---|\n"
              "| Agents  | %d    |\n| Skills  | %d    |\n")

    def test_matching_counts_are_clean(self):
        # Fixture: 2 agents, 4 skills (3 universals + daily-brief), no
        # setup-cadences so the cadence row is not required.
        write(self.root / "README.md", self.README % (2, 4))
        self.assertEqual(self.check(V.check_readme_counts), [])

    def test_stale_agent_count_is_caught(self):
        write(self.root / "README.md", self.README % (12, 4))
        errs = self.check(V.check_readme_counts)
        self.assertTrue(any("claims 12 agents, the package has 2" in e
                            for e in errs), errs)

    def test_missing_readme_is_not_this_checks_problem(self):
        self.assertEqual(self.check(V.check_readme_counts), [])

    def test_document_count_drift_is_caught(self):
        write(self.root / "README.md", self.README % (2, 4))
        write(self.root / "docs" / "README.md",
              "Founder OS adds 12 agents, 48 workflows, and 9 optional cadences.")
        errs = self.check(V.check_readme_counts)
        self.assertTrue(any("docs/README.md" in err for err in errs), errs)


class TestRealPackage(unittest.TestCase):
    def test_shipped_package_passes_every_check(self):
        """The '13 agents, 49 skills, 0 errors' acceptance line, executable.

        Every other test here validates a synthetic fixture; this is the only
        one that would catch a regression in the package actually shipped.
        """
        real = Path(__file__).resolve().parents[1] / "founder-os"
        agents, errs = V.run_checks(real)
        self.assertEqual(errs, [])
        self.assertEqual(len(agents), 13)
        self.assertEqual(len(list((real / "skills").glob("*/SKILL.md"))), 49)


class TestRunChecksContainment(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        write(self.root / ".claude-plugin" / "plugin.json",
              json.dumps({"name": "founder-os"}))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_malformed_skill_frontmatter_is_a_fail_line_not_a_traceback(self):
        write(self.root / "skills" / "broken" / "SKILL.md",
              "no frontmatter here\n")
        agents, errs = V.run_checks(self.root)
        self.assertTrue(any("frontmatter" in e for e in errs), errs)

    def test_malformed_agent_is_a_fail_line_not_a_traceback(self):
        write(self.root / "agents" / "broken.md", "no frontmatter here\n")
        agents, errs = V.run_checks(self.root)
        self.assertEqual(agents, {})
        self.assertTrue(any("frontmatter" in e for e in errs), errs)

    def test_malformed_ownership_aborts_only_its_check(self):
        write(self.root / "references" / "ownership.yaml", "owns: [unclosed\n")
        agents, errs = V.run_checks(self.root)
        self.assertEqual(agents, {})
        self.assertTrue(any(
            "check 'check_ownership' aborted at first bad file" in err
            for err in errs), errs)
        self.assertTrue(any("hooks.json" in err for err in errs), errs)


if __name__ == "__main__":
    unittest.main()
