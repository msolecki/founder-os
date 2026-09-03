"""Facts -> one dated CSV row, merged by (date, business).

Adding a column is a schema bump: `SCHEMA_VERSION` rises and `merge` keeps the
older rows, which then carry an empty cell for the new column. That is the
correct reading — the older runs did not measure it — and it is why every write
here distinguishes empty from zero.
"""
from __future__ import annotations

import csv
import io
import os
import tempfile
from pathlib import Path
from typing import Dict, Mapping, Tuple

SCHEMA_VERSION = 1

FIELDS = (
    "date",
    "business",
    "schema_version",
    "files_present",
    "files_missing",
    "sections_missing",
    "pipeline_live_count",
    "pipeline_live_amount",
    "pipeline_overdue",
    "currency",
    "queue_doing",
    "queue_queued",
    "queue_blocked",
    "queue_done",
    "queue_dropped",
    "bets_open",
    "week_available_hours",
    "week_planned_hours",
    "signals_below_normal",
    "runway_months",
    "cash_on_hand",
    "booked",
    "collected",
    "effective_rate",
    "integrity_findings",
)

_KEY = ("date", "business")


class SnapshotError(OSError):
    """The series on disk could not be read, so it must not be replaced.

    An `OSError` on purpose: the command's only handler around the
    `_dashboard/` writes is `except OSError`, so this is what turns an
    unreadable series into the documented write exit code and a message naming
    the file, rather than a traceback and an undocumented exit 1.
    """


def _format(number: float) -> str:
    if number == int(number):
        return str(int(number))
    return ("%g" % number)


def _cell(facts, panel_id: str, key: str) -> str:
    panel = facts.panels.get(panel_id)
    if panel is None:
        return ""
    for item in panel.facts:
        if item.key != key:
            continue
        if not item.known or item.number is None:
            return ""
        return _format(item.number)
    return ""


def _currency(facts) -> str:
    panel = facts.panels.get("pipeline")
    if panel is None:
        return ""
    for item in panel.facts:
        if item.key == "live_amount" and item.currency:
            return item.currency
    return ""


def _below_normal(facts) -> str:
    """How many signals read below normal, or nothing at all.

    Keyed on the count being known rather than on the panel being present: a
    `## Signals` section the reader could only half read yields a panel that is
    `partial` with an unknown `signal_count`, and a tally over the lines that
    happened to parse is exactly the confident wrong number an empty cell
    exists to avoid.
    """
    signals = facts.panels.get("signals")
    if signals is None:
        return ""
    count = next((item for item in signals.facts
                  if item.key == "signal_count"), None)
    if count is None or not count.known:
        return ""
    return str(sum(1 for signal in facts.details.get("signals") or ()
                   if signal.state == "below"))


def row_from(facts) -> Dict[str, str]:
    # The declared paths only. Members of the declared directories are in the
    # inventory so the Integrity view can report a section one of them lost,
    # but they are an archive: counting them here would grow the denominator of
    # all three columns with the workspace's own history and leave the series
    # unable to be compared with itself.
    declared = [item for item in facts.sources if item["declared"]]
    present = sum(1 for item in declared if item["exists"])
    missing_files = sum(1 for item in declared if not item["exists"])
    missing_sections = sum(
        len(item["sections_missing"]) for item in declared)
    return {
        "date": facts.today,
        "business": facts.business.get("slug") or "",
        "schema_version": str(SCHEMA_VERSION),
        "files_present": str(present),
        "files_missing": str(missing_files),
        "sections_missing": str(missing_sections),
        "pipeline_live_count": _cell(facts, "pipeline", "live_count"),
        "pipeline_live_amount": _cell(facts, "pipeline", "live_amount"),
        "pipeline_overdue": _cell(facts, "pipeline", "overdue_count"),
        "currency": _currency(facts),
        "queue_doing": _cell(facts, "queue", "doing"),
        "queue_queued": _cell(facts, "queue", "queued"),
        "queue_blocked": _cell(facts, "queue", "blocked"),
        "queue_done": _cell(facts, "queue", "done"),
        "queue_dropped": _cell(facts, "queue", "dropped"),
        "bets_open": _cell(facts, "bets", "bets_open"),
        "week_available_hours": _cell(facts, "week", "available_hours"),
        "week_planned_hours": _cell(facts, "week", "planned_hours"),
        "signals_below_normal": _below_normal(facts),
        "runway_months": _cell(facts, "cash", "runway_months"),
        "cash_on_hand": _cell(facts, "cash", "cash_on_hand"),
        "booked": _cell(facts, "cash", "booked"),
        "collected": _cell(facts, "cash", "collected"),
        "effective_rate": _cell(facts, "cash", "effective_rate"),
        "integrity_findings": str(len(facts.findings)),
    }


