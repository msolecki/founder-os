"""Workspace -> Sources. Reads every declared path; writes nothing, ever.

The set of files read is `references/ownership.yaml`, not a list in this module.
A second list of the workspace's files would go stale the first time an owner
gained a file, and it would go stale silently — the page would simply stop
mentioning something the company had started recording.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Tuple

_H2 = re.compile(r"^(##\s+.+?)\s*$", re.M)
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_HEADING_SUFFIX = re.compile(r"\s+[—–-]\s+")


@dataclass(frozen=True)
class SourceFile:
    path: str
    exists: bool
    readable: bool
    sha256: str
    mtime: Optional[str]
    sections: Mapping[str, str]
    missing: Tuple[str, ...]


@dataclass(frozen=True)
class Sources:
    slug: str
    name: str
    home: Path
    timezone: Optional[str]
    files: Mapping[str, SourceFile]
    members: Mapping[str, Tuple[SourceFile, ...]]

    def section(self, path: str, heading: str) -> Optional[str]:
        entry = self.files.get(path)
        if entry is None or not entry.readable:
            return None
        return entry.sections.get(heading)

    def newest_member(self, path: str) -> Optional[SourceFile]:
        members = self.members.get(path) or ()
        return members[-1] if members else None


def _normalise_heading(raw: str) -> str:
    return _HEADING_SUFFIX.split(raw.strip(), maxsplit=1)[0].strip()


def _split_h2(text: str) -> Dict[str, str]:
    """Every H2 body in the document, keyed by the exact heading line.

    A heading may carry a dated suffix (`## Close — 2026-06`); the section name
    is what is pinned, so the suffix is stripped for the key.
    """
    found: Dict[str, str] = {}
    current: Optional[str] = None
    body: List[str] = []
    fence: Optional[str] = None
    for line in text.splitlines(keepends=True):
        stripped = line.rstrip("\r\n")
        marker = _FENCE.match(stripped)
        if fence is None and marker:
            fence = marker.group(1)[0]
        elif fence is not None and marker and marker.group(1)[0] == fence:
            fence = None
        if fence is None:
            heading = _H2.match(stripped)
            if heading:
                if current is not None:
                    found.setdefault(current, "".join(body))
                current = _normalise_heading(heading.group(1))
                body = []
                continue
        if current is not None:
            body.append(line)
    if current is not None:
        found.setdefault(current, "".join(body))
    return found


def _read(path: Path):
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return None, None, None
    except OSError:
        return None, "", None
    digest = hashlib.sha256(raw).hexdigest()
    stamp = datetime.fromtimestamp(
        path.stat().st_mtime, tz=timezone.utc).isoformat()
    try:
        return raw.decode("utf-8"), digest, stamp
    except UnicodeError:
        return None, digest, stamp


def collect(home: Path, view, slug: str = "") -> Sources:
    root = Path(home)
    files: Dict[str, SourceFile] = {}
    members: Dict[str, Tuple[SourceFile, ...]] = {}

    declared = tuple(view.workspace_files) + tuple(view.portfolio_files)
    for declared_path in declared:
        headings = tuple(view.sections.get(declared_path, ()))
        if declared_path.endswith("/"):
            directory = root / declared_path
            found = []
            if directory.is_dir():
                for item in sorted(directory.glob("*.md")):
                    relative = declared_path + item.name
                    text, digest, stamp = _read(item)
                    present = _split_h2(text) if text is not None else {}
                    found.append(SourceFile(
                        path=relative, exists=True, readable=text is not None,
                        sha256=digest or "", mtime=stamp, sections=present,
                        missing=tuple(h for h in headings if h not in present)))
            members[declared_path] = tuple(found)
            continue

        text, digest, stamp = _read(root / declared_path)
        if text is None and digest is None:
            files[declared_path] = SourceFile(
                path=declared_path, exists=False, readable=False, sha256="",
                mtime=None, sections={}, missing=headings)
            continue
        if text is None:
            files[declared_path] = SourceFile(
                path=declared_path, exists=True, readable=False,
                sha256=digest or "", mtime=stamp, sections={}, missing=headings)
            continue
        present = _split_h2(text)
        files[declared_path] = SourceFile(
            path=declared_path, exists=True, readable=True, sha256=digest or "",
            mtime=stamp, sections=present,
            missing=tuple(h for h in headings if h not in present))

    charter = files.get("charter.md")
    name = slug or root.parent.name
    zone = None
    if charter is not None and charter.readable:
        business = charter.sections.get("## Business") or ""
        first = business.strip().splitlines()
        if first:
            name = first[0].split(" is ")[0].strip() or name
        zone = (charter.sections.get("## Timezone") or "").strip() or None
    return Sources(slug=slug, name=name, home=root, timezone=zone,
                   files=files, members=members)
