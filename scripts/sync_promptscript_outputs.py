#!/usr/bin/env python3
"""Sync PromptScript's Claude build into the dual-host plugin layout."""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Optional


GENERATED_MARKER = "# promptscript-generated:"
CODEX_INTERFACE_MARKER = f"{GENERATED_MARKER}codex-skill-interface"
COMPILER_MARKER_RE = re.compile(
    r"^# promptscript-generated: "
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z "
    r"\| source: \.promptscript/project\.prs \| target: claude$"
)
MARKER_TIMESTAMP_RE = re.compile(
    rb"(?m)^((?:<!-- PromptScript |# promptscript-generated: ))"
    rb"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z(?= \|)"
)
CLAUDE_TOOL_PREFIX = "mcp__plugin_founder-os_founder-os-state__"
COMMON_ROLE_ACTIONS = (
    "resolve_workspace",
    "list_state",
    "read_state",
    "read_reference",
    "write_owned_state",
    "close_role_session",
)
CANONICAL_AGENT_NAMES = frozenset({
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
})
SINGLETON_OWNERSHIP = {
    "schema": 1,
    "managed": [
        ".mcp.json",
        "CLAUDE.md",
        "hooks/codex-hooks.json",
        "hooks/hooks.json",
    ],
}


def is_generated(path: Path) -> bool:
    """Return whether a file carries PromptScript's ownership marker."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[:50]
    except (OSError, UnicodeDecodeError):
        return False
    return any(
        line == CODEX_INTERFACE_MARKER or COMPILER_MARKER_RE.fullmatch(line)
        for line in lines
    )


def files_under(path: Path) -> set[Path]:
    """Return file paths relative to a directory."""
    if not path.is_dir():
        return set()
    return {file.relative_to(path) for file in path.rglob("*") if file.is_file()}


def symlinks_under(path: Path) -> list[Path]:
    """Return symlink entries without following their targets."""
    if not path.is_dir():
        return []
    return sorted(entry for entry in path.rglob("*") if entry.is_symlink())


def load_singleton_ownership(plugin: Path) -> set[str]:
    """Load the exact list of markerless generated package adapters."""
    ownership_path = plugin / ".promptscript-generated.json"
    if has_symlink_component(ownership_path, plugin):
        raise ValueError(f"symlink destination refused {ownership_path}")
    try:
        ownership = json.loads(ownership_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"missing or invalid singleton ownership {ownership_path}"
        ) from exc
    if ownership != SINGLETON_OWNERSHIP:
        raise ValueError(f"unexpected singleton ownership {ownership_path}")
    return set(ownership["managed"])


def comparable_content(content: bytes) -> bytes:
    """Ignore compiler timestamps when comparing generated outputs."""
    return MARKER_TIMESTAMP_RE.sub(rb"\1<timestamp>", content)


def has_symlink_component(path: Path, stop: Path) -> bool:
    """Return whether a destination path crosses a symlink before its root."""
    current = path.absolute()
    stop = stop.absolute()
    while True:
        if current.is_symlink():
            return True
        if current == stop or current.parent == current:
            return False
        current = current.parent


def write_generated(path: Path, content: bytes) -> None:
    """Replace a generated file atomically without following its old inode."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        temporary_name = ""
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary_name:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


class SyncPlan:
    """Apply all synchronized writes and removals as one rollback-safe batch."""

    def __init__(self) -> None:
        self.writes: dict[Path, bytes] = {}
        self.removals: set[Path] = set()

    def add_write(self, path: Path, content: bytes) -> None:
        """Schedule one file replacement."""
        self.removals.discard(path)
        self.writes[path] = content

    def add_removal(self, path: Path) -> None:
        """Schedule one generated-file removal."""
        if path not in self.writes:
            self.removals.add(path)

    def apply(self) -> None:
        """Apply the batch and restore every touched file after a failure."""
        touched = sorted(set(self.writes) | self.removals)
        originals: dict[Path, Optional[bytes]] = {
            path: path.read_bytes() if path.is_file() else None
            for path in touched
        }
        try:
            for path in sorted(self.writes):
                write_generated(path, self.writes[path])
            for path in sorted(self.removals):
                path.unlink()
        except OSError as exc:
            rollback_errors = []
            for path in reversed(touched):
                try:
                    original = originals[path]
                    if original is None:
                        try:
                            path.unlink()
                        except FileNotFoundError:
                            pass
                    else:
                        write_generated(path, original)
                except OSError as rollback_exc:
                    rollback_errors.append(f"{path}: {rollback_exc}")
            if rollback_errors:
                raise OSError(
                    f"{exc}; rollback also failed: {'; '.join(rollback_errors)}"
                ) from exc
            raise


