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
from datetime import date, timedelta
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


def _as_number(text: Optional[str]) -> Optional[float]:
    """`float()` that answers instead of raising."""
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def unlistable(key: str, cite: str) -> Fact:
    """A section holding content this reader could not turn into items.

    Distinct from `unknown`'s default, which says the workspace records nothing:
    here the founder wrote something and the reader could not list it. Both read
    as "not recorded" on the page, and the point of having either is that neither
    is ever a zero — a `## Live` describing two deals in a sentence used to be
    counted as zero deals, cited to the file that names them.
    """
    return unknown(key, cite, "%s — %s is not written as a list"
                   % (NOT_RECORDED, cite))


def unlistable_finding(cite: str) -> "Finding":
    return Finding("warn", "section-unlistable",
                   "%s holds text this reader could not read as a list, so "
                   "nothing in it is counted" % cite, cite)


def number_fact(key, number, display, cite, currency=None) -> Fact:
    return Fact(key=key, number=float(number), display=display, cite=cite,
                currency=currency)


def text_fact(key: str, text: str, cite: str) -> Fact:
    return Fact(key=key, number=None, display=text, cite=cite)


def _count_fact(key: str, count: Optional[float], cite: str) -> Fact:
    if count is None:
        return unknown(key, cite)
    return number_fact(key, count, "%g" % count, cite)


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


def _entry_amount(entry) -> parse.Value:
    """What an entry records as its amount, or a Value carrying no number.

    `Amount:` is the record. A heading is read only when it carries a currency
    marker, because a heading is prose and prose has digits in it: "Q3 2026
    offsite" holds a number and no money, and a pipeline total built out of it
    is a figure the workspace never wrote. An entry with neither comes back
    unread, which is the caller's signal to stop counting rather than to count
    a zero.
    """
    recorded = parse.parse_field(entry.body, "Amount")
    if recorded is not None:
        return parse.parse_money(recorded)
    titled = parse.parse_money(entry.title)
    if titled.currency is not None:
        return titled
    return parse.Value(raw=entry.title, number=None, currency=None)


# The ingestion gate stamps an unverified claim inline — "$15,000 [VALIDATE]
# (per the founder's call note, 2026-07-10)" — and house-rules.md:89 allows such
# a figure to be written "but only carrying its tier". A total that swallows one
# and prints it bare is where the tier comes off, on the surface most likely to
# be quoted back: `references/ingestion-gate.md` calls a flattering number
# guilty until validated, and the whole file exists to stop exactly this.
_TIERED = re.compile(r"\[(VALIDATE|DISREGARD)\]")


def _tier_note(values, cite: str) -> Tuple[Fact, ...]:
    """A note naming how much of a total is not yet validated, or nothing."""
    counted = [item for item in values if item.number is not None]
    tiered = [item for item in counted if _TIERED.search(item.raw or "")]
    if not tiered:
        return ()
    return (text_fact(
        "live_unvalidated",
        "%d of %d amounts here carry [VALIDATE] and are counted in this total"
        % (len(tiered), len(counted)), cite),)


