"""Tests for PromptScript output synchronization."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC_SCRIPT = REPO_ROOT / "scripts" / "sync_promptscript_outputs.py"


def load_sync_module():
    """Load the synchronization script as a test module."""
    spec = importlib.util.spec_from_file_location("sync_promptscript_outputs", SYNC_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load synchronization script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PromptScriptSyncTest(unittest.TestCase):
    """Verify managed resources cannot remain stale."""

    def test_claude_agent_adapter_drops_unsupported_mcp_servers(self):
        sync = load_sync_module()
        generated = (
            "---\n"
            "name: reviewer\n"
            "description: Review safely.\n"
            "tools:\n"
            "  [\n"
            '    "Read",\n'
            '    "Grep"\n'
            "  ]\n"
            'mcpServers: ["founder-os-state"]\n'
            "---\n"
            "Review.\n"
        ).encode("utf-8")

        adapted = sync.adapt_claude_agent_frontmatter(
            generated, "reviewer"
        ).decode("utf-8")

        self.assertIn(
            "tools: "
            "mcp__plugin_founder-os_founder-os-state__resolve_workspace, "
            "mcp__plugin_founder-os_founder-os-state__list_state, ",
            adapted,
        )
        self.assertNotIn("tools:\n", adapted)
        self.assertNotIn("Read, Grep", adapted)
        self.assertNotIn("mcpServers", adapted)

    def test_claude_portfolio_agent_gets_its_bounded_extra_tool(self):
        sync = load_sync_module()
        generated = (
            "---\n"
            "name: portfolio-manager\n"
            "description: Compare businesses.\n"
            'mcpServers: ["founder-os-state"]\n'
            "---\n"
            "Compare.\n"
        ).encode("utf-8")

        adapted = sync.adapt_claude_agent_frontmatter(
            generated, "portfolio-manager"
        ).decode("utf-8")

        self.assertIn(
            "mcp__plugin_founder-os_founder-os-state__read_portfolio_inputs",
            adapted,
        )

    def test_claude_agent_adapter_rejects_unknown_tool_shapes(self):
        sync = load_sync_module()
        generated = (
            "---\n"
            "name: reviewer\n"
            "description: Review safely.\n"
            "tools: unexpected\n"
            'mcpServers: ["founder-os-state"]\n'
            "---\n"
            "Review.\n"
        ).encode("utf-8")

        with self.assertRaisesRegex(
            ValueError, "unsupported generated Claude agent tools field"
        ):
            sync.adapt_claude_agent_frontmatter(generated, "reviewer")

    def test_claude_mcp_adapter_rejects_extra_generated_configuration(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / ".mcp.json"
            source.write_text(
                json.dumps({
                    "mcpServers": {
                        "founder-os-state": {
                            "type": "stdio",
                            "command": "python3",
                            "args": ["founder-os/mcp/founder_os_state.py"],
                        },
                        "unexpected": {
                            "type": "stdio",
                            "command": "python3",
                            "args": ["other.py"],
                        },
                    }
                }),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError, "unsupported PromptScript MCP output contract"
            ):
                sync.plugin_mcp_content(source)

    def test_generated_marker_requires_an_exact_owned_line(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prose = root / "prose.md"
            prose.write_text(
                "Do not add # promptscript-generated: to user files.\n",
                encoding="utf-8",
            )
            compiler = root / "compiler.md"
            compiler.write_text(
                "# promptscript-generated: "
                "2026-08-14T15:23:25.027Z | "
                "source: .promptscript/project.prs | target: claude\n",
                encoding="utf-8",
            )

            self.assertFalse(sync.is_generated(prose))
            self.assertTrue(sync.is_generated(compiler))

    def test_stale_codex_interface_is_reported_and_removed(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            destination = root / "destination"
            source.mkdir()
            stale = destination / "skill" / "agents" / "openai.yaml"
            stale.parent.mkdir(parents=True)
            stale.write_text(
                "# promptscript-generated:codex-skill-interface\n"
                "interface: {}\n",
                encoding="utf-8",
            )

            errors = sync.sync_tree(root, source, destination, True, "skills")

            self.assertEqual(
                errors,
                [f"skills: stale generated file {stale}"],
            )
            sync.sync_tree(root, source, destination, False, "skills")
            self.assertFalse(stale.exists())

    def test_stale_compiler_output_is_not_resynchronized(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            destination = root / "destination"
            stale_source = source / "removed.md"
            stale_source.parent.mkdir()
            stale_source.write_text("obsolete compiler output\n", encoding="utf-8")
            stale_destination = destination / "removed.md"
            stale_destination.parent.mkdir()
            stale_destination.write_text(
                "# promptscript-generated: "
                "2026-08-14T15:23:25.027Z | "
                "source: .promptscript/project.prs | target: claude\n",
                encoding="utf-8",
            )

            errors = sync.sync_tree(
                root,
                source,
                destination,
                False,
                "agents",
                expected_files=set(),
            )

            self.assertEqual(errors, [])
            self.assertFalse(stale_destination.exists())

    def test_canonical_agent_set_must_be_complete(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / ".promptscript" / "agents.prs"
            source.parent.mkdir()
            source.write_text(
                "@agents {\n"
                + "".join(
                    f"  {name}: {{\n"
                    for name in sorted(
                        sync.CANONICAL_AGENT_NAMES - {"strategist"}
                    )
                )
                + "}\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError, "invalid canonical agent declarations"
            ):
                sync.canonical_agent_files(root)

    def test_canonical_modular_agents_are_complete_and_body_resolves(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            promptscript = root / ".promptscript"
            agents = promptscript / "agents"
            agents.mkdir(parents=True)
            names = sorted(sync.CANONICAL_AGENT_NAMES)
            (promptscript / "agents.prs").write_text(
                '@meta { id: "agents" syntax: "1.5.0" }\n'
                + "".join(f"@use ./agents/{name}\n" for name in names),
                encoding="utf-8",
            )
            for name in names:
                (agents / f"{name}.prs").write_text(
                    "@meta { id: \"agent\" syntax: \"1.5.0\" }\n"
                    "@agents {\n"
                    f"  {name}: {{\n"
                    f'    description: "{name}"\n'
                    '    content: """\n'
                    f"      Body for {name}.\n"
                    '    """\n'
                    "  }\n"
                    "}\n",
                    encoding="utf-8",
                )

            self.assertEqual(
                sync.canonical_agent_files(root),
                {Path(f"{name}.md") for name in names},
            )
            self.assertEqual(
                sync.canonical_agent_body(root, "strategist"),
                "Body for strategist.\n",
            )

    def test_canonical_agent_directives_ignore_triple_quoted_content(self):
        sync = load_sync_module()
        source = (
            '@meta { id: "agents" syntax: "1.5.0" }\n'
            '@agents {\n'
            '  strategist: {\n'
            '    description: "Contains source-like text"\n'
            '    content: """\n'
            '      @use ./agents/rogue\n'
            '      strategist: {\n'
            '      }\n'
            '    """\n'
            '  }\n'
            '}\n'
        )

        self.assertEqual(
            sync.canonical_agent_directives(source),
            (["strategist"], []),
        )

        crlf_source = (
            '@meta { id: "agents" syntax: "1.5.0" }\r\n'
            "@use ./agents/strategist\r\n"
        )
        self.assertEqual(
            sync.canonical_agent_directives(crlf_source),
            ([], ["strategist"]),
        )

    def test_canonical_agent_body_supports_valid_promptscript_layouts(self):
        sync = load_sync_module()
        layouts = {
            "double-quoted-key": (
                '  "strategist": {\n'
                '    content: "Inline body."\n'
                "    description: \"x\"\n"
                "  }\n"
            ),
            "one-line": (
                '  strategist: { description: "x" '
                'content: "One line body." }\n'
            ),
            "single-quoted-key": (
                "  'strategist': {\n"
                '    content: "Single quoted body."\n'
                "    description: \"x\"\n"
                "  }\n"
            ),
            "bare-content": (
                "  strategist: {\n"
                "    description: \"x\"\n"
                "    content: Body\n"
                "  }\n"
            ),
            "indented": (
                "    strategist: {\n"
                '      description: "x"\n'
                '      content: """\n'
                "        Indented body.\n"
                '      """\n'
                "    }\n"
            ),
            "content-first": (
                "  strategist: {\n"
                '    content: """\n'
                "      First body.\n"
                '    """\n'
                '    description: "x"\n'
                "  }\n"
            ),
            "following-line": (
                "  strategist: {\n"
                "    description: \"x\"\n"
                "    content:\n"
                '    """\n'
                "      Following line body.\n"
                '    """\n'
                "  }\n"
            ),
            "trailing-comma": (
                "  strategist: {\n"
                '    content: "Comma body.",\n'
                '    description: "x",\n'
                "  }\n"
            ),
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            promptscript = root / ".promptscript"
            agents = promptscript / "agents"
            agents.mkdir(parents=True)
            names = sorted(sync.CANONICAL_AGENT_NAMES)
            (promptscript / "agents.prs").write_text(
                '@meta { id: "agents" syntax: "1.5.0" }\n'
                + "".join(f"@use ./agents/{name}\n" for name in names),
                encoding="utf-8",
            )
            for name, declaration in layouts.items():
                for agent_name in names:
                    if agent_name == "strategist":
                        agent_declaration = declaration
                    else:
                        agent_declaration = (
                            f"  {agent_name}: {{\n"
                            f'    description: "{agent_name}"\n'
                            '    content: """\n'
                            f"      Body for {agent_name}.\n"
                            '    """\n'
                            "  }\n"
                        )
                    fragment = (
                        '@meta { id: "agent" syntax: "1.5.0" }\n'
                        "@agents {\n"
                        + agent_declaration
                        + "}\n"
                    )
                    (agents / f"{agent_name}.prs").write_text(
                        fragment,
                        encoding="utf-8",
                    )
                expected = {
                    "double-quoted-key": "Inline body.\n",
                    "one-line": "One line body.\n",
                    "single-quoted-key": "Single quoted body.\n",
                    "bare-content": "Body\n",
                    "indented": "Indented body.\n",
                    "content-first": "First body.\n",
                    "following-line": "Following line body.\n",
                    "trailing-comma": "Comma body.\n",
                }[name]

                self.assertEqual(
                    sync.canonical_agent_body(root, "strategist"),
                    expected,
                )

    def test_canonical_modular_agent_rejects_duplicate_fragment_definitions(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            promptscript = root / ".promptscript"
            agents = promptscript / "agents"
            agents.mkdir(parents=True)
            names = sorted(sync.CANONICAL_AGENT_NAMES)
            (promptscript / "agents.prs").write_text(
                '@meta { id: "agents" syntax: "1.5.0" }\n'
                + "".join(f"@use ./agents/{name}\n" for name in names),
                encoding="utf-8",
            )
            for name in names:
                declaration = (
                    f"  {name}: {{\n"
                    f'    description: "{name}"\n'
                    '    content: """\n'
                    f"      Body for {name}.\n"
                    '    """\n'
                    "  }\n"
                )
                content = (
                    '@meta { id: "agent" syntax: "1.5.0" }\n'
                    "@agents {\n"
                    + declaration
                    + "}\n"
                )
                if name == "strategist":
                    content += "@agents {\n" + declaration + "}\n"
                (agents / f"{name}.prs").write_text(
                    content,
                    encoding="utf-8",
                )

            with self.assertRaisesRegex(
                ValueError, "invalid canonical agent fragment"
            ):
                sync.canonical_agent_files(root)

    def test_source_only_skill_files_are_not_expected_compiler_outputs(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = root / ".promptscript" / "skills" / "example"
            (skill / "agents").mkdir(parents=True)
            (skill / "SKILL.md").write_text("skill\n", encoding="utf-8")
            (skill / "agents" / "openai.yaml").write_text(
                "interface: {}\n",
                encoding="utf-8",
            )
            (skill / "README.md").write_text("source notes\n", encoding="utf-8")

            expected = sync.canonical_skill_files(root)

        self.assertEqual(
            expected,
            {
                Path("example/SKILL.md"),
                Path("example/agents/openai.yaml"),
            },
        )

    def test_unmarked_codex_interface_is_preserved(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            destination = root / "destination"
            source.mkdir()
            custom = destination / "skill" / "agents" / "openai.yaml"
            custom.parent.mkdir(parents=True)
            custom.write_text("interface: {custom: true}\n", encoding="utf-8")

            self.assertEqual(
                sync.sync_tree(root, source, destination, True, "skills"),
                [],
            )
            self.assertEqual(
                sync.sync_tree(root, source, destination, False, "skills"),
                [],
            )
            self.assertEqual(
                custom.read_text(encoding="utf-8"),
                "interface: {custom: true}\n",
            )

    def test_synced_codex_interface_gets_an_ownership_marker(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            destination = root / "destination"
            interface = source / "skill" / "agents" / "openai.yaml"
            interface.parent.mkdir(parents=True)
            interface.write_text("interface: {}\n", encoding="utf-8")

            self.assertEqual(
                sync.sync_tree(root, source, destination, False, "skills"),
                [],
            )

            copied = destination / "skill" / "agents" / "openai.yaml"
            self.assertEqual(
                copied.read_text(encoding="utf-8"),
                "# promptscript-generated:codex-skill-interface\n"
                "interface: {}\n",
            )

    def test_source_symlink_is_refused(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            destination = root / "destination"
            source.mkdir()
            secret = root / "secret.txt"
            secret.write_text("secret\n", encoding="utf-8")
            linked = source / "linked.txt"
            linked.symlink_to(secret)

            errors = sync.sync_tree(
                root, source, destination, False, "skills"
            )

            self.assertEqual(
                errors,
                [f"skills: symlink source refused {linked}"],
            )
            self.assertFalse(destination.exists())

    def test_symlinked_source_root_cannot_trigger_stale_cleanup(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_source = root / "real-source"
            real_source.mkdir()
            source = root / "source"
            source.symlink_to(real_source, target_is_directory=True)
            destination = root / "destination"
            stale = destination / "skill" / "agents" / "openai.yaml"
            stale.parent.mkdir(parents=True)
            stale.write_text(
                "# promptscript-generated:codex-skill-interface\n"
                "interface: {}\n",
                encoding="utf-8",
            )

            errors = sync.sync_tree(
                root, source, destination, False, "skills"
            )

            self.assertEqual(
                errors,
                [f"skills: symlink source refused {source}"],
            )
            self.assertTrue(stale.is_file())

    def test_nested_source_symlink_cannot_trigger_stale_cleanup(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            elsewhere = root / "elsewhere"
            elsewhere.mkdir()
            linked = source / "skill"
            linked.symlink_to(elsewhere, target_is_directory=True)
            destination = root / "destination"
            stale = destination / "skill" / "agents" / "openai.yaml"
            stale.parent.mkdir(parents=True)
            stale.write_text(
                "# promptscript-generated:codex-skill-interface\n"
                "interface: {}\n",
                encoding="utf-8",
            )

            errors = sync.sync_tree(
                root, source, destination, False, "skills"
            )

            self.assertEqual(
                errors,
                [f"skills: symlink source refused {linked}"],
            )
            self.assertTrue(stale.is_file())

    def test_unmarked_file_at_generated_path_is_a_conflict(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            destination = root / "destination"
            generated = source / "skill" / "agents" / "openai.yaml"
            generated.parent.mkdir(parents=True)
            generated.write_text("interface: {}\n", encoding="utf-8")
            custom = destination / "skill" / "agents" / "openai.yaml"
            custom.parent.mkdir(parents=True)
            custom.write_text("interface: {custom: true}\n", encoding="utf-8")

            errors = sync.sync_tree(
                root, source, destination, False, "skills"
            )

            self.assertEqual(
                errors,
                [f"skills: unmarked destination conflict {custom}"],
            )
            self.assertEqual(
                custom.read_text(encoding="utf-8"),
                "interface: {custom: true}\n",
            )

    def test_sync_plan_restores_every_file_after_a_write_failure(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "a.txt"
            second = root / "b.txt"
            first.write_bytes(b"old-a")
            second.write_bytes(b"old-b")
            plan = sync.SyncPlan()
            plan.add_write(first, b"new-a")
            plan.add_write(second, b"new-b")
            original_write = sync.write_generated
            failed = False

            def flaky_write(path, content):
                nonlocal failed
                if path == second and not failed:
                    failed = True
                    raise OSError("simulated failure")
                original_write(path, content)

            with mock.patch.object(
                sync, "write_generated", side_effect=flaky_write
            ):
                with self.assertRaisesRegex(OSError, "simulated failure"):
                    plan.apply()

            self.assertEqual(first.read_bytes(), b"old-a")
            self.assertEqual(second.read_bytes(), b"old-b")

    def test_sync_plan_restores_removed_files_after_a_delete_failure(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "a.txt"
            second = root / "b.txt"
            first.write_bytes(b"old-a")
            second.write_bytes(b"old-b")
            plan = sync.SyncPlan()
            plan.add_removal(first)
            plan.add_removal(second)
            original_unlink = Path.unlink
            failed = False

            def flaky_unlink(path, *args, **kwargs):
                nonlocal failed
                if path == second and not failed:
                    failed = True
                    raise OSError("simulated delete failure")
                return original_unlink(path, *args, **kwargs)

            with mock.patch.object(Path, "unlink", flaky_unlink):
                with self.assertRaisesRegex(
                    OSError, "simulated delete failure"
                ):
                    plan.apply()

            self.assertEqual(first.read_bytes(), b"old-a")
            self.assertEqual(second.read_bytes(), b"old-b")

    def test_adaptation_error_prevents_every_planned_write(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            destination = root / "destination"
            interface = source / "a" / "agents" / "openai.yaml"
            interface.parent.mkdir(parents=True)
            interface.write_text("interface: {}\n", encoding="utf-8")
            skill = source / "z" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: z\n---\nbody\n", encoding="utf-8")

            errors = sync.sync_tree(
                root, source, destination, False, "skills"
            )

            self.assertTrue(
                any("cannot adapt" in error for error in errors),
                errors,
            )
            self.assertFalse(destination.exists())


class SingletonOwnershipTest(unittest.TestCase):
    def _write_canonical_sources(self, root):
        promptscript = root / ".promptscript"
        (promptscript / "skills").mkdir(parents=True)
        (promptscript / "project.prs").write_text(
            "@identity {}\n",
            encoding="utf-8",
        )
        (promptscript / "agents.prs").write_text(
            "@agents {}\n",
            encoding="utf-8",
        )

    def _write_manifest(self, plugin, value):
        plugin.mkdir(parents=True, exist_ok=True)
        (plugin / ".promptscript-generated.json").write_text(
            json.dumps(value),
            encoding="utf-8",
        )

    def test_exact_singleton_ownership_is_accepted(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            plugin = Path(temporary) / "founder-os"
            self._write_manifest(plugin, sync.SINGLETON_OWNERSHIP)

            managed = sync.load_singleton_ownership(plugin)

        self.assertEqual(managed, set(sync.SINGLETON_OWNERSHIP["managed"]))

    def test_missing_singleton_ownership_stops_before_writes(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "founder-os" / "CLAUDE.md"
            destination.parent.mkdir(parents=True)
            destination.write_text("maintainer content\n", encoding="utf-8")
            self._write_canonical_sources(root)

            errors = sync.sync_plugin(
                root,
                False,
                source_validated=True,
            )

            self.assertTrue(
                any("missing or invalid singleton ownership" in error
                    for error in errors),
                errors,
            )
            self.assertEqual(
                destination.read_text(encoding="utf-8"),
                "maintainer content\n",
            )

    def test_missing_canonical_source_stops_before_writes(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "founder-os" / "CLAUDE.md"
            destination.parent.mkdir(parents=True)
            destination.write_text("maintainer content\n", encoding="utf-8")
            self._write_manifest(
                root / "founder-os",
                sync.SINGLETON_OWNERSHIP,
            )

            errors = sync.sync_plugin(
                root,
                False,
                source_validated=True,
            )

            self.assertTrue(
                any("missing canonical source" in error for error in errors),
                errors,
            )
            self.assertEqual(
                destination.read_text(encoding="utf-8"),
                "maintainer content\n",
            )

    def test_promptscript_fragment_symlink_stops_before_writes(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            promptscript = root / ".promptscript"
            promptscript.mkdir()
            outside = root / "outside.prs"
            outside.write_text("@identity {}\n", encoding="utf-8")
            (promptscript / "context.prs").symlink_to(outside)
            self._write_canonical_sources(root)
            self._write_manifest(
                root / "founder-os",
                sync.SINGLETON_OWNERSHIP,
            )
            destination = root / "founder-os" / "CLAUDE.md"
            destination.write_text("maintainer content\n", encoding="utf-8")

            errors = sync.sync_plugin(root, False, source_validated=True)

            self.assertEqual(
                errors,
                [f"plugin: symlink source refused {promptscript / 'context.prs'}"],
            )
            self.assertEqual(
                destination.read_text(encoding="utf-8"),
                "maintainer content\n",
            )

    def test_sync_requires_prior_strict_source_validation(self):
        sync = load_sync_module()

        errors = sync.sync_plugin(Path("/not-used"), False)

        self.assertEqual(
            errors,
            ["plugin: canonical PromptScript source validation is required"],
        )

    def test_failed_strict_source_validation_is_rejected(self):
        sync = load_sync_module()
        result = mock.Mock(
            returncode=1,
            stdout="validation failed\n",
            stderr="",
        )
        with mock.patch.object(sync.subprocess, "run", return_value=result):
            with self.assertRaisesRegex(
                ValueError,
                "canonical PromptScript source failed strict validation",
            ):
                sync.validate_promptscript_source(Path("/project"))

    def test_malformed_singleton_ownership_is_rejected(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            plugin = Path(temporary) / "founder-os"
            plugin.mkdir()
            (plugin / ".promptscript-generated.json").write_text(
                "{not json",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError, "missing or invalid singleton ownership"
            ):
                sync.load_singleton_ownership(plugin)

    def test_altered_singleton_ownership_is_rejected(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            plugin = Path(temporary) / "founder-os"
            altered = {
                **sync.SINGLETON_OWNERSHIP,
                "managed": ["CLAUDE.md"],
            }
            self._write_manifest(plugin, altered)

            with self.assertRaisesRegex(
                ValueError, "unexpected singleton ownership"
            ):
                sync.load_singleton_ownership(plugin)

    @unittest.skipIf(os.name == "nt", "symlink behavior differs on Windows")
    def test_symlinked_singleton_ownership_is_rejected(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plugin = root / "founder-os"
            plugin.mkdir()
            outside = root / "ownership.json"
            outside.write_text(
                json.dumps(sync.SINGLETON_OWNERSHIP),
                encoding="utf-8",
            )
            (plugin / ".promptscript-generated.json").symlink_to(outside)

            with self.assertRaisesRegex(
                ValueError, "symlink destination refused"
            ):
                sync.load_singleton_ownership(plugin)


class ClaudeHookAdaptationTest(unittest.TestCase):
    def _generated_hooks(self):
        preamble = (
            'if [ -z "${CLAUDE_PROJECT_DIR:-}" ]; then printf \'%s\\n\' '
            "'PromptScript claude hook requires non-empty "
            "CLAUDE_PROJECT_DIR.' >&2; exit 1; fi; "
            'cd "${CLAUDE_PROJECT_DIR}" && '
        )

        def group(matcher, file_name, marker, status):
            return [{
                "matcher": matcher,
                "hooks": [{
                    "type": "command",
                    "command": (
                        f"{preamble}python3 founder-os/hooks/{file_name} "
                        f"# promptscript-generated:{marker}"
                    ),
                    "timeout": 10,
                    "statusMessage": status,
                }],
            }]

        return {
            "hooks": {
                "SessionStart": group(
                    "startup|resume|clear|compact",
                    "session-context.py",
                    "session-context",
                    "Loading Founder OS context",
                ),
                "SubagentStart": group(
                    ".*",
                    "record-agent.py",
                    "record-agent",
                    "Recording Founder OS decision role",
                ),
                "PreToolUse": group(
                    "^(Read|Write|Edit|NotebookEdit|Glob|Grep|Bash|WebFetch|"
                    "WebSearch|apply_patch|Task|Agent|mcp__.*)$",
                    "ownership-guard.py",
                    "ownership-guard",
                    "Checking Founder OS boundaries",
                ),
            }
        }

    def test_claude_hook_adapter_requires_the_exact_compiler_contract(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "settings.json"
            generated = self._generated_hooks()
            generated["hooks"]["SessionStart"][0]["hooks"][0][
                "command"
            ] = "true"
            source.write_text(json.dumps(generated), encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError, "unsupported PromptScript Claude SessionStart hook"
            ):
                sync.plugin_hooks_content(source)

    def test_claude_hook_adapter_emits_plugin_root_commands(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "settings.json"
            source.write_text(
                json.dumps(self._generated_hooks()), encoding="utf-8"
            )

            adapted = json.loads(sync.plugin_hooks_content(source))

        serialized = json.dumps(adapted)
        self.assertNotIn("CLAUDE_PROJECT_DIR", serialized)
        self.assertNotIn("timeout", serialized)
        self.assertIn(
            '${CLAUDE_PLUGIN_ROOT}/hooks/ownership-guard.py',
            serialized,
        )
        self.assertNotIn(
            "matcher", adapted["hooks"]["SubagentStart"][0]
        )


class CodexHookAdaptationTest(unittest.TestCase):
    def _generated_hooks(self):
        guard = (
            "PROMPTSCRIPT_PROJECT_ROOT=\"$(git rev-parse --show-toplevel "
            "2>/dev/null)\" || { printf '%s\\n' 'PromptScript codex hook "
            "requires a Git worktree project root.' >&2; exit 1; }; case "
            "\"$PROMPTSCRIPT_PROJECT_ROOT\" in *[![:space:]]*) ;; *) printf "
            "'%s\\n' 'PromptScript codex hook requires a Git worktree "
            "project root.' >&2; exit 1 ;; esac; cd "
            "\"$PROMPTSCRIPT_PROJECT_ROOT\" && "
        )
        windows_guard = (
            "$promptscriptProjectRoot = git rev-parse --show-toplevel "
            "2>$null; if ($LASTEXITCODE -ne 0 -or "
            "[string]::IsNullOrWhiteSpace($promptscriptProjectRoot)) { "
            "[Console]::Error.WriteLine('PromptScript codex hook requires a "
            "Git worktree project root.'); exit 1 }; Set-Location "
            "-LiteralPath $promptscriptProjectRoot -ErrorAction Stop; "
        )

        def group(matcher, file_name, marker, status):
            value = {
                "hooks": [{
                    "type": "command",
                    "command": (
                        guard
                        + f"python3 founder-os/hooks/{file_name} "
                        f"# promptscript-generated:{marker}"
                    ),
                    "commandWindows": (
                        windows_guard
                        + "& 'python3' "
                        f"'founder-os/hooks/{file_name}' "
                        f"# promptscript-generated:{marker}"
                    ),
                    "statusMessage": status,
                }],
            }
            if matcher is not None:
                value["matcher"] = matcher
            return [value]

        return {
            "hooks": {
                "SessionStart": group(
                    "startup|resume|clear|compact",
                    "session-context.py",
                    "session-context",
                    "Loading Founder OS context",
                ),
                "SubagentStart": group(
                    None,
                    "record-agent.py",
                    "record-agent",
                    "Recording Founder OS decision role",
                ),
                "PreToolUse": group(
                    "^(Read|Write|Edit|NotebookEdit|Glob|Grep|Bash|WebFetch|"
                    "WebSearch|apply_patch|Task|Agent|mcp__.*)$",
                    "ownership-guard.py",
                    "ownership-guard",
                    "Checking Founder OS boundaries",
                ),
            },
        }

    def _adapt(self, root):
        source = root / "hooks.json"
        source.write_text(
            json.dumps(self._generated_hooks()),
            encoding="utf-8",
        )
        return json.loads(
            load_sync_module().plugin_codex_hooks_content(source)
        )

    def test_codex_hooks_use_supported_root_without_git_preamble(self):
        with tempfile.TemporaryDirectory() as temporary:
            adapted = self._adapt(Path(temporary))

        serialized = json.dumps(adapted)
        self.assertNotIn("git rev-parse", serialized)
        self.assertNotIn("PROMPTSCRIPT_PROJECT_ROOT", serialized)
        self.assertNotIn("CODEX_PLUGIN_ROOT", serialized)
        self.assertIn("${PLUGIN_ROOT}/hooks/session-context.py", serialized)
        self.assertIn("$env:PLUGIN_ROOT", serialized)
        self.assertIn("& 'python'", serialized)

    @unittest.skipIf(os.name == "nt", "POSIX command probe")
    def test_codex_hook_runs_outside_a_git_worktree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            adapted = self._adapt(root)
            plugin = root / "installed plugin"
            hooks = plugin / "hooks"
            hooks.mkdir(parents=True)
            (hooks / "session-context.py").write_text(
                "print('hook-ok')\n",
                encoding="utf-8",
            )
            outside_git = root / "business"
            outside_git.mkdir()
            command = adapted["hooks"]["SessionStart"][0]["hooks"][0][
                "command"
            ]
            environment = {**os.environ, "PLUGIN_ROOT": str(plugin)}

            result = subprocess.run(
                ["/bin/sh", "-c", command],
                cwd=outside_git,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "hook-ok")

    def test_codex_hook_adapter_rejects_noop_commands(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "hooks.json"
            generated = self._generated_hooks()
            generated["hooks"]["SessionStart"][0]["hooks"][0][
                "command"
            ] = "true"
            source.write_text(
                json.dumps(generated),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "unsupported PromptScript Codex SessionStart hook command",
            ):
                sync.plugin_codex_hooks_content(source)

    def test_codex_hook_adapter_requires_every_event(self):
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "hooks.json"
            generated = self._generated_hooks()
            del generated["hooks"]["PreToolUse"]
            source.write_text(json.dumps(generated), encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError, "unexpected Codex hook events"
            ):
                sync.plugin_codex_hooks_content(source)
