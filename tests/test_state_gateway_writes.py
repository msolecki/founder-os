import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import stat
import tempfile
import textwrap
import threading
import unittest
from unittest import mock


PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "founder-os"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from mcp.gateway import Gateway
from mcp.ownership import OwnershipSchema
from mcp.safe_io import SafeStateIO
from mcp.sessions import JournalError, RoleSessionStore
from mcp.workspaces import WorkspaceResolver


ROLES = (
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
)

ROLE_WORKFLOWS = {
    "board-member": "red-team",
    "brand-editor": "content-plan",
    "cfo": "revenue-review",
    "chief-of-staff": "daily-brief",
    "delivery-lead": "capacity-check",
    "focus-coach": "week-plan",
    "network-manager": "follow-up-sweep",
    "ops-engineer": "automation-audit",
    "pipeline-coach": "pipeline-review",
    "portfolio-manager": "portfolio-review",
    "positioning-advisor": "offer-design",
    "skills-mentor": "skill-gap",
    "strategist": "quarterly-planning",
}


def _ownership_yaml():
    return textwrap.dedent(
        """\
        workspace_files:
          - charter.md
          - inbox.md
          - queue.md
          - decisions/
          - evaluations/
          - reviews/daily/
          - reviews/weekly/
          - reviews/monthly/
          - goals.md
          - reviews/quarterly/
          - metrics.md
          - offer.md
          - pipeline.md
          - drafts/outreach/
          - drafts/proposals/
          - week.md
          - clients/
          - network.md
          - skills.md
          - content.md
          - voice.md
          - drafts/content/
          - systems.md
        portfolio_files:
          - portfolio.md
        owns:
          portfolio-manager:
            - portfolio.md
          chief-of-staff:
            - charter.md
            - inbox.md
            - queue.md
            - decisions/
            - evaluations/
            - reviews/daily/
            - reviews/weekly/
            - reviews/monthly/
          strategist:
            - goals.md
            - reviews/quarterly/
          cfo:
            - metrics.md
          positioning-advisor:
            - offer.md
          pipeline-coach:
            - pipeline.md
            - drafts/outreach/
            - drafts/proposals/
          focus-coach:
            - week.md
          delivery-lead:
            - clients/
          network-manager:
            - network.md
          skills-mentor:
            - skills.md
          brand-editor:
            - content.md
            - voice.md
            - drafts/content/
          ops-engineer:
            - systems.md
        sections:
          portfolio.md:
            - "## Businesses"
            - "## Allocation"
            - "## Starving"
            - "## Review"
          inbox.md:
            - "## Inbox"
          charter.md:
            - "## Business"
            - "## North star"
            - "## Timezone"
          goals.md:
            - "## Bets"
          metrics.md:
            - "## Close"
            - "## Runway"
            - "## Profitability"
            - "## Rate"
          offer.md:
            - "## ICP"
            - "## Offer"
            - "## Pricing"
          pipeline.md:
            - "## Live"
            - "## Won"
            - "## Dead"
            - "## Win/loss"
            - "## Last review"
          queue.md:
            - "## Doing"
            - "## Queued"
            - "## Blocked"
            - "## Done"
            - "## Dropped"
          week.md:
            - "## Arithmetic"
            - "## Shape"
            - "## Blocks"
            - "## Unfunded"
            - "## The trade"
            - "## Audit"
            - "## Ledger"
          network.md:
            - "## Map"
            - "## Not in the map"
            - "## Sweep"
          skills.md:
            - "## Gap"
            - "## Hypotheses"
            - "## Learning plan"
          content.md:
            - "## Plan"
            - "## Shipped"
            - "## Drafts"
            - "## Audience"
          voice.md:
            - "## Samples"
            - "## Tells"
            - "## Never"
            - "## Register"
          systems.md:
            - "## Stack"
            - "## Automation decisions"
          clients/:
            - "## Scope"
            - "## Health"
            - "## Retro"
          drafts/outreach/:
            - "## Draft"
            - "## Provenance"
            - "## Sent"
          drafts/proposals/:
            - "## Draft"
            - "## Provenance"
            - "## Sent"
          drafts/content/:
            - "## Draft"
            - "## Provenance"
            - "## Sent"
          decisions/:
            - "## Context"
            - "## Rejected"
            - "## What would change our mind"
            - "## Supersedes"
          evaluations/:
            - "## Decision"
            - "## Scope"
            - "## Observations"
            - "## Interpretations"
            - "## Options"
            - "## Recommendation"
            - "## Challenge"
            - "## Open questions"
            - "## Evidence appendix"
          reviews/daily/:
            - "## The one thing"
            - "## Rotting"
            - "## The trade"
            - "## Triage"
          reviews/weekly/:
            - "## Committed vs done"
            - "## Days per bet"
            - "## The pattern"
            - "## Next week"
          reviews/monthly/:
            - "## What the month says we do"
            - "## vs the charter"
            - "## Bets"
            - "## Decisions"
            - "## Last month's correction"
            - "## The correction"
          reviews/quarterly/:
            - "## Last quarter's verdicts"
            - "## Never measured"
            - "## This quarter's bets"
            - "## What we are not doing"
            - "## Verdicts"
            - "## Scorecard"
            - "## Bad call, good outcome"
            - "## Falsifiers that fired and were ignored"
            - "## Blind months"
            - "## Rules for next year"
        """
    )