# An amount with no marker beside it is not "the same currency as the others" —
# it is an amount whose unit nobody wrote. Adding it into a dollar total invents
# the dollar, so it gets its own bucket and the panel goes contested.
_UNMARKED = ""
_UNMARKED_LABEL = "no currency recorded"


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
    if entries is None:
        return Panel(
            id="pipeline", title="Pipeline", status=STATUS_MISSING,
            facts=(unlistable("live_amount", live_cite),
                   unlistable("live_count", live_cite),
                   unlistable("overdue_count", live_cite)),
            citations=citations)
    values = [_entry_amount(entry) for entry in entries]

    # Everything below the amount is counted first, because none of it depends
    # on the currency. A panel that refuses to sum two currencies and then also
    # withholds the overdue count has stopped reporting a figure it could read.
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
    counted = (
        number_fact("live_count", len(entries), str(len(entries)), live_cite),
        number_fact("overdue_count", overdue, str(overdue), live_cite),
        coverage,
    ) + _tier_note(values, live_cite)

    priced = [item for item in values if item.number is not None]
    currencies = sorted({item.currency or _UNMARKED for item in priced})
    if len(currencies) > 1:
        readings = tuple(
            Reading(
                label=symbol or _UNMARKED_LABEL,
                fact=number_fact(
                    "live_amount", sum(
                        item.number for item in priced
                        if (item.currency or _UNMARKED) == symbol),
                    "%s%s" % (symbol, _money(sum(
                        item.number for item in priced
                        if (item.currency or _UNMARKED) == symbol))),
                    live_cite, currency=symbol or None))
            for symbol in currencies)
        settle = (
            "pipeline.md ## Live carries more than one currency; "
            "record one currency per workspace or split the file")
        if _UNMARKED in currencies:
            settle = ("pipeline.md ## Live mixes amounts that name a currency "
                      "with amounts that do not; write the currency against "
                      "every Amount:")
        return Panel(
            id="pipeline", title="Pipeline", status=STATUS_CONTESTED,
            facts=counted, citations=citations, readings=readings,
            settle_with=settle)

    symbol = (currencies[0] if currencies else None) or None
    unread = len(entries) - len(priced)
    if unread:
        # A sum of the deals that happened to carry a price, printed beside a
        # count of all of them, is a smaller number than the pipeline wearing
        # the pipeline's name.
        amount = unknown(
            "live_amount", live_cite,
            "%s — %d of %d deals record no amount"
            % (NOT_RECORDED, unread, len(entries)))
    elif priced:
        total = sum(item.number for item in priced)
        amount = number_fact(
            "live_amount", total, "%s%s" % (symbol or "", _money(total)),
            live_cite, currency=symbol)
    else:
        amount = number_fact("live_amount", 0, "%s0" % (symbol or ""), live_cite)

    facts = (amount,) + counted
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
    verdict: Optional[str] = None
    verdict_line: Optional[str] = None


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
        if entries is None:
            return None
        if spec.minimum is None:
            return float(len(entries))
        matched = 0
        for entry in entries:
            value = _entry_amount(entry)
            # One unreadable amount and the filtered count is a guess for the
            # whole section, because the entry that could not be read is
            # exactly the one that might have cleared the minimum.
            if value.number is None:
                return None
            if value.number >= spec.minimum:
                matched += 1
        return float(matched)

    # A directory that exists and holds nothing counts zero — that is a reading,
    # and the founder has sent no proposals. A directory nobody has created
    # records nothing at all, and a zero there is a measurement of a drawer that
    # does not exist. `Sources.directories` is the only thing that separates the
    # two, since both arrive as an empty members tuple.
    members = sources.members.get(spec.path)
    if not members:
        if sources.directories.get(spec.path):
            return 0.0
        return None
    matched = 0
    for member in members:
        section = member.sections.get(spec.section)
        if section is None or not section.strip() or parse.is_declared_empty(section):
            continue
        if spec.minimum is not None:
            # A member section is founder prose, so the first number in it is
            # whatever the sentence happened to mention — a date, a day of the
            # month, an hour. Only a labelled `Amount:` is the amount.
            recorded = parse.parse_field(section, "Amount")
            if recorded is None:
                return None
            value = parse.parse_money(recorded)
            if value.number is None:
                return None
            if value.number < spec.minimum:
                continue
        matched += 1
    return float(matched)


# `quarterly-planning` replaces goals.md every quarter and writes the second
# form; `### B1 — <name>` is what the worked example and the first-run scaffold
# carry. Both split into the id the week plan's `serves` cell names and the name
# the founder reads, so both are accepted and the id is normalised to `B<n>`.
_BET_TITLE = re.compile(r"\s+[—–-]\s+|:\s+")
_BET_KEY = re.compile(r"^bet\s+B?(?P<number>\d+)$", re.I)

# The label on the left is what the owning skill writes; the one on the right is
# what the worked example carries. A reader that knows only one of the two is a
# reader that reports a recorded bet as blank.
_THRESHOLD_LABELS = ("Threshold", "Outcome")
_KILL_LABELS = ("Kill condition", "Kill if")
_OPENED_LABELS = ("Opened", "Start date")

_CONTINUED_JUDGMENT = re.compile(r"\bby\s+(\d{4}-\d{2}-\d{2})")


def _first_field(body, labels):
    for label in labels:
        found = parse.parse_field(body, label)
        if found is not None:
            return found
    return None


def _bet_key(title: str):
    parts = _BET_TITLE.split(title, maxsplit=1)
    key = parts[0].strip()
    name = parts[1].strip() if len(parts) > 1 else ""
    numbered = _BET_KEY.match(key)
    return ("B%s" % numbered.group("number") if numbered else key, name)