def _existing_rows(
    target: Path,
) -> Tuple[Dict[Tuple[str, ...], Dict[str, str]], Tuple[str, ...]]:
    """The series already on disk, keyed by (date, business), and its own columns.

    Decoded as `utf-8-sig` because the founder is told this file is theirs to
    keep, and a spreadsheet round-trip through "CSV UTF-8" prepends a BOM. Read
    as plain UTF-8 those three bytes land inside the first field name, so every
    historical row comes back with an empty date, the whole history folds onto
    one key, and `merge` writes that single row back over the file.

    Everything else unreadable raises instead. This is the only file the
    dashboard writes that a rerun cannot rebuild, so refusing to run is the
    cheap failure and rewriting a file we did not understand is the expensive
    one — the previous content is gone the moment the replace lands.

    Each refusal speaks for this file and nothing else. The command writes
    `_dashboard/facts.json` for the same business immediately before it merges
    the series, so a refusal claiming the run wrote nothing would already be
    false by the time the command prints it.

    The columns the file carries and this command does not write come back
    beside the rows. The file is the founder's to keep, so a column they added
    is theirs too: rewriting the header from `FIELDS` alone deletes it and its
    contents silently, on every run after the one that added it.
    """
    try:
        raw = target.read_bytes()
    except OSError as error:
        raise SnapshotError("%s could not be read (%s); it was left as it is"
                            % (target, error))
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise SnapshotError(
            "%s is not UTF-8 (%s); it was left as it is, and no row was added "
            "to it" % (target, error))
    if not text.strip():
        return {}, ()

    handle = io.StringIO(text, newline="")
    reader = csv.DictReader(handle)
    try:
        rows = list(reader)
    except csv.Error as error:
        raise SnapshotError("%s is not readable as CSV (%s); it was left as it "
                            "is, and no row was added to it" % (target, error))
    if not set(_KEY) <= set(reader.fieldnames or ()):
        raise SnapshotError(
            "%s has no %s column, so it is not the series this command writes; "
            "it was left as it is" % (target, " or ".join(
                key for key in _KEY if key not in (reader.fieldnames or ()))))
    extra = tuple(name for name in (reader.fieldnames or ())
                  if name and name not in FIELDS)
    return ({tuple(old.get(key) or "" for key in _KEY): {
        field: old.get(field) or "" for field in FIELDS + extra}
        for old in rows}, extra)


def merge(path: Path, row: Mapping[str, str]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    existing, extra = _existing_rows(target) if target.exists() else ({}, ())
    fields = FIELDS + extra
    cell = tuple(row.get(key, "") for key in _KEY)
    previous = existing.get(cell, {})
    merged = {field: row.get(field, "") for field in FIELDS}

    # A column the founder added is theirs, and this run has no value for it,
    # so the one already on that date's row stays. Building the row from `row`
    # alone kept the header and blanked every founder column underneath it —
    # on the ordinary second run of a day, which docs/dashboard.md documents as
    # the normal path, in the one file whose loss costs history.
    for field in extra:
        merged[field] = previous.get(field, "")
    existing[cell] = merged

    handle = tempfile.NamedTemporaryFile(
        "w", delete=False, dir=str(target.parent), encoding="utf-8", newline="")
    try:
        writer = csv.DictWriter(handle, fieldnames=list(fields))
        writer.writeheader()
        for key in sorted(existing):
            writer.writerow(existing[key])
        handle.close()
        os.replace(handle.name, target)
    except BaseException:
        handle.close()
        if os.path.exists(handle.name):
            os.unlink(handle.name)
        raise
