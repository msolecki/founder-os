"""Contract tests for the dependency-free workflow catalogue landing section."""
import json
import re
import shutil
import subprocess
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
HTML = (REPO_ROOT / "docs" / "index.html").read_text(encoding="utf-8")
MARKETPLACE = json.loads(
    (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(
        encoding="utf-8"
    )
)
RELEASE_VERSION = MARKETPLACE["plugins"][0]["version"]
AGENT_COUNT = len(list((REPO_ROOT / "founder-os" / "agents").glob("*.md")))
CLAUDE_INSTALL = (
    "/plugin marketplace add msolecki/founder-os",
    "/plugin install founder-os@founder-os",
)
CODEX_INSTALL = (
    "codex plugin marketplace add msolecki/founder-os",
    "codex plugin add founder-os@founder-os",
)
CLAUDE_WORKFLOWS = (
    "/founder-os:founder-os-init",
    "/founder-os:setup-cadences",
)
CODEX_WORKFLOWS = (
    "$founder-os:founder-os-init",
    "$founder-os:setup-cadences",
)
BEHAVIOR_TEST = (
    REPO_ROOT / "tests" / "docs_workflows.behavior.test.js"
).read_text(encoding="utf-8")
CONTROLLER_SOURCES = (
    "workflow-library.js", "demo-tabs.js", "workspace-demo.js",
)
SKILL_COUNT = len(list((REPO_ROOT / "founder-os" / "skills").glob("*/SKILL.md")))
CADENCE_SOURCE = (
    REPO_ROOT / "founder-os" / "skills" / "setup-cadences" / "SKILL.md"
).read_text(encoding="utf-8")
CADENCE_COUNT = len(re.findall(
    r"^\|\s*`/[a-z0-9-]+`\s*\|[^|]*\|\s*`[^`]+`\s*\|\s*$",
    CADENCE_SOURCE,
    re.MULTILINE,
))
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
    "plan": (11, "Set direction"),
    "sell": (4, "Move a deal"),
    "deliver": (4, "Deliver well"),
    "money": (6, "Know the numbers"),
    "focus": (12, "Protect focus"),
    "grow": (8, "Grow deliberately"),
    "run": (11, "Run operations"),
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
    def test_one_page_publishes_the_current_dual_host_contract(self):
        nav = HTML[HTML.index('<div class="nav-links"'):HTML.index("</nav>")]
        self.assertIn('<a href="#trust">Trust</a>', nav)
        self.assertIn('<a href="trust.html">Read the full Trust Center', HTML)
        self.assertIn(f"Founder OS {RELEASE_VERSION}", HTML)
        self.assertIn(f"{SKILL_COUNT} workflows", HTML)
        self.assertIn(f"{AGENT_COUNT} roles", HTML)
        install_sections = {
            "Claude Code": (
                '<section class="install-box" '
                'aria-labelledby="install-claude-title">',
                CLAUDE_INSTALL + CLAUDE_WORKFLOWS,
            ),
            "Codex": (
                '<section class="install-box" '
                'aria-labelledby="install-codex-title">',
                CODEX_INSTALL + CODEX_WORKFLOWS,
            ),
        }
        for host, (marker, expected_commands) in install_sections.items():
            start = HTML.index(marker)
            panel = HTML[start:HTML.index("</section>", start)]
            commands = re.findall(
                r'<li class="install-row"><code>([^<]+)</code>', panel
            )
            with self.subTest(host=host):
                self.assertEqual(commands, list(expected_commands))
        self.assertIn("Python 3.9+", HTML)
        self.assertIn("local state gateway and host hooks", HTML)
        self.assertIn(
            "PyYAML is needed only for development, tests, and package validation",
            HTML,
        )
        for stale in (
            "all 50 commands",
            "you use Claude Code and want",
            "existing Claude Code plan",
            "PyYAML recommended",
            "PyYAML is needed only for development and package validation",
            "Python runs the ownership hook",
        ):
            with self.subTest(stale=stale):
                self.assertNotIn(stale, HTML)
        self.assertEqual(
            {path.name for path in (REPO_ROOT / "docs").glob("*.html")},
            {"index.html", "trust.html"},
        )

    def test_static_trust_center_matches_the_canonical_claims(self):
        trust_path = REPO_ROOT / "docs" / "trust.html"
        self.assertTrue(trust_path.is_file())
        trust_html = trust_path.read_text(encoding="utf-8")
        trust_md = (REPO_ROOT / "docs" / "trust.md").read_text(
            encoding="utf-8"
        )
        claims = (
            "one product",
            "local state gateway",
            "no cloud service",
            "telemetry",
            "one owner",
            "never sends",
            "never pays",
            "model host",
            "cached installed copies",
            "not a security sandbox",
        )
        for claim in claims:
            with self.subTest(claim=claim):
                self.assertRegex(trust_md, rf"(?i){re.escape(claim)}")
                self.assertRegex(trust_html, rf"(?i){re.escape(claim)}")

        for marker in (
            'class="skip-link" href="#main"',
            '<main id="main">',
            'aria-label="Trust Center sections"',
            '<meta name="viewport"',
            'http-equiv="Content-Security-Policy"',
            'name="referrer"',
        ):
            self.assertIn(marker, trust_html)
        self.assertNotIn("<script", trust_html)
        self.assertIn('href="index.html"', trust_html)
        self.assertIn('href="trust.html"', HTML)

    def test_launch_page_declares_favicon_and_apple_touch_icon(self):
        self.assertIn('rel="icon" type="image/svg+xml"', HTML)
        self.assertIn('rel="apple-touch-icon"', HTML)

    def test_trust_center_and_host_parity_are_public(self):
        trust = (REPO_ROOT / "docs" / "trust.md").read_text(encoding="utf-8")
        for token in (
            "local Markdown", "Prompts,", "review and trust",
            "fail open", "not a security sandbox", "cached installed copies",
            "does not delete", "same `skills",
        ):
            self.assertRegex(trust, rf"(?i){re.escape(token)}")
        self.assertIn("trust.html", HTML)

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

    def test_category_counts_still_partition_every_workflow(self):
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
        self.assertEqual(sum(counts.values()), SKILL_COUNT)

    def test_complete_catalogue_and_cadence_contract_survives(self):
        commands = re.findall(
            r'<article class="workflow-item".*?<code>(/[^<]+)</code>',
            SECTION, re.S)
        self.assertEqual(len(commands), SKILL_COUNT)
        self.assertEqual(len(set(commands)), SKILL_COUNT)
        self.assertEqual(SECTION.count('class="workflow-badge"'), CADENCE_COUNT)

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
            compact, r"\.workflow-catalogue \{[^}]*max-width: none")
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

    def test_disclosure_badge_never_lands_on_summary_content(self):
        """The shared summary::after badge is absolutely positioned at the
        right edge, so every summary that overrides the base padding must
        reserve room for it, and no summary may inherit an open-state badge
        from an ancestor <details>."""
        compact = re.sub(r"\s+", " ", HTML)

        # The badge is absolute at right: 0.25rem with a 1.9rem box, so any
        # summary needs at least ~2.15rem of right padding to stay clear.
        self.assertRegex(
            compact, r"summary \{[^}]*padding: 1\.5rem 3rem 1\.5rem 0")
        self.assertRegex(
            compact, r"\.reference-summary \{[^}]*padding: 1rem 3rem 1rem 0")
        self.assertRegex(
            compact,
            r"\.workflow-catalogue > summary \{"
            r"[^}]*padding: 0\.9rem 3\.4rem 0\.9rem 1\.1rem",
        )

        # Group rows carry their own .workflow-group-meta indicator, so the
        # shared badge is suppressed there rather than padded around.
        self.assertRegex(
            compact, r"\.workflow-group summary::after \{[^}]*content: none")

        # A descendant selector here would paint every nested summary as open
        # whenever any ancestor <details> is open.
        self.assertIn("details[open] > summary::after", HTML)
        self.assertNotRegex(HTML, r"details\[open\] summary::after")

        # The catalogue label must stay one flex item; splitting it across
        # text nodes lets space-between tear the phrase apart.
        self.assertIn(
            '<summary class="workflow-catalogue-summary">'
            f"<span>Browse all <strong>{SKILL_COUNT}</strong> workflows</span>"
            "</summary>",
            HTML,
        )

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

    def test_primary_path_follows_the_decision_first_information_architecture(self):
        positions = [
            HTML.index(marker)
            for marker in (
                '<section class="hero" id="top">',
                'id="decision-loop"',
                'id="situations"',
                'id="sample-workspace"',
                'id="first-run"',
                'id="rhythm"',
                'id="trust"',
                'id="fit-summary"',
                'id="requirements-summary"',
                'id="install"',
                'id="workflows"',
                'id="team"',
                'id="multi-business"',
            )
        ]
        self.assertEqual(positions, sorted(positions))

        nav = HTML[HTML.index('<div class="nav-links"'):HTML.index("</nav>")]
        self.assertEqual(
            re.findall(r'href="(#[^"]+)"', nav),
            [
                "#decision-loop",
                "#sample-workspace",
                "#first-run",
                "#trust",
                "#install",
            ],
        )
        self.assertNotIn("Multi-business", nav)
        self.assertNotRegex(nav, rf"\b{SKILL_COUNT} workflows\b")

    def test_secondary_role_and_multi_business_reference_is_expandable(self):
        team_start = HTML.index('<section class="section team" id="team">')
        multi_start = HTML.index(
            '<section class="section multi-business" id="multi-business">'
        )
        memory_start = HTML.index(
            '<section class="section ownership" id="memory">'
        )

        for section in (
            HTML[team_start:multi_start],
            HTML[multi_start:memory_start],
        ):
            with self.subTest(section=section[:80]):
                self.assertIn(
                    '<details class="reference-panel" open>', section)
                self.assertIn('<summary class="reference-summary">', section)

    def test_hero_names_the_user_problem_result_time_and_decision_first_cta(self):
        compact = re.sub(r"\s+", " ", self.HERO)
        for marker in (
            "solo service founders",
            "Claude Code or Codex",
            "decisions disappear into chats and disconnected notes",
            "source-linked decision",
            "local",
            "less than fifteen minutes",
            "Local Markdown · No automatic sending · Explicit ownership · "
            "No hidden actions",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, compact)
        decision_cta = compact.index(">See one decision move through the system")
        install_cta = compact.index(">Install Founder OS")
        self.assertLess(decision_cta, install_cta)

    def test_canonical_decision_loop_and_five_situations_are_complete(self):
        decision_start = HTML.index('id="decision-loop"')
        decision_loop = HTML[decision_start:HTML.index("</section>", decision_start)]
        scenario = (
            "I need to finish the Acme proposal, follow up with Northwind, and "
            "redesign the website. What actually matters today?"
        )
        for marker in (
            scenario,
            "goals.md",
            "queue.md",
            "week.md",
            "pipeline.md",
            "Chief of Staff",
            "/daily-brief",
            "q-0720a",
            "B1",
            "website redesign",
            "Northwind",
            "reviews/daily/",
            "Friday",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, decision_loop)

        situations_start = HTML.index('id="situations"')
        situations = HTML[
            situations_start:HTML.index("</section>", situations_start)
        ]
        cards = re.findall(
            r'<a class="situation-entry"[^>]*data-workflow-query="([^"]+)"'
            r'[^>]*>(.*?)</a>',
            situations,
            re.S,
        )
        self.assertEqual(len(cards), 5)
        expected = {
            "/daily-brief": (
                "I do not know what matters today",
                "Chief of Staff",
                "reviews/daily/",
                "queue.md",
            ),
            "/capacity-check": (
                "I do not know whether I can take a new client",
                "Delivery Lead",
                "clients/_capacity.md",
            ),
            "/pipeline-review": (
                "A deal has stopped moving",
                "Pipeline Coach",
                "pipeline.md",
            ),
            "/scope-guard": (
                "A client request may be outside scope",
                "Delivery Lead",
                "clients/",
            ),
            "/profitability-analysis": (
                "I do not know which work makes money",
                "CFO",
                "metrics.md",
            ),
        }
        self.assertEqual({query for query, _ in cards}, set(expected))
        for query, body in cards:
            compact = re.sub(r"\s+", " ", body)
            for marker in expected[query] + (query,):
                with self.subTest(query=query, marker=marker):
                    self.assertIn(marker, compact)

        self.assertLess(situations_start, HTML.index('id="sample-workspace"'))
        sample = HTML[
            HTML.index('id="sample-workspace"'):HTML.index(
                '<section class="section how"',
            )
        ]
        self.assertRegex(sample, r"(?i)proof of (?:that|the) decision loop")

    def test_hero_leads_with_approved_outcome_and_trust_copy(self):
        compact = re.sub(r"\s+", " ", self.HERO)
        self.assertIn("<h1>Know what matters today.</h1>", compact)
        self.assertIn(
            "Founder OS turns current business state into one source-linked "
            "decision, saves it to local Markdown",
            compact,
        )
        self.assertIn(">Install Founder OS</a>", compact)
        self.assertIn(">See one decision move through the system", compact)
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

    def test_entry_docs_explain_activation_intent_receipt_and_consentful_return(self):
        for document in (GETTING_STARTED, ROOT_README, PLUGIN_README):
            compact = re.sub(r"\s+", " ", document)
            with self.subTest(document=document[:24]):
                for marker in (
                    "What made you install Founder OS today?",
                    "You came with:",
                    "Your first decision:",
                    "Based on:",
                    "Saved to:",
                    "Founder OS will remember:",
                    "Recommended next move:",
                    "/situation-review",
                    "Continue",
                    "Stop",
                ):
                    self.assertIn(marker, compact)
                self.assertRegex(
                    compact,
                    r"(?i)specialist workflow.*only after.*Continue",
                )

    def test_operator_docs_publish_receipts_freshness_and_error_recovery(self):
        receipt_labels = (
            "Decision:",
            "Evidence:",
            "Changed:",
            "Gaps:",
            "Returns:",
            "Your move:",
        )
        for document in (
            GETTING_STARTED,
            ROOT_README,
            PLUGIN_README,
            ARCHITECTURE,
        ):
            compact = re.sub(r"\s+", " ", document)
            with self.subTest(document=document[:24]):
                for marker in receipt_labels:
                    self.assertIn(marker, compact)
                self.assertRegex(compact, r"(?i)read-only.*Changed:.*none")
                self.assertRegex(
                    compact, r"(?i)current.*stale.*unknown|unknown.*stale.*current"
                )
                self.assertIn("source date", compact.lower())

        for document in (ARCHITECTURE, TROUBLESHOOTING):
            with self.subTest(error_document=document[:24]):
                for code in (
                    "WORKSPACE_UNRESOLVED",
                    "ROLE_SESSION_INVALID",
                    "PATH_OUTSIDE_WORKSPACE",
                    "ROLE_NOT_OWNER",
                    "INVALID_DOCUMENT_STRUCTURE",
                    "STALE_WRITE",
                    "STATE_IO_ERROR",
                ):
                    self.assertIn(code, document)
                compact = re.sub(r"\s+", " ", document)
                self.assertRegex(
                    compact,
                    r"(?i)write occurred.*original file.*canonical owner.*"
                    r"system will do next.*founder must act",
                )

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
            "/capture",
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

    def test_entry_documents_share_the_primary_user_promise_and_front_door(self):
        documents = {
            "root readme": ROOT_README,
            "plugin readme": PLUGIN_README,
            "getting started": GETTING_STARTED,
        }
        for name, document in documents.items():
            compact = re.sub(r"\s+", " ", document)
            with self.subTest(document=name):
                for marker in (
                    "solo service founder",
                    "Claude Code or Codex",
                    "source-linked decision",
                    "local Markdown",
                    "fifteen minutes",
                    "/situation-review",
                    "I do not know what matters today",
                    "never sends",
                ):
                    self.assertRegex(compact, rf"(?i){re.escape(marker)}")