def build_bets(sources, today: date):
    cite = "goals.md ## Bets"
    body = sources.section("goals.md", "## Bets")
    if body is None:
        return (Panel(id="bets", title="Bets", status=STATUS_MISSING,
                      facts=(unknown("bets_open", cite),), citations=(cite,)),
                (), ())

    entries = parse.split_entries(body)
    if entries is None:
        return (Panel(id="bets", title="Bets", status=STATUS_MISSING,
                      facts=(unlistable("bets_open", cite),),
                      citations=(cite,)),
                (), (unlistable_finding(cite),))

    bets = []
    findings = []
    facts = [number_fact("bets_open", 0, "0", cite)]
    for entry in entries:
        key, name = _bet_key(entry.title)
        judgment = parse.parse_iso_date(parse.parse_field(entry.body, "Judgment date"))
        opened = parse.parse_iso_date(_first_field(entry.body, _OPENED_LABELS))
        kill = _first_field(entry.body, _KILL_LABELS)

        # `kill-or-continue` adds one line and is forbidden from deleting the
        # block, so a verdict under `## Bets` is the prescribed state of a bet
        # that is over. Counting it open reports two bets on a day the company
        # ran one, and the countdown on its card counts down to a judgment that
        # has already been delivered.
        killed = parse.parse_field(entry.body, "Killed")
        continued = parse.parse_field(entry.body, "Continued")
        verdict = "killed" if killed else ("continued" if continued else None)
        verdict_line = killed or continued
        if continued:
            # The continue's own date is the day it was granted; the new
            # judgment date is the one written after `by`.
            extended = _CONTINUED_JUDGMENT.search(continued)
            if extended is not None:
                judgment = parse.parse_iso_date(extended.group(1))

        raw_counted = parse.parse_field(entry.body, "Counted from")
        counted = parse_counted_from(raw_counted)
        if raw_counted is not None and counted is None:
            findings.append(Finding(
                "warn", "counted-from-unreadable",
                "goals.md %s carries a Counted from: line outside the grammar "
                "(%s), so the bet is not being measured" % (key, raw_counted),
                cite))
        raw_kill_counted = parse.parse_field(entry.body, "Kill counted from")
        kill_counted = parse_counted_from(raw_kill_counted)
        if raw_kill_counted is not None and kill_counted is None:
            findings.append(Finding(
                "warn", "counted-from-unreadable",
                "goals.md %s carries a Kill counted from: line outside the "
                "grammar (%s), so the kill condition is not being measured"
                % (key, raw_kill_counted), cite))

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
            threshold=_first_field(entry.body, _THRESHOLD_LABELS),
            opened=opened, judgment=judgment, kill=kill,
            kill_date=parse.parse_iso_date(kill), counted=counted,
            kill_counted=kill_counted, progress=progress, target=target,
            elapsed=elapsed, elapsed_assumed=elapsed_assumed,
            verdict=verdict, verdict_line=verdict_line))

        if verdict == "killed":
            facts.append(text_fact("%s.verdict" % key, verdict_line, cite))
            continue
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

    open_bets = [bet for bet in bets if bet.verdict != "killed"]
    facts[0] = number_fact("bets_open", len(open_bets), str(len(open_bets)), cite)
    return (Panel(id="bets", title="Bets", status=panel_status(tuple(facts)),
                  facts=tuple(facts), citations=(cite,)), tuple(bets),
            tuple(findings))


_ARITHMETIC = re.compile(
    r"Available\s+(?P<available>[\d.]+)\s*h.*?"
    r"Committed delivery\s+(?P<delivery>[\d.]+)\s*h.*?"
    r"Free\s+(?P<free>[\d.]+)\s*h.*?"
    r"Planned\s+(?P<planned>[\d.]+)\s*h", re.S)
