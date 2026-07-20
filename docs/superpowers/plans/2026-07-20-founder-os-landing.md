# Founder OS — sales landing page

Status: complete with an explicit review limitation
Date: 2026-07-20

## Goal

Build a standalone English-language HTML page that explains to a solo business
owner what Founder OS is, how it works in practice, and why it is more than
another AI chat.

## Decisions

- Format: one `site/index.html` file with no build step or dependencies.
- Audience: a global service-business founder, consultant, or owner of several
  small businesses who works in Claude Code.
- Core promise: Founder OS turns scattered AI conversations into an executive
  team that remembers company state and protects decisions and operating rhythm.
- Product proof: 13 agents, 49 workflows, 10 cadences, local Markdown state, an
  ownership guard, and agents that cannot send or pay.
- CTA: install the plugin; no price or form because the repository did not
  define a paid offer or sales model.
- Style: editorial command center — warm background, navy, electric orange,
  strong typography, and an operating interface instead of stock photography.

## Step 1 — narrative and information architecture [S]

**What:** Build the path from the founder's problem through the product
mechanism to installation.

**Where:** This plan and the copy in `site/index.html`.

**How:** Hero → cost of chaos → Founder OS difference → day/week of work →
team → memory and safety mechanism → FAQ → installation.

**Test:** Every sales claim is supported by `founder-os/README.md`,
`founder-os/COMMANDS.md`, or the canonical `founder-os/CLAUDE.md`.

## Step 2 — page implementation [M]

**What:** A responsive, accessible landing page with lightweight interactions.

**Where:** `site/index.html`.

**How:** Semantic HTML, inline CSS, and vanilla JavaScript; no external fonts,
frameworks, or scripts. Add mobile navigation, switchable brief previews,
command copying, an FAQ built with `details`, and animations that respect
`prefers-reduced-motion`.

**Test:** The document has a valid heading structure, visible focus states,
works without JavaScript, and has no horizontal overflow at 375 px.

## Step 3 — validation [M]

**What:** Check the page and prove the package has no regressions.

**Where:** `site/index.html` and the repository.

**How:** Parse the HTML, check links and IDs, serve the page locally, capture
desktop and mobile screenshots, run
`python3 scripts/validate_package.py founder-os`, and run
`python3 -m unittest discover -s tests`.

**Test:** No parser or internal-link errors; both repository test commands
pass; screenshots confirm the desktop and mobile layouts.

## Step 4 — fresh review [S]

**What:** Independently review the final HTML and address the findings.

**Where:** `site/index.html`.

**How:** Give a fresh subagent only the objective, path, constraints, and
expected result format; verify any changes locally after its verdict.

**Test:** No unresolved high- or medium-severity issues.

## Invariant

The landing page is additive and does not change plugin behavior or
installation. Existing unrelated changes in hooks and tests stay untouched.

## Next step

No implementation remains. Preserve the documented review and screenshot
limitations in any future handoff.

## Progress

- 2026-07-20: completed the narrative and information architecture.
- 2026-07-20: completed the standalone HTML/CSS/JavaScript landing page.
- 2026-07-20: HTML parsing, ID/anchor/ARIA checks, and JavaScript parsing
  passed; the package validator reported 13 agents, 49 skills, and zero errors;
  all 80 unit tests passed.
- 2026-07-20: the contrast audit found and fixed small text on the orange
  background; mobile navigation that works without JavaScript was also added.
- 2026-07-20: headless Chrome exited with code 134 and the execution profile
  blocked the local server, so desktop and mobile screenshots were not created.
- 2026-07-20: the active `ownership-guard.py` blocked two attempts to use a
  fresh review subagent because Codex classified its read-only terminal as
  outbound `Bash`. The guard was not bypassed or modified; a final local audit
  was completed and the limitation remains explicit in the handoff.
- 2026-07-20: after user feedback, all copy, metadata, anchors, JavaScript
  messages, and accessibility labels were rewritten in natural sales English;
  the layout and behavior remained unchanged.
