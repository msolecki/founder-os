"""The release bump, and the check that keeps its list of places honest.

A release moves one number through eleven files. That list used to live in a
prose checklist in docs/development.md, which is a hand-kept list of places —
the same shape as every count this package refuses to hand-keep. These tests pin
both halves: the script rewrites every declared site, and the validator fails
when a twelfth appears that the script was never told about.
"""
import contextlib
import io
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import bump_version as bump
import validate_package as validator


class TestVersionSites(unittest.TestCase):
    def test_every_declared_site_matches_exactly_once(self):
        """`bump_version.py` rewrites by pattern. A pattern matching twice
        rewrites something nobody looked at; one matching zero times moves
        nothing and reports success."""
        version = bump.current_version(REPO_ROOT)
        for relative, pattern, description in bump.SITES:
            with self.subTest(site=relative):
                text = (REPO_ROOT / relative).read_text(encoding="utf-8")
                found = re.findall(pattern, text)
                self.assertEqual(1, len(found), description)
                self.assertEqual(version, found[0][1])

    def test_the_package_agrees_with_itself_about_its_version(self):
        version = bump.current_version(REPO_ROOT)
        for relative in (".claude-plugin/marketplace.json",
                         "founder-os/.claude-plugin/plugin.json",
                         "founder-os/.codex-plugin/plugin.json"):
            with self.subTest(manifest=relative):
                data = json.loads(
                    (REPO_ROOT / relative).read_text(encoding="utf-8")
                )
                found = data.get("version") or data["plugins"][0]["version"]
                self.assertEqual(version, found)

    def test_a_version_the_script_does_not_know_fails_the_build(self):
        errs = validator.check_version_sites(
            REPO_ROOT / "founder-os", validator.load_agents(
                REPO_ROOT / "founder-os"
            )
        )
        self.assertEqual([], errs)


class TestBumpRoundTrip(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name) / "repo"
        shutil.copytree(
            REPO_ROOT, self.repo,
            ignore=shutil.ignore_patterns(".git", "__pycache__",
                                          "node_modules", ".venv"),
        )

    def seed_unreleased(self, text="**Something.** It shipped.\n"):
        """A bump needs an entry to rename. Right after a release there is
        none, which is correct — and which is why these tests write one."""
        changelog = self.repo / "CHANGELOG.md"
        head, tail = changelog.read_text(encoding="utf-8").split(
            "## Unreleased", 1
        )
        changelog.write_text(
            head + "## Unreleased\n\n" + text + "\n## " +
            tail.split("\n## ", 1)[1],
            encoding="utf-8",
        )

    def run_bump(self, *argv):
        original = bump.REPO_ROOT
        bump.REPO_ROOT = self.repo
        try:
            with contextlib.redirect_stdout(io.StringIO()) as out:
                bump.main(list(argv))
            return out.getvalue()
        finally:
            bump.REPO_ROOT = original

    def test_a_bump_moves_every_site_and_leaves_the_records_alone(self):
        self.seed_unreleased()
        # A record holds whatever release it names — not necessarily the one
        # the package is on. The property is that the bump does not touch it.
        before = {
            relative: re.findall(
                pattern, (self.repo / relative).read_text(encoding="utf-8")
            )
            for relative, pattern, _ in bump.RECORDS
        }
        self.run_bump("9.9.9", "--date", "2026-12-01")

        self.assertEqual("9.9.9", bump.current_version(self.repo))
        for relative, pattern, description in bump.SITES:
            with self.subTest(site=relative):
                found = re.findall(
                    pattern, (self.repo / relative).read_text(encoding="utf-8")
                )
                self.assertEqual("9.9.9", found[0][1], description)
        for relative, pattern, description in bump.RECORDS:
            with self.subTest(record=relative):
                found = re.findall(
                    pattern, (self.repo / relative).read_text(encoding="utf-8")
                )
                self.assertEqual(
                    before[relative], found,
                    "%s names a release that already shipped and must not "
                    "move" % description,
                )
                self.assertNotIn("9.9.9", found)

    def test_the_unreleased_entry_becomes_the_release_and_a_fresh_one_opens(self):
        self.seed_unreleased()
        changelog = self.repo / "CHANGELOG.md"
        before = changelog.read_text(encoding="utf-8")
        body = before.split("## Unreleased", 1)[1].split("\n## ", 1)[0].strip()

        self.run_bump("9.9.9", "--date", "2026-12-01")

        after = changelog.read_text(encoding="utf-8")
        self.assertIn("## 9.9.9 — 2026-12-01", after)
        released = after.split("## 9.9.9 — 2026-12-01", 1)[1].split(
            "\n## ", 1
        )[0].strip()
        self.assertEqual(body, released)
        self.assertEqual(
            "", after.split("## Unreleased", 1)[1].split("\n## ", 1)[0].strip()
        )
        # The entry that already shipped is untouched, which is the whole
        # reason this script exists rather than a checklist.
        self.assertIn("## 2.6.0 — 2026-08-01", after)

    def test_a_bump_with_nothing_written_in_unreleased_is_refused(self):
        changelog = self.repo / "CHANGELOG.md"
        head, tail = changelog.read_text(encoding="utf-8").split(
            "## Unreleased", 1
        )
        changelog.write_text(
            head + "## Unreleased\n\n## " + tail.split("\n## ", 1)[1],
            encoding="utf-8",
        )

        with self.assertRaises(SystemExit) as raised:
            self.run_bump("9.9.9")

        self.assertIn("written from memory", str(raised.exception))

    def test_a_dry_run_writes_nothing(self):
        self.seed_unreleased()
        before = (self.repo / "CHANGELOG.md").read_text(encoding="utf-8")
        was = bump.current_version(self.repo)

        self.run_bump("9.9.9", "--dry-run")

        self.assertEqual(was, bump.current_version(self.repo))
        self.assertEqual(
            before, (self.repo / "CHANGELOG.md").read_text(encoding="utf-8")
        )

    def test_the_bumped_repository_still_passes_its_own_validator(self):
        """The point of the script: after it runs, nothing disagrees."""
        self.seed_unreleased()
        self.run_bump("9.9.9", "--date", "2026-12-01")

        errs = validator.check_version_sites(
            self.repo / "founder-os",
            validator.load_agents(self.repo / "founder-os"),
        )

        self.assertEqual([], errs)


if __name__ == "__main__":
    unittest.main()