def adapt_claude_agent_frontmatter(content: bytes, agent_name: str) -> bytes:
    """Adapt portable agent metadata to Claude's supported plugin fields."""
    text = content.decode("utf-8")
    match = re.search(
        r"(?m)^tools:\n(?P<block>  \[\n(?:    \"[^\"]+\",?\n)+  \]\n)",
        text,
    )
    if match is not None:
        text = text[: match.start()] + text[match.end() :]
    if re.search(r"(?m)^tools:", text):
        raise ValueError("unsupported generated Claude agent tools field")
    actions = list(COMMON_ROLE_ACTIONS)
    if agent_name == "portfolio-manager":
        actions.insert(4, "read_portfolio_inputs")
    tools = ", ".join(f"{CLAUDE_TOOL_PREFIX}{action}" for action in actions)
    description = re.search(r"(?m)^description: .+\n", text)
    if description is None:
        raise ValueError("generated Claude agent is missing description")
    text = text[: description.end()] + f"tools: {tools}\n" + text[description.end() :]
    text, removed = re.subn(
        r'(?m)^mcpServers: \["founder-os-state"\]\n',
        "",
        text,
        count=1,
    )
    if removed != 1 or re.search(r"(?m)^mcpServers:", text):
        raise ValueError("unsupported generated Claude agent MCP field")
    return text.encode("utf-8")


def with_source_body(generated: bytes, source_body: str) -> bytes:
    """Keep PromptScript metadata while preserving the source procedure text."""
    text = generated.decode("utf-8")
    match = re.match(r"^(---\n.*?\n---)\n", text, re.S)
    if match is None:
        raise ValueError("generated Markdown file is missing frontmatter")
    body = source_body.rstrip("\n") + "\n"
    return (match.group(1) + "\n" + body).encode("utf-8")


def canonical_agent_sources(root: Path) -> dict[str, Path]:
    """Return each canonical agent name and the source file that defines it."""
    promptscript_root = root / ".promptscript"
    entry_path = promptscript_root / "agents.prs"
    if has_symlink_component(entry_path, promptscript_root):
        raise ValueError(f"symlink source refused: {entry_path}")
    source = entry_path.read_text(encoding="utf-8")

    direct_names, imported_names = canonical_agent_directives(source)
    if direct_names and imported_names:
        raise ValueError(f"mixed canonical agent declarations: {entry_path}")

    if direct_names:
        if len(direct_names) != len(set(direct_names)):
            raise ValueError(f"duplicate canonical agent declarations: {entry_path}")
        sources = {name: entry_path for name in direct_names}
    else:
        if len(imported_names) != len(set(imported_names)):
            raise ValueError(f"duplicate canonical agent imports: {entry_path}")
        agents_dir = promptscript_root / "agents"
        sources = {}
        for name in imported_names:
            source_path = agents_dir / f"{name}.prs"
            if has_symlink_component(source_path, promptscript_root):
                raise ValueError(f"symlink source refused: {source_path}")
            if not source_path.is_file():
                raise ValueError(f"missing canonical agent fragment: {source_path}")
            fragment = source_path.read_text(encoding="utf-8")
            fragment_direct, fragment_imports = canonical_agent_directives(
                fragment
            )
            if fragment_imports or fragment_direct != [name]:
                raise ValueError(
                    f"invalid canonical agent fragment: {source_path}"
                )
            sources[name] = source_path

    if set(sources) != CANONICAL_AGENT_NAMES:
        raise ValueError(f"invalid canonical agent declarations: {entry_path}")
    return sources


def canonical_agent_directives(source: str) -> tuple[list[str], list[str]]:
    """Read top-level agent declarations while ignoring triple-quoted content."""
    direct_names = [name for name, _, _, _ in canonical_agent_blocks(source)]
    masked = mask_promptscript_strings(source)
    imported_names = []
    for start, end, _ in promptscript_lines(masked):
        line = masked[start:end].rstrip("\r\n")
        imported_match = re.fullmatch(
            r"[ \t]*@use\s+\./agents/([a-z0-9-]+)(?:\.prs)?[ \t]*",
            line,
        )
        if imported_match:
            imported_names.append(imported_match.group(1))
    return direct_names, imported_names


