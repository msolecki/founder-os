"""Contract tests for the dependency-free workflow catalogue landing section."""
import re
import shutil
import struct
import subprocess
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
HTML = (REPO_ROOT / "docs" / "index.html").read_text(encoding="utf-8")
BEHAVIOR_TEST = (
    REPO_ROOT / "tests" / "docs_workflows.behavior.test.js"
).read_text(encoding="utf-8")
CONTROLLER_SOURCES = ("workflow-library.js", "demo-tabs.js")
GETTING_STARTED = (REPO_ROOT / "docs" / "getting-started.md").read_text(
    encoding="utf-8"
)
TROUBLESHOOTING = (REPO_ROOT / "docs" / "troubleshooting.md").read_text(
    encoding="utf-8"
)
ARCHITECTURE = (REPO_ROOT / "docs" / "architecture.md").read_text(
    encoding="utf-8"
)
COMMANDS = (REPO_ROOT / "docs" / "commands.md").read_text(encoding="utf-8")
ROOT_README = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
PLUGIN_README = (REPO_ROOT / "founder-os" / "README.md").read_text(
    encoding="utf-8"
)
EXAMPLE_DAILY = (
    REPO_ROOT / "examples" / "studio-north" / "reviews" / "daily"
    / "2026-07-20.md"
)
EXAMPLE_QUEUE = REPO_ROOT / "examples" / "studio-north" / "queue.md"
EXAMPLE_GOALS = REPO_ROOT / "examples" / "studio-north" / "goals.md"
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

PRODUCT_HUNT_DIR = REPO_ROOT / "docs" / "product-hunt"
PRODUCT_HUNT_TEXT_FILES = (
    "README.md",
    "listing.md",
    "maker-comment.md",
    "demo-script.md",
    "activation-study.md",
)
PRODUCT_HUNT_IMAGES = {
    "thumbnail-240.png": (240, 240),
    "gallery-01-outcome.png": (1270, 760),
    "gallery-02-onboarding.png": (1270, 760),
    "gallery-03-trust.png": (1270, 760),
    "gallery-04-operating-loop.png": (1270, 760),
}


def markdown_section(document, heading):
    marker = f"## {heading}\n"
    start = document.index(marker) + len(marker)
    end = document.find("\n## ", start)
    return document[start:end if end >= 0 else None].strip()


def png_dimensions(path):
    data = path.read_bytes()[:24]
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise AssertionError(f"{path} is not a PNG with an IHDR header")
    return struct.unpack(">II", data[16:24])


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


