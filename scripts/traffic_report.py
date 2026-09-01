#!/usr/bin/env python3
"""Read metrics/traffic.csv and print the five lines worth reading.

A data file with no reader is an archive, not a measurement — the same argument
`/experiment` makes about a test with no judgment date. Fifty-two weekly rows
that nobody compares are a slower way of knowing nothing.

Five lines, one comparison each, and the comparison is always four weeks against
the four before them. Week-on-week noise on numbers this small says nothing and
invites acting on it.
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import date, timedelta
from pathlib import Path

WINDOW_DAYS = 28


def load(path: Path):
    with path.open(encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("date")]
    return sorted(rows, key=lambda row: row["date"])


def _number(row, field) -> int:
    try:
        return int(row.get(field) or 0)
    except ValueError:
        return 0


def _split(rows, today):
    """The two 28-day windows, newest first, with nothing excluded yet.

    Bounded at the top as well as the bottom: `--today` can name a past date,
    and a row after it belongs to neither window rather than silently inflating
    the recent one.
    """
    recent_from = today - timedelta(days=WINDOW_DAYS)
    prior_from = today - timedelta(days=WINDOW_DAYS * 2)
    recent, prior = [], []
    for row in rows:
        try:
            stamp = date.fromisoformat(row["date"])
        except ValueError:
            continue
        if stamp > today:
            continue
        if stamp > recent_from:
            recent.append(row)
        elif stamp > prior_from:
            prior.append(row)
    return recent, prior


def windows(rows, today):
    """The same two windows with automation days partitioned out.

    A flagged day is dropped rather than zeroed. Zeroing it would say the repo
    had a quiet Tuesday; dropping it says we do not know, which is true.

    Both windows lose their flagged days and both report them. Dropping from
    one and disclosing the other is how a flat month prints as growth.
    """
    def flagged(window):
        keep, drop = [], []
        for row in window:
            (drop if row.get("automation_suspected") == "true"
             else keep).append(row)
        return keep, drop

    raw_recent, raw_prior = _split(rows, today)
    recent, flagged_recent = flagged(raw_recent)
    prior, flagged_prior = flagged(raw_prior)
    return recent, prior, flagged_recent, flagged_prior


def raw_windows(rows, today):
    """The same two windows with nothing excluded, for counts that are not traffic."""
    return _split(rows, today)


def total(rows, field) -> int:
    return sum(_number(row, field) for row in rows)


def delta(now: int, before: int, now_days: int, before_days: int) -> str:
    """Compare per measured day rather than sum against sum, and say so.

    The windows rarely hold the same number of measured days: automation days
    are dropped from both, and a day nobody recorded is in neither. Twenty-eight
    days of traffic set against twenty-three invents the difference.

    Which is exactly why the percentage cannot be printed bare beside two
    totals. Three prior days at five a day against twenty-eight recent days at
    four a day is `15` and `112` — a sevenfold rise — and the honest per-day
    comparison is `-20%`. Both numbers are right and the sentence was a lie, so
    the denominators travel with the figure that was computed from them.

    The three ways this has nothing to say are three different sentences,
    because "no prior window" printed beside a prior total of 108 denies the
    number next to it.
    """
    if not now_days:
        return "no measured day in the last 28"
    if not before_days:
        return "no measured day in the previous 28 to compare"
    if before == 0:
        return "up from nothing over %d measured day(s)" % before_days
    now_rate = now / now_days
    before_rate = before / before_days
    return "%+d%% per measured day, %d vs %d of them" % (
        round((now_rate - before_rate) / before_rate * 100),
        now_days,
        before_days,
    )


def latest(rows, field) -> str:
    for row in reversed(rows):
        if row.get(field):
            return row[field]
    return "unknown"


def last_day(rows):
    """The newest row that carries a real date, or None if no row does.

    `windows()` already skips a row it cannot parse; the default reporting date
    has to survive the same hand-edited file rather than raise on it.
    """
    for row in reversed(rows):
        try:
            return date.fromisoformat(row["date"])
        except ValueError:
            continue
    return None


def sources(directory: Path, today: date, limit=3):
    """The newest referrer snapshot, and whether it falls inside the window.

    They are photographs, so the newest is the only one worth reading — but a
    photograph from outside the window is of a different month, and printing it
    beside a 28-day trend reads as part of it. Named and not counted.

    A snapshot inside the window with no rows is a quiet week that GitHub did
    report, which is a different sentence from having no snapshot at all.
    """
    window_from = today - timedelta(days=WINDOW_DAYS)
    inside, outside = None, None
    for snapshot in sorted(directory.glob("referrers-*.csv")):
        try:
            stamp = date.fromisoformat(snapshot.stem.split("referrers-", 1)[1])
        except (IndexError, ValueError):
            continue
        if stamp > window_from:
            inside = snapshot
        else:
            outside = snapshot
    if inside is None:
        return (outside.name if outside else None), [], False
    with inside.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows.sort(key=lambda row: _number(row, "uniques"), reverse=True)
    return inside.name, rows[:limit], True


def _excluded(flagged, label) -> str:
    if not flagged:
        return "0 days in the %s 28" % label
    return "%d day(s) in the %s 28 (%s)" % (
        len(flagged), label, ", ".join(row["date"] for row in flagged))


def report(rows, directory: Path, today: date):
    recent, prior, flagged_recent, flagged_prior = windows(rows, today)
    raw_recent, raw_prior = raw_windows(rows, today)
    lines = []

    now = total(recent, "clones_uniques")
    before = total(prior, "clones_uniques")
    lines.append(
        "Unique cloners, last 28d: %d (previous 28d: %d, %s). Machines that "
        "cloned the repo, never called users."
        % (now, before, delta(now, before, len(recent), len(prior)))
    )

    now = total(recent, "views_uniques")
    before = total(prior, "views_uniques")
    lines.append(
        "Unique viewers, last 28d: %d (previous 28d: %d, %s)."
        % (now, before, delta(now, before, len(recent), len(prior)))
    )

    lines.append(
        "Excluded as automation: %s, %s. Clones with no unique viewer are CI "
        "and marketplace refreshes; each window is compared per measured day."
        % (_excluded(flagged_recent, "last"),
           _excluded(flagged_prior, "previous"))
    )

    # Issues are counted over the raw window, automation days included. A day
    # whose clone numbers were CI is still a day on which a person could open an
    # issue, and excluding it would undercount the one signal here that is
    # unambiguously a human.
    now = total(raw_recent, "issues_opened")
    before = total(raw_prior, "issues_opened")
    measured_now = any(row.get("issues_opened") for row in raw_recent)
    measured_before = any(row.get("issues_opened") for row in raw_prior)
    lines.append(
        "New issues, last 28d: %s (previous 28d: %s). Stars %s | forks %s, as "
        "of the last snapshot."
        % (now if measured_now else "not recorded",
           before if measured_before else "not recorded",
           latest(rows, "stars"), latest(rows, "forks"))
    )

    name, top, in_window = sources(directory, today)
    if top:
        lines.append(
            "Traffic sources (%s): %s."
            % (name, ", ".join(
                "%s %s uniques" % (row.get("referrer", "?"),
                                   row.get("uniques", "0"))
                for row in top))
        )
    elif in_window:
        lines.append(
            "Traffic sources: %s falls inside the window and lists none — "
            "GitHub reported no referrers." % name
        )
    elif name:
        lines.append(
            "Traffic sources: no referrer snapshot in the last %dd — the "
            "newest is %s, from before the window." % (WINDOW_DAYS, name)
        )
    else:
        lines.append("Traffic sources: no referrer snapshot in %s." % directory)

    return lines


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="?", type=Path,
                        default=Path("metrics/traffic.csv"))
    parser.add_argument("--today", help="YYYY-MM-DD; defaults to the last "
                                        "dated row, so a stale file reports "
                                        "the window it actually covers")
    args = parser.parse_args(argv)

    if not args.csv.is_file():
        print("no series at %s — the snapshot workflow writes it to the "
              "orphan `metrics` branch" % args.csv, file=sys.stderr)
        return 1

    rows = load(args.csv)
    if not rows:
        print("%s has a header and no days" % args.csv, file=sys.stderr)
        return 1

    if args.today:
        try:
            today = date.fromisoformat(args.today)
        except ValueError:
            print("--today wants YYYY-MM-DD, got %r" % args.today,
                  file=sys.stderr)
            return 1
    else:
        today = last_day(rows)
        if today is None:
            print("%s has no row with a YYYY-MM-DD date" % args.csv,
                  file=sys.stderr)
            return 1

    for line in report(rows, args.csv.parent, today):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
