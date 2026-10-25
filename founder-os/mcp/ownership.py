"""Strict canonical ownership and document-structure contracts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import AbstractSet, Callable, Dict, Iterable, List, Optional, Tuple


_REQUIRED_TOP_LEVEL_KEYS = {
    "workspace_files",
    "portfolio_files",
    "owns",
    "sections",
}
# `derived_files:` is optional on purpose. The check below is a subset test, not
# an equality test: a founder's `_local/` overlay and every ownership.yaml
# written before this key existed must keep loading unchanged.
_TOP_LEVEL_KEYS = _REQUIRED_TOP_LEVEL_KEYS | {"derived_files"}
_LIST_KEYS = {"workspace_files", "portfolio_files", "derived_files"}
# A plain top-level key `read_key` may skip when it carries a scalar.
_TOP_KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*\Z")


class OwnershipError(Exception):
    _ACTIONS = {
        "PATH_OUTSIDE_WORKSPACE": (
            "Refuse without retrying a modified path guess"
        ),
        "ROLE_NOT_OWNER": "Request a handoff to the canonical owner",
        "STALE_WRITE": "Re-read, reconcile deliberately, then retry once",
        "INVALID_DOCUMENT_STRUCTURE": (
            "Carry the headings references/ownership.yaml declares for this "
            "path (every one for a file, a subset for a directory member), "
            "in its order, each once and no others, then retry"
        ),
        "STATE_IO_ERROR": "Preserve the original file and surface the error",
    }

    def __init__(self, code: str, owner: Optional[str] = None):
        self.code = (
            code if code in self._ACTIONS else "STATE_IO_ERROR"
        )
        if self.code == "ROLE_NOT_OWNER" and owner:
            self.action = (
                "Request a handoff to {0}, the canonical owner".format(owner)
            )
        else:
            self.action = self._ACTIONS[self.code]
        super().__init__(self.code)


def heading_matches(actual_heading: str, required_heading: str) -> bool:
    """`## Close — 2026-07` is `## Close`: the name is pinned, the suffix is not.

    The one suffix rule, shared with `safe_io` and the dashboard, so a heading
    the write accepts is a heading every read finds. Only an em dash separates
    a suffix: every shipped skill writes ` — `, and `## Close - 2026-07` is a
    different heading here, not `## Close`.
    """
    if actual_heading == required_heading:
        return True
    prefix = required_heading + " — "
    return (
        actual_heading.startswith(prefix)
        and bool(actual_heading[len(prefix):].strip())
    )


def split_h2(content: str) -> Tuple[Optional[str], List[Tuple[str, str]]]:
    """The `# ` title above the first H2, and every H2 line with its body.

    The one scanner for the write check, the gateway's section read and the
    dashboard: three scanners disagreed about where a fence closes, so a
    heading the write accepted could be one a read never found. A fence opens
    on three or more backticks or tildes indented at most three spaces, info
    string or not, and closes only on a run of the same character at least as
    long with nothing after it. Heading lines are returned `rstrip()`ed and in
    file order, duplicates included: each caller owns its duplicate policy.
    """
    title: Optional[str] = None
    sections: List[Tuple[str, str]] = []
    current: Optional[str] = None
    body: List[str] = []
    fence_character: Optional[str] = None
    fence_length = 0
    for line in content.splitlines(keepends=True):
        stripped = line.rstrip("\r\n")
        candidate = stripped.lstrip(" ")
        if (
            len(stripped) - len(candidate) <= 3
            and candidate[:1] in ("`", "~")
        ):
            character = candidate[0]
            run_length = len(candidate) - len(candidate.lstrip(character))
            if fence_character is None and run_length >= 3:
                fence_character = character
                fence_length = run_length
            elif (
                fence_character == character
                and run_length >= fence_length
                and not candidate[run_length:].strip()
            ):
                fence_character = None
                fence_length = 0
        elif fence_character is None and stripped.startswith("## "):
            if current is not None:
                sections.append((current, "".join(body)))
            current = stripped.rstrip()
            body = []
            continue
        elif (
            fence_character is None
            and current is None
            and title is None
            and stripped.startswith("# ")
        ):
            title = stripped[2:].strip() or None
        if current is not None:
            body.append(line)
    if current is not None:
        sections.append((current, "".join(body)))
    return title, sections


def _schema_error() -> OwnershipError:
    return OwnershipError("STATE_IO_ERROR")


def _parse_scalar(
    raw: str,
    error: Callable[[], Exception] = _schema_error,
) -> str:
    """One YAML scalar, for this map and for the business registry alike.

    The grammar is the stricter of the two parsers it replaced, on every axis:
    a quoted value is quoted at both ends with the same mark and holds neither
    that mark nor, in double quotes, a backslash, so no escape is ever
    decoded; an unquoted value holds no flow brackets; no value is empty or
    spans a line. Nothing the package ships or its tests write needed more.
    `error` builds the caller's own refusal.
    """
    value = raw.strip()
    if value[:1] in ("'", '"'):
        quote = value[0]
        inner = value[1:-1]
        if (
            len(value) < 2
            or value[-1] != quote
            or quote in inner
            or (quote == '"' and "\\" in inner)
        ):
            raise error()
        value = inner
    else:
        if " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        if any(character in value for character in "[]{}"):
            raise error()
    if not value or "\x00" in value or "\n" in value or "\r" in value:
        raise error()
    return value


def _parse_subset(contents: str) -> Dict[str, object]:
    parsed: Dict[str, object] = {}
    current_top: Optional[str] = None
    current_member: Optional[str] = None

    for raw_line in contents.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if "\t" in raw_line:
            raise _schema_error()

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = raw_line.strip()

        if indent == 0:
            if not stripped.endswith(":") or stripped.count(":") != 1:
                raise _schema_error()
            key = stripped[:-1]
            if key in parsed:
                raise _schema_error()
            if key in _LIST_KEYS:
                parsed[key] = []
            elif key in {"owns", "sections"}:
                parsed[key] = {}
            else:
                parsed[key] = None
            current_top = key
            current_member = None
            continue

        if current_top is None:
            raise _schema_error()

        if current_top in _LIST_KEYS:
            if indent != 2 or not stripped.startswith("- "):
                raise _schema_error()
            values = parsed[current_top]
            if not isinstance(values, list):
                raise _schema_error()
            values.append(_parse_scalar(stripped[2:]))
            continue

        mapping = parsed[current_top]
        if not isinstance(mapping, dict):
            raise _schema_error()
        if indent == 2:
            if not stripped.endswith(":"):
                raise _schema_error()
            member = _parse_scalar(stripped[:-1])
            if member in mapping:
                raise _schema_error()
            mapping[member] = []
            current_member = member
            continue
        if (
            indent != 4
            or current_member is None
            or not stripped.startswith("- ")
        ):
            raise _schema_error()
        member_values = mapping[current_member]
        if not isinstance(member_values, list):
            raise _schema_error()
        member_values.append(_parse_scalar(stripped[2:]))

    return parsed


def _validate_owned_path(value: str) -> None:
    if (
        not value
        or value.startswith("/")
        or "\\" in value
        or "\x00" in value
    ):
        raise _schema_error()
    directory = value.endswith("/")
    core = value[:-1] if directory else value
    parts = core.split("/")
    if not core or any(part in {"", ".", ".."} for part in parts):
        raise _schema_error()
    if not directory and not value.endswith(".md"):
        raise _schema_error()


def _validate_requested_path(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value.startswith("/")
        or value.endswith("/")
        or not value.endswith(".md")
        or "\\" in value
        or "\x00" in value
    ):
        raise OwnershipError("PATH_OUTSIDE_WORKSPACE")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise OwnershipError("PATH_OUTSIDE_WORKSPACE")
    if parts[0] == "_local":
        raise OwnershipError("PATH_OUTSIDE_WORKSPACE")
    return value


def owner_key(path: str, keys: Iterable[str]) -> Optional[str]:
    """The `owns:` entry that governs a workspace-relative path, or None.

    The one owner matcher: the guard, the gateway and the validator all call
    it. An entry is a file (`goals.md`) or a directory (`decisions/`), and the
    longest match wins, so `drafts/outreach/` beats `drafts/`.

    The case rule is casefolding, everywhere. APFS is case-insensitive by
    default, so `Goals.md` *is* `goals.md` on a Mac and an exact match lets a
    shift key dodge the map. For a deny — the guard — the casefolded answer is
    used as is: the stricter reading, and on a case-sensitive filesystem it can
    refuse a distinct `Goals.md`, which a workspace that tells files apart by
    case alone has earned. A *grant* — the gateway's write, the validator's
    `expected_persistence` check — also requires the path to start with the
    entry spelled as the map spells it, so the gateway never writes a second
    `Goals.md` beside `goals.md` on Linux. Broad to refuse, exact to allow.
    """
    folded = path.casefold()
    best: Optional[str] = None
    for key in keys:
        entry = key.casefold()
        if folded.startswith(entry) if key.endswith("/") else folded == entry:
            if best is None or len(key) > len(best):
                best = key
    return best


def derived_entry(path: str, derived: Iterable[str]) -> Optional[str]:
    """The `derived_files:` entry covering `path`, or None.

    The one derived-path matcher, for the guard's write-time deny, this
    loader's refusal of an owned derived path, and the validator's joins.
    Matched by path *segment*, never by string prefix: `_dashboard/` covers
    `_dashboard` and everything under it, and covers neither
    `_dashboard_secrets.md` nor `_dashboardish/x.md`. Casefolded like
    `owner_key`, and the trailing slash is optional rather than required: an
    entry that lost it is a typo, and the safe reading of a typo in a deny list
    is the broader one. With `_Dashboard/` declared derived, a loader that
    compared exactly owned `_dashboard/snapshots/` and the guard denied it.
    """
    parts = [part.casefold() for part in path.split("/") if part]
    for entry in derived:
        prefix = [part.casefold() for part in entry.split("/") if part]
        if prefix and parts[:len(prefix)] == prefix:
            return entry
    return None


def load_document(path: Path) -> Dict[str, object]:
    """The whole parsed map, for readers that need more than an owner lookup.

    The gateway needs owners and sections; the dashboard needs the file lists
    too. Both go through this function so the package keeps one parser and one
    validation point for the map.
    """
    try:
        contents = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        raise _schema_error()
    parsed = _parse_subset(contents)
    keys = set(parsed)
    if not keys <= _TOP_LEVEL_KEYS or not _REQUIRED_TOP_LEVEL_KEYS <= keys:
        raise _schema_error()
    parsed.setdefault("derived_files", [])
    return parsed


def read_key(contents: str, key: str) -> Optional[object]:
    """One top-level key of a map, parsed with `_parse_subset`, or None.

    For the write-time guard, which reads the packaged map and a founder's
    `_local/` overlay (`owns:` only) and must not need PyYAML to do it. Each key
    is cut out and parsed alone, so a broken `owns:` cannot take
    `derived_files:` down with it — the guard runs the derived deny on both
    sides of its `owns:` bail. Around the requested block this read is looser
    than `_parse_subset`, so valid YAML the founder wrote does not switch the
    guard off: a ` #` comment after a `key:`, a leading `---`, and other
    top-level `key: scalar` lines are accepted, and other keys are skipped.
    Inside the block `_parse_subset` decides. A column-0 line that is none of
    these, an indented line under a scalar key, a second `---` or the requested
    key written inline fails the whole read, never a truncated block. None
    means absent or not in this grammar, and the guard fails open on it;
    `load_document` stays the strict whole-map read.
    """
    block: List[str] = []
    inside = False
    scalar = False
    seen_key = False
    for line in contents.splitlines():
        if line[:1] in ("", " ", "#"):
            if scalar and line.strip() and not line.lstrip().startswith("#"):
                # PyYAML refuses this or folds it into the scalar; either
                # way it is not a line of the block below the key.
                return None
            if inside:
                block.append(line)
            continue
        stripped = line.split(" #", 1)[0].strip()
        if stripped == "---" and not seen_key:
            continue
        name, separator, value = stripped.partition(": ")
        if stripped.endswith(":") and stripped.count(":") == 1:
            name, scalar = stripped[:-1], False
        elif separator and value.strip() and _TOP_KEY.match(name):
            if name == key:
                return None
            scalar = True
        else:
            # Not a key: `_parse_subset` refuses the whole map here, and
            # cutting the block short would hand back part of `owns:`.
            return None
        seen_key = True
        inside = name == key and not scalar
        if inside:
            block.append(name + ":")
    if not block:
        return None
    try:
        return _parse_subset("\n".join(block)).get(key)
    except OwnershipError:
        return None


class OwnershipSchema:
    def __init__(
        self,
        owners: Dict[str, str],
        sections: Dict[str, Tuple[str, ...]],
        derived: Tuple[str, ...] = (),
    ):
        self._owners = owners
        self._sections = sections
        self._derived = derived

    def derived_paths(self) -> Tuple[str, ...]:
        return self._derived

    @classmethod
    def load(
        cls,
        path: Path,
        roles: Optional[AbstractSet[str]] = None,
    ) -> "OwnershipSchema":
        """Parse and validate the map; `roles` is the packaged agent set.

        The gateway passes the roles its session store derived from `agents/`,
        so an owner that is not a packaged agent refuses the map. `None` skips
        that one check for callers holding a bare map and no package.
        """
        parsed = load_document(path)

        workspace_files = parsed["workspace_files"]
        portfolio_files = parsed["portfolio_files"]
        owns = parsed["owns"]
        sections = parsed["sections"]
        if (
            not isinstance(workspace_files, list)
            or not workspace_files
            or not isinstance(portfolio_files, list)
            or not portfolio_files
            or not isinstance(owns, dict)
            or not owns
            or not isinstance(sections, dict)
            or not sections
        ):
            raise _schema_error()

        all_files: List[str] = workspace_files + portfolio_files
        if len(set(all_files)) != len(all_files):
            raise _schema_error()
        for owned_path in all_files:
            if not isinstance(owned_path, str):
                raise _schema_error()
            _validate_owned_path(owned_path)

        derived_files = parsed["derived_files"]
        if not isinstance(derived_files, list):
            raise _schema_error()
        for derived_path in derived_files:
            if not isinstance(derived_path, str):
                raise _schema_error()
            _validate_owned_path(derived_path)
        if len(set(derived_files)) != len(derived_files):
            raise _schema_error()
        if any(derived_entry(owned_path, derived_files) for owned_path in all_files):
            raise _schema_error()

        owners: Dict[str, str] = {}
        for role, role_paths in owns.items():
            if (
                not isinstance(role, str)
                or (roles is not None and role not in roles)
                or not isinstance(role_paths, list)
                or not role_paths
            ):
                raise _schema_error()
            if len(set(role_paths)) != len(role_paths):
                raise _schema_error()
            for owned_path in role_paths:
                if not isinstance(owned_path, str):
                    raise _schema_error()
                _validate_owned_path(owned_path)
                if owned_path not in all_files or owned_path in owners:
                    raise _schema_error()
                owners[owned_path] = role

        if set(owners) != set(all_files):
            raise _schema_error()
        if set(sections) != set(all_files):
            raise _schema_error()

        validated_sections: Dict[str, Tuple[str, ...]] = {}
        for owned_path, headings in sections.items():
            if (
                not isinstance(owned_path, str)
                or not isinstance(headings, list)
                or not headings
                or len(set(headings)) != len(headings)
            ):
                raise _schema_error()
            for heading in headings:
                if (
                    not isinstance(heading, str)
                    or not heading.startswith("## ")
                    or heading.startswith("### ")
                    or "\n" in heading
                    or not heading[3:].strip()
                ):
                    raise _schema_error()
            validated_sections[owned_path] = tuple(headings)

        return cls(owners, validated_sections, tuple(derived_files))

    def _matching_key(self, relative_path: str) -> Optional[str]:
        path = _validate_requested_path(relative_path)
        match = owner_key(path, self._owners)
        # A grant: the path must spell the entry as the map does (`owner_key`).
        return match if match is not None and path.startswith(match) else None

    def owner_for(self, relative_path: str) -> Optional[str]:
        match = self._matching_key(relative_path)
        return None if match is None else self._owners[match]

    def sections_for(self, relative_path: str) -> Tuple[str, ...]:
        match = self._matching_key(relative_path)
        if match is None:
            return ()
        return self._sections[match]

    def directory_for(self, relative_path: str) -> Optional[str]:
        """The declared directory this path lives in, or None for a flat file.

        `founder-os-init` scaffolds `workspace_files:` at install time, so a
        workspace scaffolded before a directory was declared does not have it
        and its owner has nowhere to write. The write path uses this to create
        the one directory the map already promised.
        """
        path = _validate_requested_path(relative_path)
        directories = [
            owned_path for owned_path in self._owners
            if owned_path.endswith("/") and path.startswith(owned_path)
        ]
        # The longest directory, not the longest key: `clients/_capacity.md`
        # is its own key and still lives in `clients/`.
        return max(directories, key=len) if directories else None

    def missing_sections(
        self,
        relative_path: str,
        content: str,
    ) -> Tuple[str, ...]:
        """Declared headings whose absence would refuse the next write.

        Reported on read so an owner sees a section added by a package update
        before its write is refused for lacking one. That only works if this
        answers the same question `validate_document` asks, which is not "is
        every heading present somewhere" but "does this document match the
        declared list exactly, in order". A file carrying all five headings with
        `## Signals` second reported nothing missing and was then refused, with
        an action line telling the owner to carry headings it already carried.

        So this reports the headings genuinely absent when any are — the
        upgrade case, where the answer the owner needs is the one heading to
        add. When every declared heading is present and the write would still
        be refused, the file carries them in the wrong order, and this names
        the ones out of position instead of reporting nothing.

        Empty does not promise the write is accepted: a document can also be
        refused for carrying a heading the map does not declare, which is not a
        missing section. `INVALID_DOCUMENT_STRUCTURE` names both halves.

        A path the ownership map does not describe has no declared headings, so
        it returns `()` rather than raising — `read_state` accepts paths this
        map was never meant to classify, and a read is not the place to refuse
        them.
        """
        if not isinstance(content, str):
            return ()
        try:
            required = self.sections_for(relative_path)
        except OwnershipError:
            return ()
        if not required:
            return ()
        present = self._headings(content)
        member = self._is_directory_member(relative_path)
        if self._headings_match(present, required, member):
            return ()
        if member:
            # A directory member needs none of its vocabulary, so nothing is
            # missing from it; a refusal there is order, a repeat or a stranger.
            return ()
        absent = tuple(
            heading for heading in required
            if not any(
                heading_matches(candidate, heading)
                for candidate in present
            )
        )
        if absent:
            return absent
        # Every declared heading is somewhere in the file and the write will
        # still be refused, so the file carries them in the wrong order. Naming
        # the ones out of position is the only answer that helps: reporting
        # nothing sent the owner to a refusal whose action line told them to
        # carry headings they already had.
        return tuple(
            heading for index, heading in enumerate(required)
            if index >= len(present)
            or not heading_matches(present[index], heading)
        )

    def _is_directory_member(self, relative_path: str) -> bool:
        match = self._matching_key(relative_path)
        return match is not None and match.endswith("/")

    @staticmethod
    def _headings_match(actual, required, directory_member=False) -> bool:
        """A flat file carries the whole list; a directory member a subset.

        A directory's list is the vocabulary its member files draw on — a
        quarterly plan and an annual review are both `reviews/quarterly/` and
        share no heading — so a member carries at least one of them, in the
        declared order, each at most once, and nothing undeclared.
        """
        if not directory_member:
            return len(actual) == len(required) and all(
                heading_matches(actual_heading, required_heading)
                for actual_heading, required_heading in zip(actual, required)
            )
        position = 0
        for actual_heading in actual:
            while position < len(required) and not heading_matches(
                actual_heading, required[position]
            ):
                position += 1
            if position == len(required):
                return False
            position += 1
        return bool(actual)

    @staticmethod
    def _headings(content: str) -> List[str]:
        return [heading for heading, _body in split_h2(content)[1]]

    def validate_document(self, relative_path: str, content: str) -> None:
        if not isinstance(content, str):
            raise OwnershipError("INVALID_DOCUMENT_STRUCTURE")
        required = self.sections_for(relative_path)
        if not required:
            raise OwnershipError("PATH_OUTSIDE_WORKSPACE")
        if not self._headings_match(
            self._headings(content),
            required,
            self._is_directory_member(relative_path),
        ):
            raise OwnershipError("INVALID_DOCUMENT_STRUCTURE")