class ActivationCopyContractTest(unittest.TestCase):
    HERO = HTML[HTML.index('<section class="hero"'):HTML.index(
        "</section>", HTML.index('<section class="hero"')
    )]

    def test_hero_leads_with_approved_outcome_and_trust_copy(self):
        compact = re.sub(r"\s+", " ", self.HERO)
        self.assertIn("<h1>Know what matters today.</h1>", compact)
        self.assertIn(
            "Founder OS turns your goals, cash, pipeline and commitments into "
            "one daily decision — stored locally and traceable to its source.",
            compact,
        )
        self.assertIn(">Install Founder OS <", compact)
        self.assertIn(">See the first brief</a>", compact)
        self.assertIn(
            "Local Markdown · No automatic sending · Explicit ownership · "
            "No hidden actions",
            compact,
        )
        self.assertNotIn("13-agent executive team", compact)

    def test_real_brief_and_empty_folder_flow_precede_org_explanation(self):
        source_brief = (
            "https://github.com/msolecki/founder-os/blob/main/examples/"
            "studio-north/reviews/daily/2026-07-20.md"
        )
        team_position = HTML.index('<section class="section team" id="team">')
        self.assertIn(source_brief, HTML)
        self.assertLess(HTML.index(source_brief), team_position)
        self.assertLess(HTML.index('<section class="section how"'), team_position)

    def test_onboarding_claims_one_resumable_path_to_persisted_activation(self):
        compact = re.sub(r"\s+", " ", GETTING_STARTED)
        self.assertIn("one continuous, resumable flow", compact)
        self.assertIn("reviews/daily/YYYY-MM-DD.md", GETTING_STARTED)
        self.assertIn("ten minutes", compact)
        self.assertIn("fifteen minutes", compact)
        for document in (HTML, GETTING_STARTED, ROOT_README, PLUGIN_README):
            with self.subTest(document=document[:24]):
                lowered = document.lower()
                self.assertNotIn("20 minutes", lowered)
                self.assertNotIn("twenty minutes", lowered)
        self.assertNotIn("hand each answer", COMMANDS.lower())

    def test_activation_requires_a_valid_brief_not_an_existing_file(self):
        activation_documents = {
            "landing": HTML,
            "getting started": GETTING_STARTED,
            "troubleshooting": TROUBLESHOOTING,
            "architecture": ARCHITECTURE,
            "root readme": ROOT_README,
            "plugin readme": PLUGIN_README,
        }
        for name, document in activation_documents.items():
            with self.subTest(document=name):
                compact = re.sub(r"\s+", " ", document.lower())
                self.assertIn("reviews/daily/yyyy-mm-dd.md", compact)
                self.assertIn("all four required headings", compact)
                self.assertIn("non-empty", compact)
                self.assertIn("the one thing", compact)
                self.assertIn("the trade", compact)

    def test_linked_example_is_local_and_traces_commitment_to_bet(self):
        sources = {
            EXAMPLE_DAILY: ("q-0720a", "B1"),
            EXAMPLE_QUEUE: ("q-0720a", "B1"),
            EXAMPLE_GOALS: ("B1",),
        }
        for path, markers in sources.items():
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                self.assertTrue(path.is_file())
                source = path.read_text(encoding="utf-8")
                for marker in markers:
                    self.assertIn(marker, source)

    def test_first_five_actions_match_activation_receipt(self):
        start = GETTING_STARTED.index("## Your first five actions")
        first_five = GETTING_STARTED[start:GETTING_STARTED.index("\n## ", start + 4)]
        for marker in (
            "/daily-brief",
            "inbox.md",
            "/pipeline-review",
            "/weekly-review",
            "Chief of Staff",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, first_five)

    def test_update_repair_and_uninstall_are_explicit(self):
        for marker in (
            "/plugin marketplace update founder-os",
            "/plugin update founder-os@founder-os",
            "/reload-plugins",
            "/founder-os-doctor",
            "/plugin uninstall founder-os@founder-os",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, GETTING_STARTED)
        self.assertIn("## Activation and install recovery", TROUBLESHOOTING)

    def test_data_handling_is_local_state_not_offline_claim(self):
        for document in (
            HTML,
            GETTING_STARTED,
            ARCHITECTURE,
            ROOT_README,
            PLUGIN_README,
        ):
            with self.subTest(document=document[:24]):
                lowered = re.sub(r"\s+", " ", document.lower())
                self.assertIn("workspace files stay on your machine", lowered)
                self.assertIn("data-handling terms", lowered)
                self.assertIn("prompts", lowered)
                self.assertIn("context", lowered)
                for prohibited in (
                    "works offline",
                    "never leaves your computer",
                    "no data leaves",
                    "zero data transmission",
                    "nothing leaves your machine",
                ):
                    self.assertNotIn(prohibited, lowered)

    def test_architecture_explains_activation_before_the_org(self):
        activation = ARCHITECTURE.index("## Activation path")
        agents = ARCHITECTURE.index("## The three moving parts")
        self.assertLess(activation, agents)
        self.assertIn("reviews/daily/YYYY-MM-DD.md", ARCHITECTURE)
        self.assertIn("Activation complete", ARCHITECTURE)

    def test_command_reference_describes_init_and_first_actions_truthfully(self):
        self.assertIn("## Start here: the first five actions", COMMANDS)
        init_row = next(
            line for line in COMMANDS.splitlines()
            if line.startswith("| `/founder-os-init`")
        )
        self.assertIn("first daily brief", init_row)
        self.assertIn("resum", init_row)

    def test_readmes_put_daily_outcome_before_agent_counts(self):
        for document in (ROOT_README, PLUGIN_README):
            with self.subTest(document=document[:24]):
                outcome = document.index("Know what matters today")
                agent_markers = [
                    position for marker in ("13 agents", "thirteen agents")
                    if (position := document.lower().find(marker)) >= 0
                ]
                self.assertTrue(agent_markers)
                agents = min(agent_markers)
                self.assertLess(outcome, agents)


