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


_COUNTED = re.compile(
    r"^(?P<path>[A-Za-z0-9_./-]+)\s+##\s+(?P<section>[^|]+?)"
    r"(?:\s*\|\s*amount\s*>=\s*(?P<amount>\d+(?:\.\d+)?))?"
    r"(?:\s*\|\s*target\s+(?P<target>\d+(?:\.\d+)?))?\s*$")


@dataclass(frozen=True)
class CountSpec:
    path: str
    section: str
    minimum: Optional[float]
    target: Optional[float]


def parse_counted_from(raw: Optional[str]) -> Optional[CountSpec]:
    """The closed grammar from spec §9, or None.

    Closed on purpose. A grammar that falls back to best effort is a grammar that
    silently reports the wrong number for a bet the founder is about to judge.
    """
    match = _COUNTED.match((raw or "").strip())
    if match is None:
        return None
    section = match.group("section").strip()
    if not section:
        return None
    amount = match.group("amount")
    target = match.group("target")
    return CountSpec(
        path=match.group("path"),
        section="## %s" % section,
        minimum=float(amount) if amount else None,
        target=float(target) if target else None,
    )


@dataclass(frozen=True)
class Bet:
    key: str
    name: str
    threshold: Optional[str]
    opened: Optional[date]
    judgment: Optional[date]
    kill: Optional[str]
    kill_date: Optional[date]
    counted: Optional[CountSpec]
    kill_counted: Optional[CountSpec]
    progress: Optional[float]
    target: Optional[float]
    elapsed: Optional[float]
    elapsed_assumed: bool


def _count_against(sources, spec: CountSpec) -> Optional[float]:
    """How many things the declared source actually holds, or None.

    Two shapes, because the workspace has two. A flat file's section holds a list
    or a run of H3 blocks; a directory's section lives once inside each member
    file, which is what makes `drafts/proposals/ ## Sent` countable — a proposal
    counts when the founder has reported sending it, and not before.
    """
    body = sources.section(spec.path, spec.section)
    if body is not None:
        entries = parse.split_entries(body)
        if spec.minimum is None:
            return float(len(entries))
        matched = 0
        for entry in entries:
            raw = parse.parse_field(entry.body, "Amount") or entry.title
            value = parse.parse_money(raw)
            if value.number is not None and value.number >= spec.minimum:
                matched += 1
        return float(matched)

    members = sources.members.get(spec.path)
    if members is None:
        return None
    matched = 0
    for member in members:
        section = member.sections.get(spec.section)
        if section is None or not section.strip() or parse.is_declared_empty(section):
            continue
        if spec.minimum is not None:
            value = parse.parse_money(section)
            if value.number is None or value.number < spec.minimum:
                continue
        matched += 1
    return float(matched)


def build_bets(sources, today: date):
    cite = "goals.md ## Bets"
    body = sources.section("goals.md", "## Bets")
    if body is None:
        return (Panel(id="bets", title="Bets", status=STATUS_MISSING,
                      facts=(unknown("bets_open", cite),), citations=(cite,)), ())

    bets = []
    facts = [number_fact("bets_open", 0, "0", cite)]
    for entry in parse.split_entries(body):
        parts = re.split(r"\s+[—–-]\s+", entry.title, maxsplit=1)
        key = parts[0].strip()
        name = parts[1].strip() if len(parts) > 1 else ""
        judgment = parse.parse_iso_date(parse.parse_field(entry.body, "Judgment date"))
        opened = parse.parse_iso_date(parse.parse_field(entry.body, "Opened"))
        kill = parse.parse_field(entry.body, "Kill condition")
        counted = parse_counted_from(parse.parse_field(entry.body, "Counted from"))
        kill_counted = parse_counted_from(
            parse.parse_field(entry.body, "Kill counted from"))

        progress = _count_against(sources, counted) if counted else None
        target = counted.target if counted else None

        # No `Opened:` means no elapsed bar. A start date inferred from the
        # quarter would draw a fraction of a window nobody recorded, which is
        # the same class of claim as a figure we could not read.
        elapsed = None
        elapsed_assumed = opened is None
        if opened is not None and judgment is not None and judgment > opened:
            span = (judgment - opened).days
            elapsed = max(0.0, min(1.0, (today - opened).days / span))

        bets.append(Bet(
            key=key, name=name,
            threshold=parse.parse_field(entry.body, "Threshold"),
            opened=opened, judgment=judgment, kill=kill,
            kill_date=parse.parse_iso_date(kill), counted=counted,
            kill_counted=kill_counted, progress=progress, target=target,
            elapsed=elapsed, elapsed_assumed=elapsed_assumed))

        if judgment is not None:
            days = (judgment - today).days
            facts.append(number_fact(
                "%s.days_to_judgment" % key, days, "%d days" % days, cite))
        else:
            facts.append(unknown("%s.days_to_judgment" % key, cite))
        kill_date = parse.parse_iso_date(kill)
        if kill_date is not None:
            days = (kill_date - today).days
            facts.append(number_fact(
                "%s.days_to_kill" % key, days, "%d days" % days, cite))

    facts[0] = number_fact("bets_open", len(bets), str(len(bets)), cite)
    return (Panel(id="bets", title="Bets", status=panel_status(tuple(facts)),
                  facts=tuple(facts), citations=(cite,)), tuple(bets))
