#!/usr/bin/env python3
"""Keep the newest N referrer and path snapshots, delete the rest.

They are photographs, not a series: two readings a week apart describe
overlapping fourteen-day windows with no way to subtract one from the other, so
nothing joins them and nothing reads one from outside the report window. At two
files a week they otherwise accumulate forever, in the directory and in the glob
`traffic_report.py` walks on every run.

Eight of each is two months — comfortably more than the 28-day window the report
compares, which is the only span anything here looks back over.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FAMILIES = ("referrers", "paths")
DATED = re.compile(r"^(referrers|paths)-(\d{4}-\d{2}-\d{2})\.csv$")


def prunable(directory: Path, keep: int):
    """Snapshots to delete, oldest first, per family.

    Sorting is on the parsed date rather than the filename so a malformed name
    is skipped rather than ordered into the middle of the real ones.
    """
    doomed = []
    for family in FAMILIES:
        dated = []
        for path in directory.glob("%s-*.csv" % family):
            match = DATED.match(path.name)
            if match:
                dated.append((match.group(2), path))
        dated.sort()
        if keep >= 0:
            doomed.extend(path for _, path in dated[:max(0, len(dated) - keep)])
    return doomed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--keep", type=int, default=8,
                        help="snapshots to keep per family (default 8)")
    args = parser.parse_args(argv)

    if args.keep < 1:
        parser.error("--keep wants at least 1; deleting every snapshot leaves "
                     "the report with no sources line at all")
    if not args.directory.is_dir():
        print("no snapshot directory at %s" % args.directory)
        return 0

    doomed = prunable(args.directory, args.keep)
    for path in doomed:
        path.unlink()
    print("%s: pruned %d snapshot(s), keeping %d per family"
          % (args.directory, len(doomed), args.keep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
