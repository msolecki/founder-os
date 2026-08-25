"""Sources -> Facts. Pure: no filesystem, no clock, no network.

Two rules govern everything here and both exist because a generated page is read
as authoritative. First, unknown is not zero — a section we could not read
produces `NOT_RECORDED`, never a confident number. Second, a figure two files
disagree about is not resolved by this module; both readings survive to the page
with the field that would settle them named.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Mapping, Optional, Tuple

from . import parse

STATUS_OK = "ok"
STATUS_PARTIAL = "partial"
STATUS_CONTESTED = "contested"
STATUS_MISSING = "missing"
NOT_RECORDED = "not recorded"

SCHEMA = 1


@dataclass(frozen=True)
class Fact:
    key: str
    number: Optional[float]
    display: str
    cite: str
    currency: Optional[str] = None
    known: bool = True


@dataclass(frozen=True)
class Reading:
    label: str
    fact: Fact


@dataclass(frozen=True)
class Panel:
    id: str
    title: str
    status: str
    facts: Tuple[Fact, ...]
    citations: Tuple[str, ...]
    readings: Tuple[Reading, ...] = ()
    settle_with: Optional[str] = None


@dataclass(frozen=True)
class Finding:
    severity: str
    check: str
    detail: str
    cite: str


@dataclass(frozen=True)
class Facts:
    schema: int
    generated: str
    today: str
    business: Mapping[str, object]
    panels: Mapping[str, Panel]
    findings: Tuple[Finding, ...]
    sources: Tuple[Mapping[str, object], ...]
    details: Mapping[str, object] = field(default_factory=dict)


def unknown(key: str, cite: str, why: str = NOT_RECORDED) -> Fact:
    return Fact(key=key, number=None, display=why, cite=cite, known=False)


def number_fact(key, number, display, cite, currency=None) -> Fact:
    return Fact(key=key, number=float(number), display=display, cite=cite,
                currency=currency)


def text_fact(key: str, text: str, cite: str) -> Fact:
    return Fact(key=key, number=None, display=text, cite=cite)


def panel_status(facts: Tuple[Fact, ...]) -> str:
    if not facts:
        return STATUS_MISSING
    unknowns = [item for item in facts if not item.known]
    if len(unknowns) == len(facts):
        return STATUS_MISSING
    return STATUS_PARTIAL if unknowns else STATUS_OK


def panel_hash(panel: Panel) -> str:
    """A digest of this panel's facts only.

    Scoped to the panel rather than the file so an edit to the queue does not
    mark the pipeline's commentary stale. Commentary that is greyed out for no
    reason gets ignored, and then real staleness gets ignored with it.
    """
    payload = [
        [item.key, item.number, item.display, item.cite, item.currency, item.known]
        for item in sorted(panel.facts, key=lambda entry: entry.key)]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:7]


def _money(amount: float) -> str:
    return "{:,.0f}".format(amount)


def build_pipeline(sources, today: date) -> Panel:
    live_cite = "pipeline.md ## Live"
    review_cite = "pipeline.md ## Last review"
    citations = (live_cite, review_cite)
    body = sources.section("pipeline.md", "## Live")
    if body is None:
        return Panel(
            id="pipeline", title="Pipeline", status=STATUS_MISSING,
            facts=(unknown("live_amount", live_cite),
                   unknown("live_count", live_cite),
                   unknown("overdue_count", live_cite)),
            citations=citations)

    entries = parse.split_entries(body)
    values = []
    for entry in entries:
        raw = parse.parse_field(entry.body, "Amount") or entry.title
        values.append(parse.parse_money(raw))

    currencies = sorted({item.currency for item in values if item.currency})
    if len(currencies) > 1:
        readings = tuple(
            Reading(
                label=symbol,
                fact=number_fact(
                    "live_amount", sum(
                        item.number or 0 for item in values
                        if item.currency == symbol),
                    "%s%s" % (symbol, _money(sum(
                        item.number or 0 for item in values
                        if item.currency == symbol))),
                    live_cite, currency=symbol))
            for symbol in currencies)
        return Panel(
            id="pipeline", title="Pipeline", status=STATUS_CONTESTED,
            facts=(number_fact("live_count", len(entries),
                               str(len(entries)), live_cite),),
            citations=citations, readings=readings,
            settle_with="pipeline.md ## Live carries more than one currency; "
                        "record one currency per workspace or split the file")

    numbers = [item.number for item in values if item.number is not None]
    symbol = currencies[0] if currencies else None
    if numbers:
        total = sum(numbers)
        amount = number_fact(
            "live_amount", total, "%s%s" % (symbol or "", _money(total)),
            live_cite, currency=symbol)
    elif entries:
        amount = unknown("live_amount", live_cite)
    else:
        amount = number_fact("live_amount", 0, "%s0" % (symbol or ""), live_cite)

    overdue = 0
    for entry in entries:
        due = parse.parse_iso_date(parse.parse_field(entry.body, "Next action"))
        if due is not None and due < today:
            overdue += 1

    coverage_raw = parse.parse_field(
        sources.section("pipeline.md", "## Last review") or "", "Coverage")
    coverage = (
        number_fact("coverage", parse.parse_money(coverage_raw).number,
                    coverage_raw, review_cite)
        if coverage_raw and parse.parse_money(coverage_raw).number is not None
        else unknown("coverage", review_cite))

    facts = (
        amount,
        number_fact("live_count", len(entries), str(len(entries)), live_cite),
        number_fact("overdue_count", overdue, str(overdue), live_cite),
        coverage,
    )
    return Panel(id="pipeline", title="Pipeline", status=panel_status(facts),
                 facts=facts, citations=citations)
