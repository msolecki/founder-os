"""Structure contract for the `claude plugin eval` suite under evals/.

A mistyped grader or a renamed case would otherwise fail only in a paid eval
run, so the shape every case needs is checked here instead.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
NOT_CASES = {"fixtures", "results"}
GRADER_TYPES = {"llm", "regex", "file_exists", "tool_used"}
README_ROW = re.compile(r"^\| `([^`]+)` \|", re.MULTILINE)


def frontmatter(path):
    """Split like `claude plugin eval`: the frontmatter ends at the first
    line after line 1 that contains `---` anywhere, not only a bare `---`."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        return None, lines
    for index in range(1, len(lines)):
        if "---" in lines[index]:
            return lines[1:index], lines[index + 1:]
    return None, lines


def case_dirs():
    return sorted(
        path for path in EVALS.iterdir()
        if path.is_dir() and path.name not in NOT_CASES
    )


class EvalSuiteStructure(unittest.TestCase):
    def test_suite_has_cases(self):
        self.assertGreaterEqual(len(case_dirs()), 10)

    def test_every_case_is_complete(self):
        for case in case_dirs():
            with self.subTest(case=case.name):
                spec = yaml.safe_load(
                    (case / "case.yaml").read_text(encoding="utf-8")
                )
                self.assertIsInstance(spec, dict)
                self.assertEqual(spec.get("name"), case.name)
                self.assertTrue((case / "prompt.md").is_file())
                script = (spec.get("context") or {}).get("scaffold_script")
                if script is not None:
                    self.assertTrue((case / script).is_file(), script)

    def test_every_case_has_a_deterministic_grader(self):
        for case in case_dirs():
            with self.subTest(case=case.name):
                graders = sorted((case / "graders").glob("*.md"))
                self.assertTrue(graders, "no graders")
                types = []
                for grader in graders:
                    head, body = frontmatter(grader)
                    self.assertIsNotNone(head, "%s has no frontmatter" % grader.name)
                    meta = yaml.safe_load("\n".join(head)) or {}
                    self.assertIn(meta.get("type"), GRADER_TYPES, grader.name)
                    if meta["type"] in {"llm", "regex"}:
                        self.assertTrue(
                            "\n".join(body).strip(), "%s is empty" % grader.name
                        )
                    types.append(meta["type"])
                self.assertTrue(set(types) - {"llm"}, "only llm graders")

    def test_frontmatter_holds_no_triple_dash(self):
        for path in sorted(EVALS.rglob("*.md")):
            if "results" in path.relative_to(EVALS).parts:
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
            if not lines or lines[0] != "---":
                continue
            with self.subTest(path=str(path.relative_to(ROOT))):
                close = lines.index("---", 1)
                for line in lines[1:close]:
                    self.assertNotIn("---", line)

    def test_readme_lists_each_case_once(self):
        rows = README_ROW.findall(
            (EVALS / "README.md").read_text(encoding="utf-8")
        )
        self.assertEqual(sorted(rows), [case.name for case in case_dirs()])


if __name__ == "__main__":
    unittest.main()
