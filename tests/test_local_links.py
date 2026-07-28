"""Repository-local Markdown/HTML link and anchor contracts."""
import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = REPO_ROOT / "scripts" / "check_local_links.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_local_links", CHECKER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class LocalLinkCheckerTest(unittest.TestCase):
    def setUp(self):
        self.checker = load_checker()
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def check(self, *tracked):
        return self.checker.check_links(self.root, tracked)

    def test_percent_decoded_markdown_target_and_anchor_resolve(self):
        write(
            self.root,
            "docs/source.md",
            "# Source\n\n[Open](target%20file.md#hello-world)\n",
        )
        write(self.root, "docs/target file.md", "# Hello, world!\n")
        self.assertEqual(
            self.check("docs/source.md", "docs/target file.md"), []
        )

    def test_html_href_src_id_and_name_resolve(self):
        write(
            self.root,
            "docs/source.html",
            '<a href="target.html#answer">Read</a>'
            '<img src="asset.svg" alt="">',
        )
        write(self.root, "docs/target.html", '<a name="answer"></a>')
        write(self.root, "docs/asset.svg", "<svg></svg>")
        self.assertEqual(
            self.check(
                "docs/source.html", "docs/target.html", "docs/asset.svg"
            ),
            [],
        )

    def test_missing_target_has_literal_source_diagnostic(self):
        write(self.root, "docs/source.md", "[Missing](missing.md)\n")
        self.assertEqual(
            self.check("docs/source.md"),
            ["docs/source.md:1: missing target 'docs/missing.md'"],
        )

    def test_missing_anchor_has_literal_target_diagnostic(self):
        write(self.root, "docs/source.md", "[Missing](target.md#absent)\n")
        write(self.root, "docs/target.md", "# Present\n")
        self.assertEqual(
            self.check("docs/source.md", "docs/target.md"),
            [
                "docs/source.md:1: missing anchor 'absent' in "
                "'docs/target.md'"
            ],
        )

    def test_duplicate_anchor_has_literal_diagnostic(self):
        write(
            self.root,
            "docs/duplicate.html",
            '<div id="same"></div>\n<a name="same"></a>\n',
        )
        self.assertEqual(
            self.check("docs/duplicate.html"),
            ["docs/duplicate.html:2: duplicate anchor 'same'"],
        )

    def test_repository_escape_is_rejected_before_existence_check(self):
        write(self.root, "docs/source.md", "[Outside](../../outside.md)\n")
        self.assertEqual(
            self.check("docs/source.md"),
            [
                "docs/source.md:1: target escapes repository "
                "'../../outside.md'"
            ],
        )

    def test_approved_external_mail_and_data_schemes_are_ignored(self):
        write(
            self.root,
            "docs/source.html",
            '<a href="https://example.com/x#y">Web</a>'
            '<a href="mailto:hello@example.com">Mail</a>'
            '<img src="data:image/svg+xml,x" alt="">',
        )
        self.assertEqual(self.check("docs/source.html"), [])

    def test_fragment_only_link_uses_the_source_document(self):
        write(self.root, "docs/source.md", "# Here\n\n[Jump](#here)\n")
        self.assertEqual(self.check("docs/source.md"), [])


class RealRepositoryLinkContract(unittest.TestCase):
    def test_checker_exists_and_real_repository_is_clean(self):
        checker = load_checker()
        self.assertEqual(checker.check_repository(REPO_ROOT), [])


if __name__ == "__main__":
    unittest.main()
