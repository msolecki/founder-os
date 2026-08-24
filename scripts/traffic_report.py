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


def windows(rows, today):
    """Split into the last 28 days and the 28 before them, automation excluded.

    A flagged day is dropped rather than zeroed. Zeroing it would say the repo
    had a quiet Tuesday; dropping it says we do not know, which is true.
    """
    recent_from = today - timedelta(days=WINDOW_DAYS)
    prior_from = today - timedelta(days=WINDOW_DAYS * 2)
    recent, prior, flagged = [], [], []
    for row in rows:
        try:
            stamp = date.fromisoformat(row["date"])
        except ValueError:
            continue
        if row.get("automation_suspected") == "true":
            if stamp > recent_from:
                flagged.append(row)
            continue
        if stamp > recent_from:
            recent.append(row)
        elif stamp > prior_from:
            prior.append(row)
    return recent, prior, flagged


def raw_windows(rows, today):
    """The same two windows with nothing excluded, for counts that are not traffic."""
    recent_from = today - timedelta(days=WINDOW_DAYS)
    prior_from = today - timedelta(days=WINDOW_DAYS * 2)
    recent, prior = [], []
    for row in rows:
        try:
            stamp = date.fromisoformat(row["date"])
        except ValueError:
            continue
        if stamp > recent_from:
            recent.append(row)
        elif stamp > prior_from:
            prior.append(row)
    return recent, prior


def total(rows, field) -> int:
    return sum(_number(row, field) for row in rows)


def delta(now: int, before: int) -> str:
    if before == 0:
        return "no prior window" if now == 0 else "no prior window to compare"
    return "%+d%%" % round((now - before) / before * 100)


def latest(rows, field) -> str:
    for row in reversed(rows):
        if row.get(field):
            return row[field]
    return "unknown"


def sources(directory: Path, today: date, limit=3):
    """The newest referrer snapshot, if one was taken. They are photographs."""
    snapshots = sorted(directory.glob("referrers-*.csv"))
    if not snapshots:
        return None, []
    newest = snapshots[-1]
    with newest.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows.sort(key=lambda row: int(row.get("uniques") or 0), reverse=True)
    return newest.name, rows[:limit]


def report(rows, directory: Path, today: date):
    recent, prior, flagged = windows(rows, today)
    raw_recent, raw_prior = raw_windows(rows, today)
    lines = []

    now = total(recent, "clones_uniques")
    before = total(prior, "clones_uniques")
    lines.append(
        "Unique cloners, last 28d: %d (previous 28d: %d, %s). Machines that "
        "cloned the repo, never called users." % (now, before, delta(now, before))
    )

    now = total(recent, "views_uniques")
    before = total(prior, "views_uniques")
    lines.append(
        "Unique viewers, last 28d: %d (previous 28d: %d, %s)."
        % (now, before, delta(now, before))
    )

    if flagged:
        lines.append(
            "Excluded as automation: %d day(s) — %s. Clones with no unique "
            "viewer are CI and marketplace refreshes."
            % (len(flagged), ", ".join(row["date"] for row in flagged))
        )
    else:
        lines.append("Excluded as automation: 0 days in the last 28.")

    # Issues are counted over the raw window, automation days included. A day
    # whose clone numbers were CI is still a day on which a person could open an
    # issue, and excluding it would undercount the one signal here that is
    # unambiguously a human.
    now = total(raw_recent, "issues_opened")
    before = total(raw_prior, "issues_opened")
    measured = any(row.get("issues_opened") for row in raw_recent)
    lines.append(
        "New issues, last 28d: %s (previous 28d: %s). Stars %s | forks %s, as "
        "of the last snapshot."
        % (now if measured else "not recorded", before,
           latest(rows, "stars"), latest(rows, "forks"))
    )

    name, top = sources(directory, today)
    if not top:
        lines.append("Traffic sources: no referrer snapshot in %s." % directory)
    else:
        lines.append(
            "Traffic sources (%s): %s."
            % (name, ", ".join(
                "%s %s uniques" % (row.get("referrer", "?"),
                                   row.get("uniques", "0"))
                for row in top))
        )

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

    today = date.fromisoformat(args.today) if args.today \
        else date.fromisoformat(rows[-1]["date"])
    for line in report(rows, args.csv.parent, today):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