class ProductHuntLaunchKitContractTest(unittest.TestCase):
    def read_required(self, filename):
        path = PRODUCT_HUNT_DIR / filename
        self.assertTrue(path.is_file(), f"missing {path.relative_to(REPO_ROOT)}")
        if not path.is_file():
            return ""
        return path.read_text(encoding="utf-8")

    def test_required_copy_and_image_files_exist_at_exact_dimensions(self):
        for filename in PRODUCT_HUNT_TEXT_FILES:
            with self.subTest(filename=filename):
                self.assertTrue((PRODUCT_HUNT_DIR / filename).is_file())
        for filename, expected in PRODUCT_HUNT_IMAGES.items():
            with self.subTest(filename=filename):
                path = PRODUCT_HUNT_DIR / filename
                self.assertTrue(path.is_file())
                if path.is_file():
                    self.assertEqual(png_dimensions(path), expected)

    def test_listing_uses_approved_identity_and_conservative_limits(self):
        listing = self.read_required("listing.md")
        if not listing:
            return
        name = markdown_section(listing, "Name")
        tagline = markdown_section(listing, "Tagline")
        description = markdown_section(listing, "Description")
        topics = [
            line for line in markdown_section(listing, "Topics").splitlines()
            if line.startswith("- ")
        ]
        self.assertEqual(name, "Founder OS")
        self.assertEqual(
            tagline, "Know what matters today — before opening your inbox"
        )
        self.assertLessEqual(len(tagline), 60)
        self.assertLessEqual(len(description), 260)
        self.assertGreaterEqual(len(topics), 1)
        self.assertLessEqual(len(topics), 3)

    def test_readme_inventory_pins_sources_dimensions_and_alt_text(self):
        readme = self.read_required("README.md")
        if not readme:
            return
        rows = re.findall(
            r"\| `([^`]+\.png)` \| (\d+)×(\d+) \| "
            r"\[`([^`]+\.svg)`\]\(([^)]+)\) \| Alt text: ([^|]+) \|",
            readme,
        )
        self.assertEqual(len(rows), len(PRODUCT_HUNT_IMAGES))
        inventory = {row[0]: row[1:] for row in rows}
        self.assertEqual(set(inventory), set(PRODUCT_HUNT_IMAGES))
        alt_texts = []
        for filename, (width, height) in PRODUCT_HUNT_IMAGES.items():
            with self.subTest(filename=filename):
                row_width, row_height, source_label, source_href, alt = (
                    inventory[filename]
                )
                expected_source = (
                    f"sources/{filename.removesuffix('.png')}.svg"
                )
                self.assertEqual((int(row_width), int(row_height)), (width, height))
                self.assertEqual(source_label, expected_source)
                self.assertEqual(source_href, expected_source)
                self.assertTrue((PRODUCT_HUNT_DIR / source_href).is_file())
                self.assertTrue(alt.strip())
                alt_texts.append(alt.strip())
        self.assertEqual(len(set(alt_texts)), len(PRODUCT_HUNT_IMAGES))
        for href in re.findall(r"\[[^]]+\]\(([^)]+)\)", readme):
            with self.subTest(href=href):
                if not href.startswith(("https://", "http://", "#")):
                    self.assertTrue((PRODUCT_HUNT_DIR / href).is_file())
        self.assertIn("Submission checklist", readme)

    def test_listing_uses_a_direct_primary_url(self):
        listing = self.read_required("listing.md")
        if not listing:
            return
        primary_url = markdown_section(listing, "Primary URL")
        self.assertEqual(primary_url, "https://msolecki.github.io/founder-os/")
        parsed = urlparse(primary_url)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "msolecki.github.io")
        self.assertEqual(parsed.path, "/founder-os/")
        self.assertFalse(parsed.query)
        self.assertFalse(parsed.fragment)

    def test_maker_comment_requests_feedback_without_vote_manipulation(self):
        comment = self.read_required("maker-comment.md")
        if not comment:
            return
        compact = re.sub(r"\s+", " ", comment.lower())
        for marker in (
            "company of one",
            "local markdown",
            "never sends",
            "who it is for",
            "where it breaks",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, compact)
        for prohibited in ("upvote", "vote for", "support us", "hunter"):
            with self.subTest(prohibited=prohibited):
                self.assertNotIn(prohibited, compact)

    def test_demo_script_covers_real_uncut_activation_in_45_to_60_seconds(self):
        script = self.read_required("demo-script.md")
        if not script:
            return
        spoken = markdown_section(script, "Spoken script")
        word_count = len(re.findall(r"\b[\w’'-]+\b", spoken))
        self.assertGreaterEqual(word_count, 105)
        self.assertLessEqual(word_count, 150)
        for marker in (
            "/plugin marketplace add msolecki/founder-os",
            "/plugin install founder-os@founder-os",
            "/founder-os-init",
            "Business",
            "Customer",
            "Quarter",
            "Money",
            "reviews/daily/YYYY-MM-DD.md",
            "no hidden cuts",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, script)

    def test_activation_study_records_only_consented_operational_fields(self):
        study = self.read_required("activation-study.md")
        if not study:
            return
        normalized = " ".join(study.split())
        for marker in (
            "Consented participant ID",
            "First brief persisted",
            "Elapsed minutes",
            "First confusion",
            "Outcome useful",
            "Seven-day return",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, normalized)
        compact = study.lower()
        self.assertIn("do not paste workspace contents", compact)
        self.assertIn("voluntary", compact)
        self.assertNotIn("synthetic copy rehearsal", compact)

    def test_activation_study_pins_resume_integrity_and_separate_codex_gate(self):
        study = self.read_required("activation-study.md")
        if not study:
            return
        normalized = " ".join(study.split())
        for marker in (
            "Assigned interruption boundary",
            "Resume preserved protected sections",
            "Integrity incident",
            "after Business checkpoint, before Customer",
            "after offer checkpoint, before Quarter",
            "after ready-bet checkpoint, before Money",
            "after activation close, before runway",
            "after runway checkpoint, before first brief",
            "Separate Codex clean-install check",
            "Codex status",
            "beta/manual",
            "Do not count the Codex result toward the five-person Claude Code gate",
            "0 overwrites, ownership breaches, or false completions",
            "Protected populated sections",
            "Expected post-resume write",
            "Do not hash the whole file",
            "existing `## Close — YYYY-MM` block",
            "append `## Runway — as of YYYY-MM-DD` to the same `metrics.md`",
            "Stop the activation timer",
            "Do not include the seven-day wait",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, normalized)

    def test_every_png_has_a_reviewable_svg_source(self):
        for filename, expected in PRODUCT_HUNT_IMAGES.items():
            with self.subTest(filename=filename):
                source = PRODUCT_HUNT_DIR / "sources" / (
                    filename.removesuffix(".png") + ".svg"
                )
                self.assertTrue(source.is_file())
                if source.is_file():
                    svg = source.read_text(encoding="utf-8")
                    self.assertIn(
                        f'viewBox="0 0 {expected[0]} {expected[1]}"', svg
                    )
                    self.assertIn("<title", svg)
                    self.assertIn("<desc", svg)

    def test_operating_loop_starts_with_the_brief_and_feeds_inbox_forward(self):
        source = (
            PRODUCT_HUNT_DIR / "sources" / "gallery-04-operating-loop.svg"
        ).read_text(encoding="utf-8")
        self.assertLess(
            source.index(">daily brief</text>"),
            source.index(">inbox.md</text>"),
        )
        self.assertIn("feeds the next brief", source.lower())


if __name__ == "__main__":
    unittest.main()
