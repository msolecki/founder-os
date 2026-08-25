"""Facts -> one dated CSV row, merged by (date, business).

Adding a column is a schema bump: `SCHEMA_VERSION` rises and `merge` keeps the
older rows, which then carry an empty cell for the new column. That is the
correct reading — the older runs did not measure it — and it is why every write
here distinguishes empty from zero.
"""
from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path
from typing import Dict, Mapping

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
    signals = facts.panels.get("signals")
    if signals is None or signals.status == "missing":
        return ""
    return str(sum(1 for signal in facts.details.get("signals") or ()
                   if signal.state == "below"))


def row_from(facts) -> Dict[str, str]:
    present = sum(1 for item in facts.sources if item["exists"])
    missing_files = sum(1 for item in facts.sources if not item["exists"])
    missing_sections = sum(
        len(item["sections_missing"]) for item in facts.sources)
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


def merge(path: Path, row: Mapping[str, str]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if target.exists():
        with target.open(encoding="utf-8", newline="") as handle:
            for old in csv.DictReader(handle):
                existing[tuple(old.get(key, "") for key in _KEY)] = {
                    field: old.get(field, "") for field in FIELDS}
    existing[tuple(row.get(key, "") for key in _KEY)] = {
        field: row.get(field, "") for field in FIELDS}

    handle = tempfile.NamedTemporaryFile(
        "w", delete=False, dir=str(target.parent), encoding="utf-8", newline="")
    try:
        writer = csv.DictWriter(handle, fieldnames=list(FIELDS))
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
