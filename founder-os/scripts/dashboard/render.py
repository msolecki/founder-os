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
            .replace(">", "&gt;").replace('"', "&quot;")
            .replace("'", "&#39;"))


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


class Markup(str):
    """A table cell that is already HTML, so `_numbers` must not escape it.

    `_numbers` escapes every cell it is handed, which is right for the raw
    strings the other panels give it. The cash table needs the
    `<span class="unknown">` that marks a value the workspace does not record:
    escaped again it prints as angle brackets, dropped altogether it makes
    "not calculated this month" look like a figure.
    """


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
        "<tr>%s</tr>" % "".join(
            "<td>%s</td>" % (cell if isinstance(cell, Markup) else escape(cell))
            for cell in row)
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
                       "no Start date: for this bet</p>")
        # A judged bet says so. `kill-or-continue` leaves the block in place, so
        # without the verdict a dead bet keeps its threshold, its meter and its
        # judgment date and reads exactly like one still running — and a killed
        # bet has no countdown left, so the card fell through to "Judged in not
        # recorded" about a bet whose date and verdict goals.md both carry.
        verdict = ""
        if bet.verdict:
            verdict = "<p><b>%s</b> — %s</p>" % (
                escape(bet.verdict.title()), escape(bet.verdict_line or ""))
        countdown = ("" if bet.verdict == "killed"
                     else "<p>Judged in %s</p>" % fact_html(days))
        blocks.append(
            '<article class="bet"><div><span class="chip chip-bet-%d">%s</span> '
            "<b>%s</b></div><p>%s</p>%s%s%s%s</article>"
            % (index % 2 + 1, escape(bet.key), escape(bet.name),
               escape(bet.threshold or "no threshold recorded"), meter, elapsed,
               verdict, countdown))
    # A target the workspace records as 0 is a number. Only `None` is the
    # unread target, which is why this cell tests for it and the meter above
    # keeps its truthiness test — a meter against a target of nothing has no
    # fraction to draw.
    #
    # "open" is the absence of a verdict line, which is the same reading
    # `bets_open` is counted from: `kill-or-continue` may not delete the block,
    # so a bet with no verdict under `## Bets` has not been judged.
    rows = [[bet.key, bet.threshold or "", "%g" % bet.progress
             if bet.progress is not None else "not recorded",
             "%g" % bet.target if bet.target is not None else "not recorded",
             bet.judgment.isoformat() if bet.judgment else "not recorded",
             bet.verdict or "open"]
            for bet in bets]
    return _panel("Bets against their thresholds", "judgment dates from goals.md",
                  "".join(blocks) + _numbers(
                      "Show the numbers",
                      ("Bet", "Threshold", "Now", "Target", "Judgment",
                       "Verdict"), rows),
                  panel, wide=True)


def _pipeline(facts) -> str:
    panel = facts.panels.get("pipeline")
    amount = _find(panel, "live_amount")
    body = ('<div class="stat-value">%s</div>'
            "<p>live across %s deals · %s overdue · coverage %s</p>%s"
            % (fact_html(amount), fact_html(_find(panel, "live_count")),
               fact_html(_find(panel, "overdue_count")),
               fact_html(_find(panel, "coverage")), _contested(panel)))
    tier = _find(panel, "live_unvalidated")
    return _panel("Pipeline", tier.display if tier is not None else "", body,
                  panel)


def _band(signal) -> str:
    """The normal band as written, or the words for a signal that has none.

    `signal-check` rule 5 forbids inventing a range under four readings and
    mandates `range: not yet`, so a band of None is a signal too young to have
    one — not a signal read wrong, and not a band of zero.
    """
    if signal.low is None or signal.high is None:
        return ""
    return "%g–%g" % (signal.low, signal.high)


def _signals(facts) -> str:
    panel = facts.panels.get("signals")
    signals = facts.details.get("signals") or ()
    cards = []
    for signal in signals:
        colour = _SIGNAL_COLOUR.get(signal.state, "var(--neutral-mark)")
        band = _band(signal)
        cards.append(
            '<div class="signal"><div>%s</div>%s'
            '<div><span class="stat-value" style="color:%s">%g</span> '
            '<span class="chip">normal %s</span></div></div>'
            % (escape(signal.name),
               charts.sparkline(list(signal.series), signal.low, signal.high,
                                colour, signal.name),
               colour, signal.value,
               escape(band) if band
               else '<span class="unknown">not recorded</span>'))
    # `last four:` is a rolling window of four by convention, not by parse: the
    # regex accepts any count and metrics.md is hand-edited. A fixed seven-column
    # header shifts every later cell under the wrong heading the moment one
    # signal carries a different number of readings, so the header follows the
    # widest series and short rows are padded out to it.
    width = max((len(s.series) for s in signals), default=0)
    headers = (("Signal",) + tuple(str(index + 1) for index in range(width))
               + ("Normal", "Source"))
    rows = [[s.name] + ["%g" % v for v in s.series]
            + [""] * (width - len(s.series))
            + [_band(s) or "not recorded", s.source] for s in signals]
    # A line outside the signal grammar produces no card and no row, so without
    # this the measure simply vanishes: the founder sees two signals where
    # metrics.md records three, and nothing on the page says a line was dropped.
    # The analyzer already refuses to count them and says how many; the panel's
    # note is where that reaches the reader.
    count = _find(panel, "signal_count")
    note = "" if count is None or count.known else count.display
    return _panel("Signals", note, "".join(cards) + _numbers(
        "Show the numbers", headers, rows), panel)


