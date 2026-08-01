from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "founder-os"
sys.path.insert(0, str(PACKAGE_ROOT))

from mcp.gateway import Gateway, TOOL_SCHEMAS
from mcp.safe_io import SafeStateError, SafeStateIO
from mcp.sessions import RoleSessionError, RoleSessionStore
from mcp.workspaces import WorkspaceResolutionError, WorkspaceResolver


ROLE_FILENAMES = (
    "board-member.md",
    "brand-editor.md",
    "cfo.md",
    "chief-of-staff.md",
    "delivery-lead.md",
    "focus-coach.md",
    "network-manager.md",
    "ops-engineer.md",
    "pipeline-coach.md",
    "portfolio-manager.md",
    "positioning-advisor.md",
    "skills-mentor.md",
    "strategist.md",
)


def write_packaged_root(root: Path) -> Path:
    """Create a small package fixture without depending on installed assets."""
    agents = root / "agents"
    agents.mkdir(parents=True)
    for filename in ROLE_FILENAMES:
        (agents / filename).write_text("# role\n", encoding="utf-8")

    workflow = root / "skills" / "week-plan"
    workflow.mkdir(parents=True)
    (workflow / "SKILL.md").write_text("# workflow\n", encoding="utf-8")
    return root


def write_registry(home: Path, body: str) -> None:
    registry = home / ".founder-os"
    registry.mkdir(parents=True)
    (registry / "businesses.yaml").write_text(body, encoding="utf-8")


