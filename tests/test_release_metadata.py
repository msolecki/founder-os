"""Release metadata and reproducible gate contracts for Founder OS."""

import ast
import json
import re
import subprocess
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
ROOT_README_PATH = REPO_ROOT / "README.md"
PLUGIN_README_PATH = REPO_ROOT / "founder-os" / "README.md"
DOCS_README_PATH = REPO_ROOT / "docs" / "README.md"
ARCHITECTURE_PATH = REPO_ROOT / "docs" / "architecture.md"
ENFORCEMENT_PATH = REPO_ROOT / "docs" / "enforcement.md"
GETTING_STARTED_PATH = REPO_ROOT / "docs" / "getting-started.md"
TROUBLESHOOTING_PATH = REPO_ROOT / "docs" / "troubleshooting.md"
COMMANDS_PATH = REPO_ROOT / "docs" / "commands.md"
LANDING_PATH = REPO_ROOT / "docs" / "index.html"
VALIDATOR_PATH = REPO_ROOT / "scripts" / "validate_package.py"
CADENCES_PATH = (
    REPO_ROOT / "founder-os" / "skills" / "setup-cadences" / "SKILL.md"
)
DOCTOR_PATH = (
    REPO_ROOT / "founder-os" / "skills" / "founder-os-doctor" / "SKILL.md"
)
FEATURE_LIST_PATH = REPO_ROOT / "feature_list.json"
RELEASE_VERSION = "2.7.0"
# The most recent published tag, and a record rather than a site: it names an
# entry that already shipped, so a bump moves RELEASE_VERSION above and leaves
# this alone until the release after next freezes a new one.
PUBLISHED_RELEASE = "2.6.0"
PUBLISHED_RELEASE_DATE = "2026-08-01"
ACTIVATION_DESCRIPTION = (
    "Know what matters today with one source-linked daily decision from your "
    "goals, cash, pipeline, and commitments."
)


