"""What the published surfaces are allowed to say about the dashboard.

A release note is the one document nobody rewrites: `bump_version.py` renames
`## Unreleased` to a dated heading and `docs/development.md` makes that entry a
record. So every sentence here is checked against the tree it describes rather
than against the sentence a reviewer remembers writing.
"""

import ast
import importlib.util
import re
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "founder-os"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"
DASHBOARD_DOC_PATH = REPO_ROOT / "docs" / "dashboard.md"
COMMANDS_PATH = REPO_ROOT / "docs" / "commands.md"
ARCHITECTURE_PATH = REPO_ROOT / "docs" / "architecture.md"
DEVELOPMENT_PATH = REPO_ROOT / "docs" / "development.md"
ROOT_README_PATH = REPO_ROOT / "README.md"
SKILL_PATH = REPO_ROOT / "founder-os" / "skills" / "dashboard" / "SKILL.md"
QUEUE_SKILL_PATH = REPO_ROOT / "founder-os" / "skills" / "queue" / "SKILL.md"
DOCTOR_SKILL_PATH = PLUGIN_ROOT / "skills" / "founder-os-doctor" / "SKILL.md"
GUARD_PATH = PLUGIN_ROOT / "hooks" / "ownership-guard.py"
VALIDATOR_PATH = REPO_ROOT / "scripts" / "validate_package.py"
PACKAGE_META_PATH = REPO_ROOT / "scripts" / "_package.py"
DASHBOARD_CLI_PATH = (
    REPO_ROOT / "founder-os" / "scripts" / "dashboard" / "__main__.py"
)
ANALYZE_PATH = REPO_ROOT / "founder-os" / "scripts" / "dashboard" / "analyze.py"

MARKDOWN_LINK = re.compile(
    r"!?\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+[^)]*)?\)"
)
HTML_HREF = re.compile(r'(?:href|src)\s*=\s*"([^"]+)"')


def tracked_files():
    listing = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.split("\n")
    return [name for name in listing if name]


def outbound_targets(relative):
    """Every repository-local document this file links to, as repo paths."""
    text = (REPO_ROOT / relative).read_text(encoding="utf-8")
    raw = {match.group(1) or match.group(2) for match in MARKDOWN_LINK.finditer(text)}
    raw |= set(HTML_HREF.findall(text))
    resolved = set()
    for target in raw:
        target = target.split("#", 1)[0].strip()
        if not target or "://" in target or target.startswith("mailto:"):
            continue
        try:
            path = (REPO_ROOT / relative).parent.joinpath(target).resolve()
            resolved.add(path.relative_to(REPO_ROOT).as_posix())
        except ValueError:
            continue
    return resolved


def unreleased_section():
    """The topmost written CHANGELOG section — `## Unreleased` before a bump."""
    sections = re.split(r"^## ", CHANGELOG_PATH.read_text(encoding="utf-8"),
                        flags=re.M)[1:]
    return next(body for body in sections if body.split("\n", 1)[1].strip())


def sentences(text):
    """The collapsed text, cut where a sentence ends.

    A claim is true or false in the sentence that makes it. Wave 2's write-scope
    error was a lead paragraph contradicting a table row eight lines below it in
    the same file, so a document-wide search for the qualifier finds it and
    passes the paragraph that lacks it.
    """
    joined = " ".join(text.split())
    return [part for part in re.split(r"(?<=\.)\s+", joined) if part.strip()]


def repository_layout_block(path):
    """The fenced tree under `## Repository layout`."""
    text = path.read_text(encoding="utf-8")
    after = text.split("## Repository layout", 1)[1]
    return after.split("```")[1]


