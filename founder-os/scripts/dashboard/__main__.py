"""The dashboard command. The only module here that writes anything.

Every write lands inside `_dashboard/`, or on the explicit `--out` path, which
is refused when it resolves onto a file the ownership map gives an owner or onto
one of the `_dashboard/` files the run maintains itself. Every write is atomic:
a temporary file in the same directory, then a rename. A founder who interrupts
a run gets the previous page or no page, never half of one.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, List, Mapping, Optional, Tuple

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
    parser.add_argument("--open", action="store_true", dest="open_page")
    parser.add_argument("--max-bytes", type=int, default=8 * 1024 * 1024)
    return parser.parse_args([] if argv is None else argv)


def owned_destination(destination: Path, roots: Iterable[Path],
                      owners: Mapping[str, str]) -> Optional[Tuple[str, str]]:
    """The owned path and its owner an `--out` destination would land on.

    `--out` reaches `write_atomic` directly, and that write arrives through
    Bash, which the ownership guard does not inspect (hooks/ownership-guard.py).
    So this is the only place a mistyped destination can be caught before the
    page replaces a file an agent is responsible for.

    Both halves of the comparison are case-folded, the way `owner_of` in that
    guard folds the identical one: the workspace ships lowercase and APFS is
    case-insensitive by default, so `Goals.md` and `goals.md` are one file on a
    Mac and an exact match is dodged by a shift key. On a case-sensitive
    filesystem this refuses a genuinely distinct `Goals.md`; a refusal costs a
    flag, and the miss costs the quarter's bets.
    """
    target = destination.as_posix().casefold()
    for root in roots:
        prefix = root.as_posix().casefold().rstrip("/")
        if not target.startswith(prefix + "/"):
            continue
        text = target[len(prefix) + 1:]
        for owned, role in owners.items():
            folded = owned.casefold()
            if folded.endswith("/"):
                if text == folded[:-1] or text.startswith(folded):
                    return owned, role
            elif text == folded:
                return owned, role
    return None


MAINTAINED = ("facts.json", "snapshots.csv", ".gitignore")


def maintained_files(roots: Iterable[Path]) -> set:
    """Every `_dashboard/` file a run maintains, under any known root, folded.

    These are written for each business whatever `--out` says, so a destination
    that names one of them is a page landing on a file the same run just wrote.
    For `snapshots.csv` that is the series — the one file here a rerun cannot
    rebuild (docs/dashboard.md) — merged a few lines above and then destroyed.

    The roots are every workspace the refusal knows about, not the ones this run
    renders. Taking the rendered set instead left `--home <A> --out
    <B>/_dashboard/snapshots.csv` at exit 0: B is a registered business this run
    happened not to open, so B's series was outside the set and the page landed
    on it. The ownership refusal beside this one had already been widened to the
    registry for the same reason, and a run that refuses to clobber a
    strategist's markdown while destroying an irrecoverable series has its
    priorities backwards.

    `index.html` is deliberately not in the set: `--out <ws>/_dashboard/index.html`
    is the default destination written out longhand, and refusing it would
    refuse the command's own answer.
    """
    files = set()
    for root in roots:
        derived = (Path(root) / "_dashboard").resolve()
        for name in MAINTAINED:
            files.add((derived / name).as_posix().casefold())
    return files


def _workspaces():
    """The gateway's registry parser, reached through `contracts`.

    Loaded by the same helper `contracts.active_businesses` uses, so the package
    keeps exactly one copy of the module in `sys.modules` and this file reads
    the registry the run already resolved rather than parsing it a second way.
    """
    return contracts._load_sibling("workspaces", "mcp/workspaces.py")


def configured_business(live: Iterable):
    """The business the founder has already named elsewhere, or None.

    `--json` answers about exactly one business, so before refusing to guess it
    applies the precedence references/multi-business.md states and the gateway
    implements: the slug in the invocation, then `FOUNDER_OS_HOME`, then the
    registry's `default:`. A founder who set either of those has already
    answered the question the refusal asks.

    A `FOUNDER_OS_HOME` matching no single registered home resolves nothing
    rather than falling through to `default:`, which is how the gateway reads
    the same ambiguity: the more explicit setting pointing somewhere unknown is
    a reason to stop, not a reason to consult the vaguer one.
    """
    candidates = list(live)
    declared = os.environ.get("FOUNDER_OS_HOME")
    if declared:
        root = Path(declared).expanduser().resolve()
        matches = [item for item in candidates if item.home.resolve() == root]
        return matches[0] if len(matches) == 1 else None
    workspaces = _workspaces()
    try:
        registry = workspaces.load_registry(Path.home())
    except workspaces.WorkspaceResolutionError:
        return None
    default = (registry or {}).get("default")
    if not default:
        return None
    for item in candidates:
        if item.slug == default:
            return item
    return None


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
        if args.slug:
            sys.stderr.write(
                "A slug names a business in the registry and --home names a "
                "path; nothing checks that they agree, so the pair would file "
                "one workspace's numbers under the other's name. Pass one.\n")
            return EXIT_UNRESOLVED
        roots = [contracts.Business(slug="", home=Path(args.home),
                                    status="active")]
        portfolio = None
        paused = 0
    else:
        registry_error = _workspaces().WorkspaceResolutionError
        try:
            roots, portfolio, paused = contracts.active_businesses()
        except registry_error as error:
            # The registry is config the founder hand-edits, so a file it
            # rejects is an expected state with an exit code and a sentence,
            # not a traceback out of the parser. Only the parser's own error is
            # caught: a TypeError raised inside the resolver is our bug, and
            # sending the founder to edit a file that is fine costs more than a
            # traceback naming the line that actually broke.
            sys.stderr.write(
                "%s could not be read (%s). Fix that file and run again; "
                "nothing was read and nothing was written.\n"
                % (Path.home() / ".founder-os" / "businesses.yaml", error))
            return EXIT_UNRESOLVED

    live = []
    for business in roots:
        if (business.home / "charter.md").exists():
            live.append(business)
        else:
            # Dropping it silently makes a shorter page the only evidence that
            # a business is missing, which reads as a smaller company.
            sys.stderr.write(
                "Skipped %s: no charter.md under %s, so it is not on the "
                "page.\n" % (business.slug or "the workspace", business.home))
    if not live:
        sys.stderr.write(
            "No Founder OS workspace found. Run /founder-os:founder-os-init "
            "in Claude Code or $founder-os:founder-os-init in Codex.\n")
        return EXIT_UNRESOLVED

    selected = live[0]
    if args.slug:
        named = [business for business in live if business.slug == args.slug]
        if not named:
            sys.stderr.write(
                "No readable active business is registered as %r. Answering "
                "about another one would be a figure traced to the wrong "
                "company. Registered and readable: %s.\n"
                % (args.slug,
                   ", ".join(business.slug or "(unnamed)" for business in live)))
            return EXIT_UNRESOLVED
        selected = named[0]
    elif len(live) > 1:
        # FOUNDER_OS_HOME and `default:` answer "which business" for the page
        # too, not only for --json: `selected` is the workspace the page is
        # written into and the view that opens. Consulting them only under
        # --json left the page landing in the alphabetically first business's
        # `_dashboard/` on a registry whose one configured answer named another.
        configured = configured_business(live)
        if configured is not None:
            selected = configured
        elif args.json:
            # The page carries every business, so with nothing configured it
            # can stay silent about which one the founder meant and open the
            # first. One JSON envelope cannot: picking the alphabetically first
            # is a figure filed under another company's name.
            sys.stderr.write(
                "%d active businesses are readable (%s) and --json answers "
                "about one. Name it: dashboard <slug> --json, or set default: "
                "in %s.\n"
                % (len(live),
                   ", ".join(business.slug or "(unnamed)" for business in live),
                   Path.home() / ".founder-os" / "businesses.yaml"))
            return EXIT_UNRESOLVED

    view = contracts.load_ownership()
    thresholds = contracts.load_thresholds()
    generated = datetime.now().astimezone().isoformat(timespec="seconds")

    payloads = []
    chosen_facts = None
    for business in live:
        sources = collect.collect(business.home, view, slug=business.slug)
        facts = analyze.build_facts(sources, today, generated, thresholds)
        payloads.append((business, facts))
        if business is selected:
            chosen_facts = facts

    if args.json:
        sys.stdout.write(json.dumps(
            analyze.to_dict(chosen_facts), indent=2, sort_keys=True))
        return EXIT_OK

    if args.out:
        destination = Path(args.out).expanduser().resolve()
        known = [business.home.resolve() for business in roots]
        if portfolio:
            known.append(Path(portfolio).resolve())
        if args.home:
            # `--home` renders one workspace and never loads the registry, so
            # `known` held only that root and the guard allowed the page onto a
            # second registered business's `goals.md` — a file the strategist
            # owns, in a workspace this run merely did not resolve. The registry
            # is consulted here and only here, for the refusal: nothing it says
            # changes what is read or rendered, so `--home` still bypasses it in
            # every sense the flag documents. A registry the parser rejects
            # leaves the escape hatch as it was — refusing no more than before
            # rather than failing, because an unreadable registry is the state
            # `--home` exists to get out of.
            try:
                registered, sibling, _ = contracts.active_businesses()
            except _workspaces().WorkspaceResolutionError:
                registered, sibling = [], None
            known.extend(business.home.resolve() for business in registered)
            if sibling:
                known.append(Path(sibling).resolve())
        owned = owned_destination(destination, known, view.owners)
        if owned is not None:
            sys.stderr.write(
                "Refusing to write %s: %s is owned by %s and the dashboard "
                "owns nothing. Nothing was written.\n"
                % (destination, owned[0], owned[1]))
            return EXIT_WRITE
        if destination.as_posix().casefold() in maintained_files(known):
            sys.stderr.write(
                "Refusing to write %s: this run writes that file itself, and "
                "snapshots.csv is the one file here a rerun cannot rebuild. "
                "Nothing was written.\n" % destination)
            return EXIT_WRITE
    else:
        # Resolved, because `--home` takes a relative path and `as_uri()` below
        # refuses one: unresolved, `--home ws --open` writes every file and
        # then dies on the line that opens the page it just wrote.
        destination = ((portfolio or selected.home) / "_dashboard"
                       / "index.html").resolve()

    # Rendered and measured before anything is written, so that the refusal
    # below can truthfully say the run left the workspace as it found it.
    page = render.render(payloads, generated=generated,
                         active_slug=selected.slug, paused=paused)
    size = len(page.encode("utf-8"))
    if size > args.max_bytes:
        sys.stderr.write(
            "Page is %d bytes, over the %d limit; nothing was written.\n"
            % (size, args.max_bytes))
        return EXIT_WRITE

    updated = []
    try:
        for business, facts in payloads:
            derived = business.home / "_dashboard"
            ensure_gitignore(derived)
            write_atomic(derived / "facts.json", json.dumps(
                analyze.to_dict(facts), indent=2, sort_keys=True))
            snapshots.merge(derived / "snapshots.csv", snapshots.row_from(facts))
            updated.append(derived)
    except OSError as error:
        # Merging the series reads the existing file first, and a corrupt or
        # non-UTF-8 snapshots.csv arrives here as `snapshots.SnapshotError`,
        # which subclasses OSError precisely so this handler names the file
        # instead of letting a decode error out as a traceback.
        #
        # This loop is not a transaction and cannot be made one: each business
        # is a separate directory and the writes are already atomic per file.
        # So the businesses before the failing one keep what this run wrote
        # them, and the message says so. "Nothing was written" is the promise
        # the two --out refusals and the size refusal above keep, because they
        # return before any write; here it would be false, and a founder who
        # believed it would not go looking for the files that did change.
        sys.stderr.write("Could not update %s: %s\n" % (derived, error))
        if updated:
            sys.stderr.write(
                "Already written this run and left in place: %s.\n"
                % ", ".join(str(path) for path in updated))
        return EXIT_WRITE

    try:
        if not args.out:
            ensure_gitignore(destination.parent)
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