_TABLE_ROW = re.compile(r"^\|(?P<cells>.+)\|[ \t]*$", re.M)
_TIME_RANGE = re.compile(r"(\d{1,2}):(\d{2})\s*[–—-]\s*(\d{1,2}):(\d{2})")
# The normal band may be written as a range ("normal 3-5") or as a single value
# ("normal 1"), which is the form signal-check's own output template ships and
# the only form available for a signal whose normal is one. A single value is a
# band of width nothing, not a missing band.
#
# `range: not yet` is the third form, and signal-check rule 5 mandates it for a
# signal with fewer than four readings: with no range yet, writing one is
# inventing the target the founder then manages against for a quarter. The
# reading itself is recorded, so the line is read and the band is the part that
# is unknown — refusing the whole line drops the newest signal in the file,
# which is the one a founder starting a measurement most needs to see.
_SIGNAL = re.compile(
    r"^(?P<name>[^—]+?)\s*—\s*source:\s*(?P<source>[^—]+?)\s*—\s*"
    r"(?P<value>-?[\d.]+)\s*—\s*"
    r"(?:normal\s*(?P<low>[\d.]+)(?:\s*[–—-]\s*(?P<high>[\d.]+))?"
    r"|range:\s*not\s+yet)"
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


# `+7 more — handed to triage` under `## Rotting`, and `+7 items handed to
# triage` as the whole of `## Triage`. Both are the brief's own record of the
# items it chose not to print, and both are prose rather than list items.
_HANDED_OVER = re.compile(r"^\+\s*(?P<count>\d+)\b", re.M)


def _rotting_count(body: str) -> Optional[float]:
    """Printed items plus the remainder the brief says it withheld."""
    handed = _HANDED_OVER.search(body)
    entries = parse.split_entries(
        _HANDED_OVER.sub("", body) if handed else body)
    if entries is None:
        return None
    return float(len(entries) + (int(handed.group("count")) if handed else 0))


def _triage_count(body: str) -> Optional[float]:
    """`## Triage` is one line of prose, so it is read as a line, not a list.

    daily-brief writes `none | <+n items handed to triage>` — never bullets, so
    counting entries in it reported 0 for every brief the package has ever
    written, and reported it as a number rather than as "not recorded".
    """
    text = body.strip()
    handed = _HANDED_OVER.search(text)
    if handed is not None:
        return float(handed.group("count"))
    if not text or text.lower().startswith("none"):
        return 0.0
    return None


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
        _count_fact("rotting_count", _rotting_count(rotting)
                    if rotting is not None else None,
                    "%s ## Rotting" % cite),
        _count_fact("triage_count", _triage_count(triage)
                    if triage is not None else None,
                    "%s ## Triage" % cite),
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
                      facts=(unknown("signal_count", cite),), citations=(cite,)),
                (), ())
    entries = parse.split_entries(body)
    if entries is None:
        return (Panel(id="signals", title="Signals", status=STATUS_MISSING,
                      facts=(unlistable("signal_count", cite),),
                      citations=(cite,)),
                (), (unlistable_finding(cite),))
    signals = []
    unreadable = []
    for entry in entries:
        match = _SIGNAL.match(entry.title.strip())
        if match is None:
            unreadable.append(entry.title.strip())
            continue
        series_raw = match.group("series") or ""
        raw_low = match.group("low")
        raw_high = match.group("high") or raw_low
        value = _as_number(match.group("value"))
        low = _as_number(raw_low) if raw_low else None
        high = _as_number(raw_high) if raw_high else None

        # The grammar accepts anything shaped like a number, and only the
        # conversion can tell "3-5" from "3..5". A figure that will not convert
        # makes the line one this reader could not read — which this module
        # already knows how to report — and never a traceback: a mistyped band
        # in metrics.md must not take the whole page down.
        if (value is None or (raw_low and low is None)
                or (raw_high and high is None)):
            unreadable.append(entry.title.strip())
            continue
        series = tuple(
            number for number in
            (_as_number(part) for part in re.findall(r"-?[\d.]+", series_raw))
            if number is not None)
        if low is None or high is None:
            state = "unknown"
        elif value < low:
            state = "below"
        elif value > high:
            state = "above"
        else:
            state = "in"
        signals.append(Signal(
            name=match.group("name").strip(),
            source=match.group("source").strip(),
            value=value, low=low, high=high, series=series, state=state))

    # A count over a section whose lines were dropped is the confident number
    # this module exists to refuse. `## Signals` is hand-edited prose, and the
    # line that fell outside the grammar is as likely as any other to be the
    # one the founder needed read.
    if unreadable:
        count = unknown(
            "signal_count", cite,
            "%s — %d of %d lines in ## Signals could not be read"
            % (NOT_RECORDED, len(unreadable), len(signals) + len(unreadable)))
    else:
        count = number_fact("signal_count", len(signals), str(len(signals)), cite)
    facts = [count]
    for signal in signals:
        facts.append(number_fact(
            "signal.%s" % signal.name, signal.value,
            "%g" % signal.value, cite))
    findings = tuple(
        Finding("warn", "signal-unreadable",
                "metrics.md ## Signals holds a line outside the signal grammar "
                "(%s), so it is counted nowhere" % line, cite)
        for line in unreadable)
    return (Panel(id="signals", title="Signals",
                  status=panel_status(tuple(facts)), facts=tuple(facts),
                  citations=(cite,)), tuple(signals), findings)


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


