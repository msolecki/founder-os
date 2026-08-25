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


_ARITHMETIC = re.compile(
    r"Available\s+(?P<available>[\d.]+)\s*h.*?"
    r"Committed delivery\s+(?P<delivery>[\d.]+)\s*h.*?"
    r"Free\s+(?P<free>[\d.]+)\s*h.*?"
    r"Planned\s+(?P<planned>[\d.]+)\s*h", re.S)
_TABLE_ROW = re.compile(r"^\|(?P<cells>.+)\|[ \t]*$", re.M)
_TIME_RANGE = re.compile(r"(\d{1,2}):(\d{2})\s*[–—-]\s*(\d{1,2}):(\d{2})")
_SIGNAL = re.compile(
    r"^(?P<name>[^—]+?)\s*—\s*source:\s*(?P<source>[^—]+?)\s*—\s*"
    r"(?P<value>-?[\d.]+)\s*—\s*normal\s*(?P<low>[\d.]+)\s*[–—-]\s*"
    r"(?P<high>[\d.]+)"
    r"(?:\s*—\s*last four:\s*(?P<series>[\d.,\s]+))?\s*$")


@dataclass(frozen=True)
class Signal:
    name: str
    source: str
    value: Optional[float]
    low: Optional[float]
    high: Optional[float]
    series: Tuple[float, ...]
    state: str


@dataclass(frozen=True)
class Block:
    day: str
    hours: Optional[float]
    title: str
    serves: str


def build_brief(sources, today: date) -> Panel:
    cite = "reviews/daily/"
    newest = sources.newest_member("reviews/daily/")
    if newest is None or not newest.readable:
        return Panel(id="brief", title="Today", status=STATUS_MISSING,
                     facts=(unknown("one_thing", cite),), citations=(cite,))
    cite = newest.path
    one_thing = (newest.sections.get("## The one thing") or "").strip()
    trade = (newest.sections.get("## The trade") or "").strip()
    rotting = newest.sections.get("## Rotting")
    triage = newest.sections.get("## Triage")

    facts = [
        text_fact("one_thing", one_thing, "%s ## The one thing" % cite)
        if one_thing else unknown("one_thing", "%s ## The one thing" % cite),
        text_fact("trade", trade, "%s ## The trade" % cite)
        if trade else unknown("trade", "%s ## The trade" % cite),
        number_fact("rotting_count", len(parse.split_entries(rotting)),
                    str(len(parse.split_entries(rotting))),
                    "%s ## Rotting" % cite)
        if rotting is not None else unknown("rotting_count", "%s ## Rotting" % cite),
        number_fact("triage_count", len(parse.split_entries(triage)),
                    str(len(parse.split_entries(triage))),
                    "%s ## Triage" % cite)
        if triage is not None else unknown("triage_count", "%s ## Triage" % cite),
    ]
    stamped = parse.parse_iso_date(Path(cite).stem)
    if stamped is not None:
        age = (today - stamped).days
        facts.append(number_fact("brief_age_days", age, "%d days" % age, cite))
    else:
        facts.append(unknown("brief_age_days", cite))
    return Panel(id="brief", title="Today", status=panel_status(tuple(facts)),
                 facts=tuple(facts), citations=(cite,))


def build_signals(sources):
    cite = "metrics.md ## Signals"
    body = sources.section("metrics.md", "## Signals")
    if body is None:
        return (Panel(id="signals", title="Signals", status=STATUS_MISSING,
                      facts=(unknown("signal_count", cite),), citations=(cite,)), ())
    signals = []
    for entry in parse.split_entries(body):
        match = _SIGNAL.match(entry.title.strip())
        if match is None:
            continue
        series_raw = match.group("series") or ""
        series = tuple(
            float(part) for part in re.findall(r"-?[\d.]+", series_raw))
        value = float(match.group("value"))
        low = float(match.group("low"))
        high = float(match.group("high"))
        if value < low:
            state = "below"
        elif value > high:
            state = "above"
        else:
            state = "in"
        signals.append(Signal(
            name=match.group("name").strip(),
            source=match.group("source").strip(),
            value=value, low=low, high=high, series=series, state=state))
    facts = [number_fact("signal_count", len(signals), str(len(signals)), cite)]
    for signal in signals:
        facts.append(number_fact(
            "signal.%s" % signal.name, signal.value,
            "%g" % signal.value, cite))
    return (Panel(id="signals", title="Signals",
                  status=panel_status(tuple(facts)), facts=tuple(facts),
                  citations=(cite,)), tuple(signals))


