#!/usr/bin/env python3
"""Move the plugin version, everywhere it is written, in one command.

Eleven files carry it: three manifests, the gateway's protocol constant, the
host probe, three test constants, the landing page, the architecture note, and
the changelog heading. A release used to mean editing all of them by hand from a
checklist, and the checklist was itself a hand-kept list of places — the same
shape as every count this package refuses to hand-keep elsewhere.

So the list lives here, `check_version_sites` in the validator reads it, and a
twelfth site added without telling this script fails the build rather than
shipping a package that disagrees with itself about what it is.

The changelog is not a rewrite. `## Unreleased` is renamed to the dated heading
and a fresh empty one is opened above it, which is why the entry has to be
written before the bump rather than after: what is true in that section on the
day of the release is what the release says forever.
"""
from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION = re.compile(r"^\d+\.\d+\.\d+$")

# (path, pattern with one capture group holding the version, what it is)
# The pattern must match exactly once per file; `check_version_sites` relies on
# that to tell a declared site from a literal nobody registered.
SITES = (
    (".claude-plugin/marketplace.json",
     r'("version"\s*:\s*")(\d+\.\d+\.\d+)(")', "marketplace entry"),
    ("founder-os/.claude-plugin/plugin.json",
     r'("version"\s*:\s*")(\d+\.\d+\.\d+)(")', "Claude manifest"),
    ("founder-os/.codex-plugin/plugin.json",
     r'("version"\s*:\s*")(\d+\.\d+\.\d+)(")', "Codex manifest"),
    ("founder-os/mcp/protocol.py",
     r'(SERVER_VERSION = ")(\d+\.\d+\.\d+)(")', "gateway server version"),
    ("scripts/probe_installed_hosts.py",
     r'(VERSION = ")(\d+\.\d+\.\d+)(")', "installed-host probe"),
    ("tests/test_release_metadata.py",
     r'(RELEASE_VERSION = ")(\d+\.\d+\.\d+)(")', "release metadata contract"),
    ("tests/test_installed_host_probes.py",
     r'("version": ")(\d+\.\d+\.\d+)(")', "probe fixture"),
    ("tests/test_session_context.py",
     r'(report\["version"\], ")(\d+\.\d+\.\d+)(")', "doctor report contract"),
    ("docs/index.html",
     r'(Founder OS )(\d+\.\d+\.\d+)( ·)', "landing page proof line"),
    ("docs/architecture.md",
     r'(Current candidate: \*\*)(\d+\.\d+\.\d+)(\*\*)', "architecture note"),
)

# Places that hold a version on purpose and must survive a bump: they name a
# release that already shipped. Registered rather than guessed, so "this literal
# is history" is a reviewed decision and not a pattern that happens to miss it.
RECORDS = (
    ("tests/test_release_metadata.py",
     r'PUBLISHED_RELEASE = "(\d+\.\d+\.\d+)"',
     "the most recent published tag"),
    ("docs/development.md",
     r'`v(\d+\.\d+\.\d+)` was tagged with',
     "the worked example of a rewritten release entry"),
)

CHANGELOG = "CHANGELOG.md"
UNRELEASED = "## Unreleased"


def current_version(root: Path) -> str:
    path = root / "founder-os" / ".claude-plugin" / "plugin.json"
    match = re.search(r'"version"\s*:\s*"(\d+\.\d+\.\d+)"',
                      path.read_text(encoding="utf-8"))
    if not match:
        raise SystemExit("%s declares no version" % path)
    return match.group(1)


def rewrite(root: Path, new_version: str, apply: bool):
    """Every site, reported whether or not anything is written."""
    changes = []
    for relative, pattern, description in SITES:
        path = root / relative
        text = path.read_text(encoding="utf-8")
        found = re.findall(pattern, text)
        if len(found) != 1:
            raise SystemExit(
                "%s: expected exactly one %s, found %d — the site moved and "
                "SITES was not told" % (relative, description, len(found))
            )
        was = found[0][1]
        if apply and was != new_version:
            path.write_text(
                re.sub(pattern, lambda m: m.group(1) + new_version + m.group(3),
                       text),
                encoding="utf-8",
            )
        changes.append((relative, was, description))
    return changes


def open_release(root: Path, new_version: str, released_on: str, apply: bool):
    """Rename `## Unreleased` to the dated heading and open a fresh one."""
    path = root / CHANGELOG
    text = path.read_text(encoding="utf-8")
    if UNRELEASED not in text:
        raise SystemExit("%s has no %s heading" % (CHANGELOG, UNRELEASED))
    body = text.split(UNRELEASED, 1)[1].split("\n## ", 1)[0]
    if not body.strip():
        raise SystemExit(
            "%s is empty. Describe the release before tagging it: written "
            "afterwards it is written from memory, and the entry outlives the "
            "memory." % UNRELEASED
        )
    if apply:
        path.write_text(
            text.replace(
                UNRELEASED,
                "%s\n\n## %s — %s" % (UNRELEASED, new_version, released_on),
                1,
            ),
            encoding="utf-8",
        )
    return "%s — %s" % (new_version, released_on)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="the new version, X.Y.Z")
    parser.add_argument("--date", help="release date (default: today, UTC)")
    parser.add_argument("--dry-run", action="store_true",
                        help="report every site and write nothing")
    args = parser.parse_args(argv)

    if not VERSION.match(args.version):
        parser.error("version wants X.Y.Z, got %r" % args.version)
    released_on = args.date or datetime.datetime.now(
        datetime.timezone.utc
    ).date().isoformat()
    try:
        datetime.date.fromisoformat(released_on)
    except ValueError:
        parser.error("--date wants YYYY-MM-DD, got %r" % released_on)

    was = current_version(REPO_ROOT)
    if was == args.version:
        parser.error("the package is already %s" % args.version)

    apply = not args.dry_run
    heading = open_release(REPO_ROOT, args.version, released_on, apply)
    changes = rewrite(REPO_ROOT, args.version, apply)

    width = max(len(relative) for relative, _, _ in changes)
    for relative, previous, _ in changes:
        print("  %-*s  %s -> %s" % (width, relative, previous, args.version))
    print("  %-*s  ## Unreleased -> ## %s" % (width, CHANGELOG, heading))
    print("\n%d site(s) %s. Now run the six gates."
          % (len(changes) + 1, "would change" if args.dry_run else "updated"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