def _minimal_ownership_yaml():
    return textwrap.dedent(
        """\
        workspace_files:
          - metrics.md
        portfolio_files:
          - portfolio.md
        owns:
          cfo:
            - metrics.md
          portfolio-manager:
            - portfolio.md
        sections:
          metrics.md:
            - "## Close"
          portfolio.md:
            - "## Businesses"
        """
    )


def _metrics(close="Booked: 10", suffix=""):
    return (
        "# Metrics\n\n"
        "## Close{0}\n\n{1}\n\n"
        "## Runway{0}\n\nSix months.\n\n"
        "## Profitability{0}\n\nPositive.\n\n"
        "## Rate{0}\n\n100/hour.\n"
    ).format(suffix, close)


class OwnershipSchemaTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def _load(self, contents=None):
        path = self.root / "ownership.yaml"
        path.write_text(
            _ownership_yaml() if contents is None else contents,
            encoding="utf-8",
        )
        return OwnershipSchema.load(path)

    def test_load_rejects_unknown_or_missing_top_level_keys_and_wrong_types(self):
        valid = _minimal_ownership_yaml()
        invalid_documents = {
            "unknown top-level key": valid + "surprise:\n  - value\n",
            "missing workspace_files": valid.replace(
                "workspace_files:\n", "not_workspace_files:\n", 1
            ),
            "workspace_files is not a sequence": valid.replace(
                "workspace_files:\n  - metrics.md",
                "workspace_files: metrics.md",
                1,
            ),
            "portfolio_files contains an empty string": valid.replace(
                "  - portfolio.md", '  - ""', 1
            ),
            "missing owns": valid.replace("owns:\n", "not_owns:\n", 1),
            "owns is not a mapping": valid.replace(
                "owns:\n  cfo:", "owns: cfo\nnot_owns:", 1
            ),
            "missing sections": valid.replace(
                "sections:\n", "not_sections:\n", 1
            ),
            "sections is not a mapping": valid.replace(
                "sections:\n  metrics.md:",
                "sections: metrics.md\nnot_sections:",
                1,
            ),
        }

        for mutation, document in invalid_documents.items():
            with self.subTest(mutation=mutation):
                with self.assertRaises(Exception):
                    self._load(document)

    def test_load_rejects_unknown_roles_and_malformed_owns_and_sections(self):
        valid = _minimal_ownership_yaml()
        invalid_documents = {
            "unknown owner role": valid.replace("  cfo:", "  mystery-role:", 1),
            "owner paths are not a sequence": valid.replace(
                "  cfo:\n    - metrics.md", "  cfo: metrics.md", 1
            ),
            "owner path is empty": valid.replace(
                "    - metrics.md", '    - ""', 1
            ),
            "section headings are not a sequence": valid.replace(
                '  metrics.md:\n    - "## Close"',
                "  metrics.md: Close",
                1,
            ),
            "section heading is empty": valid.replace(
                '    - "## Close"', '    - ""', 1
            ),
            "owned path is absent from file collections": valid.replace(
                "  - metrics.md", "  - goals.md", 1
            ),
            "owned path has no section schema": valid.replace(
                '  metrics.md:\n    - "## Close"\n', "", 1
            ),
        }

        for mutation, document in invalid_documents.items():
            with self.subTest(mutation=mutation):
                with self.assertRaises(Exception):
                    self._load(document)

    def test_resolves_every_exact_file_and_directory_member_owner(self):
        schema = self._load()
        expected = {
            "portfolio.md": "portfolio-manager",
            "charter.md": "chief-of-staff",
            "inbox.md": "chief-of-staff",
            "queue.md": "chief-of-staff",
            "decisions/2026-07-27.md": "chief-of-staff",
            "evaluations/bet.md": "chief-of-staff",
            "reviews/daily/2026-07-27.md": "chief-of-staff",
            "reviews/weekly/2026-W31.md": "chief-of-staff",
            "reviews/monthly/2026-07.md": "chief-of-staff",
            "goals.md": "strategist",
            "reviews/quarterly/2026-Q3.md": "strategist",
            "metrics.md": "cfo",
            "offer.md": "positioning-advisor",
            "pipeline.md": "pipeline-coach",
            "drafts/outreach/acme.md": "pipeline-coach",
            "drafts/proposals/acme.md": "pipeline-coach",
            "week.md": "focus-coach",
            "clients/acme.md": "delivery-lead",
            "network.md": "network-manager",
            "skills.md": "skills-mentor",
            "content.md": "brand-editor",
            "voice.md": "brand-editor",
            "drafts/content/launch.md": "brand-editor",
            "systems.md": "ops-engineer",
        }

        for relative_path, expected_owner in expected.items():
            with self.subTest(path=relative_path):
                self.assertEqual(expected_owner, schema.owner_for(relative_path))

        self.assertIsNone(schema.owner_for("README.md"))
        self.assertIsNone(schema.owner_for("client-notes.md"))

    def test_directory_matching_uses_longest_prefix_for_owner_and_sections(self):
        document = _ownership_yaml()
        document = document.replace(
            "  - clients/\n  - network.md",
            "  - clients/\n  - clients/vip/\n  - network.md",
            1,
        )
        document = document.replace(
            "  cfo:\n    - metrics.md",
            "  cfo:\n    - metrics.md\n    - clients/vip/",
            1,
        )
        document += '  clients/vip/:\n    - "## Private"\n'
        schema = self._load(document)

        self.assertEqual("delivery-lead", schema.owner_for("clients/acme.md"))
        self.assertEqual("cfo", schema.owner_for("clients/vip/acme.md"))
        self.assertEqual(
            ["## Private"],
            list(schema.sections_for("clients/vip/acme.md")),
        )
        self.assertEqual(
            ["## Scope", "## Health", "## Retro"],
            list(schema.sections_for("clients/acme.md")),
        )


class StateGatewayWriteTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.package = self.base / "package"
        self.data_root = self.base / "plugin-data"
        self.home = self.base / "home"
        self.clock_value = 1_700_000_000.25

        for role in ROLES:
            agent = self.package / "agents" / (role + ".md")
            agent.parent.mkdir(parents=True, exist_ok=True)
            workflow = ROLE_WORKFLOWS[role]
            agent.write_text(
                "---\nname: " + role + "\nskills:\n  - " + workflow
                + "\n---\n# " + role + "\n",
                encoding="utf-8",
            )
            skill = self.package / "skills" / workflow / "SKILL.md"
            skill.parent.mkdir(parents=True, exist_ok=True)
            skill.write_text("# " + workflow + "\n", encoding="utf-8")
        ownership = self.package / "references" / "ownership.yaml"
        ownership.parent.mkdir(parents=True, exist_ok=True)
        ownership.write_text(_ownership_yaml(), encoding="utf-8")

        self.resolver = WorkspaceResolver(env={}, home=self.home)
        self.sessions = RoleSessionStore(
            data_root=self.data_root,
            packaged_root=self.package,
            clock=lambda: self.clock_value,
            ttl_seconds=300,
        )
        self.gateway = Gateway(
            resolver=self.resolver,
            sessions=self.sessions,
            packaged_root=self.package,
        )
        self.binding, self.workspace = self._new_workspace("primary")

    def _new_workspace(self, label):
        project = self.base / "projects" / label
        workspace = project / "founder-os"
        workspace.mkdir(parents=True, exist_ok=True)
        return self.resolver.resolve(project), workspace

    def _call(self, name, arguments):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            response = self.gateway.call(name, arguments)
        self.assertEqual(
            "",
            stdout.getvalue(),
            "MCP gateway calls must not emit journal or document text to stdout",
        )
        self.assertEqual(
            response["structuredContent"],
            json.loads(response["content"][0]["text"]),
        )
        return response

    def _open(self, role, binding=None, correlation_id=None):
        binding = self.binding if binding is None else binding
        response = self._call(
            "open_role_session",
            {
                "workspace_id": binding.workspace_id,
                "role": role,
                "correlation_id": correlation_id or "corr-" + role,
                "workflow": ROLE_WORKFLOWS[role],
            },
        )
        self.assertFalse(response["isError"], response)
        self.assertEqual({"capability"}, set(response["structuredContent"]))
        return response["structuredContent"]["capability"]

    def _write(self, capability, path, content, **mode):
        arguments = {
            "capability": capability,
            "path": path,
            "content": content,
        }
        arguments.update(mode)
        return self._call("write_owned_state", arguments)

    def _assert_error(self, response, code=None, action=None):
        self.assertTrue(response["isError"], response)
        error = response["structuredContent"]["error"]
        if code is not None:
            self.assertEqual(code, error["code"])
        if action is not None:
            self.assertEqual(action, error["action"])
        return error

    def _journal_events(self):
        journal_paths = list(self.data_root.rglob("*.jsonl"))
        self.assertEqual(1, len(journal_paths), journal_paths)
        lines = [
            line
            for line in journal_paths[0].read_text(encoding="utf-8").splitlines()
            if line
        ]
        return [json.loads(line) for line in lines]

    def _assert_journal_shape(self, event):
        self.assertEqual(
            {
                "timestamp",
                "correlation_id",
                "role",
                "workspace_id",
                "path",
                "operation",
                "result",
                "before_sha256",
                "after_sha256",
            },
            set(event),
        )

    def test_an_upgrade_that_adds_a_section_is_reported_on_read_then_written(self):
        """The whole upgrade path for a section the founder's file predates.

        The write is refused, correctly — a document that has lost a declared
        heading is the drift this check exists for. What the founder needs is
        to learn which heading before the refusal, which is what the read says.
        """
        capability = self._open("cfo", correlation_id="corr-upgrade")
        before = _metrics()
        created = self._write(capability, "metrics.md", before, create_only=True)
        self.assertFalse(created["isError"], created)
        digest = created["structuredContent"]["after_sha256"]

        ownership = self.package / "references" / "ownership.yaml"
        ownership.write_text(
            _ownership_yaml().replace(
                '  metrics.md:\n    - "## Close"\n',
                '  metrics.md:\n    - "## Close"\n    - "## Signals"\n',
            ),
            encoding="utf-8",
        )

        read = self._call(
            "read_state", {"capability": capability, "paths": ["metrics.md"]}
        )
        self.assertFalse(read["isError"], read)
        self.assertEqual(
            ["## Signals"],
            read["structuredContent"]["files"][0]["missing_sections"],
        )

        refused = self._write(
            capability, "metrics.md", before, expected_sha256=digest
        )
        self._assert_error(refused, code="INVALID_DOCUMENT_STRUCTURE")

        repaired = before.replace(
            "## Runway", "## Signals\n\nNone yet.\n\n## Runway"
        )
        accepted = self._write(
            capability, "metrics.md", repaired, expected_sha256=digest
        )
        self.assertFalse(accepted["isError"], accepted)

        read = self._call(
            "read_state", {"capability": capability, "paths": ["metrics.md"]}
        )
        self.assertEqual(
            [], read["structuredContent"]["files"][0]["missing_sections"]
        )

    def test_a_declared_directory_the_scaffold_never_made_is_created(self):
        """An upgrade adds a directory to the map; older workspaces lack it.

        `founder-os-init` creates `workspace_files:` at install time and never
        runs again, so the owner of a newly declared directory would otherwise
        get STATE_IO_ERROR on its first write and no way to repair it.
        """
        capability = self._open("chief-of-staff", correlation_id="corr-dir")
        self.assertFalse((self.workspace / "decisions").exists())
        document = (
            "# Decision\n\n## Context\n\nWhy.\n\n"
            "## Rejected\n\nThe other one.\n\n"
            "## What would change our mind\n\nA number.\n\n"
            "## Supersedes\n\nNothing.\n"
        )

        created = self._write(
            capability, "decisions/2026-08-25.md", document, create_only=True
        )

        self.assertFalse(created["isError"], created)
        self.assertEqual(
            document,
            (self.workspace / "decisions" / "2026-08-25.md").read_text(
                encoding="utf-8"
            ),
        )
        self.assertEqual(
            0o700,
            stat.S_IMODE((self.workspace / "decisions").stat().st_mode),
        )

    def test_only_the_declared_directory_is_created_never_a_deeper_one(self):
        """`decisions/` is a promise the map made; `decisions/2026/` is not.

        Longest-prefix ownership makes a nested path owned, so without this
        bound a typo would quietly scaffold a directory tree nobody declared.
        """
        capability = self._open("chief-of-staff", correlation_id="corr-deep")

        response = self._write(
            capability,
            "decisions/2026/08/25.md",
            "# D\n\n## Context\n\nA.\n\n## Rejected\n\nB.\n\n"
            "## What would change our mind\n\nC.\n\n## Supersedes\n\nD.\n",
            create_only=True,
        )

        self._assert_error(response, code="STATE_IO_ERROR")
        self.assertFalse((self.workspace / "decisions" / "2026").exists())

    def test_a_symlinked_directory_component_is_refused_not_followed(self):
        outside = self.base / "outside"
        outside.mkdir()
        (self.workspace / "decisions").symlink_to(outside)
        capability = self._open("chief-of-staff", correlation_id="corr-link")

        response = self._write(
            capability,
            "decisions/2026-08-25.md",
            "# D\n\n## Context\n\nA.\n\n## Rejected\n\nB.\n\n"
            "## What would change our mind\n\nC.\n\n## Supersedes\n\nD.\n",
            create_only=True,
        )

        self._assert_error(response, code="PATH_OUTSIDE_WORKSPACE")
        self.assertEqual([], list(outside.iterdir()))

    def test_cfo_can_create_and_replace_metrics_with_literal_sha256_values(self):
        capability = self._open("cfo", correlation_id="corr-success")
        before_literal = _metrics(close="Booked: 10")
        after_literal = _metrics(close="Booked: 20")
        independently_calculated_before = hashlib.sha256(
            before_literal.encode("utf-8")
        ).hexdigest()
        independently_calculated_after = hashlib.sha256(
            after_literal.encode("utf-8")
        ).hexdigest()

        created = self._write(
            capability, "metrics.md", before_literal, create_only=True
        )
        self.assertFalse(created["isError"], created)
        self.assertEqual(
            {
                "path": "metrics.md",
                "operation": "create",
                "before_sha256": None,
                "after_sha256": independently_calculated_before,
            },
            created["structuredContent"],
        )
        self.assertEqual(
            before_literal,
            (self.workspace / "metrics.md").read_text(encoding="utf-8"),
        )

        replaced = self._write(
            capability,
            "metrics.md",
            after_literal,
            expected_sha256=independently_calculated_before,
        )
        self.assertFalse(replaced["isError"], replaced)
        self.assertEqual(
            {
                "path": "metrics.md",
                "operation": "replace",
                "before_sha256": independently_calculated_before,
                "after_sha256": independently_calculated_after,
            },
            replaced["structuredContent"],
        )

        events = self._journal_events()
        self.assertEqual(2, len(events))
        for event in events:
            self._assert_journal_shape(event)
            self.assertEqual(self.clock_value, event["timestamp"])
            self.assertEqual("corr-success", event["correlation_id"])
            self.assertEqual("cfo", event["role"])
            self.assertEqual(self.binding.workspace_id, event["workspace_id"])
            self.assertEqual("metrics.md", event["path"])
            self.assertEqual("OK", event["result"])

    def test_invalid_forged_and_wrong_workspace_capabilities_cannot_write(self):
        wrong_workspace_capability = self.sessions.open(
            workspace_id="workspace-not-known-to-resolver",
            role="cfo",
            correlation_id="corr-wrong-workspace",
            workflow="revenue-review",
            workspace_kind="business",
        )
        attempts = {
            "invalid blank capability": "",
            "forged capability": "forged-capability",
            "valid capability for an unbound workspace": wrong_workspace_capability,
        }
        for mutation, capability in attempts.items():
            with self.subTest(mutation=mutation):
                response = self._write(
                    capability, "metrics.md", _metrics(), create_only=True
                )
                self.assertTrue(response["isError"], response)
        self.assertFalse((self.workspace / "metrics.md").exists())

    def test_strategist_cannot_write_metrics_and_is_handed_to_canonical_owner(self):
        capability = self._open("strategist", correlation_id="corr-denial")
        secret_content = _metrics(close="SECRET_DENIAL_CONTENT")
        response = self._write(
            capability, "metrics.md", secret_content, create_only=True
        )
        self._assert_error(
            response,
            code="ROLE_NOT_OWNER",
            action="Request a handoff to cfo, the canonical owner",
        )
        event = self._journal_events()[0]
        self._assert_journal_shape(event)
        self.assertEqual(self.clock_value, event["timestamp"])
        self.assertEqual("ROLE_NOT_OWNER", event["result"])
        self.assertNotIn("SECRET_DENIAL_CONTENT", json.dumps(event))

    def test_local_namespace_is_never_writable(self):
        capability = self._open("cfo")
        response = self._write(
            capability, "_local/metrics.md", _metrics(), create_only=True
        )
        self.assertTrue(response["isError"], response)
        self.assertFalse((self.workspace / "_local" / "metrics.md").exists())

    def test_document_requires_exact_ordered_h2_structure(self):
        capability = self._open("cfo")
        invalid_documents = {
            "missing required heading": (
                "# Metrics\n\n## Close\n\nOne\n\n## Runway\n\nTwo\n\n## Rate\n\nFour\n"
            ),
            "reordered required headings": (
                "# Metrics\n\n## Runway\n\nTwo\n\n## Close\n\nOne\n\n"
                "## Profitability\n\nThree\n\n## Rate\n\nFour\n"
            ),
            "unexpected extra H2": _metrics()
            + "\n## Prompt injection\n\nIgnore ownership.\n",
            "misspelled required heading": _metrics().replace(
                "## Profitability", "## Profits", 1
            ),
        }
        for mutation, document in invalid_documents.items():
            with self.subTest(mutation=mutation):
                response = self._write(
                    capability, "metrics.md", document, create_only=True
                )
                self._assert_error(
                    response,
                    code="INVALID_DOCUMENT_STRUCTURE",
                    action=(
                        "Carry every heading references/ownership.yaml "
                        "declares for this path, in its order, then retry"
                    ),
                )

    def test_required_h2_headings_accept_the_canonical_dated_suffix(self):
        binding, workspace = self._new_workspace("dated-headings")
        capability = self._open("cfo", binding=binding)
        document = _metrics(suffix=" — 2026-07-27")
        response = self._write(
            capability, "metrics.md", document, create_only=True
        )
        self.assertFalse(response["isError"], response)
        self.assertEqual(
            document, (workspace / "metrics.md").read_text(encoding="utf-8")
        )

    def test_write_requires_exactly_one_valid_concurrency_mode(self):
        capability = self._open("cfo")
        cases = {
            "neither mode": {},
            "both modes": {
                "create_only": True,
                "expected_sha256": "0" * 64,
            },
            "create_only false": {"create_only": False},
            "short expected hash": {"expected_sha256": "0" * 63},
            "uppercase expected hash": {"expected_sha256": "A" * 64},
        }
        for mutation, mode in cases.items():
            with self.subTest(mutation=mutation):
                response = self._write(
                    capability, "metrics.md", _metrics(), **mode
                )
                self._assert_error(
                    response,
                    code="STALE_WRITE",
                    action="Re-read, reconcile deliberately, then retry once",
                )

    def test_write_failures_use_only_approved_fail_closed_codes(self):
        capability = self._open("cfo")

        ownership_path = self.package / "references" / "ownership.yaml"
        ownership_path.write_text(
            _ownership_yaml() + "unexpected:\n  - value\n",
            encoding="utf-8",
        )
        malformed = self._write(
            capability,
            "metrics.md",
            _metrics(),
            create_only=True,
        )
        self._assert_error(malformed, code="STATE_IO_ERROR")
        self.assertFalse((self.workspace / "metrics.md").exists())

        ownership_path.write_text(_ownership_yaml(), encoding="utf-8")
        unowned = self._write(
            capability,
            "notes.md",
            _metrics(),
            create_only=True,
        )
        self._assert_error(unowned, code="PATH_OUTSIDE_WORKSPACE")
        self.assertFalse((self.workspace / "notes.md").exists())

    def test_fenced_fake_h2_headings_are_ignored(self):
        capability = self._open("cfo")
        backtick_fence = chr(96) * 3
        valid = (
            _metrics()
            + "\n"
            + backtick_fence
            + "markdown\n## Fake backtick heading\n"
            + backtick_fence
            + "\n\n~~~markdown\n## Fake tilde heading\n~~~\n"
        )
        response = self._write(
            capability,
            "metrics.md",
            valid,
            create_only=True,
        )
        self.assertFalse(response["isError"], response)
        self.assertEqual(
            valid,
            (self.workspace / "metrics.md").read_text(encoding="utf-8"),
        )

        fenced_documents = {
            "backtick": (
                "# Metrics sample\n\n"
                + backtick_fence
                + "markdown\n## Close\n## Runway\n## Profitability\n## Rate\n"
                + backtick_fence
                + "\n"
            ),
            "tilde": (
                "# Metrics sample\n\n~~~markdown\n"
                "## Close\n## Runway\n## Profitability\n## Rate\n~~~\n"
            ),
        }
        for label, document in fenced_documents.items():
            with self.subTest(fence=label):
                binding, workspace = self._new_workspace(
                    "only-fenced-" + label
                )
                fenced_capability = self._open("cfo", binding=binding)
                rejected = self._write(
                    fenced_capability,
                    "metrics.md",
                    document,
                    create_only=True,
                )
                self._assert_error(
                    rejected,
                    code="INVALID_DOCUMENT_STRUCTURE",
                )
                self.assertFalse((workspace / "metrics.md").exists())

    def test_unsafe_journal_target_denies_before_state_mutation(self):
        capability = self._open("cfo")
        journal = self.data_root / "operations.jsonl"
        outside = self.base / "outside-journal"
        outside.write_text("must survive\n", encoding="utf-8")
        journal.symlink_to(outside)

        symlinked = self._write(
            capability,
            "metrics.md",
            _metrics(),
            create_only=True,
        )
        self._assert_error(symlinked, code="STATE_IO_ERROR")
        self.assertFalse((self.workspace / "metrics.md").exists())
        self.assertEqual(
            "must survive\n",
            outside.read_text(encoding="utf-8"),
        )

        journal.unlink()
        journal.mkdir()
        special = self._write(
            capability,
            "metrics.md",
            _metrics(),
            create_only=True,
        )
        self._assert_error(special, code="STATE_IO_ERROR")
        self.assertFalse((self.workspace / "metrics.md").exists())

    def test_unsafe_target_lock_denies_before_state_mutation(self):
        capability = self._open("cfo")
        lock_name = ".founder-os-write-{0}.lock".format(
            hashlib.sha256(b"metrics.md").hexdigest()
        )
        lock_path = self.workspace / lock_name
        outside = self.base / "outside-lock"
        outside.write_text("must survive\n", encoding="utf-8")
        lock_path.symlink_to(outside)

        symlinked = self._write(
            capability,
            "metrics.md",
            _metrics(),
            create_only=True,
        )
        self._assert_error(symlinked, code="STATE_IO_ERROR")
        self.assertFalse((self.workspace / "metrics.md").exists())
        self.assertEqual("must survive\n", outside.read_text(encoding="utf-8"))

        lock_path.unlink()
        os.link(outside, lock_path)
        hardlinked = self._write(
            capability,
            "metrics.md",
            _metrics(),
            create_only=True,
        )
        self._assert_error(hardlinked, code="STATE_IO_ERROR")
        self.assertFalse((self.workspace / "metrics.md").exists())
        self.assertEqual("must survive\n", outside.read_text(encoding="utf-8"))

    def test_post_replace_journal_failure_reports_landed_write_as_success(self):
        capability = self._open("cfo")
        content = _metrics(close="Committed before journal failure")

        with mock.patch.object(
            self.sessions,
            "append_journal",
            side_effect=JournalError(),
        ):
            response = self._write(
                capability,
                "metrics.md",
                content,
                create_only=True,
            )

        self.assertFalse(response["isError"], response)
        self.assertEqual(
            content,
            (self.workspace / "metrics.md").read_text(encoding="utf-8"),
        )

    def test_journal_rotates_at_size_limit_and_keeps_three_archives(self):
        self.sessions.JOURNAL_MAX_BYTES = 1
        capability = self._open("cfo", correlation_id="corr-rotation")
        metadata = self.sessions.resolve(capability)

        for index in range(5):
            self.sessions.append_journal(
                metadata,
                path="metrics.md",
                operation="replace",
                result="rotation-%d" % index,
                before_sha256="0" * 64,
                after_sha256="1" * 64,
            )

        self.assertTrue((self.data_root / "operations.jsonl").is_file())
        for index in range(1, 4):
            archive = self.data_root / ("operations.jsonl.%d" % index)
            self.assertTrue(archive.is_file(), archive)
            self.assertTrue(archive.read_text(encoding="utf-8").strip())
        self.assertFalse((self.data_root / "operations.jsonl.4").exists())

    def test_journal_rotation_rejects_symlink_and_non_regular_archives(self):
        self.data_root.mkdir(parents=True, exist_ok=True)
        active = self.data_root / "operations.jsonl"
        active.write_text("{}\n", encoding="utf-8")
        self.sessions.JOURNAL_MAX_BYTES = 1
        archive = self.data_root / "operations.jsonl.1"
        outside = self.base / "outside-archive"
        outside.write_text("must survive\n", encoding="utf-8")

        archive.symlink_to(outside)
        with self.assertRaises(JournalError):
            self.sessions.preflight_journal()
        self.assertEqual("must survive\n", outside.read_text(encoding="utf-8"))

        archive.unlink()
        archive.mkdir()
        with self.assertRaises(JournalError):
            self.sessions.preflight_journal()

    def test_concurrent_journal_preflights_are_serialized(self):
        first = self.sessions.preflight_journal()
        started = threading.Event()
        completed = threading.Event()
        descriptors = []
        errors = []

        def second_preflight():
            started.set()
            try:
                descriptors.append(self.sessions.preflight_journal())
            except Exception as error:  # pragma: no cover - asserted below
                errors.append(error)
            finally:
                completed.set()

        contender = threading.Thread(target=second_preflight)
        contender.start()
        self.assertTrue(started.wait(1))
        self.assertFalse(completed.wait(0.05))
        os.close(first)
        contender.join(1)

        self.assertFalse(contender.is_alive())
        self.assertTrue(completed.is_set())
        self.assertEqual([], errors)
        self.assertEqual(1, len(descriptors))
        os.close(descriptors[0])

    def test_post_replace_clock_failure_reports_landed_write_as_success(self):
        capability = self._open("cfo")
        content = _metrics(close="Committed before clock failure")
        clock_calls = [0]

        def fail_during_success_journal():
            clock_calls[0] += 1
            if clock_calls[0] == 1:
                return self.clock_value
            raise ValueError("injected journal clock failure")

        self.sessions._clock = fail_during_success_journal
        response = self._write(
            capability,
            "metrics.md",
            content,
            create_only=True,
        )

        self.assertFalse(response["isError"], response)
        self.assertEqual(2, clock_calls[0])
        self.assertEqual(
            content,
            (self.workspace / "metrics.md").read_text(encoding="utf-8"),
        )

    def test_concurrent_change_before_replace_is_preserved_as_stale(self):
        capability = self._open("cfo", correlation_id="corr-concurrent")
        initial = _metrics(close="Initial")
        concurrent = _metrics(close="Concurrent winner")
        proposed = _metrics(close="Stale contender")
        initial_hash = hashlib.sha256(initial.encode("utf-8")).hexdigest()
        target = self.workspace / "metrics.md"
        target.write_text(initial, encoding="utf-8")
        callback_count = [0]

        def concurrent_change(*unused):
            callback_count[0] += 1
            target.write_text(concurrent, encoding="utf-8")

        def io_factory(workspace_root, *unused, **unused_keywords):
            return SafeStateIO(
                workspace_root,
                self.package,
                before_replace=concurrent_change,
            )

        self.gateway._io_factory = io_factory
        response = self._write(
            capability,
            "metrics.md",
            proposed,
            expected_sha256=initial_hash,
        )

        self._assert_error(
            response,
            code="STALE_WRITE",
            action="Re-read, reconcile deliberately, then retry once",
        )
        self.assertEqual(1, callback_count[0])
        self.assertEqual(concurrent, target.read_text(encoding="utf-8"))
        self.assertFalse(
            any(
                entry.name.startswith(".metrics.md.")
                and entry.name.endswith(".tmp")
                for entry in self.workspace.iterdir()
            )
        )

    def test_gateway_writers_cannot_race_between_final_check_and_replace(self):
        initial = _metrics(close="Initial")
        first = _metrics(close="First committed writer")
        second = _metrics(close="Second stale writer")
        initial_hash = hashlib.sha256(initial.encode("utf-8")).hexdigest()
        target = self.workspace / "metrics.md"
        target.write_text(initial, encoding="utf-8")
        second_started = threading.Event()
        second_finished = threading.Event()
        second_errors = []
        second_io = SafeStateIO(self.workspace, self.package)
        self.addCleanup(second_io.close)

        def competing_writer():
            second_started.set()
            try:
                second_io.atomic_replace(
                    "metrics.md",
                    second.encode("utf-8"),
                    expected_sha256=initial_hash,
                )
            except Exception as error:
                second_errors.append(error)
            finally:
                second_finished.set()

        competitor = threading.Thread(target=competing_writer)

        def start_competitor_after_final_check(*unused):
            competitor.start()
            self.assertTrue(second_started.wait(1))
            self.assertFalse(second_finished.wait(0.05))

        first_io = SafeStateIO(
            self.workspace,
            self.package,
            before_commit=start_competitor_after_final_check,
        )
        self.addCleanup(first_io.close)
        result = first_io.atomic_replace(
            "metrics.md",
            first.encode("utf-8"),
            expected_sha256=initial_hash,
        )
        competitor.join(1)

        self.assertFalse(competitor.is_alive())
        self.assertTrue(second_finished.is_set())
        self.assertEqual("replace", result["operation"])
        self.assertEqual(first, target.read_text(encoding="utf-8"))
        self.assertEqual(1, len(second_errors), second_errors)
        self.assertEqual("STALE_WRITE", second_errors[0].code)

    def test_create_only_existing_expected_on_missing_and_stale_hash_are_rejected(self):
        capability = self._open("cfo")
        existing = _metrics(close="Existing")
        existing_hash = hashlib.sha256(existing.encode("utf-8")).hexdigest()
        (self.workspace / "metrics.md").write_text(existing, encoding="utf-8")
        create_existing = self._write(
            capability,
            "metrics.md",
            _metrics(close="Overwrite"),
            create_only=True,
        )
        self.assertTrue(create_existing["isError"], create_existing)
        stale = self._write(
            capability,
            "metrics.md",
            _metrics(close="Stale overwrite"),
            expected_sha256="0" * 64,
        )
        self._assert_error(
            stale,
            code="STALE_WRITE",
            action="Re-read, reconcile deliberately, then retry once",
        )
        binding, missing_workspace = self._new_workspace("missing-target")
        missing_capability = self._open("cfo", binding=binding)
        expected_on_missing = self._write(
            missing_capability,
            "metrics.md",
            _metrics(),
            expected_sha256=existing_hash,
        )
        self._assert_error(expected_on_missing, code="STALE_WRITE")
        self.assertFalse((missing_workspace / "metrics.md").exists())

    def test_stale_write_journal_records_actual_hash_without_raw_expected_hash(self):
        capability = self._open("cfo", correlation_id="corr-stale")
        existing_literal = _metrics(close="Existing")
        actual_hash = hashlib.sha256(
            existing_literal.encode("utf-8")
        ).hexdigest()
        raw_expected_hash = "1" * 64
        (self.workspace / "metrics.md").write_text(
            existing_literal, encoding="utf-8"
        )
        response = self._write(
            capability,
            "metrics.md",
            _metrics(close="Rejected"),
            expected_sha256=raw_expected_hash,
        )
        self._assert_error(response, code="STALE_WRITE")
        event = self._journal_events()[0]
        self._assert_journal_shape(event)
        self.assertEqual(self.clock_value, event["timestamp"])
        self.assertEqual(actual_hash, event["before_sha256"])
        self.assertIsNone(event["after_sha256"])
        self.assertNotIn(raw_expected_hash, json.dumps(event))

    def test_traversal_symlink_and_special_file_targets_are_rejected(self):
        capability = self._open("cfo")
        traversal = self._write(
            capability, "../metrics.md", _metrics(), create_only=True
        )
        self._assert_error(traversal, code="PATH_OUTSIDE_WORKSPACE")

        binding, symlink_workspace = self._new_workspace("symlink")
        symlink_capability = self._open("cfo", binding=binding)
        outside = self.base / "outside.md"
        outside.write_text("outside must survive\n", encoding="utf-8")
        (symlink_workspace / "metrics.md").symlink_to(outside)
        symlink_response = self._write(
            symlink_capability, "metrics.md", _metrics(), create_only=True
        )
        self.assertTrue(symlink_response["isError"], symlink_response)
        self.assertEqual(
            "outside must survive\n", outside.read_text(encoding="utf-8")
        )

        if hasattr(os, "mkfifo"):
            binding, fifo_workspace = self._new_workspace("fifo")
            fifo_capability = self._open("cfo", binding=binding)
            fifo = fifo_workspace / "metrics.md"
            os.mkfifo(str(fifo))
            fifo_response = self._write(
                fifo_capability, "metrics.md", _metrics(), create_only=True
            )
            self.assertTrue(fifo_response["isError"], fifo_response)

    def test_atomic_replace_failure_preserves_original_and_removes_temp_file(self):
        capability = self._open("cfo", correlation_id="corr-atomic")
        before_literal = _metrics(close="Before atomic failure")
        before_hash = hashlib.sha256(
            before_literal.encode("utf-8")
        ).hexdigest()
        target = self.workspace / "metrics.md"
        target.write_text(before_literal, encoding="utf-8")
        entries_before = {entry.name for entry in self.workspace.iterdir()}
        real_replace = os.replace

        def fail_only_target_replace(source, destination, *args, **kwargs):
            if Path(os.fspath(destination)).name == "metrics.md":
                raise OSError("injected atomic replace failure")
            return real_replace(source, destination, *args, **kwargs)

        with mock.patch(
            "mcp.safe_io.os.replace", side_effect=fail_only_target_replace
        ):
            response = self._write(
                capability,
                "metrics.md",
                _metrics(close="Must not land"),
                expected_sha256=before_hash,
            )
        self._assert_error(response, code="STATE_IO_ERROR")
        self.assertEqual(before_literal, target.read_text(encoding="utf-8"))
        self.assertEqual(
            entries_before,
            {
                entry.name
                for entry in self.workspace.iterdir()
                if not entry.name.startswith(".founder-os-write-")
            },
        )
        event = self._journal_events()[0]
        self._assert_journal_shape(event)
        self.assertEqual(self.clock_value, event["timestamp"])
        self.assertEqual("STATE_IO_ERROR", event["result"])

    def test_protocol_response_and_journal_never_expose_content_prompt_or_capability(self):
        capability = self._open("cfo", correlation_id="corr-redaction")
        secret_content = (
            _metrics()
            + "\n## PROMPT_SECRET_MARKER\n\nCAPABILITY_SECRET_MARKER\n"
        )
        response = self._write(
            capability, "metrics.md", secret_content, create_only=True
        )
        self._assert_error(response, code="INVALID_DOCUMENT_STRUCTURE")
        response_text = json.dumps(response)
        self.assertNotIn("PROMPT_SECRET_MARKER", response_text)
        self.assertNotIn("CAPABILITY_SECRET_MARKER", response_text)
        self.assertNotIn(capability, response_text)
        event = self._journal_events()[0]
        self._assert_journal_shape(event)
        self.assertNotIn("prompt", json.dumps(event).lower())
        self.assertNotIn(capability, json.dumps(event))


if __name__ == "__main__":
    unittest.main()
