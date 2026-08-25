"""Inline SVG and HTML chart primitives. Pure functions returning strings.

No chart library, vendored or otherwise. The page must open from `file://` on a
machine with no network, and a founder should be able to read the markup and see
exactly which number produced which mark.
"""
from __future__ import annotations

import math
from typing import Optional, Sequence, Tuple

PLOT_TOP = 8.0
PLOT_BOTTOM = 44.0
PLOT_INSET = 8.0
PLOT_HEIGHT = PLOT_BOTTOM - PLOT_TOP


def _escape(text: str) -> str:
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def domain_max(values: Sequence[float], high: Optional[float]) -> float:
    candidates = [value for value in values if value is not None]
    if high is not None:
        candidates.append(high)
    if not candidates:
        return 1.0
    return float(math.floor(max(candidates)) + 1)


def point_at(index: int, value: float, count: int, ceiling: float,
             width: int = 160) -> Tuple[float, float]:
    span = width - 2 * PLOT_INSET
    x = PLOT_INSET if count <= 1 else PLOT_INSET + index * (span / (count - 1))
    y = PLOT_BOTTOM - (value / ceiling) * PLOT_HEIGHT if ceiling else PLOT_BOTTOM
    return (round(x, 2), round(y, 2))


def sparkline(values: Sequence[float], low: Optional[float],
              high: Optional[float], colour: str, label: str,
              width: int = 160, height: int = 52) -> str:
    if not values:
        return ""
    ceiling = domain_max(values, high)
    points = [point_at(index, value, len(values), ceiling, width)
              for index, value in enumerate(values)]
    parts = [
        '<svg class="spark" viewBox="0 0 %d %d" role="img" aria-label="%s">'
        % (width, height, _escape("%s: %s" % (
            label, ", ".join("%g" % value for value in values))))]
    if low is not None and high is not None:
        top = PLOT_BOTTOM - (high / ceiling) * PLOT_HEIGHT
        bottom = PLOT_BOTTOM - (low / ceiling) * PLOT_HEIGHT
        parts.append(
            '<rect x="0" y="%s" width="%d" height="%s" fill="var(--band)"></rect>'
            % (round(top, 2), width, round(bottom - top, 2)))
    parts.append(
        '<line x1="0" y1="%s" x2="%d" y2="%s" stroke="var(--grid)" '
        'stroke-width="1"></line>' % (PLOT_BOTTOM, width, PLOT_BOTTOM))
    parts.append(
        '<polyline points="%s" fill="none" stroke="%s" stroke-width="2" '
        'stroke-linejoin="round" stroke-linecap="round"></polyline>'
        % (" ".join("%s,%s" % pair for pair in points), colour))
    for index, (x, y) in enumerate(points):
        if index == len(points) - 1:
            parts.append(
                '<circle cx="%s" cy="%s" r="5" fill="%s" stroke="var(--surface)" '
                'stroke-width="2"></circle>' % (x, y, colour))
        else:
            parts.append('<circle cx="%s" cy="%s" r="2.5" fill="%s" '
                         'opacity="0.45"></circle>' % (x, y, colour))
    parts.append("</svg>")
    return "".join(parts)


def track(segments: Sequence[Tuple[float, str, str, bool]],
          marker: Optional[float] = None, tall: bool = False) -> str:
    pieces = []
    for fraction, colour, tooltip, hatched in segments:
        percent = round(max(0.0, min(1.0, fraction)) * 100, 2)
        classes = "fill hatch" if hatched else "fill"
        style = ("color:%s" % colour) if hatched else ("background:%s" % colour)
        pieces.append(
            '<div class="%s" style="width:%g%%;%s" data-tip="%s"></div>'
            % (classes, percent, style, _escape(tooltip)))
    body = '<div class="track%s">%s</div>' % (
        " tall" if tall else "", "".join(pieces))
    if marker is None:
        return body
    position = round(max(0.0, min(1.0, marker)) * 100, 2)
    return ('<div class="marker-wrap">%s<span class="marker" style="left:%g%%">'
            "</span></div>" % (body, position))