def _row_cells(line: str):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _range_hours(text: str) -> Optional[float]:
    match = _TIME_RANGE.search(text)
    if match is None:
        return None
    start = int(match.group(1)) * 60 + int(match.group(2))
    end = int(match.group(3)) * 60 + int(match.group(4))
    return round((end - start) / 60.0, 2) if end > start else None


def build_week(sources):
    arithmetic_cite = "week.md ## Arithmetic"
    blocks_cite = "week.md ## Blocks"
    arithmetic = sources.section("week.md", "## Arithmetic")
    match = _ARITHMETIC.search(arithmetic or "")
    labels = (("available_hours", "available"), ("delivery_hours", "delivery"),
              ("free_hours", "free"), ("planned_hours", "planned"))
    facts = []
    for key, group in labels:
        if match is None:
            facts.append(unknown(key, arithmetic_cite))
        else:
            value = float(match.group(group))
            facts.append(number_fact(key, value, "%gh" % value, arithmetic_cite))

    blocks = []
    body = sources.section("week.md", "## Blocks")
    for row in _TABLE_ROW.finditer(body or ""):
        cells = _row_cells(row.group(0))
        if len(cells) < 4:
            continue
        hours = _range_hours(cells[1])
        if hours is None:
            continue
        blocks.append(Block(day=cells[0], hours=hours, title=cells[2],
                            serves=cells[3]))

    per_bet = {}
    for block in blocks:
        per_bet[block.serves] = per_bet.get(block.serves, 0.0) + (block.hours or 0.0)
    for key in sorted(per_bet):
        facts.append(number_fact("planned.%s" % key, round(per_bet[key], 2),
                                 "%gh" % round(per_bet[key], 2), blocks_cite))
    facts.append(number_fact("block_count", len(blocks), str(len(blocks)),
                             blocks_cite))
    return (Panel(id="week", title="This week",
                  status=panel_status(tuple(facts)), facts=tuple(facts),
                  citations=(arithmetic_cite, blocks_cite)), tuple(blocks))


def _money_fact(key, body, label, cite):
    raw = parse.parse_field(body or "", label)
    value = parse.parse_money(raw)
    if value.number is None:
        return unknown(key, cite)
    return number_fact(key, value.number, raw, cite, currency=value.currency)


def build_cash(sources, today: date) -> Panel:
    close_cite = "metrics.md ## Close"
    runway_cite = "metrics.md ## Runway"
    close = sources.section("metrics.md", "## Close")
    runway = sources.section("metrics.md", "## Runway")
    facts = [
        _money_fact("booked", close, "Booked", close_cite),
        _money_fact("collected", close, "Collected", close_cite),
        _money_fact("effective_rate", close, "Effective rate", close_cite),
        _money_fact("cash_on_hand", close, "Cash on hand", close_cite),
        _money_fact("runway_months", runway, "Runway", runway_cite),
    ]
    closed = parse.parse_iso_date(parse.parse_field(close or "", "Closed"))
    if closed is not None:
        age = (today - closed).days
        facts.append(number_fact("close_age_days", age, "%d days" % age, close_cite))
    else:
        facts.append(unknown("close_age_days", close_cite))
    return Panel(id="cash", title="Cash and rate",
                 status=panel_status(tuple(facts)), facts=tuple(facts),
                 citations=(close_cite, runway_cite))