def _week(facts) -> str:
    panel = facts.panels.get("week")
    blocks = facts.details.get("blocks") or ()
    available = _find(panel, "available_hours")
    segments = []
    booked = []
    total = 0.0
    if available is not None and available.known and available.number:
        total = available.number
        delivery = _find(panel, "delivery_hours")
        if delivery is not None and delivery.known:
            booked.append(("%gh delivery" % delivery.number, delivery.number))
            segments.append((delivery.number / total, "var(--neutral-mark)",
                             "delivery %gh" % delivery.number, False))
        planned = sorted((item for item in panel.facts
                          if item.key.startswith("planned.")),
                         key=lambda item: item.key)
        planned_hours = sum(item.number for item in planned)
        if planned:
            booked.append(("%gh in blocks" % planned_hours, planned_hours))
        for index, item in enumerate(planned):
            segments.append((item.number / total,
                             "var(--bet-%d)" % (index % 2 + 1),
                             "%s %gh" % (item.key.split(".")[1], item.number),
                             False))
    body = (charts.track(segments, tall=True) if segments else
            '<p class="unknown">not recorded</p>')
    # The bar can only draw a hundred per cent of the week. Committing more than
    # the week holds is exactly the thing a founder needs to see, and a clipped
    # bar looks identical to a week that fits, so the overflow is stated in
    # words as well.
    #
    # In hours, and by its parts. Adding the segments' fractions instead pushes
    # a week that lands exactly on the available hours past 1.0 by float error
    # (15.5/30 + 7.75/30 + 6.75/30 is 1.0000000000000002) and warns about a week
    # that fits. Block hours are rounded to a hundredth, so half of that is the
    # widest gap that can only be arithmetic noise. And the total of delivery
    # plus blocks is written in no file — week.md ## Arithmetic records its own,
    # different "Planned" figure — so the sentence states the two hours the
    # workspace does record rather than a sum the founder cannot look up.
    if booked and sum(hours for _label, hours in booked) - total > 0.005:
        body += ('<p class="over">Over-committed: %s against %gh available.</p>'
                 % (" plus ".join(label for label, _hours in booked), total))
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
    rows = [[label, Markup(fact_html(_find(panel, key)))] for key, label in keys]
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


def _name_of(business, facts) -> str:
    return str(facts.business.get("name") or business.slug or "this business")


def _switcher(pages, active: int) -> str:
    """One button per business, or nothing at all when there is only one.

    Without this the page holds every business but can reach only the first: the
    others are emitted `hidden` and no control in the document can clear it.
    """
    if len(pages) < 2:
        return ""
    buttons = []
    for index, (business, facts) in enumerate(pages):
        slug = escape(business.slug or "single")
        buttons.append(
            '<button class="tab" type="button" role="tab" data-business="%s" '
            'data-name="%s" aria-selected="%s" aria-controls="business-%s">'
            "%s</button>"
            % (slug, escape(_name_of(business, facts)),
               "true" if index == active else "false", slug,
               escape(_name_of(business, facts))))
    return ('<nav class="switch" role="tablist" aria-label="Business">%s</nav>'
            % "".join(buttons))


def render(pages: Sequence[Tuple[object, object]], generated: str,
           active_slug: str = "", paused: int = 0) -> str:
    # A slug naming no active business falls back to the first rather than
    # raising: the caller decides whether an unresolvable slug is an error, and
    # a page that renders nothing is worse than a page that renders the default.
    active = next((index for index, (business, _facts) in enumerate(pages)
                   if business.slug == active_slug), 0)
    current = pages[active][1]
    title = escape(current.business.get("name") or "Founder OS")
    excluded = (" · %d paused business%s excluded"
                % (paused, "es" if paused > 1 else "")) if paused else ""
    views = "".join(
        '<section class="view" id="business-%s"%s>%s</section>'
        % (escape(business.slug or "single"),
           "" if index == active else " hidden", _view(business, facts))
        for index, (business, facts) in enumerate(pages))
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "%s\n<title>%s — Founder OS</title>\n<style>%s</style>\n</head>\n<body>\n"
        '<header class="masthead"><div class="wrap"><b>Founder OS</b> · '
        '<span id="business-name">%s</span>'
        '<span class="chip">generated %s%s</span></div>%s</header>\n'
        '<div class="wrap">%s%s</div>\n'
        "<script>%s</script>\n"
        "</body>\n</html>\n"
        % (theme.CSP, title, theme.STYLESHEET, title, escape(generated),
           escape(excluded), _tabs(), _switcher(pages, active), views,
           theme.SCRIPT))
