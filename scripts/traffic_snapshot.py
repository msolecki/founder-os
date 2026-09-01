#!/usr/bin/env python3
"""Merge a GitHub Traffic API reading into a dated CSV series.

The Traffic API keeps fourteen days. Everything before that is gone and cannot
be recovered — the launch week already is. This turns a fortnight-wide sliding
window into a series by writing each reading into a file keyed by date, so the
same day read twice updates one row instead of adding a second.

It lives here rather than inline in the workflow because the interesting part is
not the API call. It is what counts as a real day: the Traffic API counts
`actions/checkout` against a repository's own clone numbers, and a marketplace
repository is re-cloned by every `/plugin marketplace update`. A day with
forty-one clones and no unique visitors is machines, and reporting it as
adoption is how a project talks itself into a strategy.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, timedelta
from pathlib import Path

FIELDS = [
    "date",
    "clones_count",
    "clones_uniques",
    "views_count",
    "views_uniques",
    "stars",
    "forks",
    "issues_opened",
    "automation_suspected",
]

# A day this busy with nobody looking is not people. The threshold is low on
# purpose: ten clones in a day with zero unique views has never once been a
# human on this repository, and a false positive costs one excluded day while a
# false negative costs a number quoted in a decision.
AUTOMATION_CLONE_FLOOR = 10


def suspect_automation(row) -> bool:
    """A day with no unique viewer and a pile of clones is CI, not adoption."""
    return int(row["views_uniques"] or 0) == 0 and \
        int(row["clones_count"] or 0) > AUTOMATION_CLONE_FLOOR


def _day_key(timestamp: str) -> str:
    """The API stamps midnight UTC; the series is keyed by the date alone."""
    return timestamp.split("T", 1)[0]


def _days_from(first: str, last: str):
    """Every date in the closed interval, so a quiet day is a zero and not a gap."""
    start, end = date.fromisoformat(first), date.fromisoformat(last)
    while start <= end:
        yield start.isoformat()
        start += timedelta(days=1)


def read_series(path: Path):
    """Load the existing series, keyed by date. A missing file is an empty one."""
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {row["date"]: {field: row.get(field, "") for field in FIELDS}
            for row in rows if row.get("date")}


def merge(series, clones, views, repository, snapshot_date, issues=None,
          issues_since=None):
    """Fold one API reading into the series and return it, sorted by date.

    Traffic rows overwrite by date: the API is authoritative about a day and the
    most recent one is always partial, so today's row is corrected by tomorrow's
    run rather than duplicated. Stars and forks are the opposite — they are a
    reading taken now, not a property of any past day, so they are written only
    against the snapshot date and never backfilled over an earlier reading.

    Issues are a third shape. They belong to the day they were opened, like
    traffic, but the traffic endpoints only return days with activity — so a day
    that saw an issue and no clone would have no row to write it into. Every day
    from `issues_since` forward therefore gets an explicit count, zero included,
    because a blank and a zero mean different things and the whole point of this
    column is telling a quiet week from an unmeasured one.
    """
    merged = {date: dict(row) for date, row in series.items()}

    for entry in clones.get("clones") or []:
        row = merged.setdefault(_day_key(entry["timestamp"]),
                                {field: "" for field in FIELDS})
        row["date"] = _day_key(entry["timestamp"])
        row["clones_count"] = str(entry.get("count", 0))
        row["clones_uniques"] = str(entry.get("uniques", 0))

    for entry in views.get("views") or []:
        row = merged.setdefault(_day_key(entry["timestamp"]),
                                {field: "" for field in FIELDS})
        row["date"] = _day_key(entry["timestamp"])
        row["views_count"] = str(entry.get("count", 0))
        row["views_uniques"] = str(entry.get("uniques", 0))

    if issues is not None and issues_since:
        opened = {}
        for timestamp in issues:
            opened[_day_key(timestamp)] = opened.get(_day_key(timestamp), 0) + 1
        for day in _days_from(issues_since, snapshot_date):
            row = merged.setdefault(day, {field: "" for field in FIELDS})
            row["date"] = day
            row["issues_opened"] = str(opened.get(day, 0))

    today = merged.setdefault(snapshot_date, {field: "" for field in FIELDS})
    today["date"] = snapshot_date
    today["stars"] = str(repository.get("stargazers_count", ""))
    today["forks"] = str(repository.get("forks_count", ""))

    for row in merged.values():
        for field in FIELDS:
            row.setdefault(field, "")
        row["automation_suspected"] = \
            "true" if suspect_automation(row) else "false"

    return [merged[date] for date in sorted(merged)]


def write_series(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS,
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_snapshot(path: Path, header, records, keys) -> None:
    """Referrers and paths are point-in-time and cannot be merged into a series.

    Two readings a week apart describe overlapping fourteen-day windows with no
    way to subtract one from the other, so each is written whole under its own
    date and read as a photograph rather than a trend.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        for record in records:
            writer.writerow([record.get(key, "") for key in keys])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clones", required=True, type=Path)
    parser.add_argument("--views", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--issues", type=Path,
                        help="JSON list of ISO timestamps, one per issue "
                             "opened in the window")
    parser.add_argument("--issues-since",
                        help="YYYY-MM-DD; the first day --issues covers, so "
                             "quiet days are recorded as zero")
    parser.add_argument("--referrers", type=Path)
    parser.add_argument("--paths", type=Path)
    parser.add_argument("--out", required=True, type=Path,
                        help="the CSV series, updated in place")
    parser.add_argument("--date", required=True,
                        help="the snapshot date, YYYY-MM-DD")
    args = parser.parse_args(argv)

    if bool(args.issues) != bool(args.issues_since):
        parser.error(
            "--issues and --issues-since go together. Without the start date "
            "a quiet day is written blank, and a blank is how this file says "
            "unmeasured"
        )

    load = lambda path: json.loads(path.read_text(encoding="utf-8"))
    rows = merge(read_series(args.out), load(args.clones), load(args.views),
                 load(args.repository), args.date,
                 issues=load(args.issues) if args.issues else None,
                 issues_since=args.issues_since)
    write_series(args.out, rows)

    if args.referrers:
        write_snapshot(
            args.out.parent / ("referrers-%s.csv" % args.date),
            ["referrer", "count", "uniques"],
            load(args.referrers),
            ["referrer", "count", "uniques"],
        )
    if args.paths:
        write_snapshot(
            args.out.parent / ("paths-%s.csv" % args.date),
            ["path", "title", "count", "uniques"],
            load(args.paths),
            ["path", "title", "count", "uniques"],
        )

    flagged = sum(1 for row in rows if row["automation_suspected"] == "true")
    print("%s: %d day(s), %d flagged as automation"
          % (args.out, len(rows), flagged))
    return 0


if __name__ == "__main__":
    sys.exit(main())
