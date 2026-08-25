"""Facts -> one HTML document. Pure: it takes values and returns a string.

Two rules shape the markup. Every panel ends with the file and section its
numbers came from, because a figure without a source is the thing this package
argues against. And a value that could not be read renders as words — "not
recorded" — never as a zero that looks like a measurement.
"""
from __future__ import annotations

from typing import Sequence, Tuple

from . import charts, theme

TABS = (("today", "Today", True), ("track", "Track record", False),
        ("integrity", "Integrity", False), ("state", "State", False))

_SIGNAL_COLOUR = {"below": "var(--crit)", "above": "var(--warn)",
                  "in": "var(--good)", "unknown": "var(--neutral-mark)"}


def escape(text) -> str:
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _find(panel, key):
    if panel is None:
        return None
    for item in panel.facts:
        if item.key == key:
            return item
    return None


def fact_html(fact) -> str:
    if fact is None:
        return '<span class="unknown">not recorded</span>'
    if not fact.known:
        return '<span class="unknown">%s</span>' % escape(fact.display)
    return escape(fact.display)


def _cite(panel) -> str:
    if panel is None:
        return ""
    return '<div class="cite">%s</div>' % "".join(
        "<span>%s</span>" % escape(item) for item in panel.citations)


def _panel(title, note, body, panel, wide=False) -> str:
    return (
        '<section class="panel%s"><div class="panel-head">'
        '<h2 class="panel-title">%s</h2>'
        '<span class="panel-note">%s</span></div>%s%s</section>'
        % (" span-2" if wide else "", escape(title), escape(note), body,
           _cite(panel)))


def _numbers(caption, headers, rows) -> str:
    head = "".join("<th>%s</th>" % escape(item) for item in headers)
    body = "".join(
        "<tr>%s</tr>" % "".join("<td>%s</td>" % escape(cell) for cell in row)
        for row in rows)
    return ('<details class="numbers"><summary>%s</summary>'
            '<div class="table-scroll"><table><thead><tr>%s</tr></thead>'
            "<tbody>%s</tbody></table></div></details>"
            % (escape(caption), head, body))


def _contested(panel) -> str:
    if panel is None or not panel.readings:
        return ""
    rows = "".join(
        '<li><b>%s</b> — %s <span class="cite">%s</span></li>'
        % (escape(reading.label), escape(reading.fact.display),
           escape(reading.fact.cite))
        for reading in panel.readings)
    return ('<div class="contested"><p><b>Two readings disagree.</b></p>'
            "<ul>%s</ul><p>%s</p></div>"
            % (rows, escape(panel.settle_with or "")))


def _brief(facts) -> str:
    panel = facts.panels.get("brief")
    return ('<section class="brief">'
            '<div class="panel-title">The one thing</div>'
            '<p class="one-thing">%s</p>'
            '<div class="panel-title">The trade</div><p>%s</p>'
            '<div class="panel-title">Rotting</div><p>%s</p>'
            '<div class="panel-title">Triage</div><p>%s</p>%s</section>'
            % (fact_html(_find(panel, "one_thing")),
               fact_html(_find(panel, "trade")),
               fact_html(_find(panel, "rotting_count")),
               fact_html(_find(panel, "triage_count")),
               _cite(panel)))


def _bets(facts) -> str:
    panel = facts.panels.get("bets")
    bets = facts.details.get("bets") or ()
    blocks = []
    for index, bet in enumerate(bets):
        colour = "var(--bet-%d)" % (index % 2 + 1)
        days = _find(panel, "%s.days_to_judgment" % bet.key)
        meter = ""
        if bet.progress is not None and bet.target:
            meter = charts.track(
                [(bet.progress / bet.target, colour,
                  "%g of %g" % (bet.progress, bet.target), False)], marker=1.0,
                tall=True)
        elapsed = ""
        if bet.elapsed is not None:
            elapsed = charts.track(
                [(bet.elapsed, "var(--neutral-mark)",
                  "%d%% of the window spent" % round(bet.elapsed * 100), False)])
        elif bet.elapsed_assumed:
            elapsed = ('<p class="unknown">window not recorded — goals.md carries '
                       "no Opened: date for this bet</p>")
        blocks.append(
            '<article class="bet"><div><span class="chip chip-bet-%d">%s</span> '
            "<b>%s</b></div><p>%s</p>%s%s<p>%s</p></article>"
            % (index % 2 + 1, escape(bet.key), escape(bet.name),
               escape(bet.threshold or "no threshold recorded"), meter, elapsed,
               "Judged in %s" % fact_html(days)))
    rows = [[bet.key, bet.threshold or "", "%g" % bet.progress
             if bet.progress is not None else "not recorded",
             bet.judgment.isoformat() if bet.judgment else "not recorded"]
            for bet in bets]
    return _panel("Bets against their thresholds", "judgment dates from goals.md",
                  "".join(blocks) + _numbers(
                      "Show the numbers", ("Bet", "Threshold", "Now", "Judgment"),
                      rows),
                  panel, wide=True)


def _pipeline(facts) -> str:
    panel = facts.panels.get("pipeline")
    amount = _find(panel, "live_amount")
    body = ('<div class="stat-value">%s</div>'
            "<p>live across %s deals · %s overdue · coverage %s</p>%s"
            % (fact_html(amount), fact_html(_find(panel, "live_count")),
               fact_html(_find(panel, "overdue_count")),
               fact_html(_find(panel, "coverage")), _contested(panel)))
    return _panel("Pipeline", "", body, panel)


