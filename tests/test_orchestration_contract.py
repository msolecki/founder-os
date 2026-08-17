"""Portable one-level orchestration contracts for every Founder OS role."""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "founder-os"
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import validate_package as package_validator


ROLE_NAMES = {
    "board-member",
    "brand-editor",
    "cfo",
    "chief-of-staff",
    "delivery-lead",
    "focus-coach",
    "network-manager",
    "ops-engineer",
    "pipeline-coach",
    "portfolio-manager",
    "positioning-advisor",
    "skills-mentor",
    "strategist",
}
ROLE_TOOLS = {
    "mcp__plugin_founder-os_founder-os-state__resolve_workspace",
    "mcp__plugin_founder-os_founder-os-state__list_state",
    "mcp__plugin_founder-os_founder-os-state__read_state",
    "mcp__plugin_founder-os_founder-os-state__read_reference",
    "mcp__plugin_founder-os_founder-os-state__write_owned_state",
    "mcp__plugin_founder-os_founder-os-state__close_role_session",
}
PORTFOLIO_READ_TOOL = (
    "mcp__plugin_founder-os_founder-os-state__read_portfolio_inputs"
)
MANAGERS = {
    "chief-of-staff",
    "delivery-lead",
    "focus-coach",
    "positioning-advisor",
}
DELEGATION_FIELDS = {
    "role",
    "workflow",
    "workspace_id",
    "correlation_id",
    "handoff",
    "expected_persistence",
}
WORKFLOW_RESULT_FIELDS = {
    "decision",
    "evidence",
    "gaps",
    "return_point",
    "human_action",
    "expected_persistence",
}


class TestPackagedSiblingContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agents = package_validator.load_agents(PLUGIN_ROOT)

    def test_all_thirteen_roles_have_only_their_gateway_tools(self):
        self.assertEqual(set(self.agents), ROLE_NAMES)
        for slug, (frontmatter, _) in self.agents.items():
            with self.subTest(role=slug):
                expected = set(ROLE_TOOLS)
                if slug == "portfolio-manager":
                    expected.add(PORTFOLIO_READ_TOOL)
                self.assertEqual(
                    set(package_validator._tool_names(frontmatter["tools"])),
                    expected,
                )

    def test_every_role_carries_the_shared_state_and_handoff_contract(self):
        required = (
            "## State and handoff contract",
            "main thread",
            "capability",
            "only state you own",
            "never spawn or invoke another role",
            "expected_persistence",
        )
        for slug, (_, body) in self.agents.items():
            with self.subTest(role=slug):
                for phrase in required:
                    self.assertIn(phrase, body)
                self.assertIn("workflow result", body.lower())
                for field in WORKFLOW_RESULT_FIELDS:
                    self.assertIn("`%s`" % field, body)
                self.assertNotIn("Agent(", body)

    def test_managers_return_the_exact_delegation_request_shape(self):
        for slug in MANAGERS:
            body = self.agents[slug][1]
            section = body.split("## Delegation request", 1)[-1]
            self.assertNotEqual(section, body, slug)
            for field in DELEGATION_FIELDS:
                with self.subTest(role=slug, field=field):
                    self.assertIn("`%s`" % field, section)
            self.assertIn("return", section.lower())
            self.assertIn("main thread", section.lower())
            self.assertIn("do not execute", section.lower())

    def test_reference_defines_one_main_thread_and_one_persistence_gate(self):
        reference = (
            PLUGIN_ROOT / "references" / "orchestration.md"
        ).read_text(encoding="utf-8")
        for heading in (
            "## Main-thread protocol",
            "## Role execution envelope",
            "## Delegation request",
            "## Native and generic parity",
            "## Persistence gate",
        ):
            self.assertIn(heading, reference)
        self.assertIn("agents/{role}.md", reference)
        self.assertIn("byte-identical", reference)
        self.assertIn("named native role", reference)
        self.assertIn("otherwise", reference)
        self.assertIn("generic", reference)
        self.assertIn("re-read", reference)
        self.assertIn("before", reference)
        self.assertIn("close", reference)

    def test_reference_separates_results_from_delegation_and_gates_receipts(self):
        reference = (
            PLUGIN_ROOT / "references" / "orchestration.md"
        ).read_text(encoding="utf-8")
        for heading in (
            "## Workflow result",
            "## User-facing receipt",
            "## Freshness vocabulary",
            "## First-week guidance",
            "## Error experience",
        ):
            self.assertIn(heading, reference)
        result_section = reference.split("## Workflow result", 1)[1].split(
            "\n## ", 1
        )[0]
        for field in WORKFLOW_RESULT_FIELDS:
            self.assertIn("`%s`" % field, result_section)
        self.assertRegex(
            result_section,
            r"(?is)separate from.*delegation request",
        )

        receipt = reference.split("## User-facing receipt", 1)[1].split(
            "\n## ", 1
        )[0]
        labels = (
            "Decision:",
            "Evidence:",
            "Changed:",
            "Gaps:",
            "Returns:",
            "Your move:",
        )
        positions = [receipt.index(label) for label in labels]
        self.assertEqual(positions, sorted(positions))
        self.assertRegex(receipt, r"(?is)read-only.*Changed.*none")
        self.assertRegex(
            receipt, r"(?is)Changed.*re-read.*verified|re-read.*Changed"
        )
        self.assertRegex(
            receipt,
            r"(?is)(?:failed|uncertain) persistence.*error receipt.*never.*success",
        )
        self.assertRegex(receipt, r"(?is)creates no workspace file")

    def test_reference_uses_only_threshold_backed_freshness_states(self):
        reference = (
            PLUGIN_ROOT / "references" / "orchestration.md"
        ).read_text(encoding="utf-8")
        section = reference.split("## Freshness vocabulary", 1)[1].split(
            "\n## ", 1
        )[0]
        for state in ("`current`", "`stale`", "`unknown`"):
            self.assertIn(state, section)
        self.assertRegex(section, r"(?is)current.*threshold.*inside")
        self.assertRegex(section, r"(?is)stale.*threshold.*crossed")
        self.assertRegex(section, r"(?is)unknown.*absent")
        self.assertRegex(
            section, r"(?is)no threshold.*source date.*without.*state"
        )
        self.assertRegex(section, r"(?is)do not invent.*global freshness")
        self.assertRegex(section, r"(?is)no.*confidence\s+percentage")

    def test_reference_maps_all_gateway_errors_to_five_fact_recovery(self):
        reference = (
            PLUGIN_ROOT / "references" / "orchestration.md"
        ).read_text(encoding="utf-8")
        section = reference.split("## Error experience", 1)[1].split(
            "\n## ", 1
        )[0]
        for fact in (
            "whether any write occurred",
            "whether the original file is preserved",
            "canonical owner or unresolved context",
            "what the system will do next",
            "whether the founder must act",
        ):
            self.assertRegex(section, re.escape(fact).replace(r"\ ", r"\s+"))
        expected = {
            "WORKSPACE_UNRESOLVED": "which business is active",
            "ROLE_SESSION_INVALID": "return control to the main thread",
            "PATH_OUTSIDE_WORKSPACE": "workspace boundary",
            "ROLE_NOT_OWNER": "canonical owner",
            "INVALID_DOCUMENT_STRUCTURE": "structural mismatch",
            "STALE_WRITE": "retry once",
            "STATE_IO_ERROR": "concrete recovery step",
        }
        for code, action in expected.items():
            row = next(
                line for line in section.splitlines() if "`%s`" % code in line
            )
            with self.subTest(code=code):
                self.assertRegex(
                    row, re.escape(action).replace(r"\ ", r"\s+")
                )
        self.assertRegex(
            section,
            r"(?is)first line.*user impact.*no.*failed write.*persisted",
        )

    def test_first_week_guidance_selects_one_action_in_priority_order(self):
        reference = (
            PLUGIN_ROOT / "references" / "orchestration.md"
        ).read_text(encoding="utf-8")
        section = reference.split("## First-week guidance", 1)[1].split(
            "\n## ", 1
        )[0]
        ordered = (
            "founder-os-init",
            "/capture",
            "/pipeline-review",
            "/weekly-review",
            "none",
        )
        positions = [section.index(value) for value in ordered]
        self.assertEqual(positions, sorted(positions))
        self.assertRegex(section, r"(?is)Your move.*exactly one")
        self.assertRegex(section, r"(?is)creates no progress file")

    def test_house_rules_forbid_every_nested_role_edge(self):
        house_rules = (
            PLUGIN_ROOT / "references" / "house-rules.md"
        ).read_text(encoding="utf-8")
        self.assertIn("No role spawns or invokes another role", house_rules)
        self.assertIn("main thread", house_rules)
        self.assertIn("delegation request", house_rules)
        self.assertNotIn("Agent(...)` allowlist", house_rules)