def _flowed(text):
    """Text with every run of whitespace collapsed to one space.

    Every assertion below is about wording, not line wrapping. Matching the
    raw bytes would pin the hard wrap too, so a reflow that changes no words
    would fail and — worse — a phrase that happens to straddle a line break
    would read as absent. Both were live: `docs/concepts.md` and
    `founder-os/agents/cfo.md` carry "no subscription cancelled" across a
    newline.
    """
    return " ".join(text.split())


class CanonicalGuidanceContractTest(unittest.TestCase):
    """The always-loaded CLAUDE.md must agree with the map it defers to."""

    # A term in the file map: a lowercase word that may carry digits or
    # hyphens, so the first workspace file named like `client-health.md` does
    # not break a test that is correct on both sides.
    TERM = r"[a-z][a-z0-9-]*"
    CANONICAL = (REPO_ROOT / "founder-os" / "CLAUDE.md").read_text(
        encoding="utf-8"
    )
    OWNERSHIP = (
        REPO_ROOT / "founder-os" / "references" / "ownership.yaml"
    ).read_text(encoding="utf-8")
    WORKSPACE_STATE = (REPO_ROOT / "docs" / "workspace-state.md").read_text(
        encoding="utf-8"
    )
    # Every file that recites rule 0's enumeration must recite all of it. The
    # 2026-07-30 fix listed the three it knew about and a fourth
    # (`docs/concepts.md`) kept the short version, so the list is discovered
    # rather than maintained — but it may never silently discover nothing.
    RULE_ZERO_MARKER = "no signature"
    RULE_ZERO_REQUIRED = {
        "founder-os/CLAUDE.md",
        "founder-os/references/house-rules.md",
        "docs/house-rules.md",
        "docs/concepts.md",
    }

    def _workspace_files(self):
        return set(yaml.safe_load(self.OWNERSHIP)["workspace_files"])

    def test_claude_md_file_map_matches_ownership_workspace_files(self):
        # CLAUDE.md carries the file map as one prose sentence ("one owner per
        # file: inbox, charter, …"). Expand it and require set equality with
        # `workspace_files:` — the 2026-07-30 audit found `evaluations/`
        # shipped in the map but missing from the sentence (RULE-001).
        match = re.search(
            r"one owner per file:\s*(.*?)\.\s", _flowed(self.CANONICAL)
        )
        self.assertIsNotNone(
            match, "CLAUDE.md no longer carries the file-map sentence"
        )
        expanded = []
        for term in re.findall(
            r"{t}/\{{[a-z0-9,-]+\}}/|{t}/|{t}".format(t=self.TERM),
            match.group(1),
        ):
            brace = re.fullmatch(
                r"({t})/\{{([a-z0-9,-]+)\}}/".format(t=self.TERM), term
            )
            if brace:
                expanded.extend(
                    "%s/%s/" % (brace.group(1), leaf)
                    for leaf in brace.group(2).split(",")
                )
            elif term.endswith("/"):
                expanded.append(term)
            else:
                expanded.append(term + ".md")
        self.assertEqual(sorted(set(expanded)), sorted(self._workspace_files()))

    def test_public_state_page_lists_every_owned_workspace_file(self):
        # docs/workspace-state.md calls itself "the full map of that state".
        # It is the reader-facing twin of `workspace_files:` and drifted the
        # same way CLAUDE.md did: `evaluations/` shipped owned but unlisted.
        listed = {
            row[0]
            for row in re.findall(
                r"^\|\s*`([^`]+)`\s*\|\s*([a-z-]+)\s*\|",
                self.WORKSPACE_STATE,
                re.M,
            )
        }
        self.assertEqual(sorted(listed), sorted(self._workspace_files()))

    def test_rule_zero_enumerations_agree_everywhere(self):
        # The CLAUDE.md summary may not be stricter than the full text it
        # defers to, and no public mirror may lag either (RULE-002).
        tracked = subprocess.run(
            ["git", "ls-files", "--", "*.md"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
        reciting = {
            name
            for name in tracked
            if self.RULE_ZERO_MARKER
            in _flowed((REPO_ROOT / name).read_text(encoding="utf-8"))
        }
        self.assertTrue(
            self.RULE_ZERO_REQUIRED <= reciting,
            "rule 0's enumeration vanished from %s — if it moved, move this "
            "list with it" % sorted(self.RULE_ZERO_REQUIRED - reciting),
        )
        for name in sorted(reciting):
            with self.subTest(source=name):
                self.assertIn(
                    "no subscription cancelled",
                    _flowed((REPO_ROOT / name).read_text(encoding="utf-8")),
                    "%s dropped an item from rule 0's enumeration" % name,
                )


if __name__ == "__main__":
    unittest.main()
