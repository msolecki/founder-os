#!/usr/bin/env python3
"""Validate repository-local Markdown and HTML links without dependencies."""

from __future__ import annotations

import html
import re
import subprocess
import sys
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


DOCUMENT_SUFFIXES = {".md", ".markdown", ".html", ".htm"}
IGNORED_SCHEMES = {"data", "http", "https", "mailto", "tel"}
MARKDOWN_LINK = re.compile(
    r"!?\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+[^)]*)?\)"
)
ATX_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")
SETEXT_HEADING = re.compile(r"^\s{0,3}(?:=+|-+)\s*$")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")


class _HTMLReferences(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.anchors = []

    def handle_starttag(self, _tag, attrs):
        line, _ = self.getpos()
        for name, value in attrs:
            if not value:
                continue
            lowered = name.lower()
            if lowered in {"href", "src"}:
                self.links.append((line, value))
            elif lowered in {"id", "name"}:
                self.anchors.append((line, value))


def _markdown_slug(value):
    value = html.unescape(re.sub(r"<[^>]*>", "", value)).strip().lower()
    value = value.replace("`", "")
    value = re.sub(r"[^\w\- ]", "", value, flags=re.UNICODE)
    return re.sub(r"\s", "-", value)


def _visible_markdown_lines(text):
    visible = []
    fence_marker = None
    for number, line in enumerate(text.splitlines(), 1):
        match = FENCE.match(line)
        if match:
            marker = match.group(1)[0]
            if fence_marker is None:
                fence_marker = marker
            elif fence_marker == marker:
                fence_marker = None
            visible.append((number, ""))
        elif fence_marker is None:
            visible.append((number, line))
        else:
            visible.append((number, ""))
    return visible


def _markdown_references(text):
    lines = _visible_markdown_lines(text)
    anchors = []
    links = []
    heading_counts = defaultdict(int)

    def add_heading(number, value):
        base = _markdown_slug(value)
        if not base:
            return
        count = heading_counts[base]
        heading_counts[base] += 1
        anchors.append((number, base if count == 0 else "%s-%d" % (base, count)))

    for index, (number, line) in enumerate(lines):
        heading = ATX_HEADING.match(line)
        if heading:
            add_heading(number, heading.group(1))
        elif (SETEXT_HEADING.match(line) and index > 0
              and lines[index - 1][1].strip()):
            add_heading(lines[index - 1][0], lines[index - 1][1])
        for match in MARKDOWN_LINK.finditer(line):
            links.append((number, match.group(1) or match.group(2)))

    parser = _HTMLReferences()
    parser.feed("\n".join(line for _, line in lines))
    links.extend(parser.links)
    anchors.extend(parser.anchors)
    return links, anchors


def _html_references(text):
    parser = _HTMLReferences()
    parser.feed(text)
    return parser.links, parser.anchors


def _document_references(path):
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".md", ".markdown"}:
        return _markdown_references(text)
    return _html_references(text)


def _relative_path(root, value):
    path = Path(value)
    if path.is_absolute():
        path = path.resolve().relative_to(root)
    return path.as_posix()


def tracked_paths(root):
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(detail or "git ls-files failed")
    return sorted(
        item.decode("utf-8")
        for item in result.stdout.split(b"\0")
        if item
    )


def check_links(root, tracked):
    root = Path(root).resolve()
    tracked = sorted({_relative_path(root, item) for item in tracked})
    documents = [
        relative for relative in tracked
        if Path(relative).suffix.lower() in DOCUMENT_SUFFIXES
        and (root / relative).is_file()
    ]
    errors = []
    indexes = {}

    def index(relative):
        if relative in indexes:
            return indexes[relative]
        path = root / relative
        try:
            links, anchors = _document_references(path)
        except (OSError, UnicodeError) as exc:
            errors.append("%s: cannot read document (%s)" % (relative, exc))
            links, anchors = [], []
        by_anchor = defaultdict(list)
        for line, anchor in anchors:
            by_anchor[unquote(anchor)].append(line)
        for anchor, lines in sorted(by_anchor.items()):
            for line in lines[1:]:
                errors.append(
                    "%s:%d: duplicate anchor '%s'" % (relative, line, anchor)
                )
        indexes[relative] = (links, set(by_anchor))
        return indexes[relative]

    for relative in documents:
        index(relative)

    for source in documents:
        links, _ = index(source)
        for line, raw_target in links:
            target = html.unescape(raw_target.strip())
            if not target or target.startswith("//"):
                continue
            try:
                parsed = urlsplit(target)
            except ValueError:
                errors.append(
                    "%s:%d: invalid link target '%s'" % (source, line, target)
                )
                continue
            scheme = parsed.scheme.lower()
            if scheme in IGNORED_SCHEMES:
                continue
            if scheme:
                errors.append(
                    "%s:%d: unsupported link scheme '%s'" % (
                        source, line, scheme
                    )
                )
                continue

            decoded_path = unquote(parsed.path)
            decoded_fragment = unquote(parsed.fragment)
            source_path = root / source
            candidate = (
                source_path
                if not decoded_path
                else source_path.parent / decoded_path
            )
            try:
                resolved = candidate.resolve()
                target_relative = resolved.relative_to(root).as_posix()
            except (OSError, ValueError):
                errors.append(
                    "%s:%d: target escapes repository '%s'" % (
                        source, line, decoded_path
                    )
                )
                continue

            if not resolved.exists():
                errors.append(
                    "%s:%d: missing target '%s'" % (
                        source, line, target_relative
                    )
                )
                continue
            if decoded_fragment:
                _, anchors = index(target_relative)
                if decoded_fragment not in anchors:
                    errors.append(
                        "%s:%d: missing anchor '%s' in '%s'" % (
                            source, line, decoded_fragment, target_relative
                        )
                    )

    return sorted(set(errors))


def check_repository(root):
    root = Path(root).resolve()
    return check_links(root, tracked_paths(root))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    root = Path(argv[0]).resolve() if argv else Path(__file__).resolve().parents[1]
    try:
        errors = check_repository(root)
    except (OSError, RuntimeError, UnicodeError) as exc:
        print("FAIL: %s" % exc)
        return 1
    for error in errors:
        print("FAIL: %s" % error)
    if errors:
        print("\n%d local link error(s)" % len(errors))
        return 1
    print("local links: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
