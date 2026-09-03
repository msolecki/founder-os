"""Strict canonical ownership and document-structure contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


_ROLES = {
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


class OwnershipError(Exception):
    _ACTIONS = {
        "PATH_OUTSIDE_WORKSPACE": (
            "Refuse without retrying a modified path guess"
        ),
        "ROLE_NOT_OWNER": "Request a handoff to the canonical owner",
        "STALE_WRITE": "Re-read, reconcile deliberately, then retry once",
        "INVALID_DOCUMENT_STRUCTURE": (
            "Carry every heading references/ownership.yaml declares for this "
            "path, in its order and no others, then retry"
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


def _schema_error() -> OwnershipError:
    return OwnershipError("STATE_IO_ERROR")


def _parse_scalar(raw: str) -> str:
    value = raw.strip()
    if not value:
        raise _schema_error()
    if value.startswith('"'):
        try:
            decoded = json.loads(value)
        except (TypeError, ValueError):
            raise _schema_error()
        if not isinstance(decoded, str) or not decoded:
            raise _schema_error()
        return decoded
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise _schema_error()
        decoded = value[1:-1].replace("''", "'")
        if not decoded:
            raise _schema_error()
        return decoded
    if " #" in value:
        value = value.split(" #", 1)[0].rstrip()
    if not value or value in {"[]", "{}"}:
        raise _schema_error()
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


def _derived_segments(value: str) -> Tuple[str, ...]:
    return tuple(part.casefold() for part in value.split("/") if part)


def _is_derived(derived_files: List[str], value: str) -> bool:
    """Is `value` a derived path, or a path inside a derived directory?

    A `derived_files:` entry ending in `/` names a directory, and comparing the
    two lists as sets read that slash as part of a filename: `_dashboard/` was
    refused as owned state and `_dashboard/snapshots/` was accepted one segment
    down, with `owner_for("_dashboard/snapshots/x.md")` then answering with a
    role.

    Matched by segment, casefolded, and with the trailing slash optional rather
    than required, because `hooks/ownership-guard.py:_derived_entry` is what
    decides at write time and that is the rule it applies. A map this loader
    accepts and the guard reads as derived hands an agent an owner for a path it
    will then be refused: with `_Dashboard/` declared derived,
    `_dashboard/snapshots/` was owned here and denied there. Broad is the safe
    direction for a deny list, and `_dashboardx/` is a different first segment,
    so it stays outside.
    """
    parts = _derived_segments(value)
    for entry in derived_files:
        prefix = _derived_segments(entry)
        if prefix and parts[:len(prefix)] == prefix:
            return True
    return False


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
    def load(cls, path: Path) -> "OwnershipSchema":
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
        if any(_is_derived(derived_files, owned_path) for owned_path in all_files):
            raise _schema_error()

        owners: Dict[str, str] = {}
        for role, role_paths in owns.items():
            if (
                not isinstance(role, str)
                or role not in _ROLES
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
        matches = []
        for owned_path in self._owners:
            if owned_path.endswith("/"):
                if path.startswith(owned_path):
                    matches.append(owned_path)
            elif path == owned_path:
                matches.append(owned_path)
        if not matches:
            return None
        return max(matches, key=len)

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
        match = self._matching_key(relative_path)
        if match is None or not match.endswith("/"):
            return None
        return match

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
        if self._headings_match(present, required):
            return ()
        absent = tuple(
            heading for heading in required
            if not any(
                self._heading_matches(candidate, heading)
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
            or not self._heading_matches(present[index], heading)
        )

    @classmethod
    def _headings_match(cls, actual, required) -> bool:
        return len(actual) == len(required) and all(
            cls._heading_matches(actual_heading, required_heading)
            for actual_heading, required_heading in zip(actual, required)
        )

    @staticmethod
    def _heading_matches(actual_heading: str, required_heading: str) -> bool:
        if actual_heading == required_heading:
            return True
        prefix = required_heading + " — "
        return (
            actual_heading.startswith(prefix)
            and bool(actual_heading[len(prefix):].strip())
        )

    @staticmethod
    def _headings(content: str) -> List[str]:
        actual = []
        fence_character = None
        fence_length = 0
        for line in content.splitlines():
            candidate = line.lstrip(" ")
            indentation = len(line) - len(candidate)
            if (
                indentation <= 3
                and candidate
                and candidate[0] in {chr(96), "~"}
            ):
                character = candidate[0]
                run_length = len(candidate) - len(
                    candidate.lstrip(character)
                )
                remainder = candidate[run_length:]
                if fence_character is None and run_length >= 3:
                    fence_character = character
                    fence_length = run_length
                    continue
                if (
                    fence_character == character
                    and run_length >= fence_length
                    and not remainder.strip()
                ):
                    fence_character = None
                    fence_length = 0
                    continue
            if (
                fence_character is None
                and line.startswith("## ")
                and not line.startswith("### ")
            ):
                actual.append(line.rstrip())
        return actual

    def validate_document(self, relative_path: str, content: str) -> None:
        if not isinstance(content, str):
            raise OwnershipError("INVALID_DOCUMENT_STRUCTURE")
        required = self.sections_for(relative_path)
        if not required:
            raise OwnershipError("PATH_OUTSIDE_WORKSPACE")
        if not self._headings_match(self._headings(content), required):
            raise OwnershipError("INVALID_DOCUMENT_STRUCTURE")