def _money_fact(key, body, labels, cite):
    if isinstance(labels, str):
        labels = (labels,)
    raw = _first_field(body or "", labels)
    value = parse.parse_money(raw)
    if value.number is None:
        return unknown(key, cite)
    return number_fact(key, value.number, raw, cite, currency=value.currency)


# `runway-forecast` writes `Runway, zero new revenue:`; the worked example
# writes `Runway:`. Both are the same figure under the same heading.
_RUNWAY_LABELS = ("Runway", "Runway, zero new revenue")

_CLOSE_MONTH = re.compile(r"(?P<year>\d{4})-(?P<month>\d{2})(?!-)")


def _close_date(sources, close):
    """The day the close describes, and whether that day itself was recorded.

    `revenue-review` writes no `Closed:` line — the month is in the heading
    (`## Close — 2026-06`), which is the only record of which month was closed.
    A month names its last day and no more, so that is what the age is measured
    from; nothing here invents the day the founder actually did the close.

    The two are not the same measurement — the day the close was performed and
    the last day of the period it covers can be weeks apart — so the caller is
    told which one it got, and says so beside the number.
    """
    stamped = parse.parse_iso_date(parse.parse_field(close or "", "Closed"))
    if stamped is not None:
        return stamped, True
    heading = sources.heading("metrics.md", "## Close") or ""
    dated = parse.parse_iso_date(heading)
    if dated is not None:
        return dated, True
    month = _CLOSE_MONTH.search(heading)
    if month is None:
        return None, False
    year, number = int(month.group("year")), int(month.group("month"))
    if not 1 <= number <= 12:
        return None, False
    return (date(year + number // 12, number % 12 + 1, 1)
            - timedelta(days=1)), False


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
        _money_fact("runway_months", runway, _RUNWAY_LABELS, runway_cite),
    ]
    closed, performed = _close_date(sources, close)
    if closed is not None:
        age = (today - closed).days
        facts.append(number_fact(
            "close_age_days", age,
            "%d days" % age if performed else "%d days from month end" % age,
            close_cite))
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
        entries = parse.split_entries(body)
        if entries is None:
            facts.append(unlistable(key, section_cite))
            continue
        counts[key] = len(entries)
        facts.append(number_fact(key, len(entries), str(len(entries)),
                                 section_cite))

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
    bets_panel, bets, bet_findings = build_bets(sources, today)
    signals_panel, signals, signal_findings = build_signals(sources)
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

    findings = list(bet_findings) + list(signal_findings)
    described = []

    # Eleven of the twenty-five declared paths are directories, and a daily
    # review or a proposal is only ever written inside one. Describing the flat
    # files alone left the Integrity view unable to report the section a member
    # lost — the one thing that view exists to report.
    #
    # A member is described, and it is not declared. `declared` is what the
    # counted inventory is drawn from: the map's own paths are a fixed set, and
    # counting members instead would put every archived daily review into
    # snapshots.csv's denominator, so the same workspace would score 13 files
    # present in month one and 52 in month six against a series a founder keeps
    # to compare with itself.
    inventory = [(path, sources.files[path], True) for path in sources.files]
    for directory in sources.members:
        inventory.extend(
            (member.path, member, False)
            for member in sources.members[directory])
    for path, entry, declared_path in sorted(inventory, key=lambda item: item[0]):
        described.append({
            "path": path, "declared": declared_path,
            "exists": entry.exists, "readable": entry.readable,
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

    # A declared directory is reported absent and nothing more: it has no
    # sections to lose and no digest to record, so it stays out of the counted
    # inventory, whose two columns are about files.
    for directory in sorted(sources.directories):
        if not sources.directories[directory]:
            findings.append(Finding(
                "warn", "file-absent",
                "%s is declared but not present" % directory, directory))

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