def _validator_check_count():
    """len(CHECKS) read out of the validator's source, never typed twice."""
    tree = ast.parse(VALIDATOR_PATH.read_text(encoding="utf-8"))
    checks = next(
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "CHECKS"
                for target in node.targets)
    )
    return len(checks.elts)


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
        cls.root_readme = ROOT_README_PATH.read_text(encoding="utf-8")
        cls.plugin_readme = PLUGIN_README_PATH.read_text(encoding="utf-8")
        cls.docs_readme = DOCS_README_PATH.read_text(encoding="utf-8")
        cls.architecture = ARCHITECTURE_PATH.read_text(encoding="utf-8")
        cls.enforcement = ENFORCEMENT_PATH.read_text(encoding="utf-8")
        cls.getting_started = GETTING_STARTED_PATH.read_text(encoding="utf-8")
        cls.troubleshooting = TROUBLESHOOTING_PATH.read_text(encoding="utf-8")
        cls.commands = COMMANDS_PATH.read_text(encoding="utf-8")

    def test_all_release_versions_match_2_6_0(self):
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

    def test_changelog_records_activation_trust_tests_and_host_status(self):
        release_heading = "## 2.5.0 — 2026-07-27"
        self.assertIn(release_heading, self.changelog)
        release = self.changelog.split(release_heading, 1)[1].split(
            "\n## 2.4.0", 1
        )[0]
        for marker in (
            "**Full host parity.**",
            "`founder-os-state`",
            "seven gateway tools",
            "generic-agent fallback",
            "fail closed",
            "**Trust and reliability.**",
            "Trust Center",
            "**Verification.**",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, release)
        self.assertNotIn("Codex remains beta/manual", release)

        historical = self.changelog.split("## 2.4.0 — 2026-07-22", 1)[1]
        self.assertIn("Codex remains beta/manual", historical)

    def test_a_published_release_entry_is_never_rewritten(self):
        """A tagged entry is a record, not a draft.

        This used to assert that the published section carried the *current*
        skill and check counts, so every workflow added after the tag forced
        that released entry to be edited — and it had been, to describe three
        workflows the tag does not contain. A test that pins a shipped section
        to the moving package is the thing certifying the drift it exists to
        prevent.

        Frozen literals here, on purpose. The moving counts belong to
        `## Unreleased`, and the test below is where they are derived.
        """
        release_heading = "## %s — %s" % (
            PUBLISHED_RELEASE, PUBLISHED_RELEASE_DATE
        )
        self.assertIn(release_heading, self.changelog)
        release = self.changelog.split(release_heading, 1)[1].split(
            "\n## 2.5.0", 1
        )[0]
        for marker in (
            "decision-first",
            "activation intent",
            "workflow receipt",
            "/capture",
            "53 workflows",
            "Continue",
            "17 build-time checks",
        ):
            with self.subTest(marker=marker):
                self.assertRegex(release, rf"(?i){re.escape(marker)}")

    def test_the_topmost_written_entry_carries_the_counts_we_ship_now(self):
        """Whichever section currently describes the package must match it.

        Mid-development that is `## Unreleased`; on the day of a release
        `bump_version.py` renames that heading and opens an empty one, so the
        section describing what ships is the release just cut. Following the
        topmost *written* section means this holds on both sides of a bump
        without anyone editing the assertion — and, unlike the version of this
        test it replaces, it never asks a section that already shipped to carry
        a count the package moved past.
        """
        sections = re.split(r"^## ", self.changelog, flags=re.M)[1:]
        current = next(
            body for body in sections
            if body.split("\n", 1)[1].strip()
        )
        for marker in (
            "%d workflows" % len(list(
                (REPO_ROOT / "founder-os" / "skills").glob("*/SKILL.md")
            )),
            "%d build-time checks" % _validator_check_count(),
        ):
            with self.subTest(marker=marker, section=current.split("\n", 1)[0]):
                self.assertRegex(current, rf"(?i){re.escape(marker)}")

    def test_source_derived_counts_are_published_without_drift(self):
        agent_count = len(list((REPO_ROOT / "founder-os" / "agents").glob("*.md")))
        skill_count = len(list((REPO_ROOT / "founder-os" / "skills").glob("*/SKILL.md")))

        cadence_source = CADENCES_PATH.read_text(encoding="utf-8")
        cadence_count = len(re.findall(
            r"^\|\s*`/[a-z0-9-]+`\s*\|[^|]*\|\s*`[^`]+`\s*\|\s*$",
            cadence_source,
            re.MULTILINE,
        ))

        validator_count = _validator_check_count()

        doctor_source = DOCTOR_PATH.read_text(encoding="utf-8")
        doctor_table = doctor_source.split("## The checks", 1)[1].split(
            "\n## Steps", 1
        )[0]
        doctor_count = len(re.findall(r"^\| \*\*[^|]+\*\* \|", doctor_table, re.M))

        counts = {
            "agents": agent_count,
            "skills": skill_count,
            "cadences": cadence_count,
            "validator": validator_count,
            "doctor": doctor_count,
        }
        self.assertEqual(counts, {
            "agents": 13,
            "skills": 56,
            "cadences": 11,
            "validator": 20,
            "doctor": 20,
        })

        expected_markers = {
            "README.md": (
                f"{agent_count} agents, {skill_count} skills, "
                f"{cadence_count} scheduled cadences",
                f"{validator_count} build-time checks",
                f"founder-os-doctor`: {doctor_count} checks",
            ),
            "founder-os/README.md": (
                f"| Agents | {agent_count} |",
                f"| Skills | {skill_count} |",
                f"| Cadences | {cadence_count} |",
            ),
            "docs/README.md": (
                f"{agent_count} agents, {skill_count} skills, "
                f"{cadence_count} optional cadences",
            ),
            "docs/development.md": (f"{validator_count} build-time checks",),
            "docs/troubleshooting.md": (f"{doctor_count} health checks",),
            "docs/commands.md": (
                f"{skill_count} workflows",
                f"## The {cadence_count} cadences",
            ),
        }
        documents = {
            "README.md": self.root_readme,
            "founder-os/README.md": self.plugin_readme,
            "docs/README.md": self.docs_readme,
            "docs/development.md": self.development,
            "docs/troubleshooting.md": self.troubleshooting,
            "docs/commands.md": self.commands,
        }
        for name, markers in expected_markers.items():
            normalized = " ".join(documents[name].split())
            for marker in markers:
                with self.subTest(document=name, marker=marker):
                    self.assertIn(marker, normalized)

    def test_current_docs_describe_gateway_siblings_and_portable_fallback(self):
        required = {
            "README.md": ("`founder-os-state`", "role capability", "sibling"),
            "founder-os/README.md": (
                "`founder-os-state`", "role capability", "generic-agent fallback",
            ),
            "docs/architecture.md": (
                "eight-tool", "fail closed", "generic-agent fallback",
            ),
            "docs/enforcement.md": (
                "authoritative write boundary", "fail closed", "defense in depth",
            ),
            "docs/getting-started.md": (
                "codex plugin marketplace add msolecki/founder-os",
                "codex plugin add founder-os@founder-os",
            ),
        }
        documents = {
            "README.md": self.root_readme,
            "founder-os/README.md": self.plugin_readme,
            "docs/architecture.md": self.architecture,
            "docs/enforcement.md": self.enforcement,
            "docs/getting-started.md": self.getting_started,
        }
        for name, markers in required.items():
            normalized = documents[name].lower()
            for marker in markers:
                with self.subTest(document=name, marker=marker):
                    self.assertIn(marker.lower(), normalized)

        active_docs = "\n".join(documents.values())
        for stale in (
            "13 agents, 50 skills",
            "Agent(...) edges for managers",
            "Managers can summon",
            "it can summon the rest",
            "Every unknown **fails open**",
            "Current: **2.3.0**",
        ):
            with self.subTest(stale=stale):
                self.assertNotIn(stale.lower(), active_docs.lower())

    def test_active_public_docs_have_no_superseded_release_contract(self):
        active_paths = (
            ROOT_README_PATH,
            PLUGIN_README_PATH,
            DOCS_README_PATH,
            ARCHITECTURE_PATH,
            ENFORCEMENT_PATH,
            GETTING_STARTED_PATH,
            TROUBLESHOOTING_PATH,
            COMMANDS_PATH,
            LANDING_PATH,
        )
        active = "\n".join(
            path.read_text(encoding="utf-8") for path in active_paths
        ).lower()
        for stale in (
            "49 workflows",
            "50 workflows",
            "all 50 commands",
            "current: **2.4.0**",
            "current: **2.3.0**",
            "codex remains beta/manual",
            "seven-tool state gateway",
            "managers can summon",
            "it can summon the rest",
            "pyyaml recommended",
            "python runs the ownership hook",
        ):
            with self.subTest(stale=stale):
                self.assertNotIn(stale, active)

    def test_internal_planning_artifacts_are_ignored_and_not_shipped(self):
        ignored = subprocess.run(
            [
                "git",
                "check-ignore",
                "--quiet",
                "docs/superpowers/plans/example.md",
            ],
            cwd=REPO_ROOT,
            check=False,
        )
        self.assertEqual(ignored.returncode, 0)
        # `docs/` is published from tracked files, so "not shipped" means "not
        # tracked" — not "not on disk". An active plan lives at
        # `docs/superpowers/plans/` while the work is open; asserting the
        # directory is absent failed on any machine mid-task and never checked
        # trackedness at all, which is the property that actually ships.
        tracked = subprocess.run(
            ["git", "ls-files", "--", "docs/superpowers"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(tracked.stdout.strip(), "")

        # `docs/superpowers/` is the only sanctioned home for a plan or design,
        # and being gitignored is what keeps it internal. A planning artifact
        # written anywhere else under `docs/` is tracked by default and ships
        # to the public site — which is how three of them reached `docs/design/`
        # and had to be deleted one release later. Pin the shape, not one path.
        published = subprocess.run(
            ["git", "ls-files", "--", "docs"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
        internal = sorted(
            name
            for name in published
            if re.search(r"/(design|plans|specs|brainstorm)/", name)
            or re.search(r"/\d{4}-\d{2}-\d{2}-", name)
        )
        self.assertEqual(
            internal,
            [],
            "internal planning artifacts are tracked under docs/ and would be "
            "published: %s — move them to docs/superpowers/" % internal,
        )

    def test_codex_manifest_names_the_real_gateway_and_trust_boundary(self):
        self.assertEqual(
            set(self.codex_manifest["mcpServers"]),
            {"founder-os-state"},
        )
        self.assertEqual(
            self.codex_manifest["interface"]["privacyPolicyURL"],
            "https://msolecki.github.io/founder-os/trust.html",
        )
        capabilities = self.codex_manifest["interface"]["capabilities"]
        self.assertIn("Local state gateway", capabilities)
        self.assertIn("Role-owned Markdown writes", capabilities)

    def test_feature_ledger_uses_the_current_workflow_count(self):
        """Derived, not copied — the ledger row quotes the catalogue summary.

        It read `Browse all 53 workflows` while the package shipped 56, which
        is the drift this test was named after and was not catching.
        """
        skills = len(list(
            (REPO_ROOT / "founder-os" / "skills").glob("*/SKILL.md")
        ))
        ledger = json.loads(FEATURE_LIST_PATH.read_text(encoding="utf-8"))
        focus_ring = next(
            feature for feature in ledger["features"]
            if "[A11Y-004]" in feature["description"]
        )
        self.assertIn(
            "Browse all %d workflows" % skills, focus_ring["description"]
        )

    def test_internal_launch_working_material_is_not_shipped(self):
        product_hunt = REPO_ROOT / "docs" / "product-hunt"
        self.assertFalse(
            product_hunt.exists(),
            "internal launch material is shipped: docs/product-hunt",
        )

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
