"""The dashboard command. The only module here that writes anything.

Every write lands inside `_dashboard/` and every one is atomic: a temporary file
in the same directory, then a rename. A founder who interrupts a run gets the
previous page or no page, never half of one.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

# `python3 <plugin>/scripts/dashboard` runs this file as a top-level module with
# no parent, which makes every relative import below raise. Naming the package
# and putting its parent on the path is what lets the directory stay runnable as
# both a command and an import.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "dashboard"

from . import analyze, collect, contracts, render, snapshots

EXIT_OK = 0
EXIT_UNRESOLVED = 2
EXIT_WRITE = 3

GITIGNORE = (
    "# Regenerable, and together a copy of the whole workspace. Only the two\n"
    "# files named below are ignored; everything else this directory grows holds\n"
    "# history a rerun cannot rebuild, and losing it costs the series.\n"
    "index.html\n"
    "facts.json\n"
)


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        "w", delete=False, dir=str(path.parent), encoding="utf-8")
    try:
        handle.write(text)
        handle.close()
        os.replace(handle.name, path)
    except BaseException:
        handle.close()
        if os.path.exists(handle.name):
            os.unlink(handle.name)
        raise


def ensure_gitignore(directory: Path) -> None:
    target = directory / ".gitignore"
    if not target.exists():
        write_atomic(target, GITIGNORE)


def _parse_args(argv: Optional[List[str]]):
    parser = argparse.ArgumentParser(
        prog="founder-os dashboard",
        description="Render the Founder OS dashboard for one or more businesses.")
    parser.add_argument("slug", nargs="?", default=None,
                        help="business to open first; the page still contains all")
    parser.add_argument("--home", default=None,
                        help="a single workspace root, bypassing the registry")
    parser.add_argument("--out", default=None, help="where to write index.html")
    parser.add_argument("--json", action="store_true",
                        help="print facts.json to stdout and write nothing")
    parser.add_argument("--now", default=None, metavar="YYYY-MM-DD")
    parser.add_argument("--no-commentary", action="store_true")
    parser.add_argument("--open", action="store_true", dest="open_page")
    parser.add_argument("--max-bytes", type=int, default=8 * 1024 * 1024)
    return parser.parse_args([] if argv is None else argv)


def _today(raw: Optional[str]) -> date:
    if raw is None:
        return datetime.now().date()
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise ValueError("--now must be an ISO date, YYYY-MM-DD")


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        today = _today(args.now)
    except ValueError as error:
        sys.stderr.write("%s\n" % error)
        return EXIT_UNRESOLVED

    if args.home:
        roots = [contracts.Business(slug=args.slug or "", home=Path(args.home),
                                    status="active")]
        portfolio = None
        paused = 0
    else:
        roots, portfolio, paused = contracts.active_businesses()

    live = [business for business in roots if (business.home / "charter.md").exists()]
    if not live:
        sys.stderr.write(
            "No Founder OS workspace found. Run /founder-os:founder-os-init "
            "in Claude Code or $founder-os:founder-os-init in Codex.\n")
        return EXIT_UNRESOLVED

    view = contracts.load_ownership()
    thresholds = contracts.load_thresholds()
    generated = datetime.now().astimezone().isoformat(timespec="seconds")

    payloads = []
    for business in live:
        sources = collect.collect(business.home, view, slug=business.slug)
        facts = analyze.build_facts(sources, today, generated, thresholds)
        payloads.append((business, facts))

    if args.json:
        sys.stdout.write(json.dumps(
            analyze.to_dict(payloads[0][1]), indent=2, sort_keys=True))
        return EXIT_OK

    try:
        for business, facts in payloads:
            derived = business.home / "_dashboard"
            ensure_gitignore(derived)
            write_atomic(derived / "facts.json", json.dumps(
                analyze.to_dict(facts), indent=2, sort_keys=True))
            snapshots.merge(derived / "snapshots.csv", snapshots.row_from(facts))
    except OSError as error:
        sys.stderr.write("Could not write _dashboard/: %s\n" % error)
        return EXIT_WRITE

    destination = Path(args.out) if args.out else (
        (portfolio or live[0].home) / "_dashboard" / "index.html")
    page = render.render(payloads, generated=generated,
                         active_slug=args.slug or "", paused=paused)
    if len(page.encode("utf-8")) > args.max_bytes:
        sys.stderr.write(
            "Page is %d bytes, over the %d limit; nothing was written.\n"
            % (len(page.encode("utf-8")), args.max_bytes))
        return EXIT_WRITE
    try:
        write_atomic(destination, page)
    except OSError as error:
        sys.stderr.write("Could not write %s: %s\n" % (destination, error))
        return EXIT_WRITE
    if args.open_page:
        import webbrowser
        webbrowser.open(destination.as_uri())
    sys.stdout.write("%s\n" % destination)
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
