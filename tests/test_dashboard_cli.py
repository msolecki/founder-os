"""Exit codes, atomic writes, and the two files that must never be committed.

The rule under test that is easy to lose: a run that cannot resolve a workspace
writes nothing at all. A dashboard that leaves a half-written page behind after
failing is worse than one that fails, because the half-written page is the one
the founder opens.
"""
import contextlib
import csv
import hashlib
import importlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "founder-os"
DASHBOARD = PLUGIN_ROOT / "scripts" / "dashboard"
EXAMPLE = REPO_ROOT / "examples" / "studio-north"


def load_main():
    if "fos_dashboard" not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            "fos_dashboard", DASHBOARD / "__init__.py",
            submodule_search_locations=[str(DASHBOARD)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["fos_dashboard"] = package
        spec.loader.exec_module(package)
    return importlib.import_module("fos_dashboard.__main__")


class TestCli(unittest.TestCase):
    def setUp(self):
        self.main = load_main()
        self.workspace = Path(tempfile.mkdtemp()) / "founder-os"
        shutil.copytree(EXAMPLE, self.workspace)

    def _run(self, *args):
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.main.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_json_prints_facts_and_writes_nothing(self):
        code, out, _ = self._run(
            "--home", str(self.workspace), "--now", "2026-07-20", "--json")
        self.assertEqual(code, self.main.EXIT_OK)
        payload = json.loads(out)
        self.assertEqual(payload["today"], "2026-07-20")
        self.assertFalse((self.workspace / "_dashboard").exists())

    def _outside_dashboard(self):
        """Every path in the workspace but `_dashboard/`, with its content.

        A name-only, top-level, one-directional comparison passes a run that
        rewrites `queue.md`, invents `decisions/2026-07-20.md`, or deletes a
        file outright. Equality over a recursive digest catches all three.
        """
        entries = {}
        for path in self.workspace.rglob("*"):
            relative = path.relative_to(self.workspace)
            if relative.parts[0] == "_dashboard":
                continue
            entries[relative.as_posix()] = (
                hashlib.sha256(path.read_bytes()).hexdigest()
                if path.is_file() else "<directory>")
        return entries

    def test_a_normal_run_writes_only_inside_dashboard(self):
        before = self._outside_dashboard()
        code, _, _ = self._run("--home", str(self.workspace), "--now", "2026-07-20")
        self.assertEqual(code, self.main.EXIT_OK)
        self.assertEqual(self._outside_dashboard(), before)
        self.assertTrue((self.workspace / "_dashboard" / "facts.json").exists())
        self.assertTrue((self.workspace / "_dashboard" / "snapshots.csv").exists())

    def test_a_slug_with_home_is_refused_rather_than_used_as_a_label(self):
        code, _, err = self._run("zeta", "--home", str(self.workspace),
                                 "--now", "2026-07-20")
        self.assertEqual(code, self.main.EXIT_UNRESOLVED)
        self.assertIn("--home", err)
        self.assertFalse((self.workspace / "_dashboard").exists())

    def test_a_page_over_the_byte_limit_writes_nothing_at_all(self):
        code, _, err = self._run("--home", str(self.workspace),
                                 "--now", "2026-07-20", "--max-bytes", "100")
        self.assertEqual(code, self.main.EXIT_WRITE)
        self.assertIn("100", err)
        self.assertIsNotNone(re.search(r"\d+ bytes", err))
        self.assertFalse((self.workspace / "_dashboard").exists())

    def test_a_snapshots_series_that_cannot_be_decoded_is_refused(self):
        self._run("--home", str(self.workspace), "--now", "2026-07-20")
        (self.workspace / "_dashboard" / "snapshots.csv").write_bytes(
            b"\xff\xfe not utf-8\n")
        code, _, err = self._run("--home", str(self.workspace),
                                 "--now", "2026-07-21")
        self.assertEqual(code, self.main.EXIT_WRITE)
        self.assertIn("_dashboard", err)

    def test_gitignore_protects_the_two_regenerable_files_only(self):
        self._run("--home", str(self.workspace), "--now", "2026-07-20")
        text = (self.workspace / "_dashboard" / ".gitignore").read_text(
            encoding="utf-8")
        self.assertIn("index.html", text)
        self.assertIn("facts.json", text)
        self.assertNotIn("snapshots.csv", text)

    def test_running_twice_on_one_day_keeps_one_snapshot_row(self):
        self._run("--home", str(self.workspace), "--now", "2026-07-20")
        self._run("--home", str(self.workspace), "--now", "2026-07-20")
        path = self.workspace / "_dashboard" / "snapshots.csv"
        rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
        self.assertEqual(len(rows), 1)

    def test_unresolvable_workspace_exits_two_and_writes_nothing(self):
        empty = Path(tempfile.mkdtemp()) / "nowhere"
        code, _, err = self._run("--home", str(empty), "--now", "2026-07-20")
        self.assertEqual(code, self.main.EXIT_UNRESOLVED)
        self.assertIn("founder-os-init", err)
        self.assertFalse(empty.exists())

    def test_non_iso_now_is_refused(self):
        code, _, err = self._run(
            "--home", str(self.workspace), "--now", "20 July 2026")
        self.assertEqual(code, self.main.EXIT_UNRESOLVED)
        self.assertIn("YYYY-MM-DD", err)

    def test_unreadable_file_still_produces_a_page_and_exit_zero(self):
        (self.workspace / "metrics.md").write_bytes(b"\xff\xfe\x00")
        code, _, _ = self._run("--home", str(self.workspace), "--now", "2026-07-20")
        self.assertEqual(code, self.main.EXIT_OK)
        payload = json.loads(
            (self.workspace / "_dashboard" / "facts.json").read_text(
                encoding="utf-8"))
        checks = [item["check"] for item in payload["integrity"]]
        self.assertIn("file-unreadable", checks)


class TestPage(unittest.TestCase):
    def setUp(self):
        self.main = load_main()
        self.workspace = Path(tempfile.mkdtemp()) / "founder-os"
        shutil.copytree(EXAMPLE, self.workspace)

    def _run(self, *args):
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.main.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_a_normal_run_writes_the_page(self):
        self._run("--home", str(self.workspace), "--now", "2026-07-20")
        page = self.workspace / "_dashboard" / "index.html"
        self.assertTrue(page.exists())
        self.assertIn("Studio North", page.read_text(encoding="utf-8"))

    def test_out_overrides_the_destination(self):
        """`--out` stays free for a path no agent owns and no run maintains.

        The second half is inside `_dashboard/` on purpose: the directory is
        derived and owner-less, so a new file in it is allowed. The three files
        the run writes there itself are not, which the tests below pin.
        """
        target = Path(tempfile.mkdtemp()) / "elsewhere" / "page.html"
        code, _, _ = self._run("--home", str(self.workspace), "--now",
                               "2026-07-20", "--out", str(target))
        self.assertEqual(code, self.main.EXIT_OK)
        self.assertTrue(target.exists())
        inside = self.workspace / "_dashboard" / "for-the-client.html"
        code, _, _ = self._run("--home", str(self.workspace), "--now",
                               "2026-07-20", "--out", str(inside))
        self.assertEqual(code, self.main.EXIT_OK)
        self.assertTrue(inside.exists())

    def test_out_refuses_a_file_an_agent_owns_and_leaves_it_alone(self):
        goals = self.workspace / "goals.md"
        before = goals.read_bytes()
        code, _, err = self._run("--home", str(self.workspace), "--now",
                                 "2026-07-20", "--out", str(goals))
        self.assertEqual(code, self.main.EXIT_WRITE)
        self.assertIn("strategist", err)
        self.assertIn("goals.md", err)
        self.assertEqual(goals.read_bytes(), before)
        self.assertFalse((self.workspace / "_dashboard").exists())

    def test_out_refuses_an_owned_file_spelled_in_another_case(self):
        """`Goals.md` and `goals.md` are one file on the founder's Mac.

        Matched exactly, the guard is dodged by a shift key and the write
        lands on the strategist's file. No assertion here reads `Goals.md`
        back: on a case-sensitive filesystem it is a second file, and what
        must hold on both is that no page landed in the workspace root.
        """
        goals = self.workspace / "goals.md"
        before = goals.read_bytes()
        code, _, err = self._run("--home", str(self.workspace), "--now",
                                 "2026-07-20", "--out",
                                 str(self.workspace / "Goals.md"))
        self.assertEqual(code, self.main.EXIT_WRITE)
        self.assertIn("strategist", err)
        self.assertEqual(goals.read_bytes(), before)
        pages = [path.name for path in self.workspace.iterdir()
                 if path.is_file() and path.read_bytes().startswith(b"<!doctype")]
        self.assertEqual(pages, [])

    def test_out_refuses_the_series_the_run_maintains(self):
        """The one file here a rerun cannot rebuild is not an `--out` target.

        The run merges the day's row into `snapshots.csv` and would then write
        the page over it, so the series is destroyed by the same run that just
        extended it. Both spellings are refused for the reason above.
        """
        self._run("--home", str(self.workspace), "--now", "2026-07-19")
        self._run("--home", str(self.workspace), "--now", "2026-07-20")
        series = self.workspace / "_dashboard" / "snapshots.csv"
        before = series.read_bytes()
        for name in ("snapshots.csv", "Snapshots.csv"):
            code, _, err = self._run(
                "--home", str(self.workspace), "--now", "2026-07-21",
                "--out", str(self.workspace / "_dashboard" / name))
            self.assertEqual(code, self.main.EXIT_WRITE, name)
            self.assertIn("rebuild", err)
        self.assertEqual(series.read_bytes(), before)
        rows = list(csv.DictReader(before.decode("utf-8").splitlines()))
        self.assertEqual([row["date"] for row in rows],
                         ["2026-07-19", "2026-07-20"])

    def test_out_refuses_the_gitignore_the_run_maintains(self):
        """The ignore file is why the two regenerable files stay uncommitted.

        The page written over it takes `index.html` and `facts.json` out of the
        ignore list, and nothing repairs it: the `--out` branch skips
        `ensure_gitignore`, so the next run does not either, and the workspace
        starts committing a full copy of itself. Pinned because dropping
        `.gitignore` from MAINTAINED leaves every other test in this file green.
        """
        self._run("--home", str(self.workspace), "--now", "2026-07-20")
        ignore = self.workspace / "_dashboard" / ".gitignore"
        before = ignore.read_bytes()
        for name in (".gitignore", ".GitIgnore"):
            code, _, err = self._run(
                "--home", str(self.workspace), "--now", "2026-07-21",
                "--out", str(self.workspace / "_dashboard" / name))
            self.assertEqual(code, self.main.EXIT_WRITE, name)
            self.assertIn("writes that file itself", err)
        self.assertEqual(ignore.read_bytes(), before)

    def test_out_refuses_the_facts_envelope_the_run_maintains(self):
        self._run("--home", str(self.workspace), "--now", "2026-07-20")
        facts = self.workspace / "_dashboard" / "facts.json"
        code, _, _ = self._run("--home", str(self.workspace), "--now",
                               "2026-07-20", "--out", str(facts))
        self.assertEqual(code, self.main.EXIT_WRITE)
        json.loads(facts.read_text(encoding="utf-8"))

    def test_open_with_a_relative_home_prints_an_absolute_path(self):
        """`--home <relative> --open` reaches `as_uri()`, which refuses one.

        Unresolved it wrote every file and then died on the line that opens
        the page, so the founder was told the run failed after it had already
        rewritten the workspace's derived directory.
        """
        origin = Path.cwd()
        os.chdir(self.workspace.parent)
        self.addCleanup(os.chdir, str(origin))
        with mock.patch("webbrowser.open") as opened:
            code, out, _ = self._run("--home", self.workspace.name,
                                     "--now", "2026-07-20", "--open")
        self.assertEqual(code, self.main.EXIT_OK)
        printed = out.strip()
        self.assertTrue(Path(printed).is_absolute(), printed)
        self.assertTrue(Path(printed).exists(), printed)
        self.assertTrue(opened.call_args[0][0].startswith("file://"),
                        opened.call_args)

    def test_out_refuses_a_path_inside_a_directory_an_agent_owns(self):
        target = self.workspace / "clients" / "acme" / "page.html"
        code, _, err = self._run("--home", str(self.workspace), "--now",
                                 "2026-07-20", "--out", str(target))
        self.assertEqual(code, self.main.EXIT_WRITE)
        self.assertIn("delivery-lead", err)
        self.assertFalse(target.exists())

    def test_open_with_a_relative_out_prints_the_path_it_opened(self):
        directory = Path(tempfile.mkdtemp())
        origin = Path.cwd()
        os.chdir(directory)
        self.addCleanup(os.chdir, str(origin))
        with mock.patch("webbrowser.open") as opened:
            code, out, _ = self._run(
                "--home", str(self.workspace), "--now", "2026-07-20",
                "--out", "page.html", "--open")
        self.assertEqual(code, self.main.EXIT_OK)
        self.assertTrue((directory / "page.html").exists())
        printed = out.strip()
        self.assertTrue(Path(printed).is_absolute(), printed)
        self.assertTrue(printed.endswith("page.html"), printed)
        self.assertTrue(opened.call_args[0][0].startswith("file://"),
                        opened.call_args)


class TestRegistry(unittest.TestCase):
    """The multi-business path: the slug has to select something.

    Every other test here passes `--home`, which builds a one-element payload
    list where any selection is right by accident.
    """

    def setUp(self):
        self.main = load_main()
        self.lab = Path(tempfile.mkdtemp())
        self.home = self.lab / "home"
        (self.home / ".founder-os").mkdir(parents=True)
        self.acme = self.lab / "acme"
        self.zeta = self.lab / "zeta"
        shutil.copytree(EXAMPLE, self.acme)
        shutil.copytree(EXAMPLE, self.zeta)

    def test_out_refuses_another_business_series_it_did_not_render(self):
        """The refusal follows the registry, not the run.

        `--home` renders one workspace, so taking the maintained set from the
        rendered businesses left every other registered `_dashboard/` outside
        it: a run against acme overwrote zeta's `snapshots.csv` — the one file
        a rerun cannot rebuild — at exit 0, while the ownership refusal beside
        it already consulted the registry and correctly refused zeta's
        `goals.md`.
        """
        self._registry()
        self._run("--home", str(self.zeta), "--now", "2026-07-20")
        derived = self.zeta / "_dashboard"
        for name in ("snapshots.csv", "facts.json"):
            with self.subTest(name=name):
                target = derived / name
                before = target.read_bytes()
                code, _, err = self._run("--home", str(self.acme), "--now",
                                         "2026-07-21", "--out", str(target))
                self.assertEqual(code, self.main.EXIT_WRITE, err)
                self.assertEqual(target.read_bytes(), before)

    def test_out_still_allows_a_new_file_in_another_derived_directory(self):
        self._registry()
        target = self.zeta / "_dashboard" / "for-the-client.html"
        code, _, err = self._run("--home", str(self.acme), "--now",
                                 "2026-07-21", "--out", str(target))
        self.assertEqual(code, self.main.EXIT_OK, err)
        self.assertTrue(target.exists())

    def _registry(self, text=None, portfolio=None, default=None):
        if text is None:
            text = ("businesses:\n"
                    "  acme:\n    home: %s\n    status: active\n"
                    "  zeta:\n    home: %s\n    status: active\n"
                    % (self.acme, self.zeta))
            if portfolio is not None:
                text += "portfolio: %s\n" % portfolio
            if default is not None:
                text += "default: %s\n" % default
        (self.home / ".founder-os" / "businesses.yaml").write_text(
            text, encoding="utf-8")

    def _run(self, *args, home_env=None):
        environment = dict(os.environ)
        environment["HOME"] = str(self.home)
        environment.pop("FOUNDER_OS_HOME", None)
        if home_env is not None:
            environment["FOUNDER_OS_HOME"] = str(home_env)
        out = io.StringIO()
        err = io.StringIO()
        with mock.patch.dict(os.environ, environment, clear=True):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = self.main.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_json_answers_about_the_business_the_slug_names(self):
        self._registry()
        code, out, _ = self._run("zeta", "--now", "2026-07-20", "--json")
        self.assertEqual(code, self.main.EXIT_OK)
        payload = json.loads(out)
        self.assertEqual(payload["business"]["slug"], "zeta")
        self.assertEqual(payload["business"]["home"], str(self.zeta))

    def test_an_unknown_slug_is_refused_rather_than_answered_about_another(self):
        self._registry()
        code, out, err = self._run("nosuch", "--now", "2026-07-20", "--json")
        self.assertEqual(code, self.main.EXIT_UNRESOLVED)
        self.assertEqual(out, "")
        self.assertIn("nosuch", err)
        self.assertIn("acme", err)

    def test_json_without_a_slug_refuses_to_pick_a_business(self):
        """One envelope, two businesses, no slug: naming one would be a guess."""
        self._registry()
        code, out, err = self._run("--now", "2026-07-20", "--json")
        self.assertEqual(code, self.main.EXIT_UNRESOLVED)
        self.assertEqual(out, "")
        self.assertIn("acme", err)
        self.assertIn("zeta", err)

    def test_json_without_a_slug_uses_the_registry_default(self):
        """`default:` is the founder's answer, so refusing to guess is wrong.

        references/multi-business.md fixes the order — the slug, then
        `FOUNDER_OS_HOME`, then `default:` — and a refusal a founder cannot
        configure away turns the documented question-answering mode off on
        every install with two businesses.
        """
        self._registry(default="zeta")
        code, out, err = self._run("--now", "2026-07-20", "--json")
        self.assertEqual(code, self.main.EXIT_OK, err)
        self.assertEqual(json.loads(out)["business"]["slug"], "zeta")

    def test_json_without_a_slug_uses_founder_os_home_over_the_default(self):
        """The expected slug is neither `default:` nor the first business.

        `contracts.active_businesses` sorts slugs, so pointing the environment
        at `acme` makes the assertion pass for a run that resolved nothing and
        took `live[0]` — which is the wrong-company answer this test exists to
        catch. `default: acme` with the environment on `zeta` leaves exactly
        one way to reach `zeta`: reading FOUNDER_OS_HOME and preferring it.
        """
        self._registry(default="acme")
        code, out, err = self._run("--now", "2026-07-20", "--json",
                                   home_env=self.zeta)
        self.assertEqual(code, self.main.EXIT_OK, err)
        payload = json.loads(out)
        self.assertEqual(payload["business"]["slug"], "zeta")
        self.assertEqual(payload["business"]["home"], str(self.zeta))

    def test_json_writes_nothing_on_a_multi_business_registry_either(self):
        """"Writes nothing at all, in every configuration" is the published
        sentence, and the single-workspace test cannot see the per-business
        loop that `--json` returns in front of — it runs once per readable
        business, and with `--home` there is only ever one.
        """
        self._registry(default="zeta")
        code, out, err = self._run("--now", "2026-07-20", "--json")
        self.assertEqual(code, self.main.EXIT_OK, err)
        self.assertEqual(json.loads(out)["business"]["slug"], "zeta")
        for workspace in (self.acme, self.zeta):
            self.assertFalse((workspace / "_dashboard").exists(), workspace)

    def test_the_page_lands_where_the_registry_default_says_and_opens_it(self):
        """`default:` decides the page's workspace and its opening view.

        Consulted only under --json, the page was written into the
        alphabetically first business's `_dashboard/` and opened that company's
        numbers under the other's name, on a registry whose one configured
        answer said otherwise. Both halves are asserted: where the file landed,
        and which section the page leaves unhidden.
        """
        self._registry(default="zeta")
        code, out, err = self._run("--now", "2026-07-20")
        self.assertEqual(code, self.main.EXIT_OK, err)
        page = (self.zeta / "_dashboard" / "index.html")
        self.assertEqual(Path(out.strip()), page.resolve())
        text = page.read_text(encoding="utf-8")
        self.assertIn('id="business-zeta">', text)
        self.assertIn('id="business-acme" hidden>', text)

    def test_the_page_lands_where_founder_os_home_says_over_the_default(self):
        """Same precedence as --json, and again neither `default:` nor live[0].

        `default: acme` is also the first business, so `zeta` is reachable only
        by reading FOUNDER_OS_HOME and preferring it over the registry.
        """
        self._registry(default="acme")
        code, out, err = self._run("--now", "2026-07-20", home_env=self.zeta)
        self.assertEqual(code, self.main.EXIT_OK, err)
        page = (self.zeta / "_dashboard" / "index.html")
        self.assertEqual(Path(out.strip()), page.resolve())
        self.assertIn('id="business-acme" hidden>',
                      page.read_text(encoding="utf-8"))

    def test_the_page_still_opens_the_first_business_when_nothing_is_configured(self):
        """No slug, no environment, no `default:`: the page does not refuse.

        Only --json refuses an unanswered "which business", because one
        envelope can carry one. The page carries every business, so opening the
        first is a view, not a figure filed under the wrong name.
        """
        self._registry()
        code, out, err = self._run("--now", "2026-07-20")
        self.assertEqual(code, self.main.EXIT_OK, err)
        self.assertEqual(Path(out.strip()),
                         (self.acme / "_dashboard" / "index.html").resolve())

    def test_a_write_failure_names_the_businesses_already_written(self):
        """Exit 3 out of the per-business loop is not "nothing was written".

        The loop is not a transaction: every business before the failing one
        keeps the facts.json and snapshots.csv this run gave it. A founder told
        nothing was written would not go looking for them, so the message names
        them, and the assertions below check the claim is true.
        """
        self._registry()
        self._run("--now", "2026-07-20")
        (self.zeta / "_dashboard" / "snapshots.csv").write_bytes(
            b"\xff\xfe not utf-8\n")
        code, _, err = self._run("--now", "2026-07-21")
        self.assertEqual(code, self.main.EXIT_WRITE)
        self.assertIn(str(self.acme / "_dashboard"), err)
        series = (self.acme / "_dashboard" / "snapshots.csv").read_text(
            encoding="utf-8")
        rows = list(csv.DictReader(series.splitlines()))
        self.assertEqual([row["date"] for row in rows],
                         ["2026-07-20", "2026-07-21"])

    def test_json_refuses_when_founder_os_home_names_no_registered_business(self):
        """A pointer to somewhere unregistered resolves nothing, not the default.

        Reading past it to `default:` would answer about a business the
        founder's most explicit setting says they are not in.
        """
        self._registry(default="zeta")
        code, out, err = self._run("--now", "2026-07-20", "--json",
                                   home_env=self.lab / "elsewhere")
        self.assertEqual(code, self.main.EXIT_UNRESOLVED)
        self.assertEqual(out, "")
        self.assertIn("acme", err)

    def test_out_refuses_another_registered_workspace_under_home(self):
        """`--home` narrows what is rendered, not what may be overwritten.

        The registry was never loaded on this path, so the ownership guard knew
        only the `--home` root and let the page land on a second registered
        business's `goals.md`. Confirmed as a real overwrite before this test
        existed: the file's digest changed and the run exited 0.
        """
        self._registry()
        goals = self.zeta / "goals.md"
        before = goals.read_bytes()
        code, _, err = self._run("--home", str(self.acme), "--now",
                                 "2026-07-20", "--out", str(goals))
        self.assertEqual(code, self.main.EXIT_WRITE, err)
        self.assertIn("strategist", err)
        self.assertEqual(goals.read_bytes(), before)

    def test_home_and_out_survive_a_registry_the_parser_rejects(self):
        """The escape hatch has to outlive the file it exists to bypass.

        Consulting the registry for the refusal above must not let a registry
        the parser rejects break `--home`, which is the one way out of exactly
        that state.
        """
        self._registry(text="businesses:\n  acme:\n    home: relative/path\n"
                            "    status: active\n")
        target = self.lab / "elsewhere" / "page.html"
        code, _, err = self._run("--home", str(self.acme), "--now",
                                 "2026-07-20", "--out", str(target))
        self.assertEqual(code, self.main.EXIT_OK, err)
        self.assertTrue(target.exists())

    def test_a_resolver_bug_is_not_reported_as_the_founders_registry(self):
        """Only the parser's own error means "go and fix businesses.yaml".

        Catching everything sends a founder to edit a file that is fine
        whenever the failure is ours, and hides the line that broke.
        """
        self._registry()
        with mock.patch.object(self.main.contracts, "active_businesses",
                               side_effect=AttributeError("resolver bug")):
            with self.assertRaises(AttributeError):
                self._run("--now", "2026-07-20")

    def test_the_page_lands_in_the_workspace_the_slug_names(self):
        self._registry()
        code, out, _ = self._run("zeta", "--now", "2026-07-20")
        self.assertEqual(code, self.main.EXIT_OK)
        self.assertEqual(Path(out.strip()),
                         (self.zeta / "_dashboard" / "index.html").resolve())

    def test_the_portfolio_page_directory_is_ignored_by_git_too(self):
        portfolio = self.lab / "portfolio"
        portfolio.mkdir()
        self._registry(portfolio=portfolio)
        code, out, _ = self._run("--now", "2026-07-20")
        self.assertEqual(code, self.main.EXIT_OK)
        self.assertEqual(Path(out.strip()),
                         (portfolio / "_dashboard" / "index.html").resolve())
        ignore = portfolio / "_dashboard" / ".gitignore"
        self.assertTrue(ignore.exists())
        self.assertIn("index.html", ignore.read_text(encoding="utf-8"))

    def test_a_registry_that_cannot_be_read_exits_two_not_a_traceback(self):
        self._registry(text="businesses:\n  acme:\n    home: relative/path\n"
                            "    status: active\n")
        code, out, err = self._run("--now", "2026-07-20")
        self.assertEqual(code, self.main.EXIT_UNRESOLVED)
        self.assertEqual(out, "")
        self.assertIn("businesses.yaml", err)

    def test_a_business_with_no_charter_is_named_rather_than_dropped(self):
        self._registry()
        (self.zeta / "charter.md").unlink()
        code, _, err = self._run("--now", "2026-07-20")
        self.assertEqual(code, self.main.EXIT_OK)
        self.assertIn("zeta", err)
        self.assertIn("charter.md", err)


class TestRunnableAsACommand(unittest.TestCase):
    """`python3 <plugin>/scripts/dashboard` is the interface the skill documents.

    Run that way the package directory is the entry point, not an import, so
    `__main__` has no parent and every relative import in it would raise. The
    unit tests above import the module and would never see it.
    """

    def test_the_package_directory_runs_as_a_command(self):
        workspace = Path(tempfile.mkdtemp()) / "founder-os"
        shutil.copytree(EXAMPLE, workspace)
        result = subprocess.run(
            [sys.executable, str(DASHBOARD),
             "--home", str(workspace), "--now", "2026-07-20"],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("index.html", result.stdout)
        self.assertTrue((workspace / "_dashboard" / "facts.json").exists())


class TestFlagsAndDocsAgree(unittest.TestCase):
    """The parser's flags and the flag table in docs/dashboard.md, compared.

    `--no-commentary` shipped on the parser, did nothing, and appeared in no
    document; no test in the repo would have caught it. Both directions matter:
    a flag the founder can type and cannot read about is as bad as a row in the
    table naming a flag the command rejects.
    """

    FLAG = re.compile(r"--[a-z][a-z0-9-]*")

    def test_the_parser_and_the_documented_table_name_the_same_flags(self):
        main = load_main()
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            with self.assertRaises(SystemExit):
                main.main(["--help"])
        offered = set(self.FLAG.findall(printed.getvalue())) - {"--help"}
        documented = set(self.FLAG.findall(
            (REPO_ROOT / "docs" / "dashboard.md").read_text(encoding="utf-8")))
        self.assertEqual(offered, documented)


class TestPackaging(unittest.TestCase):
    def test_skill_exists_with_frontmatter(self):
        skill = PLUGIN_ROOT / "skills" / "dashboard" / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        self.assertIn("name: dashboard", text)

    def test_skill_declares_no_writes_because_it_owns_nothing(self):
        text = (PLUGIN_ROOT / "skills" / "dashboard" / "SKILL.md").read_text(
            encoding="utf-8")
        self.assertNotIn("writes:", text.split("---")[1])

    def test_skill_is_system_and_standalone(self):
        spec = importlib.util.spec_from_file_location(
            "fos_package", REPO_ROOT / "scripts" / "_package.py")
        package = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(package)
        self.assertIn("dashboard", package.SYSTEM_SKILLS)
        self.assertIn("dashboard", package.STANDALONE_SKILLS)



if __name__ == "__main__":
    unittest.main()