class TestExecutableOrchestrationEnvelope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agents = package_validator.load_agents(PLUGIN_ROOT)

    def _valid_request(self):
        return {
            "role": "cfo",
            "workflow": "revenue-review",
            "workspace_id": "workspace-1",
            "correlation_id": "corr-1",
            "handoff": "Close July from the dated metrics already in state.",
            "expected_persistence": ["metrics.md"],
        }

    def _valid_envelope(self):
        role_path = PLUGIN_ROOT / "agents" / "cfo.md"
        return {
            "role": "cfo",
            "role_file": "agents/cfo.md",
            "role_instructions": role_path.read_bytes(),
            "workflow": "revenue-review",
            "handoff": "Close July from current state.",
            "capability": "opaque-role-capability",
        }

    def test_valid_delegation_request_is_accepted(self):
        self.assertEqual(
            package_validator.delegation_request_errors(
                PLUGIN_ROOT,
                self.agents,
                self._valid_request(),
                "workspace-1",
                "corr-1",
            ),
            [],
        )

    def test_malformed_delegation_request_mutations_are_rejected(self):
        mutations = {
            "missing field": lambda request: request.pop("handoff"),
            "extra field": lambda request: request.update(extra=True),
            "unknown role": lambda request: request.update(role="ghost"),
            "role container": lambda request: request.update(role=[]),
            "wrong workflow": lambda request: request.update(workflow="daily-brief"),
            "workflow container": lambda request: request.update(workflow=[]),
            "system workflow": lambda request: request.update(workflow="guardrails"),
            "blank workspace": lambda request: request.update(workspace_id=""),
            "wrong workspace": lambda request: request.update(
                workspace_id="workspace-2"
            ),
            "wrong correlation": lambda request: request.update(
                correlation_id="corr-2"
            ),
            "oversized handoff": lambda request: request.update(handoff="x" * 4097),
            "unsafe path": lambda request: request.update(
                expected_persistence=["../metrics.md"]
            ),
            "wrong owner": lambda request: request.update(
                expected_persistence=["goals.md"]
            ),
            "file used as directory": lambda request: request.update(
                expected_persistence=["metrics.md/child.md"]
            ),
            "writing workflow without checkpoint": lambda request: request.update(
                expected_persistence=[]
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                request = self._valid_request()
                mutate(request)
                self.assertTrue(
                    package_validator.delegation_request_errors(
                        PLUGIN_ROOT,
                        self.agents,
                        request,
                        "workspace-1",
                        "corr-1",
                    )
                )

    def test_read_only_workflow_may_return_no_persistence_paths(self):
        request = self._valid_request()
        request.update(
            role="board-member",
            workflow="assumption-audit",
            expected_persistence=[],
        )
        self.assertEqual(
            package_validator.delegation_request_errors(
                PLUGIN_ROOT, self.agents, request, "workspace-1", "corr-1"
            ),
            [],
        )

    def test_falsey_malformed_writes_are_not_read_only(self):
        for value in ("{}", "0", "''", "null"):
            with self.subTest(writes=value), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                skill = root / "skills" / "revenue-review" / "SKILL.md"
                skill.parent.mkdir(parents=True)
                skill.write_text(
                    "---\nname: revenue-review\nmetadata:\n  writes: %s\n---\n"
                    % value,
                    encoding="utf-8",
                )
                self.assertIsNone(
                    package_validator._workflow_writes(root, "revenue-review")
                )

    def test_null_metadata_is_not_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "skills" / "revenue-review" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text(
                "---\nname: revenue-review\nmetadata: null\n---\n",
                encoding="utf-8",
            )
            self.assertIsNone(
                package_validator._workflow_writes(root, "revenue-review")
            )

    def test_native_and_generic_envelopes_use_identical_role_bytes(self):
        native = self._valid_envelope()
        fallback = dict(native)
        self.assertEqual(
            package_validator.execution_envelope_errors(
                PLUGIN_ROOT,
                self.agents,
                native,
                fallback,
            ),
            [],
        )

        fallback["role_instructions"] += b"\nGeneric rewrite.\n"
        errors = package_validator.execution_envelope_errors(
            PLUGIN_ROOT,
            self.agents,
            native,
            fallback,
        )
        self.assertTrue(any("byte-identical" in error for error in errors), errors)

    def test_execution_envelope_rejects_an_unbounded_handoff(self):
        native = self._valid_envelope()
        native["handoff"] = "x" * 4097
        fallback = dict(native)
        self.assertTrue(
            package_validator.execution_envelope_errors(
                PLUGIN_ROOT,
                self.agents,
                native,
                fallback,
            )
        )

    def test_execution_envelope_contains_invalid_roles_and_paths(self):
        native = self._valid_envelope()
        native["role"] = []
        fallback = dict(native)
        self.assertTrue(
            package_validator.execution_envelope_errors(
                PLUGIN_ROOT, self.agents, native, fallback
            )
        )

        native = self._valid_envelope()
        native["role_file"] = "../README.md"
        fallback = dict(native)
        errors = package_validator.execution_envelope_errors(
            PLUGIN_ROOT, self.agents, native, fallback
        )
        self.assertTrue(errors)
        self.assertFalse(
            any("byte-identical to ../README.md" in error for error in errors),
            errors,
        )


class TestMigratedWorkflowHandoffs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bodies = {
            slug: package_validator.parse_frontmatter(
                PLUGIN_ROOT / "skills" / slug / "SKILL.md"
            )[1]
            for slug in (
                "founder-os-init",
                "strategic-evaluation",
                "situation-review",
                "kill-or-continue",
            )
        }

    def test_every_migrated_workflow_uses_the_shared_request_shape(self):
        for slug, body in self.bodies.items():
            with self.subTest(workflow=slug):
                for field in DELEGATION_FIELDS:
                    self.assertIn("`%s`" % field, body)
                for phrase in (
                    "main thread",
                    "one bounded handoff",
                    "4096 UTF-8 bytes",
                    "unchanged",
                ):
                    self.assertRegex(
                        body, re.escape(phrase).replace(r"\ ", r"\s+")
                    )

    def test_migrated_workflows_have_no_legacy_nested_edge(self):
        for slug, body in self.bodies.items():
            with self.subTest(workflow=slug):
                self.assertNotIn("Agent(", body)
                self.assertNotRegex(body, r"(?i)owner allowlist")
                self.assertNotRegex(body, r"(?i)\bsummon\b")

    def test_situation_review_keeps_internal_shape_but_previews_one_route(self):
        body = self.bodies["situation-review"]
        request = body.split("## Output", 1)[1].split("\n## ", 1)[0]
        self.assertEqual(
            set(re.findall(r"(?m)^- `([^`]+)`:", request)),
            DELEGATION_FIELDS,
        )
        preview = body.split("## User-facing preview", 1)[1].split(
            "\n## ", 1
        )[0]
        for token in (
            "decision sentence",
            "selected owner",
            "reason",
            "missing state",
            "expected state destination",
            "Continue",
            "Stop",
        ):
            self.assertRegex(
                preview, re.escape(token).replace(r"\ ", r"\s+")
            )
        self.assertRegex(
            preview,
            r"(?is)only after.*Continue.*main thread.*"
            r"(?:open|opens|execute|executes).*target",
        )
        self.assertRegex(preview, r"(?is)routing role.*does not answer")


if __name__ == "__main__":
    unittest.main()