def _load(name, path, extra_path=None):
    """A module at a path no import statement reaches, by file location."""
    if extra_path is not None and str(extra_path) not in sys.path:
        sys.path.insert(0, str(extra_path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ownership_guard():
    """The guard itself. Loading it does not run `main()`."""
    return _load("ownership_guard_for_docs", GUARD_PATH)


def validator():
    return _load("validate_package_for_docs", VALIDATOR_PATH,
                 extra_path=REPO_ROOT / "scripts")


def _cli_tree():
    return ast.parse(DASHBOARD_CLI_PATH.read_text(encoding="utf-8"))


def _cli_function(name):
    return next(node for node in _cli_tree().body
                if isinstance(node, ast.FunctionDef) and node.name == name)


def maintained_names():
    """The per-business files a run maintains, off the CLI's own tuple."""
    for node in _cli_tree().body:
        if (isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "MAINTAINED"
                        for target in node.targets)):
            return tuple(element.value for element in node.value.elts)
    raise AssertionError("the CLI no longer names the files it maintains")


def modes_that_return_before_writing():
    """`{flag: line}` for each mode `main()` leaves on before it writes.

    `--json` prints one envelope and returns `EXIT_OK`; a page over
    `--max-bytes` returns `EXIT_WRITE`. Both sit above the loop that writes the
    maintained files, which is why "every run writes them" is false twice over
    — and the two line numbers say so rather than a reviewer's memory.
    """
    early = {}
    wanted = {"json": "EXIT_OK", "max_bytes": "EXIT_WRITE"}
    for node in ast.walk(_cli_function("main")):
        if not isinstance(node, ast.If):
            continue
        flags = {child.attr for child in ast.walk(node.test)
                 if isinstance(child, ast.Attribute)}
        for flag, code in wanted.items():
            if flag not in flags:
                continue
            for statement in node.body:
                if (isinstance(statement, ast.Return)
                        and isinstance(statement.value, ast.Name)
                        and statement.value.id == code):
                    early.setdefault(flag, statement.lineno)
    return early


def first_maintained_write():
    """The line on which `main()` first names a file it maintains."""
    names = set(maintained_names())
    lines = [node.lineno for node in ast.walk(_cli_function("main"))
             if isinstance(node, ast.Constant) and node.value in names]
    return min(lines) if lines else None


def partial_write_handler():
    """The handler that reports what a failed write loop had already done.

    Exit 3 does not mean nothing was written: this handler sits below the first
    maintained write, so a failure on the second business leaves the first
    business's files updated. The message it prints is read out of the CLI, so
    a doc quoting a sentence the command stopped printing goes red.
    """
    return next(
        node for node in ast.walk(_cli_function("main"))
        if isinstance(node, ast.ExceptHandler)
        and any(isinstance(child, ast.Constant)
                and isinstance(child.value, str)
                and "already written" in child.value.lower()
                for child in ast.walk(node)))


def _out_branch_scan():
    """Walk `main()`, tracking whether each node sits under an `--out` branch.

    Returns the string constants reached outside every such branch and the
    lines that refuse a destination inside one. Both are read out of the CLI
    rather than asserted, because they are the exact shape of the two sentences
    the published surfaces have to get right: what a run writes whatever the
    flag says, and how many ways the flag itself is refused.
    """
    main = _cli_function("main")
    unconditional, refusals = set(), []

    def visit(node, branched):
        if isinstance(node, ast.If):
            branched = branched or any(
                isinstance(child, ast.Attribute) and child.attr == "out"
                for child in ast.walk(node.test))
            for child in node.body + node.orelse:
                visit(child, branched)
            return
        if branched:
            if (isinstance(node, ast.Return) and isinstance(node.value, ast.Name)
                    and node.value.id == "EXIT_WRITE"):
                refusals.append(node.lineno)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            unconditional.add(node.value)
        for child in ast.iter_child_nodes(node):
            visit(child, branched)

    for statement in main.body:
        visit(statement, False)
    return unconditional, refusals


def written_whatever_out_says():
    """The names `main()` writes with no `--out` branch above them."""
    return _out_branch_scan()[0]


def refusals_under_the_out_branch():
    """The lines on which `main()` refuses an `--out` destination.

    A flag row naming one of two refusals reads as a row naming all of them,
    and the one it left out is the destination that costs the series.
    """
    return _out_branch_scan()[1]


class DocumentationReachability(unittest.TestCase):
    def test_every_docs_page_is_linked_from_another_tracked_page(self):
        """A page nothing links to is a page nobody reads.

        `check_local_links.py` validates outbound targets only, so a new page
        can ship with a perfectly valid set of links out and no route in.
        """
        pages = [name for name in tracked_files()
                 if name.startswith("docs/") and name.endswith(".md")]
        inbound = {page: 0 for page in pages}
        for name in tracked_files():
            if not name.endswith((".md", ".html")):
                continue
            for target in outbound_targets(name):
                if target in inbound and target != name:
                    inbound[target] += 1
        orphans = sorted(page for page in pages
                         if page != "docs/README.md" and not inbound[page])
        self.assertEqual(orphans, [], "no page in docs/ links to these")


class RepositoryLayoutBlocks(unittest.TestCase):
    """The published trees name what the package actually ships.

    Nothing else checks them: `check_readme_counts` reads counts out of a fixed
    file list and never inspects a layout listing.
    """

    def entries(self):
        """What the package ships, from git rather than from this checkout.

        `iterdir()` also names whatever a run left behind — importing
        `cadence_manager` by file location leaves a `__pycache__/` beside it —
        and every such name became a name README.md was required to publish.
        `.gitignore` says that directory is not part of the package, so the
        tracked list is the one that answers the question being asked.
        """
        scripts, maps = set(), set()
        for name in tracked_files():
            parts = name.split("/")
            if parts[:2] == ["founder-os", "scripts"] and len(parts) > 2:
                scripts.add(parts[2])
            elif (parts[:2] == ["founder-os", "references"] and len(parts) == 3
                    and parts[2].endswith(".yaml")):
                maps.add(parts[2])
        return sorted(scripts) + sorted(maps)

    def test_readme_layout_names_every_script_and_map_the_plugin_ships(self):
        block = repository_layout_block(ROOT_README_PATH)
        for entry in self.entries():
            with self.subTest(entry=entry):
                self.assertIn(entry, block)

    def test_architecture_layout_names_every_script_and_map_the_plugin_ships(self):
        block = repository_layout_block(ARCHITECTURE_PATH)
        for entry in self.entries():
            with self.subTest(entry=entry):
                self.assertIn(entry, block)


class DerivedDirectoryClaims(unittest.TestCase):
    """`_dashboard/` is denied to agents by a rule, and the rule has an edge."""

    SURFACES = {
        "CHANGELOG.md": lambda: unreleased_section(),
        "docs/dashboard.md": lambda: DASHBOARD_DOC_PATH.read_text(encoding="utf-8"),
        "founder-os/skills/dashboard/SKILL.md": lambda: SKILL_PATH.read_text(
            encoding="utf-8"),
        "scripts/_package.py": lambda: PACKAGE_META_PATH.read_text(encoding="utf-8"),
    }

    NOT_SHELL = re.compile(
        r"does not read (?:a )?shell commands?"
        r"|never (?:reads )?a shell command"
        r"|reads? no shell command")

    def test_the_deny_is_published_with_the_boundary_it_actually_has(self):
        """The guard reads a tool's file arguments, never a shell command.

        Both halves come out of the guard rather than out of the sentence. The
        deny is a rule of its own — revert it and `check_derived` is gone, and
        these four sentences describe a guarantee the package stopped making.
        Its edge is `_tool_paths`, which hands that rule no path at all for a
        `Bash` command: a redirect into `_dashboard/` is outside the promise,
        and a guarantee published without its edge is read as covering it.
        """
        guard = ownership_guard()
        self.assertTrue(callable(getattr(guard, "check_derived", None)),
                        "no rule denies a derived path; the four sentences "
                        "below describe a guarantee that is not in the guard")
        self.assertEqual(
            [], guard._tool_paths(
                "Bash", {"command": "echo x > _dashboard/facts.json"}),
            "the guard reads shell commands now — the published edge is stale")
        self.assertEqual(
            ["_dashboard/facts.json"],
            guard._tool_paths("Write", {"file_path": "_dashboard/facts.json"}))
        self.assertIsNone(
            self.NOT_SHELL.search("the guard reads shell commands too"),
            "a needle satisfied by the sentence asserting the opposite is not "
            "a needle")
        for name, read in self.SURFACES.items():
            with self.subTest(document=name):
                self.assertRegex(" ".join(read().split()).lower(),
                                 self.NOT_SHELL)

    def test_no_surface_attributes_the_deny_to_absence_from_the_owns_map(self):
        """An unowned path is *allowed*: `owner_of` returns None and the guard
        logs `allow`. Only a dedicated rule denies, the way `_local/` is denied.
        """
        for name, read in self.SURFACES.items():
            with self.subTest(document=name):
                text = " ".join(read().split()).lower()
                self.assertNotIn("appears in no `owns:` list", text)
                self.assertNotIn("no agent owns it, no agent may write it", text)

    def test_the_package_metadata_names_the_map_key_that_denies_it(self):
        source = PACKAGE_META_PATH.read_text(encoding="utf-8")
        self.assertIn("derived_files", source)


class WriteScopeClaims(unittest.TestCase):
    def surfaces(self):
        return {
            "CHANGELOG.md": unreleased_section(),
            "docs/dashboard.md": DASHBOARD_DOC_PATH.read_text(encoding="utf-8"),
            "docs/commands.md": COMMANDS_PATH.read_text(encoding="utf-8"),
            "founder-os/skills/dashboard/SKILL.md": SKILL_PATH.read_text(
                encoding="utf-8"),
        }

    def test_no_surface_says_the_dashboard_writes_only_that_directory(self):
        """`--out` exists, so "one directory" is a claim the CLI contradicts."""
        cli = DASHBOARD_CLI_PATH.read_text(encoding="utf-8")
        self.assertIn('"--out"', cli)
        forbidden = (
            "writes one directory",
            "writes exactly one directory",
            "writes only `_dashboard/`",
            "it writes one directory",
        )
        for name, text in self.surfaces().items():
            normalized = " ".join(text.split()).lower()
            for phrase in forbidden:
                with self.subTest(document=name, phrase=phrase):
                    self.assertNotIn(phrase, normalized)

    ALTERNATIVE = re.compile(
        r"`?_dashboard`?/?[^.;|]{0,120}\bor\b[^.;|]{0,120}`?--out"
        r"|`?--out`?[^.;|]{0,120}\bor\b[^.;|]{0,120}`?_dashboard")

    def test_the_alternative_pattern_survives_the_rewording_it_guards_against(self):
        """The needle, not the document.

        The first pattern demanded the trailing slash in `_dashboard/` and put
        the two halves within thirty characters of each other, so dropping one
        character or adding one clause walked the same claim straight past it.
        """
        for phrasing in (
                "it writes `_dashboard/`, or the path `--out` names",
                "it writes the `_dashboard` directory, or the `--out` path",
                "it writes into `_dashboard`, or, when you pass one, the "
                "destination `--out` names",
                "`--out` names where it writes, or the `_dashboard` directory "
                "under the selected business",
        ):
            with self.subTest(phrasing=phrasing):
                self.assertIsNotNone(self.ALTERNATIVE.search(phrasing))

    WRITE_QUALIFIER = re.compile(
        r"--json|writes at all|written once|only when|only if|unless")

    def test_a_sentence_listing_what_a_run_writes_names_the_runs_that_do_not(self):
        """Two modes reach `return` above the first write, and one file is
        written once rather than every run.

        Wave 1 published "`_dashboard/`, or the path `--out` names"; wave 2
        replaced it with "Every run writes `facts.json`, `snapshots.csv` and a
        `.gitignore`", which is false under `--json`, false for a page over
        `--max-bytes`, and false for the `.gitignore` after the first run. The
        two line numbers below are the first two halves of that, read out of
        `main()`; `ensure_gitignore` is the third. So a sentence that lists two
        of the three files as things a run writes has to carry the qualifier in
        the same sentence — the document-wide search passed wave 2, whose lead
        paragraph contradicted a table row in the same file.
        """
        early = modes_that_return_before_writing()
        first = first_maintained_write()
        self.assertIsNotNone(first, "main() writes none of the files it "
                                    "maintains — the surfaces are describing a "
                                    "command that no longer exists")
        for flag in ("json", "max_bytes"):
            self.assertIn(flag, early,
                          "no early return for --%s; the qualifier the "
                          "surfaces carry may now be wrong" % flag)
            self.assertLess(early[flag], first,
                            "--%s now returns below the first write" % flag)
        gitignore = _cli_function("ensure_gitignore")
        self.assertTrue(
            [node for node in ast.walk(gitignore) if isinstance(node, ast.If)],
            "ensure_gitignore writes unconditionally now, so `.gitignore` is "
            "rewritten every run and the published qualifier is stale")
        names = set(maintained_names())
        for name, text in self.surfaces().items():
            for sentence in sentences(text):
                lowered = sentence.lower()
                if not re.search(r"\bwrites?\b", lowered):
                    continue
                if sum(item in lowered for item in names) < 2:
                    continue
                with self.subTest(document=name, sentence=lowered[:70]):
                    self.assertRegex(
                        lowered, self.WRITE_QUALIFIER,
                        "lists what a run writes without naming a run that "
                        "does not")

    def test_no_surface_offers_the_out_path_as_an_alternative_to_the_directory(self):
        """`--out` moves the page. It does not move what the run maintains.

        The first version of these sentences said the command writes one
        directory, which `--out` contradicts; the correction said it writes
        `_dashboard/` **or** the `--out` path, which the CLI contradicts the
        other way. `main()` writes `facts.json` and `snapshots.csv` under every
        rendered business's `_dashboard/` with no `--out` branch above them, so
        the two destinations are not alternatives, and a founder who reads
        "or" is told a `--out` run leaves the workspace alone.
        """
        unconditional = written_whatever_out_says()
        for name in ("facts.json", "snapshots.csv"):
            self.assertIn(name, unconditional,
                          "%s is written under an --out branch now; the "
                          "surfaces may say 'or' once that is true of all "
                          "three" % name)
        for name, text in self.surfaces().items():
            normalized = " ".join(text.split()).lower()
            with self.subTest(document=name):
                offered = self.ALTERNATIVE.search(normalized)
                self.assertIsNone(
                    offered,
                    "reads --out as an alternative to _dashboard/: %r"
                    % (offered.group(0) if offered else ""))


class ValidatorCheckTable(unittest.TestCase):
    """`docs/development.md` describes the arms the checks still have.

    Nothing in the build reads that table, so a check can lose an arm and the
    row goes on describing it. `check_thresholds` did exactly that: the row
    still named a corpus arm that had been deleted, and named none of the value
    comparison that replaced it.
    """

    def row(self, check):
        text = DEVELOPMENT_PATH.read_text(encoding="utf-8")
        found = re.search(r"^\|\s*`%s`\s*\|(.+?)\|\s*$" % re.escape(check),
                          text, re.M)
        self.assertIsNotNone(found, "no row for %s" % check)
        return " ".join(found.group(1).split()).lower()

    def test_the_thresholds_row_names_the_arms_the_check_still_fires_on(self):
        checks = validator()
        unrestated = checks._restatement_errors(
            PLUGIN_ROOT, "pipeline.stale_days", 90.0)
        self.assertTrue(
            any("nothing restates 'pipeline.stale_days'" in error
                for error in unrestated), unrestated)
        disagreement = checks._restatement_errors(
            PLUGIN_ROOT, "queue.doing_cap", 99.0)
        self.assertTrue(
            any("references/thresholds.yaml says 99" in error
                for error in disagreement), disagreement)
        row = self.row("check_thresholds")
        self.assertNotIn("group nothing reads", row)
        self.assertIn("disagrees", row)
        # The citation arm loops over `_THRESHOLD_CITERS`, a hardcoded pair, so
        # the row may not promise it of skills at large — see the release note
        # that made the same claim about the same arm.
        self.assertNotRegex(
            row,
            r"\b(?:a|any|every|each) skill (?:states|enforces) an? "
            r"(?:limit|cap) without citing")


class DashboardFlagTable(unittest.TestCase):
    """The flag table is the only place the refusals are written down."""

    def row(self, flag):
        text = DASHBOARD_DOC_PATH.read_text(encoding="utf-8")
        found = re.search(r"^\|\s*`%s[^`]*`\s*\|(.+?)\|\s*$" % re.escape(flag),
                          text, re.M)
        self.assertIsNotNone(found, "docs/dashboard.md has no row for %s" % flag)
        return " ".join(found.group(1).split())

    def test_the_out_row_names_every_destination_the_cli_refuses(self):
        refusals = refusals_under_the_out_branch()
        self.assertEqual(2, len(refusals), refusals)
        row = self.row("--out")
        self.assertIn("ownership.yaml", row)
        self.assertIn("snapshots.csv", row,
                      "the second refusal is unpublished, and it is the one "
                      "that protects the file a rerun cannot rebuild")

    def test_the_json_row_says_an_unmatched_home_resolves_nothing(self):
        """`FOUNDER_OS_HOME` does not fall through to `default:`.

        `configured_business` returns out of the branch it enters when the
        variable is set, and that branch never reads `default`, so a variable
        matching no registered home — or more than one — resolves nothing. A
        row that chains the two with "else" tells a founder whose variable
        points at an unregistered path that they get the registry's default.
        They get exit 2.
        """
        chooser = _cli_function("configured_business")
        branch = next(
            node for node in chooser.body
            if isinstance(node, ast.If)
            and any(isinstance(child, ast.Name) and child.id == "declared"
                    for child in ast.walk(node.test)))
        self.assertIsInstance(
            branch.body[-1], ast.Return,
            "the FOUNDER_OS_HOME branch falls through now; the row may chain "
            "it to default: once that is true")
        self.assertEqual(
            [], [child for child in ast.walk(branch)
                 if isinstance(child, ast.Constant) and child.value == "default"],
            "the FOUNDER_OS_HOME branch consults default: now")
        row = self.row("--json").lower()
        self.assertIn("founder_os_home", row)
        self.assertIn("no registered home", row)
        self.assertRegex(row, r"does not fall through|rather than falling through")


class ExitCodeParagraph(unittest.TestCase):
    """Exit 3 is a promise about the page, not about the workspace."""

    def paragraph(self):
        text = DASHBOARD_DOC_PATH.read_text(encoding="utf-8")
        self.assertIn("Exit codes:", text)
        body = text.split("Exit codes:", 1)[1].split("\n\n", 1)[0]
        return " ".join(body.split()).lower()

    def test_exit_three_is_not_published_as_a_promise_that_nothing_was_written(self):
        """A write that fails part-way through exits 3 with files on disk.

        The handler that reports it sits below the first maintained write, so
        the businesses processed before the failing one keep what this run gave
        them. Its second stderr line names those directories, and the doc has
        to carry that sentence rather than the blanket "nothing was written" —
        a founder who believes the blanket version does not go looking.
        """
        handler = partial_write_handler()
        first = first_maintained_write()
        self.assertLess(
            first, handler.lineno,
            "nothing is written above the handler any more; exit 3 may go back "
            "to promising the workspace was left alone")
        self.assertTrue(
            [node for node in ast.walk(handler)
             if isinstance(node, ast.Return) and isinstance(node.value, ast.Name)
             and node.value.id == "EXIT_WRITE"],
            "the partial-write handler no longer exits 3")
        notice = next(
            node.value for node in ast.walk(handler)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            and "already written" in node.value.lower())
        paragraph = self.paragraph()
        self.assertNotRegex(
            paragraph, r"`3`\s+nothing was written",
            "exit 3 does not mean nothing was written")
        self.assertIn("the page was not written", paragraph)
        self.assertIn(notice.split(":")[0].strip().lower(), paragraph,
                      "the doc does not carry the sentence the command prints "
                      "when a write fails part-way through")


class EmptyCellGloss(unittest.TestCase):
    def test_an_empty_cell_is_not_published_as_only_a_run_that_did_not_look(self):
        """A pipeline of ten deals with one unpriced is looked at and refused.

        `analyze` counts the entries, reads the nine that carry an amount, and
        still files `live_amount` as not recorded — printing how many of how
        many it could not read. The CSV cell is empty either way, so the gloss
        that an empty cell means "we did not look" mis-describes the one case
        that matters: the run looked, and the answer the workspace supports is
        smaller than the pipeline wearing the pipeline's name.
        """
        source = ANALYZE_PATH.read_text(encoding="utf-8")
        partial = [node.value for node in ast.walk(ast.parse(source))
                   if isinstance(node, ast.Constant)
                   and isinstance(node.value, str)
                   and "deals record no amount" in node.value]
        self.assertTrue(
            partial,
            "a partly-priced pipeline no longer reports how much of it was "
            "unreadable; the published gloss may go back to 'we did not look'")
        text = " ".join(DASHBOARD_DOC_PATH.read_text(encoding="utf-8").split())
        bullet = next(part for part in text.split("- **")
                      if part.startswith("It does not invent a figure"))
        self.assertNotRegex(bullet.lower(), r'empty cell says "we did not look"')


class CommandsIndexRow(unittest.TestCase):
    def test_the_dashboard_row_promises_nothing_for_a_business_it_skips(self):
        """A registered active business with no `charter.md` is dropped.

        `docs/dashboard.md` says "every readable active business"; the command
        index said "each active business", which promises files for a business
        the run prints a skip line about and never touches.
        """
        skipped = [node.value for node in ast.walk(_cli_function("main"))
                   if isinstance(node, ast.Constant)
                   and isinstance(node.value, str) and "charter.md" in node.value]
        self.assertTrue(skipped, "the run no longer filters on charter.md")
        text = COMMANDS_PATH.read_text(encoding="utf-8")
        found = re.search(r"^\|\s*`/dashboard`\s*\|(.+?)\|\s*$", text, re.M)
        self.assertIsNotNone(found, "docs/commands.md has no /dashboard row")
        cell = " ".join(found.group(1).split()).lower()
        self.assertNotRegex(cell, r"(?:each|every) active business")
        self.assertIn("readable active business", cell)


class ThresholdConsolidationClaim(unittest.TestCase):
    def test_the_note_does_not_deny_a_restatement_the_package_still_ships(self):
        """`queue` prints the caps in a table and says so on the line above.

        The release note may describe the file as the one that settles them; it
        may not describe the citers as no longer restating them.
        """
        queue = QUEUE_SKILL_PATH.read_text(encoding="utf-8")
        restates = re.search(r"^\|\s*`## Doing`\s*\|\s*\d+\s*\|", queue, re.M)
        self.assertIsNotNone(
            restates, "queue no longer restates the caps — revisit this contract"
        )
        note = " ".join(unreleased_section().split()).lower()
        self.assertNotIn("rather than restating it", note)

    def test_the_note_does_not_claim_the_doctor_dropped_every_digit(self):
        """The doctor names the queue keys. It still prints the brief numbers.

        `_THRESHOLD_RESTATEMENTS` registers two sentences in that skill —
        `briefs.window` and `briefs.acted_one_in` — and both are numerals in
        the prose, so a note saying the doctor names keys instead of digits is
        true of the caps paragraph it heads and of nothing wider.
        """
        doctor = " ".join(DOCTOR_SKILL_PATH.read_text(encoding="utf-8").split())
        digits = re.findall(r"(\d+)\+ files in `reviews/daily/`", doctor)
        digits += re.findall(r"fewer than 1 in (\d+)", doctor)
        self.assertTrue(digits, "the doctor prints no threshold digit any more "
                                "— the note may generalise, revisit this")
        note = " ".join(unreleased_section().split()).lower()
        self.assertNotIn("names the keys instead of the digits", note)

    def test_the_note_does_not_claim_the_check_reaches_every_skill_that_states_a_limit(self):
        """`_THRESHOLD_CITERS` is a hardcoded pair, and a third skill states a
        cap without citing the file while the build stays green.

        The citation arm loops over that pair only. So "it fails the build when
        a skill states a limit without citing the file" is a guarantee the
        package does not make about the skill the finding named.
        """
        checks = validator()
        uncited = sorted(set(checks._threshold_staters())
                         - set(checks._THRESHOLD_CITERS))
        self.assertTrue(uncited, "every skill that states a limit is a citer "
                                 "now — the note may generalise, revisit this")
        for slug in uncited:
            skill = PLUGIN_ROOT / "skills" / slug / "SKILL.md"
            with self.subTest(skill=slug):
                self.assertNotIn("references/thresholds.yaml",
                                 skill.read_text(encoding="utf-8"))
        self.assertEqual([], checks.check_thresholds(PLUGIN_ROOT, None),
                         "the build fails on the uncited skill after all")
        note = " ".join(unreleased_section().split()).lower()
        self.assertNotRegex(
            note,
            r"\b(?:a|any|every|each) skill (?:states|enforces) an? "
            r"(?:limit|cap) without citing")

    def test_the_note_does_not_claim_a_corpus_the_check_never_reads(self):
        """Every file `check_thresholds` opens is under `skills/`.

        It reads `references/thresholds.yaml` itself and then the two citer
        skills and the registered restatements. The `references/*.md` glob the
        note describes was deleted in this same change.
        """
        checks = validator()
        opened = [rel for rules in checks._THRESHOLD_RESTATEMENTS.values()
                  for rel, _pattern in rules]
        opened += ["skills/%s/SKILL.md" % slug for slug in checks._THRESHOLD_CITERS]
        self.assertTrue(all(rel.startswith("skills/") for rel in opened), opened)
        note = " ".join(unreleased_section().split()).lower()
        self.assertNotRegex(note, r"corpus[^.;]{0,120}references/")


if __name__ == "__main__":
    unittest.main()
