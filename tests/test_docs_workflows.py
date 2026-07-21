"""Contract tests for the dependency-free workflow catalogue landing section."""
import re
import shutil
import subprocess
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HTML = (REPO_ROOT / "docs" / "index.html").read_text(encoding="utf-8")
BEHAVIOR_TEST = (
    REPO_ROOT / "tests" / "docs_workflows.behavior.test.js"
).read_text(encoding="utf-8")
CONTROLLER_SOURCES = ("workflow-library.js", "demo-tabs.js")
SECTION_START = HTML.index(
    '<section class="section workflow-library" id="workflows">')
SECTION = HTML[SECTION_START:HTML.index("</section>", SECTION_START)]

EXPECTED_ENTRIES = {
    "plan": (10, "Set direction"),
    "sell": (4, "Move a deal"),
    "deliver": (4, "Deliver well"),
    "money": (5, "Know the numbers"),
    "focus": (9, "Protect focus"),
    "grow": (8, "Grow deliberately"),
    "run": (9, "Run operations"),
}


class DocumentContractParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.references = []

    def handle_starttag(self, _tag, attrs):
        attributes = dict(attrs)
        if attributes.get("id"):
            self.ids.append(attributes["id"])
        href = attributes.get("href", "")
        if href.startswith("#") and len(href) > 1:
            self.references.append(href[1:])
        for name in ("aria-controls", "aria-labelledby", "aria-describedby"):
            self.references.extend(attributes.get(name, "").split())