class WorkspaceResolverReadTests(unittest.TestCase):
    def assert_unresolved(self, callable_object) -> None:
        with self.assertRaises(WorkspaceResolutionError) as raised:
            callable_object()
        self.assertEqual("WORKSPACE_UNRESOLVED", raised.exception.code)
        self.assertEqual(
            "Ask for the business; make no read or write",
            raised.exception.action,
        )

    def test_forged_workspace_id_cannot_unlock_a_workspace_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            resolver = WorkspaceResolver(env={}, home=root / "home")

            binding = resolver.resolve(project)
            self.assertEqual(binding, resolver.get(binding.workspace_id))
            self.assert_unresolved(lambda: resolver.get("forged-workspace-id"))

    def test_relative_env_home_is_resolved_from_project_and_mapped_to_registry_slug(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "checkout" / "app"
            workspace = root / "checkout" / "shared-business"
            project.mkdir(parents=True)
            workspace.mkdir(parents=True)
            home = root / "home"
            write_registry(
                home,
                "\n".join(
                    (
                        "businesses:",
                        "  shared:",
                        "    home: " + workspace.as_posix(),
                        "    status: active",
                    )
                ),
            )

            resolver = WorkspaceResolver(
                env={"FOUNDER_OS_HOME": "../shared-business"},
                home=home,
            )
            binding = resolver.resolve(project)

            self.assertEqual(workspace.resolve(), binding.root)
            self.assertEqual("shared", binding.business_slug)

    def test_missing_registry_uses_env_then_project_founder_os_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            configured = root / "configured"
            project.mkdir()
            configured.mkdir()

            env_resolver = WorkspaceResolver(
                env={"FOUNDER_OS_HOME": "../configured"},
                home=root / "no-registry-home",
            )
            fallback_resolver = WorkspaceResolver(
                env={},
                home=root / "another-no-registry-home",
            )

            self.assertEqual(configured.resolve(), env_resolver.resolve(project).root)
            self.assertEqual(
                (project / "founder-os").resolve(),
                fallback_resolver.resolve(project).root,
            )

    def test_explicit_slug_default_and_portfolio_select_the_intended_business(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            alpha = root / "alpha"
            beta = root / "beta"
            portfolio = root / "portfolio"
            project.mkdir()
            alpha.mkdir()
            beta.mkdir()
            portfolio.mkdir()
            home = root / "home"
            write_registry(
                home,
                "\n".join(
                    (
                        "businesses:",
                        "  alpha:",
                        "    home: " + alpha.as_posix(),
                        "    status: active",
                        "  beta:",
                        "    home: " + beta.as_posix(),
                        "    status: active",
                        "default: alpha",
                        "portfolio: " + portfolio.as_posix(),
                    )
                ),
            )
            resolver = WorkspaceResolver(env={}, home=home)

            self.assertEqual("beta", resolver.resolve(project, "beta").business_slug)
            self.assertEqual("alpha", resolver.resolve(project).business_slug)
            portfolio_binding = resolver.resolve(project, "portfolio")
            self.assertEqual("portfolio", portfolio_binding.business_slug)
            self.assertEqual(portfolio.resolve(), portfolio_binding.root)

    def test_single_active_business_is_selected_when_default_is_removed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            active = root / "active"
            project.mkdir()
            active.mkdir()
            home = root / "home"
            write_registry(
                home,
                "\n".join(
                    (
                        "businesses:",
                        "  active:",
                        "    home: " + active.as_posix(),
                        "    status: active",
                        "  paused:",
                        "    home: " + (root / "paused").as_posix(),
                        "    status: paused",
                    )
                ),
            )

            binding = WorkspaceResolver(env={}, home=home).resolve(project)
            self.assertEqual("active", binding.business_slug)

    def test_two_active_businesses_without_default_fail_closed_instead_of_guessing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            home = root / "home"
            write_registry(
                home,
                "\n".join(
                    (
                        "businesses:",
                        "  alpha:",
                        "    home: " + (root / "alpha").as_posix(),
                        "    status: active",
                        "  beta:",
                        "    home: " + (root / "beta").as_posix(),
                        "    status: active",
                    )
                ),
            )

            self.assert_unresolved(
                lambda: WorkspaceResolver(env={}, home=home).resolve(project)
            )

    def test_unknown_business_slug_fails_without_selecting_a_nearby_business(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            home = root / "home"
            write_registry(
                home,
                "\n".join(
                    (
                        "businesses:",
                        "  known:",
                        "    home: " + (root / "known").as_posix(),
                        "    status: active",
                    )
                ),
            )

            self.assert_unresolved(
                lambda: WorkspaceResolver(env={}, home=home).resolve(project, "typo")
            )

    def test_workspace_ids_are_opaque_and_bound_to_the_resolver_that_issued_them(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "customer-project"
            project.mkdir()

            first = WorkspaceResolver(env={}, home=root / "home")
            second = WorkspaceResolver(env={}, home=root / "home")
            first_binding = first.resolve(project)
            second_binding = second.resolve(project)

            self.assertEqual(first_binding, first.get(first_binding.workspace_id))
            self.assertEqual(second_binding, second.get(second_binding.workspace_id))
            self.assertNotEqual(first_binding.workspace_id, second_binding.workspace_id)
            for binding in (first_binding, second_binding):
                self.assertNotIn(str(binding.root), binding.workspace_id)
                self.assertNotIn(binding.root.name, binding.workspace_id)


    def test_registry_rejects_malformed_unselected_entries_and_container_scalars(self) -> None:
        cases = (
            (
                "malformed-unselected-entry",
                (
                    "businesses:",
                    "  alpha:",
                    "    home: {alpha}",
                    "    status: active",
                    "  beta: malformed",
                    "default: alpha",
                ),
            ),
            (
                "container-default",
                (
                    "businesses:",
                    "  alpha:",
                    "    home: {alpha}",
                    "    status: active",
                    "default: [alpha]",
                ),
            ),
            (
                "invalid-unselected-status-type",
                (
                    "businesses:",
                    "  alpha:",
                    "    home: {alpha}",
                    "    status: active",
                    "  beta:",
                    "    home: {beta}",
                    "    status: true",
                    "default: alpha",
                ),
            ),
        )
        for name, lines in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                home = root / "home"
                alpha = root / "alpha"
                beta = root / "beta"
                alpha.mkdir()
                beta.mkdir()
                write_registry(
                    home,
                    "\n".join(line.format(alpha=alpha, beta=beta) for line in lines),
                )
                resolver = WorkspaceResolver(env={}, home=home)
                self.assert_unresolved(lambda: resolver.resolve(root))

    def test_registry_rejects_unknown_and_inactive_automatic_defaults(self) -> None:
        for default in ("missing", "paused"):
            with self.subTest(default=default), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                home = root / "home"
                active = root / "active"
                paused = root / "paused"
                active.mkdir()
                paused.mkdir()
                write_registry(
                    home,
                    "\n".join(
                        (
                            "businesses:",
                            "  active:",
                            f"    home: {active.as_posix()}",
                            "    status: active",
                            "  paused:",
                            f"    home: {paused.as_posix()}",
                            "    status: paused",
                            f"default: {default}",
                        )
                    ),
                )
                resolver = WorkspaceResolver(env={}, home=home)
                self.assert_unresolved(lambda: resolver.resolve(root))


    def test_registry_supports_canonical_inline_comments_and_quoted_hashes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "home"
            alpha = root / "alpha#state"
            portfolio = root / "portfolio#state"
            alpha.mkdir()
            portfolio.mkdir()
            write_registry(
                home,
                "\n".join(
                    (
                        "businesses: # registered businesses",
                        "  alpha: # primary business",
                        f'    home: "{alpha.as_posix()}" # workspace root',
                        "    status: active # automatic selection",
                        "default: alpha # selected by default",
                        f'portfolio: "{portfolio.as_posix()}" # portfolio root',
                    )
                ),
            )

            resolver = WorkspaceResolver(env={}, home=home)
            self.assertEqual(alpha.resolve(), resolver.resolve(root).root)
            self.assertEqual(
                portfolio.resolve(),
                resolver.resolve(root, business_slug="portfolio").root,
            )

    def test_bindings_report_single_business_business_and_portfolio_kinds(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()

            single = WorkspaceResolver(
                env={},
                home=root / "single-home",
            ).resolve(project)
            self.assertEqual("single-business", single.workspace_kind)

            alpha = root / "alpha"
            portfolio = root / "portfolio"
            alpha.mkdir()
            portfolio.mkdir()
            home = root / "home"
            write_registry(
                home,
                "\n".join(
                    (
                        "businesses:",
                        "  alpha:",
                        "    home: " + alpha.as_posix(),
                        "    status: active",
                        "portfolio: " + portfolio.as_posix(),
                    )
                ),
            )
            resolver = WorkspaceResolver(env={}, home=home)

            self.assertEqual(
                "business",
                resolver.resolve(project, "alpha").workspace_kind,
            )
            self.assertEqual(
                "portfolio",
                resolver.resolve(project, "portfolio").workspace_kind,
            )

    def test_registry_rejects_equal_parent_and_child_workspace_roots(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            for name, alpha, beta in (
                ("equal", root / "shared", root / "shared"),
                ("nested", root / "shared", root / "shared" / "child"),
            ):
                with self.subTest(name=name):
                    home = root / ("home-" + name)
                    write_registry(
                        home,
                        "\n".join(
                            (
                                "businesses:",
                                "  alpha:",
                                "    home: " + alpha.as_posix(),
                                "    status: active",
                                "  beta:",
                                "    home: " + beta.as_posix(),
                                "    status: paused",
                            )
                        ),
                    )
                    self.assert_unresolved(
                        lambda home=home: WorkspaceResolver(
                            env={},
                            home=home,
                        ).resolve(project, "alpha")
                    )

    def test_registry_change_invalidates_an_existing_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            alpha = root / "alpha"
            moved = root / "moved-alpha"
            project.mkdir()
            alpha.mkdir()
            moved.mkdir()
            home = root / "home"
            write_registry(
                home,
                "\n".join(
                    (
                        "businesses:",
                        "  alpha:",
                        "    home: " + alpha.as_posix(),
                        "    status: active",
                    )
                ),
            )
            resolver = WorkspaceResolver(env={}, home=home)
            binding = resolver.resolve(project, "alpha")

            (home / ".founder-os" / "businesses.yaml").write_text(
                "\n".join(
                    (
                        "businesses:",
                        "  alpha:",
                        "    home: " + moved.as_posix(),
                        "    status: active",
                    )
                ),
                encoding="utf-8",
            )

            self.assert_unresolved(lambda: resolver.validate_binding(binding))

    def test_portfolio_binding_resolves_only_active_registered_businesses(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            alpha = root / "alpha"
            paused = root / "paused"
            portfolio = root / "portfolio"
            for directory in (project, alpha, paused, portfolio):
                directory.mkdir()
            home = root / "home"
            write_registry(
                home,
                "\n".join(
                    (
                        "businesses:",
                        "  alpha:",
                        "    home: " + alpha.as_posix(),
                        "    status: active",
                        "  paused:",
                        "    home: " + paused.as_posix(),
                        "    status: paused",
                        "portfolio: " + portfolio.as_posix(),
                    )
                ),
            )
            resolver = WorkspaceResolver(env={}, home=home)
            portfolio_binding = resolver.resolve(project, "portfolio")

            self.assertEqual(
                alpha.resolve(),
                resolver.portfolio_business_root(
                    portfolio_binding,
                    "alpha",
                ),
            )
            self.assert_unresolved(
                lambda: resolver.portfolio_business_root(
                    portfolio_binding,
                    "paused",
                )
            )
            business_binding = resolver.resolve(project, "alpha")
            self.assert_unresolved(
                lambda: resolver.portfolio_business_root(
                    business_binding,
                    "alpha",
                )
            )


class RoleSessionStoreReadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.packaged_root = write_packaged_root(self.root / "package")
        self.data_root = self.root / "data"
        self.now = [1_000.0]
        self.store = RoleSessionStore(
            data_root=self.data_root,
            packaged_root=self.packaged_root,
            clock=lambda: self.now[0],
            ttl_seconds=60,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def assert_invalid(self, callable_object) -> None:
        with self.assertRaises(RoleSessionError) as raised:
            callable_object()
        self.assertEqual("ROLE_SESSION_INVALID", raised.exception.code)
        self.assertEqual(
            "Stop and return control to the main thread",
            raised.exception.action,
        )

    def persisted_text(self) -> str:
        return "\n".join(
            path.read_text(encoding="utf-8")
            for path in self.data_root.rglob("*")
            if path.is_file()
        )

    def test_unlisted_agent_filename_cannot_open_a_role_session(self) -> None:
        self.assertEqual(13, len(ROLE_FILENAMES))
        for filename in ROLE_FILENAMES:
            capability = self.store.open(
                "workspace-1",
                filename.removesuffix(".md"),
                "corr-listed-role",
            )
            self.assertTrue(capability)

        self.assert_invalid(
            lambda: self.store.open("workspace-1", "invented-role", "corr-invalid")
        )

    def test_blank_workspace_or_correlation_id_cannot_create_persisted_session_metadata(self) -> None:
        self.assert_invalid(
            lambda: self.store.open("", "chief-of-staff", "corr-present")
        )
        self.assert_invalid(
            lambda: self.store.open("workspace-present", "chief-of-staff", "")
        )

    def test_missing_or_traversed_workflow_cannot_be_attached_to_a_role_session(self) -> None:
        capability = self.store.open(
            "workspace-1",
            "chief-of-staff",
            "corr-valid-workflow",
            workflow="week-plan",
        )
        self.assertEqual("week-plan", self.store.resolve(capability).workflow)

        self.assert_invalid(
            lambda: self.store.open(
                "workspace-1",
                "chief-of-staff",
                "corr-missing-workflow",
                workflow="missing",
            )
        )
        self.assert_invalid(
            lambda: self.store.open(
                "workspace-1",
                "chief-of-staff",
                "corr-traversal-workflow",
                workflow="../agents",
            )
        )

    def test_forged_cross_store_workspace_or_role_capability_is_rejected(self) -> None:
        capability = self.store.open(
            "workspace-1",
            "chief-of-staff",
            "corr-capability-boundary",
        )
        other_store = RoleSessionStore(
            data_root=self.root / "other-data",
            packaged_root=self.packaged_root,
            clock=lambda: self.now[0],
            ttl_seconds=60,
        )

        self.assert_invalid(lambda: self.store.resolve("forged-capability"))
        self.assert_invalid(lambda: other_store.resolve(capability))
        self.assert_invalid(
            lambda: self.store.resolve(capability, workspace_id="workspace-2")
        )
        self.assert_invalid(lambda: self.store.resolve(capability, role="cfo"))

    def test_expired_closed_and_reused_capability_cannot_read_role_metadata(self) -> None:
        expiring = self.store.open("workspace-1", "cfo", "corr-expiring")
        self.now[0] = 1_060.0
        self.assert_invalid(lambda: self.store.resolve(expiring))

        closable = self.store.open("workspace-1", "cfo", "corr-closing")
        self.store.close(closable, final_status="completed")
        self.assert_invalid(lambda: self.store.resolve(closable))
        self.assert_invalid(lambda: self.store.close(closable))

    def test_session_record_hashes_capability_and_retains_only_authorized_metadata(self) -> None:
        capability = self.store.open(
            "workspace-1",
            "chief-of-staff",
            "corr-private-token",
            workflow="week-plan",
        )
        metadata = self.store.resolve(capability)
        capability_hash = hashlib.sha256(capability.encode("utf-8")).hexdigest()
        persisted = self.persisted_text()

        self.assertEqual("workspace-1", metadata.workspace_id)
        self.assertEqual("chief-of-staff", metadata.role)
        self.assertEqual("corr-private-token", metadata.correlation_id)
        self.assertEqual("week-plan", metadata.workflow)
        self.assertEqual(1_060.0, metadata.expires_at)
        self.assertIn(capability_hash, persisted)
        self.assertNotIn(capability, persisted)
        self.assertIn("workspace-1", persisted)
        self.assertIn("chief-of-staff", persisted)
        self.assertIn("corr-private-token", persisted)
        self.assertIn("week-plan", persisted)
        self.assertIn("1060", persisted)

        self.store.close(capability, final_status="completed")
        closed = self.persisted_text()
        self.assertNotIn(capability, closed)
        self.assertIn(capability_hash, closed)
        self.assertIn("completed", closed)


    def test_resolve_rejects_every_tampered_persisted_field(self) -> None:
        mutations = (
            ("extra-field", lambda record: record.__setitem__("unexpected", "value")),
            ("missing-field", lambda record: record.pop("correlation_id")),
            ("workspace-type", lambda record: record.__setitem__("workspace_id", [])),
            ("workspace-blank", lambda record: record.__setitem__("workspace_id", " ")),
            ("unknown-role", lambda record: record.__setitem__("role", "unknown-role")),
            ("workflow-type", lambda record: record.__setitem__("workflow", 7)),
            ("unknown-workflow", lambda record: record.__setitem__("workflow", "missing")),
            ("correlation-type", lambda record: record.__setitem__("correlation_id", True)),
            ("expiry-string", lambda record: record.__setitem__("expires_at", "1060")),
            ("expiry-bool", lambda record: record.__setitem__("expires_at", True)),
            ("expiry-infinite", lambda record: record.__setitem__("expires_at", float("inf"))),
            ("invalid-status", lambda record: record.__setitem__("status", "OPEN")),
            ("open-final-status", lambda record: record.__setitem__("final_status", "done")),
            ("invalid-hash", lambda record: record.__setitem__("capability_hash", "g" * 64)),
        )
        for name, mutate in mutations:
            with self.subTest(name=name):
                capability = self.store.open(
                    "workspace-id",
                    "cfo",
                    "correlation-id",
                    "week-plan",
                )
                record_path = self.data_root / (
                    hashlib.sha256(capability.encode("utf-8")).hexdigest() + ".json"
                )
                record = json.loads(record_path.read_text(encoding="utf-8"))
                mutate(record)
                record_path.write_text(json.dumps(record), encoding="utf-8")
                self.assert_invalid(lambda: self.store.resolve(capability))

    def test_close_rejects_invalid_final_status(self) -> None:
        for final_status in ("", " ", True, 7):
            with self.subTest(final_status=final_status):
                capability = self.store.open(
                    "workspace-id",
                    "cfo",
                    "correlation-id",
                )
                self.assert_invalid(
                    lambda: self.store.close(capability, final_status=final_status)
                )


class SafeStateIOTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.package = write_packaged_root(self.root / "package")
        (self.package / "CLAUDE.md").write_text("# package\n", encoding="utf-8")
        references = self.package / "references"
        references.mkdir()
        for name in (
            "ownership.yaml",
            "house-rules.md",
            "multi-business.md",
            "orchestration.md",
        ):
            (references / name).write_text(name + "\n", encoding="utf-8")
        (self.workspace / "state.md").write_bytes(b"state bytes\n")
        (self.workspace / "empty.md").write_bytes(b"")
        nested = self.workspace / "nested"
        nested.mkdir()
        (nested / "note.md").write_bytes(b"nested\n")
        (self.workspace / "ignored.txt").write_text("ignored\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def io(self, **limits) -> SafeStateIO:
        return SafeStateIO(
            self.workspace,
            self.package,
            max_results=limits.get("max_results", 20),
            max_file_bytes=limits.get("max_file_bytes", 1024),
            max_total_bytes=limits.get("max_total_bytes", 4096),
            before_component_open=limits.get("before_component_open"),
        )

    def assert_safe_error(self, code, callable_object) -> None:
        with self.assertRaises(SafeStateError) as raised:
            callable_object()
        self.assertEqual(code, raised.exception.code)
        action = {
            "PATH_OUTSIDE_WORKSPACE": "Refuse without retrying a modified path guess",
            "STATE_IO_ERROR": "Preserve the original file and surface the error",
        }[code]
        self.assertEqual(action, raised.exception.action)

    def test_markdown_listing_omits_non_markdown_and_sorts_relative_posix_paths(self) -> None:
        paths = self.io().list_markdown("**/*.md")
        self.assertEqual(["empty.md", "nested/note.md", "state.md"], paths)

    def test_glob_metacharacters_or_parent_paths_cannot_escape_state_listing(self) -> None:
        for pattern in (
            "/tmp/*.md",
            "../*.md",
            "nested/../*.md",
            "name?.md",
            "[name].md",
            "{name}.md",
            r"name\*.md",
            "nul\x00.md",
        ):
            with self.subTest(pattern=pattern):
                self.assert_safe_error(
                    "PATH_OUTSIDE_WORKSPACE",
                    lambda pattern=pattern: self.io().list_markdown(pattern),
                )

    def test_listing_over_result_or_response_byte_limit_fails_without_partial_list(self) -> None:
        self.assert_safe_error(
            "STATE_IO_ERROR",
            lambda: self.io(max_results=1).list_markdown("**/*.md"),
        )
        self.assert_safe_error(
            "STATE_IO_ERROR",
            lambda: self.io(max_total_bytes=1).list_markdown("*.md"),
        )

    def test_read_many_returns_literal_metadata_and_hash_of_original_bytes(self) -> None:
        result = self.io().read_many(["state.md", "empty.md"])
        state, empty = result

        self.assertEqual(
            {"path", "content", "sha256", "size", "mtime_ns"},
            set(state),
        )
        self.assertEqual("state.md", state["path"])
        self.assertEqual("state bytes\n", state["content"])
        self.assertEqual(
            hashlib.sha256(b"state bytes\n").hexdigest(),
            state["sha256"],
        )
        self.assertEqual(len(b"state bytes\n"), state["size"])
        self.assertIsInstance(state["mtime_ns"], int)
        self.assertEqual("", empty["content"])
        self.assertEqual(hashlib.sha256(b"").hexdigest(), empty["sha256"])
        self.assertEqual(0, empty["size"])

    def test_read_path_mutations_cannot_be_normalized_into_workspace_access(self) -> None:
        for path in (
            "/tmp/state.md",
            "../state.md",
            "nested/../state.md",
            "state?.md",
            "[state].md",
            "{state}.md",
            r"state\*.md",
            "nul\x00.md",
        ):
            with self.subTest(path=path):
                self.assert_safe_error(
                    "PATH_OUTSIDE_WORKSPACE",
                    lambda path=path: self.io().read_many([path]),
                )

    def test_missing_directory_invalid_utf8_and_limit_breaches_preserve_state_files(self) -> None:
        (self.workspace / "binary.md").write_bytes(b"\xff")
        (self.workspace / "large.md").write_bytes(b"0123456789")

        for paths, limits in (
            (["missing.md"], {}),
            (["nested"], {}),
            (["binary.md"], {}),
            (["large.md"], {"max_file_bytes": 5}),
            (["state.md", "nested/note.md"], {"max_total_bytes": 10}),
            (["state.md", "empty.md"], {"max_results": 1}),
        ):
            with self.subTest(paths=paths, limits=limits):
                self.assert_safe_error(
                    "STATE_IO_ERROR",
                    lambda paths=paths, limits=limits: self.io(**limits).read_many(paths),
                )

        self.assertEqual(b"0123456789", (self.workspace / "large.md").read_bytes())

    def test_escape_symlink_cannot_be_read_or_listed_as_workspace_state(self) -> None:
        outside = self.root / "outside.md"
        outside.write_text("outside\n", encoding="utf-8")
        link = self.workspace / "escaped.md"
        try:
            link.symlink_to(outside)
        except OSError as error:
            self.skipTest("symlink creation denied by operating system: %s" % error)

        self.assert_safe_error(
            "PATH_OUTSIDE_WORKSPACE",
            lambda: self.io().read_many(["escaped.md"]),
        )
        self.assertNotIn("escaped.md", self.io().list_markdown("*.md"))

    def test_fifo_cannot_be_read_as_regular_workspace_state(self) -> None:
        if not hasattr(os, "mkfifo"):
            self.skipTest("os.mkfifo is unavailable")
        fifo = self.workspace / "events.md"
        os.mkfifo(fifo)
        self.assert_safe_error(
            "STATE_IO_ERROR",
            lambda: self.io().read_many(["events.md"]),
        )
        self.assertNotIn("events.md", self.io().list_markdown("*.md"))

    def test_reference_allowlist_returns_only_authorized_role_workflow_and_package_files(self) -> None:
        allowed = (
            "CLAUDE.md",
            "agents/chief-of-staff.md",
            "skills/week-plan/SKILL.md",
            "references/ownership.yaml",
            "references/house-rules.md",
            "references/multi-business.md",
            "references/orchestration.md",
        )
        for path in allowed:
            with self.subTest(path=path):
                value = self.io().read_reference(
                    path,
                    role="chief-of-staff",
                    workflow="week-plan",
                )
                self.assertEqual(
                    {"path", "content", "sha256", "size", "mtime_ns"},
                    set(value),
                )
                self.assertEqual(path, value["path"])

    def test_reference_path_cannot_substitute_another_role_workflow_or_arbitrary_package_file(self) -> None:
        other_workflow = self.package / "skills" / "other"
        other_workflow.mkdir()
        (other_workflow / "SKILL.md").write_text("# other\n", encoding="utf-8")

        for path in (
            "agents/cfo.md",
            "skills/other/SKILL.md",
            "references/not-allowed.md",
            "../CLAUDE.md",
            "agents/../CLAUDE.md",
        ):
            with self.subTest(path=path):
                self.assert_safe_error(
                    "PATH_OUTSIDE_WORKSPACE",
                    lambda path=path: self.io().read_reference(
                        path,
                        role="chief-of-staff",
                        workflow="week-plan",
                    ),
                )

        self.assert_safe_error(
            "PATH_OUTSIDE_WORKSPACE",
            lambda: self.io().read_reference(
                "skills/week-plan/SKILL.md",
                role="chief-of-staff",
            ),
        )
        (self.package / "references" / "house-rules.md").unlink()
        self.assert_safe_error(
            "STATE_IO_ERROR",
            lambda: self.io().read_reference(
                "references/house-rules.md",
                role="chief-of-staff",
            ),
        )

    def test_allowed_reference_symlink_cannot_escape_package_root(self) -> None:
        outside = self.root / "outside.md"
        outside.write_text("outside\n", encoding="utf-8")
        reference = self.package / "references" / "house-rules.md"
        reference.unlink()
        try:
            reference.symlink_to(outside)
        except OSError as error:
            self.skipTest("symlink creation denied by operating system: %s" % error)

        self.assert_safe_error(
            "PATH_OUTSIDE_WORKSPACE",
            lambda: self.io().read_reference(
                "references/house-rules.md",
                role="chief-of-staff",
            ),
        )

    def test_reference_invalid_utf8_and_size_limit_match_state_read_failures(self) -> None:
        reference = self.package / "references" / "house-rules.md"
        reference.write_bytes(b"\xff")
        self.assert_safe_error(
            "STATE_IO_ERROR",
            lambda: self.io().read_reference(
                "references/house-rules.md",
                role="chief-of-staff",
            ),
        )

        reference.write_bytes(b"0123456789")
        self.assert_safe_error(
            "STATE_IO_ERROR",
            lambda: self.io(max_file_bytes=5).read_reference(
                "references/house-rules.md",
                role="chief-of-staff",
            ),
        )


    def test_ancestor_swap_cannot_escape_trusted_workspace_descriptor(self) -> None:
        raced = self.workspace / "raced"
        raced.mkdir()
        (raced / "state.md").write_text("inside", encoding="utf-8")
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "state.md").write_text("outside-secret", encoding="utf-8")
        moved = self.workspace / "raced-original"
        swapped = False

        def swap_before_open(relative_path: str, index: int) -> None:
            nonlocal swapped
            if relative_path == "raced/state.md" and index == 0 and not swapped:
                raced.rename(moved)
                raced.symlink_to(outside, target_is_directory=True)
                swapped = True

        reader = self.io(before_component_open=swap_before_open)
        with self.assertRaises(SafeStateError) as raised:
            reader.read_many(["raced/state.md"])
        self.assertIn(
            raised.exception.code,
            ("PATH_OUTSIDE_WORKSPACE", "STATE_IO_ERROR"),
        )
        self.assertTrue(swapped)

    def test_listing_json_byte_cap_is_exact_for_multibyte_and_escaped_names(self) -> None:
        filename = 'quote"-é.md'
        (self.workspace / filename).write_text("body", encoding="utf-8")
        encoded_size = len(
            json.dumps([filename], separators=(",", ":")).encode("utf-8")
        )

        self.assertEqual(
            [filename],
            self.io(max_total_bytes=encoded_size).list_markdown(filename),
        )
        self.assert_safe_error(
            "STATE_IO_ERROR",
            lambda: self.io(max_total_bytes=encoded_size - 1).list_markdown(filename),
        )


class GatewayReadSurfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.workspace = self.project / "founder-os"
        self.workspace.mkdir()
        self.state_file = self.workspace / "state.md"
        self.state_file.write_bytes(b"gateway state\n")
        self.package = write_packaged_root(self.root / "package")
        (self.package / "CLAUDE.md").write_text("# package\n", encoding="utf-8")
        references = self.package / "references"
        references.mkdir()
        for name in (
            "ownership.yaml",
            "house-rules.md",
            "multi-business.md",
            "orchestration.md",
        ):
            (references / name).write_text(name + "\n", encoding="utf-8")
        self.resolver = WorkspaceResolver(env={}, home=self.root / "home")
        self.store = RoleSessionStore(
            data_root=self.root / "sessions",
            packaged_root=self.package,
            clock=lambda: 1000.0,
            ttl_seconds=60,
        )
        self.gateway = Gateway(
            resolver=self.resolver,
            sessions=self.store,
            packaged_root=self.package,
            io_factory=None,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def payload(self, response, is_error=False):
        self.assertEqual(is_error, response["isError"])
        payload = response["structuredContent"]
        self.assertEqual(payload, json.loads(response["content"][0]["text"]))
        return payload

    def assert_gateway_error(self, response, code, action) -> None:
        payload = self.payload(response, is_error=True)
        self.assertEqual(code, payload["error"]["code"])
        self.assertEqual(action, payload["error"]["action"])

    def test_gateway_lifecycle_binds_reads_references_and_close_to_one_capability(self) -> None:
        workspace = self.payload(
            self.gateway.call(
                "resolve_workspace",
                {"project_dir": str(self.project)},
            )
        )
        self.assertEqual("single-business", workspace["workspace_kind"])
        session = self.payload(
            self.gateway.call(
                "open_role_session",
                {
                    "workspace_id": workspace["workspace_id"],
                    "role": "chief-of-staff",
                    "correlation_id": "corr-gateway",
                    "workflow": "week-plan",
                },
            )
        )
        capability = session["capability"]
        listed = self.payload(
            self.gateway.call(
                "list_state",
                {"capability": capability, "pattern": "*.md"},
            )
        )
        self.assertEqual({"paths": ["state.md"]}, listed)

        state_entry = {
            "path": "state.md",
            "content": "gateway state\n",
            "sha256": hashlib.sha256(b"gateway state\n").hexdigest(),
            "size": len(b"gateway state\n"),
            "mtime_ns": self.state_file.stat().st_mtime_ns,
        }
        read = self.payload(
            self.gateway.call(
                "read_state",
                {"capability": capability, "paths": ["state.md"]},
            )
        )
        self.assertEqual({"files": [state_entry]}, read)

        workflow_file = self.package / "skills" / "week-plan" / "SKILL.md"
        reference_entry = {
            "path": "skills/week-plan/SKILL.md",
            "content": "# workflow\n",
            "sha256": hashlib.sha256(b"# workflow\n").hexdigest(),
            "size": len(b"# workflow\n"),
            "mtime_ns": workflow_file.stat().st_mtime_ns,
        }
        reference = self.payload(
            self.gateway.call(
                "read_reference",
                {"capability": capability, "path": "skills/week-plan/SKILL.md"},
            )
        )
        self.assertEqual({"file": reference_entry}, reference)
        closed = self.payload(
            self.gateway.call(
                "close_role_session",
                {"capability": capability, "final_status": "completed"},
            )
        )
        self.assertEqual({"closed": True, "final_status": "completed"}, closed)
        self.assert_gateway_error(
            self.gateway.call(
                "list_state",
                {"capability": capability, "pattern": "*.md"},
            ),
            "ROLE_SESSION_INVALID",
            "Stop and return control to the main thread",
        )

    def test_gateway_forged_workspace_and_capability_return_stable_domain_actions(self) -> None:
        self.assert_gateway_error(
            self.gateway.call(
                "open_role_session",
                {
                    "workspace_id": "forged-workspace",
                    "role": "chief-of-staff",
                    "correlation_id": "corr-forged",
                },
            ),
            "WORKSPACE_UNRESOLVED",
            "Ask for the business; make no read or write",
        )
        self.assert_gateway_error(
            self.gateway.call(
                "read_state",
                {"capability": "forged-capability", "paths": ["state.md"]},
            ),
            "ROLE_SESSION_INVALID",
            "Stop and return control to the main thread",
        )

    def test_gateway_rejects_reference_not_authorized_by_the_open_session(self) -> None:
        workspace = self.payload(
            self.gateway.call(
                "resolve_workspace",
                {"project_dir": str(self.project)},
            )
        )
        session = self.payload(
            self.gateway.call(
                "open_role_session",
                {
                    "workspace_id": workspace["workspace_id"],
                    "role": "cfo",
                    "correlation_id": "corr-reference-boundary",
                },
            )
        )
        self.assert_gateway_error(
            self.gateway.call(
                "read_reference",
                {
                    "capability": session["capability"],
                    "path": "agents/chief-of-staff.md",
                },
            ),
            "PATH_OUTSIDE_WORKSPACE",
            "Refuse without retrying a modified path guess",
        )

    def test_gateway_session_without_workflow_cannot_read_a_workflow_reference(self) -> None:
        workspace = self.payload(
            self.gateway.call(
                "resolve_workspace",
                {"project_dir": str(self.project)},
            )
        )
        session = self.payload(
            self.gateway.call(
                "open_role_session",
                {
                    "workspace_id": workspace["workspace_id"],
                    "role": "chief-of-staff",
                    "correlation_id": "corr-no-workflow",
                },
            )
        )
        self.assert_gateway_error(
            self.gateway.call(
                "read_reference",
                {
                    "capability": session["capability"],
                    "path": "skills/week-plan/SKILL.md",
                },
            ),
            "PATH_OUTSIDE_WORKSPACE",
            "Refuse without retrying a modified path guess",
        )


class GatewaySchemaTests(unittest.TestCase):
    def test_all_seven_tool_schemas_require_closed_objects_and_write_precondition_oneof(self) -> None:
        schemas = {schema["name"]: schema["inputSchema"] for schema in TOOL_SCHEMAS}
        expected_required = {
            "resolve_workspace": ["project_dir"],
            "open_role_session": ["workspace_id", "role", "correlation_id"],
            "list_state": ["capability", "pattern"],
            "read_state": ["capability", "paths"],
            "read_reference": ["capability", "path"],
            "close_role_session": ["capability"],
            "write_owned_state": ["capability", "path", "content"],
        }
        self.assertEqual(set(expected_required), set(schemas))
        for name, required in expected_required.items():
            with self.subTest(name=name):
                self.assertEqual(required, schemas[name]["required"])
                self.assertFalse(schemas[name]["additionalProperties"])

        write_schema = schemas["write_owned_state"]
        self.assertIn({"required": ["expected_sha256"]}, write_schema["oneOf"])
        self.assertIn(
            {
                "properties": {"create_only": {"const": True}},
                "required": ["create_only"],
            },
            write_schema["oneOf"],
        )