_QUEUE_SECTIONS = ("## Doing", "## Queued", "## Blocked", "## Done", "## Dropped")


def build_queue(sources, thresholds) -> Panel:
    cite = "queue.md"
    caps = (thresholds or {}).get("queue", {})
    facts = []
    counts = {}
    for heading in _QUEUE_SECTIONS:
        key = heading.replace("## ", "").lower()
        body = sources.section("queue.md", heading)
        section_cite = "%s %s" % (cite, heading)
        if body is None:
            facts.append(unknown(key, section_cite))
            continue
        count = len(parse.split_entries(body))
        counts[key] = count
        facts.append(number_fact(key, count, str(count), section_cite))

    over = 0
    for key, cap_key in (("doing", "doing_cap"), ("queued", "queued_cap")):
        cap = caps.get(cap_key)
        if cap is None:
            continue
        facts.append(number_fact(
            cap_key, cap, "%g" % cap, "references/thresholds.yaml"))
        if counts.get(key) is not None and counts[key] > cap:
            over += 1
    facts.append(number_fact("over_cap", over, str(over),
                             "references/thresholds.yaml"))
    return Panel(id="queue", title="Queue", status=panel_status(tuple(facts)),
                 facts=tuple(facts), citations=(cite, "references/thresholds.yaml"))


def build_facts(sources, today: date, generated: str, thresholds) -> Facts:
    bets_panel, bets = build_bets(sources, today)
    signals_panel, signals = build_signals(sources)
    week_panel, blocks = build_week(sources)
    panels = {
        "brief": build_brief(sources, today),
        "bets": bets_panel,
        "pipeline": build_pipeline(sources, today),
        "signals": signals_panel,
        "week": week_panel,
        "queue": build_queue(sources, thresholds),
        "cash": build_cash(sources, today),
    }

    findings = []
    described = []
    for path in sorted(sources.files):
        entry = sources.files[path]
        described.append({
            "path": path, "exists": entry.exists, "readable": entry.readable,
            "sha256": entry.sha256, "mtime": entry.mtime,
            "sections_found": sorted(entry.sections),
            "sections_missing": list(entry.missing),
        })
        if not entry.exists:
            findings.append(Finding("warn", "file-absent",
                                    "%s is declared but not present" % path, path))
        elif not entry.readable:
            findings.append(Finding("serious", "file-unreadable",
                                    "%s could not be decoded as UTF-8" % path, path))
        for heading in entry.missing:
            findings.append(Finding("warn", "section-missing",
                                    "%s has no %s" % (path, heading),
                                    "%s %s" % (path, heading)))

    return Facts(
        schema=SCHEMA, generated=generated, today=today.isoformat(),
        business={"slug": sources.slug, "name": sources.name,
                  "home": str(sources.home), "timezone": sources.timezone},
        panels=panels, findings=tuple(findings), sources=tuple(described),
        details={"bets": bets, "signals": signals, "blocks": blocks})


def _fact_dict(item: Fact):
    return {"key": item.key, "number": item.number, "display": item.display,
            "cite": item.cite, "currency": item.currency, "known": item.known}


def to_dict(facts: Facts):
    return {
        "schema": facts.schema,
        "generated": facts.generated,
        "today": facts.today,
        "business": dict(facts.business),
        "sources": [dict(item) for item in facts.sources],
        "panels": {
            key: {
                "id": panel.id,
                "title": panel.title,
                "status": panel.status,
                "hash": panel_hash(panel),
                "facts": [_fact_dict(item) for item in panel.facts],
                "citations": list(panel.citations),
                "readings": [
                    {"label": reading.label, "fact": _fact_dict(reading.fact)}
                    for reading in panel.readings],
                "settle_with": panel.settle_with,
            }
            for key, panel in sorted(facts.panels.items())
        },
        "integrity": [
            {"severity": f.severity, "check": f.check, "detail": f.detail,
             "cite": f.cite}
            for f in facts.findings],
    }