def _signals(facts) -> str:
    panel = facts.panels.get("signals")
    signals = facts.details.get("signals") or ()
    cards = []
    for signal in signals:
        colour = _SIGNAL_COLOUR.get(signal.state, "var(--neutral-mark)")
        cards.append(
            '<div class="signal"><div>%s</div>%s'
            '<div><span class="stat-value" style="color:%s">%g</span> '
            '<span class="chip">normal %g–%g</span></div></div>'
            % (escape(signal.name),
               charts.sparkline(list(signal.series), signal.low, signal.high,
                                colour, signal.name),
               colour, signal.value, signal.low, signal.high))
    rows = [[s.name] + ["%g" % v for v in s.series] +
            ["%g–%g" % (s.low, s.high), s.source] for s in signals]
    return _panel("Signals", "", "".join(cards) + _numbers(
        "Show the numbers", ("Signal", "1", "2", "3", "4", "Normal", "Source"),
        rows), panel)


def _week(facts) -> str:
    panel = facts.panels.get("week")
    blocks = facts.details.get("blocks") or ()
    available = _find(panel, "available_hours")
    segments = []
    if available is not None and available.known and available.number:
        total = available.number
        delivery = _find(panel, "delivery_hours")
        if delivery is not None and delivery.known:
            segments.append((delivery.number / total, "var(--neutral-mark)",
                             "delivery %gh" % delivery.number, False))
        planned = sorted((item for item in panel.facts
                          if item.key.startswith("planned.")),
                         key=lambda item: item.key)
        for index, item in enumerate(planned):
            segments.append((item.number / total,
                             "var(--bet-%d)" % (index % 2 + 1),
                             "%s %gh" % (item.key.split(".")[1], item.number),
                             False))
    body = (charts.track(segments, tall=True) if segments else
            '<p class="unknown">not recorded</p>')
    rows = [[b.day, "%g" % (b.hours or 0), b.title, b.serves] for b in blocks]
    return _panel("This week", "", body + _numbers(
        "Show the numbers", ("Day", "Hours", "Block", "Serves"), rows), panel)


def _queue(facts) -> str:
    panel = facts.panels.get("queue")
    rows = []
    body = []
    for key, cap_key in (("doing", "doing_cap"), ("queued", "queued_cap"),
                         ("blocked", None)):
        count = _find(panel, key)
        cap = _find(panel, cap_key) if cap_key else None
        body.append("<p>%s %s%s</p>" % (
            escape(key.title()), fact_html(count),
            " / %s" % fact_html(cap) if cap is not None else ""))
        if count is not None and count.known and cap is not None and cap.number:
            body.append(charts.track(
                [(count.number / cap.number, "var(--good)",
                  "%g of %g" % (count.number, cap.number), False)]))
        rows.append([key, count.display if count else "not recorded",
                     cap.display if cap else ""])
    return _panel("Queue", "caps from references/thresholds.yaml",
                  "".join(body) + _numbers(
                      "Show the numbers", ("Section", "Count", "Cap"), rows),
                  panel)


def _cash(facts) -> str:
    panel = facts.panels.get("cash")
    keys = (("runway_months", "Runway (months)"), ("effective_rate", "Effective rate"),
            ("collected", "Collected"), ("booked", "Booked"),
            ("cash_on_hand", "Cash on hand"), ("close_age_days", "Close age"))
    body = "".join(
        "<p>%s: <b>%s</b></p>" % (escape(label), fact_html(_find(panel, key)))
        for key, label in keys)
    rows = [[label, fact_html(_find(panel, key))] for key, label in keys]
    return _panel("Cash and rate", "", body + _numbers(
        "Show the numbers", ("Measure", "Value"), rows), panel)


def _view(business, facts) -> str:
    return ('<div class="layout"><aside class="rail">%s</aside>'
            '<main class="panels">%s%s%s%s%s%s</main></div>'
            % (_brief(facts), _bets(facts), _pipeline(facts), _signals(facts),
               _week(facts), _queue(facts), _cash(facts)))


def _tabs() -> str:
    return '<div class="tabs" role="tablist">%s</div>' % "".join(
        '<button class="tab" type="button" role="tab" aria-selected="%s"%s>%s'
        "</button>"
        % ("true" if active else "false", "" if active else " disabled",
           escape(label))
        for _key, label, active in TABS)


def render(pages: Sequence[Tuple[object, object]], generated: str,
           active_slug: str = "", paused: int = 0) -> str:
    first = pages[0][1]
    title = escape(first.business.get("name") or "Founder OS")
    excluded = (" · %d paused business excluded" % paused) if paused else ""
    views = "".join(
        '<section class="view" id="business-%s"%s>%s</section>'
        % (escape(business.slug or "single"),
           "" if index == 0 else " hidden", _view(business, facts))
        for index, (business, facts) in enumerate(pages))
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "%s\n<title>%s — Founder OS</title>\n<style>%s</style>\n</head>\n<body>\n"
        '<header class="masthead"><div class="wrap"><b>Founder OS</b> · %s'
        '<span class="chip">generated %s%s</span></div>%s</header>\n'
        '<div class="wrap">%s</div>\n'
        "<script>document.body.classList.add('js');</script>\n"
        "</body>\n</html>\n"
        % (theme.CSP, title, theme.STYLESHEET, title, escape(generated),
           escape(excluded), _tabs(), views))