def mask_promptscript_strings(source: str) -> str:
    """Mask strings and comments while preserving braces and line positions."""
    chars = list(source)
    index = 0
    in_comment = False
    in_quote: Optional[str] = None
    in_triple = False
    while index < len(source):
        if in_comment:
            if source[index] == "\n":
                in_comment = False
            else:
                chars[index] = " "
            index += 1
            continue
        if in_triple:
            if source.startswith('"""', index):
                chars[index : index + 3] = [" ", " ", " "]
                index += 3
                in_triple = False
            else:
                if source[index] != "\n":
                    chars[index] = " "
                index += 1
            continue
        if in_quote is not None:
            if source[index] == "\\":
                chars[index] = " "
                if index + 1 < len(source) and source[index + 1] != "\n":
                    chars[index + 1] = " "
                    index += 2
                else:
                    index += 1
            elif source[index] == in_quote:
                chars[index] = " "
                in_quote = None
                index += 1
            elif source[index] == "\n":
                in_quote = None
                index += 1
            else:
                chars[index] = " "
                index += 1
            continue
        if source.startswith('"""', index):
            chars[index : index + 3] = [" ", " ", " "]
            index += 3
            in_triple = True
        elif source[index] in {'"', "'"}:
            chars[index] = " "
            in_quote = source[index]
            index += 1
        elif source[index] == "#":
            chars[index] = " "
            in_comment = True
            index += 1
        else:
            index += 1
    return "".join(chars)


def promptscript_lines(source: str) -> list[tuple[int, int, int]]:
    """Return line ranges and brace depth at each line's start."""
    lines: list[tuple[int, int, int]] = []
    depth = 0
    line_start = 0
    line_depth = 0
    for index, character in enumerate(source):
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
        elif character == "\n":
            lines.append((line_start, index + 1, line_depth))
            line_start = index + 1
            line_depth = depth
    if line_start < len(source):
        lines.append((line_start, len(source), line_depth))
    return lines