class WorkflowLibraryContractTest(unittest.TestCase):
    def test_launch_page_declares_favicon_and_apple_touch_icon(self):
        self.assertIn('rel="icon" type="image/svg+xml"', HTML)
        self.assertIn('rel="apple-touch-icon"', HTML)

    def test_launch_page_declares_csp_and_referrer_policy(self):
        self.assertIn('http-equiv="Content-Security-Policy"', HTML)
        self.assertIn("default-src 'self'", HTML)
        self.assertIn("script-src 'self' 'unsafe-inline'", HTML)
        csp = re.search(
            r'http-equiv="Content-Security-Policy" content="([^"]+)"', HTML
        ).group(1)
        self.assertNotIn("unsafe-eval", csp)
        self.assertNotRegex(csp, r"https?://")
        self.assertIn('name="referrer" content="strict-origin-when-cross-origin"', HTML)

    def test_controllers_load_from_same_origin_scripts(self):
        for source in CONTROLLER_SOURCES:
            with self.subTest(source=source):
                self.assertTrue((REPO_ROOT / "docs" / source).is_file())
                self.assertIn(f'<script src="{source}"></script>', HTML)

    def test_behavior_suite_requires_modules_without_eval_or_source_markers(self):
        self.assertIn("require('../docs/workflow-library.js')", BEHAVIOR_TEST)
        self.assertIn("require('../docs/demo-tabs.js')", BEHAVIOR_TEST)
        self.assertNotIn("extractController", BEHAVIOR_TEST)
        self.assertNotIn("eval(", BEHAVIOR_TEST)
        self.assertNotIn(
            "const workflowCatalogue = document.querySelector", BEHAVIOR_TEST
        )
        self.assertNotIn(
            "const tabs = [...document.querySelectorAll", BEHAVIOR_TEST
        )

    def test_page_texture_avoids_svg_fractal_noise_filter(self):
        self.assertNotIn("feTurbulence", HTML)
        self.assertIn("background-image: radial-gradient", HTML)

    def test_sticky_header_does_not_use_scroll_time_blur(self):
        header = HTML[HTML.index(".site-header {"):HTML.index(".site-header::after")]
        self.assertIn("background: var(--paper);", header)
        self.assertNotIn("backdrop-filter", header)

    def test_script_error_reveals_content_fallback(self):
        self.assertIn("window.addEventListener('error'", HTML)
        self.assertIn("item.classList.add('is-visible')", HTML)

    def test_workflow_summary_focus_ring_is_visible_and_unclipped(self):
        self.assertIn(".workflow-catalogue summary:focus-visible", HTML)
        self.assertIn("outline: 3px solid var(--orange);", HTML)
        self.assertIn(".workflow-catalogue {", HTML)
        self.assertRegex(HTML, r"\.workflow-catalogue \{[^}]*overflow: visible")

    def test_labeled_generic_regions_have_naming_capable_roles(self):
        self.assertIn(
            'class="command-center reveal" role="group" aria-label=', HTML)
        self.assertIn(
            'class="hero-stats reveal" role="group" aria-label=', HTML)
        self.assertIn(
            'class="multi-diagram" role="img" aria-label=', HTML)
        self.assertIn(
            'class="multi-principles" role="group" aria-label=', HTML)

    def test_orange_section_copy_uses_solid_ink_for_contrast(self):
        self.assertRegex(
            HTML,
            r"\.multi-business \.section-copy \{[^}]*color: var\(--ink\)",
        )
        self.assertRegex(
            HTML,
            r"\.multi-principle span \{[^}]*color: var\(--ink\)",
        )
        self.assertNotIn("color: rgba(18, 33, 39, 0.78)", HTML)
        self.assertNotIn("color: rgba(18, 33, 39, 0.72)", HTML)

    def test_launch_metadata_supports_social_sharing(self):
        required = (
            'property="og:type" content="website"',
            'property="og:title"',
            'property="og:description"',
            'property="og:url"',
            'property="og:image"',
            'content="https://msolecki.github.io/founder-os/"',
            'content="https://msolecki.github.io/founder-os/og-image.svg"',
            'name="twitter:card" content="summary_large_image"',
            'name="twitter:image"',
            'rel="canonical"',
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, HTML)

    def test_problem_first_entries_are_complete(self):
        entries = re.findall(
            r'<a class="workflow-entry"[^>]*data-workflow-filter="([^"]+)"'
            r'[^>]*>\s*<strong>([^<]+)</strong>', SECTION)
        self.assertEqual(len(entries), 7)
        self.assertEqual(len({category for category, _ in entries}), 7)
        self.assertEqual(dict(entries), {
            category: label for category, (_, label) in EXPECTED_ENTRIES.items()
        })

    def test_category_counts_still_partition_all_49_workflows(self):
        counts = Counter()
        groups = re.findall(
                r'<details class="workflow-group"[^>]*data-category="([^"]+)"'
                r'[^>]*>(.*?)</details>', SECTION, re.S)
        self.assertEqual(len(groups), 14)
        for category, body in groups:
            counts[category] += body.count('class="workflow-item"')
        self.assertEqual(dict(counts), {
            category: count for category, (count, _) in EXPECTED_ENTRIES.items()
        })
        self.assertEqual(sum(counts.values()), 49)

    def test_complete_catalogue_and_cadence_contract_survives(self):
        commands = re.findall(
            r'<article class="workflow-item".*?<code>(/[^<]+)</code>',
            SECTION, re.S)
        self.assertEqual(len(commands), 49)
        self.assertEqual(len(set(commands)), 49)
        self.assertEqual(SECTION.count('class="workflow-badge"'), 10)

    def test_catalogue_is_native_and_available_without_javascript(self):
        compact = re.sub(r"\s+", " ", HTML)
        self.assertRegex(
            SECTION,
            r'<details class="workflow-catalogue" id="workflow-catalogue" open>')
        entry_tags = re.findall(r'<a class="workflow-entry"[^>]*>', SECTION)
        self.assertEqual(len(entry_tags), 7)
        self.assertTrue(all('href="#workflow-catalogue"' in tag
                            for tag in entry_tags))
        self.assertTrue(all('aria-controls="workflow-groups"' in tag
                            for tag in entry_tags))
        self.assertIn('data-show-all-workflows', SECTION)
        self.assertNotIn('class="workflow-proof"', SECTION)
        self.assertRegex(
            compact, r"\.workflow-controls \{[^}]*display: none")
        self.assertRegex(
            compact, r"\.js \.workflow-controls \{[^}]*display: block")
        self.assertRegex(
            compact, r"\.workflow-results-toolbar \{[^}]*display: none")
        self.assertRegex(
            compact, r"\.js \.workflow-results-toolbar \{[^}]*display: flex")

    def test_readability_contract_is_single_column_and_larger(self):
        compact = re.sub(r"\s+", " ", HTML)
        self.assertRegex(
            compact, r"\.workflow-catalogue \{[^}]*max-width: 60rem")
        self.assertRegex(
            compact, r"\.workflow-groups \{[^}]*grid-template-columns: 1fr")
        self.assertRegex(
            compact, r"\.workflow-item p \{[^}]*font-size: 0\.875rem")
        self.assertRegex(
            compact, r"\.workflow-entry \{[^}]*flex: 1 1 16rem")
        self.assertRegex(
            compact, r"\.workflow-entry strong \{[^}]*font-size: 1rem")
        self.assertRegex(
            compact, r"\.workflow-entry span \{[^}]*font-size: 0\.8125rem")
        self.assertRegex(
            compact,
            r"\.workflow-group-title strong \{[^}]*font-size: 1rem",
        )
        self.assertRegex(
            compact,
            r"\.workflow-group-title small \{[^}]*font-size: 0\.8125rem",
        )
        self.assertRegex(
            compact, r"\.workflow-group-meta \{[^}]*font-size: 0\.75rem")
        self.assertRegex(
            compact, r"\.workflow-item \{[^}]*grid-template-columns: 13rem")
        self.assertRegex(
            compact,
            r"\.workflow-command-line code \{[^}]*font-size: 0\.8125rem",
        )
        self.assertRegex(
            compact,
            r"@media \(max-width: 980px\).*?\.workflow-entry "
            r"\{ flex-basis: calc\(50% - 0\.375rem\)",
        )
        self.assertRegex(
            compact,
            r"@media \(max-width: 760px\).*?\.workflow-entry "
            r"\{ flex-basis: 100%",
        )
        self.assertRegex(
            compact,
            r"@media \(max-width: 760px\).*?\.workflow-item "
            r"\{ grid-template-columns: 1fr",
        )
        self.assertIn("#c3cfcc", HTML)
        self.assertIn(".workflow-search input:focus-visible", HTML)
        self.assertIn("@media (prefers-reduced-motion: reduce)", HTML)

    def test_all_fragment_and_aria_references_resolve_to_unique_ids(self):
        parser = DocumentContractParser()
        parser.feed(HTML)
        duplicates = sorted(
            identifier for identifier, count in Counter(parser.ids).items()
            if count > 1
        )
        self.assertEqual(duplicates, [])
        missing = sorted(set(parser.references) - set(parser.ids))
        self.assertEqual(missing, [])

    def test_controllers_execute_the_approved_interactions(self):
        if shutil.which("node") is None:
            self.skipTest("node required for docs/index.html behavior tests")
        behavior_test = REPO_ROOT / "tests" / "docs_workflows.behavior.test.js"
        result = subprocess.run(
            ["node", "--test", str(behavior_test)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            result.stdout + result.stderr,
        )

    def test_demo_previews_are_available_without_javascript(self):
        compact = re.sub(r"\s+", " ", HTML)
        panel_tags = re.findall(
            r'<div class="demo-panel[^"]*"[^>]*data-panel="[^"]+"[^>]*>',
            HTML,
        )
        self.assertEqual(len(panel_tags), 3)
        self.assertTrue(all(" hidden" not in tag for tag in panel_tags))
        self.assertEqual(sum("is-active" in tag for tag in panel_tags), 1)
        self.assertEqual(sum('tabindex="-1"' in tag for tag in panel_tags), 3)
        self.assertRegex(compact, r"\.demo-tabs \{[^}]*display: none")
        self.assertRegex(compact, r"\.js \.demo-tabs \{[^}]*display: flex")
        self.assertRegex(compact, r"\.js \.demo-panel \{[^}]*display: none")
        self.assertRegex(
            compact,
            r"\.js \.demo-panel\.is-active \{[^}]*display: block",
        )


if __name__ == "__main__":
    unittest.main()