def matching_brace(source: str, opening: int, base_depth: int) -> int:
    """Return the closing brace for an object opened at ``opening``."""
    depth = base_depth + 1
    for index in range(opening + 1, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == base_depth:
                return index
    return -1


def promptscript_tokens(
    source: str,
    start: int = 0,
    end: Optional[int] = None,
) -> list[tuple[str, str, int, int]]:
    """Tokenize structural PromptScript values without parsing the full AST."""
    limit = len(source) if end is None else end
    tokens: list[tuple[str, str, int, int]] = []
    index = start
    while index < limit:
        character = source[index]
        if character.isspace():
            index += 1
            continue
        if character == "#":
            newline = source.find("\n", index, limit)
            index = limit if newline < 0 else newline + 1
            continue
        if source.startswith('"""', index):
            closing = source.find('"""', index + 3, limit)
            if closing < 0:
                tokens.append(("triple", source[index + 3 : limit], index, limit))
                break
            tokens.append(
                ("triple", source[index + 3 : closing], index, closing + 3)
            )
            index = closing + 3
            continue
        if character in {'"', "'"}:
            quote = character
            closing = index + 1
            while closing < limit:
                if source[closing] == "\\":
                    closing += 2
                    continue
                if source[closing] == quote:
                    break
                closing += 1
            token_end = min(closing + 1, limit)
            raw = source[index:token_end]
            try:
                value = ast.literal_eval(raw)
            except (SyntaxError, ValueError):
                value = raw[1:-1]
            if not isinstance(value, str):
                value = raw
            tokens.append(("string", value, index, token_end))
            index = token_end
            continue
        if character.isalnum() or character in "_-./$":
            token_end = index + 1
            while token_end < limit and (
                source[token_end].isalnum()
                or source[token_end] in "_-./$"
            ):
                token_end += 1
            tokens.append(
                ("word", source[index:token_end], index, token_end)
            )
            index = token_end
            continue
        tokens.append(("symbol", character, index, index + 1))
        index += 1
    return tokens


def canonical_agent_blocks(
    source: str,
) -> list[tuple[str, int, int, int]]:
    """Return canonical agent names and their source block boundaries."""
    masked = mask_promptscript_strings(source)
    blocks: list[tuple[str, int, int, int]] = []
    lines = promptscript_lines(masked)
    for agents_match in re.finditer(
        r"(?m)^[ \t]*@agents[ \t]*\{", masked
    ):
        agents_line = next(
            (
                line
                for line in lines
                if line[0] <= agents_match.start() < line[1]
            ),
            None,
        )
        if agents_line is None:
            continue
        agents_depth = agents_line[2]
        agent_depth = agents_depth + 1
        agents_opening = masked.find(
            "{", agents_match.start(), agents_match.end()
        )
        agents_closing = matching_brace(masked, agents_opening, agents_depth)
        if agents_closing < 0:
            continue
        tokens = promptscript_tokens(
            source, agents_opening + 1, agents_closing
        )
        depth = agent_depth
        for index, token in enumerate(tokens):
            kind, value, start, _ = token
            if value == "}":
                depth -= 1
                continue
            if (
                depth == agent_depth
                and kind in {"word", "string"}
                and index + 2 < len(tokens)
                and tokens[index + 1][1] == ":"
                and tokens[index + 2][1] == "{"
            ):
                opening = tokens[index + 2][2]
                closing = matching_brace(masked, opening, agent_depth)
                if closing >= 0:
                    blocks.append(
                        (value, start, closing + 1, agent_depth)
                    )
            if value == "{":
                depth += 1
    return blocks


def canonical_agent_body(root: Path, name: str) -> str:
    """Read one agent body from its canonical PromptScript source."""
    sources = canonical_agent_sources(root)
    source_path = sources.get(name)
    if source_path is None:
        raise ValueError(f"missing canonical agent body: {name}")
    source = source_path.read_text(encoding="utf-8")
    matching_blocks = [
        block for block in canonical_agent_blocks(source) if block[0] == name
    ]
    if len(matching_blocks) != 1:
        raise ValueError(f"invalid canonical agent body: {source_path}")
    _, block_start, block_end, agent_depth = matching_blocks[0]
    tokens = promptscript_tokens(source, block_start, block_end)
    depth = agent_depth
    field_depth = agent_depth + 1
    for index, token in enumerate(tokens):
        kind, value, _, _ = token
        if value == "}":
            depth -= 1
            continue
        if (
            depth == field_depth
            and kind in {"word", "string"}
            and value == "content"
            and index + 2 < len(tokens)
            and tokens[index + 1][1] == ":"
        ):
            value_kind, value_text, _, _ = tokens[index + 2]
            if value_kind == "triple":
                body = value_text
                if body.startswith("\n"):
                    body = body[1:]
                body = textwrap.dedent(body)
                return body if body.endswith("\n") else body + "\n"
            if value_kind == "string":
                return (
                    value_text
                    if value_text.endswith("\n")
                    else value_text + "\n"
                )
            if value_kind == "word":
                return value_text + "\n"
            break
        if value == "{":
            depth += 1
    raise ValueError(f"missing canonical agent body: {name}")


def canonical_agent_files(root: Path) -> set[Path]:
    """Return the Claude agent paths declared by canonical PromptScript."""
    return {Path(f"{name}.md") for name in canonical_agent_sources(root)}


def canonical_skill_files(root: Path) -> set[Path]:
    """Return only source skill paths that PromptScript emits."""
    skill_root = root / ".promptscript" / "skills"
    return {
        relative
        for relative in files_under(skill_root)
        if relative.name == "SKILL.md"
        or relative.parts[-2:] == ("agents", "openai.yaml")
    }


def adapted_source_content(
    root: Path, source_file: Path, relative: Path, label: str
) -> bytes:
    """Adapt compiler output to the installable Claude plugin contract."""
    content = source_file.read_bytes()
    if label == "skills" and relative.parts[-2:] == ("agents", "openai.yaml"):
        marker = f"{CODEX_INTERFACE_MARKER}\n".encode("utf-8")
        if not content.startswith(marker):
            content = marker + content
    if label == "skills" and relative.name == "SKILL.md":
        canonical = root / ".promptscript" / "skills" / relative
        if has_symlink_component(canonical, root / ".promptscript"):
            raise ValueError(f"symlink source refused: {canonical}")
        if not canonical.is_file():
            raise ValueError(f"missing canonical skill source: {canonical}")
        source = canonical.read_text(encoding="utf-8")
        parts = source.split("\n---\n", 1)
        if len(parts) != 2:
            raise ValueError(f"canonical skill is missing frontmatter: {canonical}")
        return with_source_body(content, parts[1])
    if label == "agents" and relative.suffix == ".md":
        content = adapt_claude_agent_frontmatter(content, relative.stem)
        return with_source_body(content, canonical_agent_body(root, relative.stem))
    return content


def sync_tree(
    root: Path,
    source: Path,
    destination: Path,
    check: bool,
    label: str,
    plan: Optional[SyncPlan] = None,
    expected_files: Optional[set[Path]] = None,
) -> list[str]:
    """Copy generated files while preserving unmarked user files."""
    errors: list[str] = []
    own_plan = plan is None and not check
    if plan is None and not check:
        plan = SyncPlan()

    if not source.is_dir():
        return [f"{label}: missing compiler output {source}"]
    if has_symlink_component(source, root):
        return [f"{label}: symlink source refused {source}"]

    source_symlinks = symlinks_under(source)
    if source_symlinks:
        return [
            f"{label}: symlink source refused {source_path}"
            for source_path in source_symlinks
        ]

    source_files = files_under(source)
    if expected_files is not None:
        for relative in sorted(expected_files - source_files):
            errors.append(f"{label}: missing compiler output {source / relative}")
        source_files &= expected_files
    destination_files = files_under(destination)

    for relative in sorted(source_files):
        source_file = source / relative
        destination_file = destination / relative
        if has_symlink_component(source_file, root):
            errors.append(f"{label}: symlink source refused {source_file}")
            continue
        try:
            source_content = adapted_source_content(
                root, source_file, relative, label
            )
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            errors.append(f"{label}: cannot adapt {source_file} ({exc})")
            continue
        if has_symlink_component(destination_file, destination):
            errors.append(f"{label}: symlink destination refused {destination_file}")
            continue
        if destination_file.is_file() and not is_generated(destination_file):
            errors.append(
                f"{label}: unmarked destination conflict {destination_file}"
            )
            continue
        if destination_file.exists() and not destination_file.is_file():
            errors.append(f"{label}: non-file destination conflict {destination_file}")
            continue
        if check:
            if not destination_file.is_file():
                errors.append(f"{label}: missing {destination_file}")
            elif comparable_content(destination_file.read_bytes()) != comparable_content(
                source_content
            ):
                errors.append(f"{label}: drift in {destination_file}")
            continue
        plan.add_write(destination_file, source_content)

    stale = destination_files - source_files
    for relative in sorted(stale):
        destination_file = destination / relative
        if has_symlink_component(destination_file, destination):
            errors.append(f"{label}: symlink destination refused {destination_file}")
            continue
        if not is_generated(destination_file):
            continue
        if check:
            errors.append(f"{label}: stale generated file {destination_file}")
        else:
            plan.add_removal(destination_file)

    if own_plan and not errors:
        try:
            plan.apply()
        except OSError as exc:
            errors.append(f"{label}: failed to apply synchronized outputs ({exc})")

    return errors


def plugin_mcp_content(build_mcp: Path) -> bytes:
    """Adapt portable MCP output to Claude's plugin-root contract."""
    expected = {
        "mcpServers": {
            "founder-os-state": {
                "type": "stdio",
                "command": "python3",
                "args": ["founder-os/mcp/founder_os_state.py"],
            }
        }
    }
    try:
        config = json.loads(build_mcp.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid PromptScript MCP output: {build_mcp}") from exc
    if config != expected:
        raise ValueError(
            f"unsupported PromptScript MCP output contract: {build_mcp}"
        )
    adapted = {
        "mcpServers": {
            "founder-os-state": {
                "command": "python3",
                "args": [
                    "${CLAUDE_PLUGIN_ROOT}/mcp/founder_os_state.py"
                ],
            }
        }
    }
    return (json.dumps(adapted, indent=2) + "\n").encode("utf-8")


def plugin_hooks_content(build_settings: Path) -> bytes:
    """Adapt portable Claude hooks to the plugin-root runtime manifest."""
    expected = {
        "SessionStart": {
            "matcher": "startup|resume|clear|compact",
            "file": "session-context.py",
            "marker": "session-context",
            "status": "Loading Founder OS context",
        },
        "SubagentStart": {
            "matcher": ".*",
            "file": "record-agent.py",
            "marker": "record-agent",
            "status": "Recording Founder OS decision role",
        },
        "PreToolUse": {
            "matcher": (
                "^(Read|Write|Edit|NotebookEdit|Glob|Grep|Bash|WebFetch|"
                "WebSearch|apply_patch|Task|Agent|mcp__.*)$"
            ),
            "file": "ownership-guard.py",
            "marker": "ownership-guard",
            "status": "Checking Founder OS boundaries",
        },
    }
    try:
        config = json.loads(build_settings.read_text(encoding="utf-8"))
        hooks = config["hooks"]
        if not isinstance(hooks, dict) or set(hooks) != set(expected):
            raise ValueError("unexpected Claude hook events")
        adapted = {}
        preamble = (
            'if [ -z "${CLAUDE_PROJECT_DIR:-}" ]; then printf \'%s\\n\' '
            "'PromptScript claude hook requires non-empty "
            "CLAUDE_PROJECT_DIR.' >&2; exit 1; fi; "
            'cd "${CLAUDE_PROJECT_DIR}" && '
        )
        for event, contract in expected.items():
            groups = hooks[event]
            if not isinstance(groups, list) or len(groups) != 1:
                raise ValueError(f"unexpected Claude {event} hook groups")
            group = groups[0]
            event_hooks = group.get("hooks") if isinstance(group, dict) else None
            expected_command = (
                f"{preamble}python3 founder-os/hooks/{contract['file']} "
                f"# promptscript-generated:{contract['marker']}"
            )
            expected_hook = {
                "type": "command",
                "command": expected_command,
                "timeout": 10,
                "statusMessage": contract["status"],
            }
            if (
                not isinstance(group, dict)
                or group.get("matcher") != contract["matcher"]
                or set(group) != {"matcher", "hooks"}
                or not isinstance(event_hooks, list)
                or event_hooks != [expected_hook]
            ):
                raise ValueError(f"unsupported PromptScript Claude {event} hook")
            adapted_group = {
                "hooks": [{
                    "type": "command",
                    "command": (
                        'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/%s"'
                        % contract["file"]
                    ),
                    "statusMessage": contract["status"],
                }]
            }
            if contract["matcher"] != ".*":
                adapted_group["matcher"] = contract["matcher"]
            adapted[event] = [adapted_group]
        config = {"hooks": adapted}
    except (OSError, UnicodeDecodeError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid PromptScript hook output: {build_settings}") from exc
    except ValueError as exc:
        raise ValueError(f"invalid PromptScript hook output: {build_settings} ({exc})") from exc
    return (json.dumps(config, indent=2) + "\n").encode("utf-8")


def plugin_codex_hooks_content(build_hooks: Path) -> bytes:
    """Adapt Codex project hooks to the installable plugin root."""
    expected = {
        "SessionStart": {
            "matcher": "startup|resume|clear|compact",
            "file": "session-context.py",
            "marker": "session-context",
            "status": "Loading Founder OS context",
        },
        "SubagentStart": {
            "matcher": None,
            "file": "record-agent.py",
            "marker": "record-agent",
            "status": "Recording Founder OS decision role",
        },
        "PreToolUse": {
            "matcher": (
                "^(Read|Write|Edit|NotebookEdit|Glob|Grep|Bash|WebFetch|"
                "WebSearch|apply_patch|Task|Agent|mcp__.*)$"
            ),
            "file": "ownership-guard.py",
            "marker": "ownership-guard",
            "status": "Checking Founder OS boundaries",
        },
    }
    try:
        config = json.loads(build_hooks.read_text(encoding="utf-8"))
        hooks = config["hooks"]
        if not isinstance(hooks, dict) or set(hooks) != set(expected):
            raise ValueError("unexpected Codex hook events")
        adapted = {}
        for event, contract in expected.items():
            groups = hooks[event]
            if not isinstance(groups, list) or len(groups) != 1:
                raise ValueError(f"unexpected Codex {event} hook groups")
            group = groups[0]
            expected_group_keys = {"hooks"}
            if contract["matcher"] is not None:
                expected_group_keys.add("matcher")
            event_hooks = group.get("hooks") if isinstance(group, dict) else None
            if (
                not isinstance(group, dict)
                or set(group) != expected_group_keys
                or group.get("matcher") != contract["matcher"]
                or not isinstance(event_hooks, list)
                or len(event_hooks) != 1
            ):
                raise ValueError(f"unsupported PromptScript Codex {event} hook")
            hook = event_hooks[0]
            if (
                not isinstance(hook, dict)
                or set(hook) != {
                    "type",
                    "command",
                    "commandWindows",
                    "statusMessage",
                }
                or hook.get("type") != "command"
                or hook.get("statusMessage") != contract["status"]
            ):
                raise ValueError(f"unsupported PromptScript Codex {event} hook")
            posix = re.fullmatch(
                r'PROMPTSCRIPT_PROJECT_ROOT=.*?; cd '
                r'"\$PROMPTSCRIPT_PROJECT_ROOT" && python3 '
                r'founder-os/hooks/(?P<file>[A-Za-z0-9_.-]+\.py) '
                r'(?P<marker># promptscript-generated:[A-Za-z0-9_-]+)',
                hook["command"] if isinstance(hook["command"], str) else "",
            )
            windows = re.fullmatch(
                r"\$promptscriptProjectRoot = .*?; & 'python3' "
                r"'founder-os/hooks/(?P<file>[A-Za-z0-9_.-]+\.py)' "
                r"(?P<marker># promptscript-generated:[A-Za-z0-9_-]+)",
                (
                    hook["commandWindows"]
                    if isinstance(hook["commandWindows"], str)
                    else ""
                ),
            )
            marker = f"# promptscript-generated:{contract['marker']}"
            if (
                posix is None
                or windows is None
                or posix.group("file") != contract["file"]
                or windows.group("file") != contract["file"]
                or posix.group("marker") != marker
                or windows.group("marker") != marker
            ):
                raise ValueError(
                    f"unsupported PromptScript Codex {event} hook command"
                )
            adapted_group = {
                "hooks": [{
                    "type": "command",
                    "command": (
                        'python3 "${PLUGIN_ROOT}/hooks/%s" %s'
                        % (contract["file"], marker)
                    ),
                    "commandWindows": (
                        "& 'python' (Join-Path $env:PLUGIN_ROOT 'hooks/%s') %s"
                        % (contract["file"], marker)
                    ),
                    "statusMessage": contract["status"],
                }]
            }
            if contract["matcher"] is not None:
                adapted_group["matcher"] = contract["matcher"]
            adapted[event] = [adapted_group]
        config = {"hooks": adapted}
    except (OSError, UnicodeDecodeError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid PromptScript Codex hook output: {build_hooks}") from exc
    except ValueError as exc:
        raise ValueError(
            f"invalid PromptScript Codex hook output: {build_hooks} ({exc})"
        ) from exc
    return (json.dumps(config, indent=2) + "\n").encode("utf-8")


def validate_promptscript_source(root: Path) -> None:
    """Require strict canonical validation before trusting compiler outputs."""
    try:
        result = subprocess.run(
            ["pnpm", "exec", "prs", "validate", "--strict"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError(
            f"cannot validate canonical PromptScript source ({exc})"
        ) from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        if detail:
            detail = detail.splitlines()[-1]
        raise ValueError(
            "canonical PromptScript source failed strict validation"
            + (f" ({detail})" if detail else "")
        )


def sync_plugin(
    root: Path,
    check: bool,
    source_validated: bool = False,
) -> list[str]:
    """Sync the generated Claude target into the installable plugin."""
    if not source_validated:
        return ["plugin: canonical PromptScript source validation is required"]
    build = root / ".promptscript" / "build" / "claude"
    plugin = root / "founder-os"
    errors: list[str] = []
    plan = None if check else SyncPlan()
    promptscript_root = root / ".promptscript"
    project_source = promptscript_root / "project.prs"
    agents_source = promptscript_root / "agents.prs"
    skills_source = promptscript_root / "skills"
    for canonical_root in (project_source, agents_source, skills_source):
        if has_symlink_component(canonical_root, promptscript_root):
            return [f"plugin: symlink source refused {canonical_root}"]
    missing_sources = [
        path
        for path in (project_source, agents_source)
        if not path.is_file()
    ]
    if not skills_source.is_dir():
        missing_sources.append(skills_source)
    if missing_sources:
        return [
            f"plugin: missing canonical source {source}"
            for source in missing_sources
        ]
    promptscript_symlinks = symlinks_under(promptscript_root)
    if promptscript_symlinks:
        return [
            f"plugin: symlink source refused {source}"
            for source in promptscript_symlinks
        ]
    canonical_sources = [
        project_source,
        agents_source,
    ]
    canonical_sources.extend(
        skills_source / relative
        for relative in files_under(skills_source)
    )
    canonical_symlinks = [
        source
        for source in canonical_sources
        if has_symlink_component(source, promptscript_root)
    ]
    canonical_symlinks.extend(symlinks_under(skills_source))
    if canonical_symlinks:
        return [
            f"plugin: symlink source refused {source}"
            for source in sorted(set(canonical_symlinks))
        ]
    try:
        managed_singletons = load_singleton_ownership(plugin)
    except ValueError as exc:
        return [f"plugin: {exc}"]

    main_source = build / "CLAUDE.md"
    main_destination = plugin / "CLAUDE.md"
    if main_destination.relative_to(plugin).as_posix() not in managed_singletons:
        errors.append(f"plugin: unowned generated destination {main_destination}")
    if not main_source.is_file():
        errors.append(f"plugin: missing compiler output {main_source}")
    elif has_symlink_component(main_source, build):
        errors.append(f"plugin: symlink source refused {main_source}")
    elif has_symlink_component(main_destination, plugin):
        errors.append(f"plugin: symlink destination refused {main_destination}")
    elif check:
        if (
            not main_destination.is_file()
            or comparable_content(main_destination.read_bytes())
            != comparable_content(main_source.read_bytes())
        ):
            errors.append(f"plugin: drift in {main_destination}")
    else:
        plan.add_write(main_destination, main_source.read_bytes())

    errors.extend(
        sync_tree(
            root,
            build / "skills",
            plugin / "skills",
            check,
            "skills",
            plan,
            canonical_skill_files(root),
        )
    )
    try:
        agent_files = canonical_agent_files(root)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        errors.append(f"agents: cannot read canonical declarations ({exc})")
    else:
        errors.extend(
            sync_tree(
                root,
                build / ".claude" / "agents",
                plugin / "agents",
                check,
                "agents",
                plan,
                agent_files,
            )
        )

    build_mcp = build / ".mcp.json"
    destination_mcp = plugin / ".mcp.json"
    if destination_mcp.relative_to(plugin).as_posix() not in managed_singletons:
        errors.append(f"plugin: unowned generated destination {destination_mcp}")
    expected_mcp = None
    if has_symlink_component(build_mcp, build):
        errors.append(f"plugin: symlink source refused {build_mcp}")
    else:
        try:
            expected_mcp = plugin_mcp_content(build_mcp)
        except ValueError as exc:
            errors.append(str(exc))
            expected_mcp = None
    if expected_mcp is not None:
        if has_symlink_component(destination_mcp, plugin):
            errors.append(f"plugin: symlink destination refused {destination_mcp}")
        elif check:
            if not destination_mcp.is_file() or destination_mcp.read_bytes() != expected_mcp:
                errors.append(f"plugin: drift in {destination_mcp}")
        else:
            plan.add_write(destination_mcp, expected_mcp)

    build_settings = build / ".claude" / "settings.json"
    destination_hooks = plugin / "hooks" / "hooks.json"
    if destination_hooks.relative_to(plugin).as_posix() not in managed_singletons:
        errors.append(f"plugin: unowned generated destination {destination_hooks}")
    expected_hooks = None
    if has_symlink_component(build_settings, build):
        errors.append(f"plugin: symlink source refused {build_settings}")
    else:
        try:
            expected_hooks = plugin_hooks_content(build_settings)
        except ValueError as exc:
            errors.append(str(exc))
            expected_hooks = None
    if expected_hooks is not None:
        if has_symlink_component(destination_hooks, plugin):
            errors.append(f"plugin: symlink destination refused {destination_hooks}")
        elif check:
            if not destination_hooks.is_file() or destination_hooks.read_bytes() != expected_hooks:
                errors.append(f"plugin: drift in {destination_hooks}")
        else:
            plan.add_write(destination_hooks, expected_hooks)

    build_codex_hooks = root / ".promptscript" / "build" / "codex" / ".codex" / "hooks.json"
    destination_codex_hooks = plugin / "hooks" / "codex-hooks.json"
    if (
        destination_codex_hooks.relative_to(plugin).as_posix()
        not in managed_singletons
    ):
        errors.append(
            f"plugin: unowned generated destination {destination_codex_hooks}"
        )
    codex_build = root / ".promptscript" / "build" / "codex"
    expected_codex_hooks = None
    if has_symlink_component(build_codex_hooks, codex_build):
        errors.append(f"plugin: symlink source refused {build_codex_hooks}")
    else:
        try:
            expected_codex_hooks = plugin_codex_hooks_content(build_codex_hooks)
        except ValueError as exc:
            errors.append(str(exc))
            expected_codex_hooks = None
    if expected_codex_hooks is not None:
        if has_symlink_component(destination_codex_hooks, plugin):
            errors.append(
                f"plugin: symlink destination refused {destination_codex_hooks}"
            )
        elif check:
            if (
                not destination_codex_hooks.is_file()
                or comparable_content(destination_codex_hooks.read_bytes())
                != comparable_content(expected_codex_hooks)
            ):
                errors.append(f"plugin: drift in {destination_codex_hooks}")
        else:
            plan.add_write(destination_codex_hooks, expected_codex_hooks)

    if plan is not None and not errors:
        try:
            plan.apply()
        except OSError as exc:
            errors.append(f"plugin: failed to apply synchronized outputs ({exc})")

    return errors


def main() -> int:
    """Run the sync or drift check."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when generated outputs drift")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        validate_promptscript_source(root)
    except ValueError as exc:
        errors = [f"plugin: {exc}"]
    else:
        errors = sync_plugin(root, args.check, source_validated=True)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PromptScript plugin outputs are current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
