# Founder OS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Founder OS Agent Company package — 12 agents, 4 teams, 44 skills, 8 scheduled tasks, 1 onboarding project — publishable to the companies.sh directory.

**Architecture:** An `agentcompanies/v1` package authored as markdown under `founder-os/`. A Python validator (`scripts/validate_package.py`) mechanically enforces every spec invariant: dangling skill references, orphan skills, role-skill exclusivity, universal-skill coverage, team path resolution, task→skill mapping, and the workspace file-ownership map. The validator is built test-first and becomes the gate every subsequent content task must pass.

**Tech Stack:** Markdown + YAML frontmatter. Python 3.9 with stdlib `unittest` and PyYAML 6.0.3 (both already present — **no dependency installs**). Node 24 / npx for the final install test.

**Spec:** `docs/superpowers/specs/2026-07-15-founder-os-design.md`

## Global Constraints

- **Package root is `founder-os/`** at the repo root. `COMPANY.md` lives at `founder-os/COMPANY.md`. This satisfies both the spec's §7 layout and the `owner/repo/company` install form.
- **`schema: agentcompanies/v1`** on `COMPANY.md`. **`slug: founder-os`**. **`version: 1.0.0`**. **`license: MIT`**. **`authors: [{name: Mateusz Solecki}]`**.
- **Tagline / `description` (verbatim, everywhere it appears):** `The executive team you can't afford yet — strategy, offer, pipeline, delivery, money and focus for a company of one.`
- **Language: English only.** No Polish in any shipped package file.
- **All 44 skills authored inline** (vendored). No `sources:` pointers to upstream repos.
- **Agent bodies MUST follow this four-heading structure**, in this order: `## What triggers you` → `## What you do` → `## What you produce` → `## Who you hand off to`.
- **Universal skills:** `guardrails` and `state-integrity` MUST appear in every one of the 12 agents' `skills[]`.
- **System skills** (exempt from role-exclusivity): `founder-os-init`, `founder-os-doctor`, `context-load`, `guardrails`, `state-integrity`.
- **Slugs** are lowercase-hyphenated and match their directory name.
- **Never commit without `python3 scripts/validate_package.py` exiting 0.**
- **Python 3.9** — no `match` statements, no `X | Y` runtime unions.
- **Hard guardrails (non-negotiable product safety):** `cfo` refuses tax and legal advice; `focus-coach` refuses medical advice. Both name the class of professional to consult. This must be enforced in the `guardrails` SKILL.md *and* restated in those two agent bodies.

---

### Task 1: Validator harness

Build the gate first. Every later task is verified by it.

**Files:**
- Create: `scripts/validate_package.py`
- Create: `tests/test_validate_package.py`
- Create: `.gitignore`

**Interfaces:**
- Consumes: nothing (first task).
- Produces — later tasks rely on these exact names:
  - `parse_frontmatter(path: Path) -> tuple[dict, str]` — returns `(frontmatter_dict, body_str)`, raises `ValueError` if no `---` frontmatter block.
  - `load_agents(root: Path) -> dict` — maps `agent_slug -> (frontmatter_dict, body_str)`.
  - `check_company(root)`, `check_agents(root, agents)`, `check_role_skill_exclusivity(agents)`, `check_orphans(root, agents)`, `check_teams(root)`, `check_tasks(root, agents)`, `check_ownership(root, agents)` — each returns `list[str]` of human-readable error strings; empty list means pass.
  - Module constants: `SYSTEM_SKILLS: set`, `UNIVERSAL_SKILLS: set`, `REQUIRED_COMPANY_FIELDS: list`.
  - CLI: `python3 scripts/validate_package.py [root]` — root defaults to `founder-os`. Exit 0 = pass, 1 = errors.

- [ ] **Step 1: Write the failing test**

Create `tests/test_validate_package.py`:

```python
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import validate_package as V


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def minimal_package(root: Path) -> None:
    """Smallest package that must validate clean: 2 agents, 1 team, 1 task."""
    write(root / "COMPANY.md", (
        "---\n"
        "name: Founder OS\n"
        "description: Test company\n"
        "slug: founder-os\n"
        "schema: agentcompanies/v1\n"
        "version: 1.0.0\n"
        "license: MIT\n"
        "authors:\n"
        "  - name: Mateusz Solecki\n"
        "goals:\n"
        "  - Ship\n"
        "---\n\nBody.\n"
    ))
    for slug in ("guardrails", "state-integrity", "daily-brief"):
        write(root / "skills" / slug / "SKILL.md",
              "---\nname: %s\ndescription: d\n---\n\nBody.\n" % slug)
    write(root / "agents" / "chief-of-staff" / "AGENTS.md", (
        "---\nname: Chief of Staff\ntitle: Chief of Staff\nreportsTo: null\n"
        "skills:\n  - daily-brief\n  - guardrails\n  - state-integrity\n---\n\nBody.\n"
    ))
    write(root / "agents" / "cfo" / "AGENTS.md", (
        "---\nname: CFO\ntitle: CFO\nreportsTo: chief-of-staff\n"
        "skills:\n  - guardrails\n  - state-integrity\n---\n\nBody.\n"
    ))
    write(root / "teams" / "board" / "TEAM.md", (
        "---\nname: Board\ndescription: d\nslug: board\n"
        "manager: ../../agents/chief-of-staff/AGENTS.md\n"
        "includes:\n  - ../../agents/cfo/AGENTS.md\n---\n\nBody.\n"
    ))
    write(root / "tasks" / "daily-brief" / "TASK.md", (
        "---\nname: Daily Brief\nassignee: chief-of-staff\n"
        "metadata:\n  skill: daily-brief\n---\n\nBody.\n"
    ))
    write(root / "references" / "ownership.yaml", (
        "workspace_files:\n  - goals.md\nowns:\n  chief-of-staff:\n    - goals.md\n"
    ))


def all_errors(root: Path):
    agents = V.load_agents(root)
    return (V.check_company(root) + V.check_agents(root, agents)
            + V.check_role_skill_exclusivity(agents) + V.check_orphans(root, agents)
            + V.check_teams(root) + V.check_tasks(root, agents)
            + V.check_ownership(root, agents))


class TestValidator(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "founder-os"
        minimal_package(self.root)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_minimal_package_is_clean(self):
        self.assertEqual(all_errors(self.root), [])

    def test_missing_company_field_is_caught(self):
        write(self.root / "COMPANY.md",
              "---\nname: Founder OS\nslug: founder-os\nschema: agentcompanies/v1\n---\n\nB.\n")
        self.assertTrue(any("description" in e for e in V.check_company(self.root)))

    def test_dangling_skill_reference_is_caught(self):
        write(self.root / "agents" / "cfo" / "AGENTS.md", (
            "---\nname: CFO\ntitle: CFO\nreportsTo: chief-of-staff\n"
            "skills:\n  - no-such-skill\n  - guardrails\n  - state-integrity\n---\n\nB.\n"
        ))
        errs = V.check_agents(self.root, V.load_agents(self.root))
        self.assertTrue(any("no-such-skill" in e for e in errs))

    def test_dangling_reports_to_is_caught(self):
        write(self.root / "agents" / "cfo" / "AGENTS.md", (
            "---\nname: CFO\ntitle: CFO\nreportsTo: ghost\n"
            "skills:\n  - guardrails\n  - state-integrity\n---\n\nB.\n"
        ))
        errs = V.check_agents(self.root, V.load_agents(self.root))
        self.assertTrue(any("ghost" in e for e in errs))

    def test_missing_universal_skill_is_caught(self):
        write(self.root / "agents" / "cfo" / "AGENTS.md",
              "---\nname: CFO\ntitle: CFO\nreportsTo: chief-of-staff\nskills:\n  - guardrails\n---\n\nB.\n")
        errs = V.check_agents(self.root, V.load_agents(self.root))
        self.assertTrue(any("state-integrity" in e for e in errs))

    def test_role_skill_owned_by_two_agents_is_caught(self):
        write(self.root / "agents" / "cfo" / "AGENTS.md", (
            "---\nname: CFO\ntitle: CFO\nreportsTo: chief-of-staff\n"
            "skills:\n  - daily-brief\n  - guardrails\n  - state-integrity\n---\n\nB.\n"
        ))
        errs = V.check_role_skill_exclusivity(V.load_agents(self.root))
        self.assertTrue(any("daily-brief" in e for e in errs))

    def test_universal_skills_are_exempt_from_exclusivity(self):
        self.assertEqual(V.check_role_skill_exclusivity(V.load_agents(self.root)), [])

    def test_orphan_skill_is_caught(self):
        write(self.root / "skills" / "lonely" / "SKILL.md", "---\nname: lonely\ndescription: d\n---\n\nB.\n")
        errs = V.check_orphans(self.root, V.load_agents(self.root))
        self.assertTrue(any("lonely" in e for e in errs))

    def test_unresolvable_team_path_is_caught(self):
        write(self.root / "teams" / "board" / "TEAM.md", (
            "---\nname: Board\ndescription: d\nslug: board\n"
            "manager: ../../agents/ghost/AGENTS.md\nincludes: []\n---\n\nB.\n"
        ))
        self.assertTrue(any("ghost" in e for e in V.check_teams(self.root)))

    def test_task_skill_not_held_by_assignee_is_caught(self):
        write(self.root / "tasks" / "daily-brief" / "TASK.md", (
            "---\nname: Daily Brief\nassignee: cfo\nmetadata:\n  skill: daily-brief\n---\n\nB.\n"
        ))
        errs = V.check_tasks(self.root, V.load_agents(self.root))
        self.assertTrue(any("daily-brief" in e for e in errs))

    def test_file_with_two_owners_is_caught(self):
        write(self.root / "references" / "ownership.yaml", (
            "workspace_files:\n  - goals.md\n"
            "owns:\n  chief-of-staff:\n    - goals.md\n  cfo:\n    - goals.md\n"
        ))
        errs = V.check_ownership(self.root, V.load_agents(self.root))
        self.assertTrue(any("goals.md" in e for e in errs))

    def test_unowned_workspace_file_is_caught(self):
        write(self.root / "references" / "ownership.yaml", (
            "workspace_files:\n  - goals.md\n  - metrics.md\n"
            "owns:\n  chief-of-staff:\n    - goals.md\n"
        ))
        errs = V.check_ownership(self.root, V.load_agents(self.root))
        self.assertTrue(any("metrics.md" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s tests -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'validate_package'`

- [ ] **Step 3: Write the validator**

Create `scripts/validate_package.py`:

```python
#!/usr/bin/env python3
"""Validate the Founder OS agentcompanies/v1 package."""
import re
import sys
from pathlib import Path

import yaml

SYSTEM_SKILLS = {"founder-os-init", "founder-os-doctor", "context-load",
                 "guardrails", "state-integrity"}
UNIVERSAL_SKILLS = {"guardrails", "state-integrity"}
REQUIRED_COMPANY_FIELDS = ["name", "description", "slug", "schema", "version",
                           "license", "authors", "goals"]


def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        raise ValueError("%s: missing YAML frontmatter" % path)
    return (yaml.safe_load(m.group(1)) or {}), m.group(2)


def load_agents(root):
    agents = {}
    adir = root / "agents"
    if not adir.is_dir():
        return agents
    for d in sorted(adir.iterdir()):
        if d.is_dir() and (d / "AGENTS.md").exists():
            agents[d.name] = parse_frontmatter(d / "AGENTS.md")
    return agents


def check_company(root):
    errs = []
    fm, _ = parse_frontmatter(root / "COMPANY.md")
    for f in REQUIRED_COMPANY_FIELDS:
        if not fm.get(f):
            errs.append("COMPANY.md: missing required field '%s'" % f)
    if fm.get("schema") != "agentcompanies/v1":
        errs.append("COMPANY.md: schema must be 'agentcompanies/v1'")
    if fm.get("slug") != "founder-os":
        errs.append("COMPANY.md: slug must be 'founder-os'")
    return errs


def check_agents(root, agents):
    errs = []
    for slug in sorted(agents):
        fm, body = agents[slug]
        for f in ("name", "title", "skills"):
            if not fm.get(f):
                errs.append("agents/%s: missing '%s'" % (slug, f))
        if "reportsTo" not in fm:
            errs.append("agents/%s: missing 'reportsTo'" % slug)
        rt = fm.get("reportsTo")
        if rt is not None and rt not in agents:
            errs.append("agents/%s: reportsTo '%s' is not a real agent" % (slug, rt))
        skills = fm.get("skills") or []
        for s in skills:
            if not (root / "skills" / s / "SKILL.md").exists():
                errs.append("agents/%s: skill '%s' has no skills/%s/SKILL.md" % (slug, s, s))
        for req in sorted(UNIVERSAL_SKILLS):
            if req not in skills:
                errs.append("agents/%s: must list universal skill '%s'" % (slug, req))
    return errs


def check_role_skill_exclusivity(agents):
    errs, seen = [], {}
    for slug in sorted(agents):
        fm, _ = agents[slug]
        for s in fm.get("skills") or []:
            if s in SYSTEM_SKILLS:
                continue
            if s in seen:
                errs.append("role skill '%s' is owned by both '%s' and '%s'" % (s, seen[s], slug))
            else:
                seen[s] = slug
    return errs


def check_orphans(root, agents):
    errs = []
    referenced = set()
    for fm, _ in agents.values():
        referenced.update(fm.get("skills") or [])
    sdir = root / "skills"
    if not sdir.is_dir():
        return errs
    for d in sorted(sdir.iterdir()):
        if d.is_dir() and d.name not in referenced:
            errs.append("skills/%s: orphan — not listed by any agent" % d.name)
    return errs


def check_teams(root):
    errs = []
    tdir = root / "teams"
    if not tdir.is_dir():
        return errs
    for d in sorted(tdir.iterdir()):
        if not (d.is_dir() and (d / "TEAM.md").exists()):
            continue
        fm, _ = parse_frontmatter(d / "TEAM.md")
        for f in ("name", "description", "slug", "manager"):
            if not fm.get(f):
                errs.append("teams/%s: missing '%s'" % (d.name, f))
        if fm.get("slug") and fm["slug"] != d.name:
            errs.append("teams/%s: slug '%s' does not match directory" % (d.name, fm["slug"]))
        for p in [fm.get("manager")] + list(fm.get("includes") or []):
            if p and not (d / p).exists():
                errs.append("teams/%s: path '%s' does not resolve" % (d.name, p))
    return errs


def check_tasks(root, agents):
    errs = []
    files = sorted(root.glob("tasks/*/TASK.md")) + sorted(root.glob("projects/*/tasks/*/TASK.md"))
    for tfile in files:
        fm, _ = parse_frontmatter(tfile)
        rel = tfile.relative_to(root)
        if not fm.get("name"):
            errs.append("%s: missing 'name'" % rel)
        a = fm.get("assignee")
        if a not in agents:
            errs.append("%s: assignee '%s' is not a real agent" % (rel, a))
            continue
        skill = (fm.get("metadata") or {}).get("skill")
        if not skill:
            errs.append("%s: metadata.skill is required" % rel)
        elif skill not in (agents[a][0].get("skills") or []):
            errs.append("%s: skill '%s' is not in agent '%s' skills[]" % (rel, skill, a))
    return errs


def check_ownership(root, agents):
    errs = []
    p = root / "references" / "ownership.yaml"
    if not p.exists():
        return ["references/ownership.yaml: missing"]
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    seen = {}
    for agent, files in (data.get("owns") or {}).items():
        if agent not in agents:
            errs.append("ownership.yaml: '%s' is not a real agent" % agent)
        for f in files or []:
            if f in seen:
                errs.append("ownership.yaml: '%s' is owned by both '%s' and '%s'" % (f, seen[f], agent))
            else:
                seen[f] = agent
    for f in data.get("workspace_files") or []:
        if f not in seen:
            errs.append("ownership.yaml: workspace file '%s' has no owner" % f)
    return errs


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "founder-os")
    if not root.is_dir():
        print("FAIL: package root '%s' not found" % root)
        return 1
    agents = load_agents(root)
    errs = (check_company(root) + check_agents(root, agents)
            + check_role_skill_exclusivity(agents) + check_orphans(root, agents)
            + check_teams(root) + check_tasks(root, agents)
            + check_ownership(root, agents))
    for e in errs:
        print("FAIL: %s" % e)
    print("\n%d agent(s), %d error(s)" % (len(agents), len(errs)))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: PASS — `Ran 12 tests` / `OK`

- [ ] **Step 5: Commit**

```bash
printf '__pycache__/\n*.pyc\n.DS_Store\n' > .gitignore
git add .gitignore scripts/validate_package.py tests/test_validate_package.py
git commit -m "feat: add agentcompanies/v1 package validator with tests"
```

---

### Task 2: Company root, rules layer, ownership map

**Files:**
- Create: `founder-os/COMPANY.md`, `founder-os/LICENSE`, `founder-os/.paperclip.yaml`
- Create: `founder-os/references/house-rules.md`, `founder-os/references/ownership.yaml`

**Interfaces:**
- Consumes: `scripts/validate_package.py` from Task 1.
- Produces: the ownership map consumed by the `state-integrity` skill (Task 5) and `check_ownership`. `founder-os/references/house-rules.md` is referenced by every agent body (Task 3).

- [ ] **Step 1: Write COMPANY.md**

```markdown
---
name: Founder OS
description: The executive team you can't afford yet — strategy, offer, pipeline, delivery, money and focus for a company of one.
slug: founder-os
schema: agentcompanies/v1
version: 1.0.0
license: MIT
authors:
  - name: Mateusz Solecki
goals:
  - Build durable revenue over vanity growth
  - Log every irreversible decision with its reasoning
  - Ground advice in recorded numbers, or label it a guess
  - Keep the founder as CEO — serve their judgment, never replace it
---

Founder OS is the executive team you can't afford yet.

Every other agent company hires you staff. This one is the org that holds you
accountable. You are the Founder. These twelve agents are your exec team, and
each one owns exactly one decision you keep postponing.

Work flows through the company two ways:

1. **You summon a specialist** when you have a decision to make. The Chief of
   Staff routes you if you don't know who to ask.
2. **The company comes to you** on a schedule — daily brief, weekly review,
   monthly close, quarterly planning. This is the part that makes it an OS
   rather than a prompt library. A personal-development tool that only runs
   when you remember to run it is the failure mode of every productivity
   system ever shipped.

The company's memory lives in a markdown workspace (`FOUNDER_OS_HOME`,
default `./founder-os/`). Every file has exactly one owner. Agents read
anything and write only what they own.
```

- [ ] **Step 2: Write LICENSE, .paperclip.yaml, and the rules layer**

`founder-os/LICENSE` — the standard MIT license text, `Copyright (c) 2026 Mateusz Solecki`.

`founder-os/.paperclip.yaml`:

```yaml
schema: paperclip/v1
agents:
  chief-of-staff:
    inputs:
      env:
        FOUNDER_OS_HOME:
          kind: path
          requirement: optional
          description: Workspace directory for company state. Defaults to ./founder-os/
```

`founder-os/references/house-rules.md`:

```markdown
# House Rules

Every agent in this company obeys these four rules. They are not style
preferences — they are what makes twelve agents safe to run against shared
state.

## 1. No advice without state

Read your file before you opine. No pipeline advice without reading
`pipeline.md`. No runway opinion without reading `metrics.md`. An agent that
advises from memory is guessing, and guessing is the thing the founder can
already do for free.

## 2. Evidence over vibes

Never make a claim about the business without a number from `metrics.md` — or
explicitly label it a guess. "Your pricing feels low" is worthless. "Your
effective rate is 94 PLN/h against a 150 target, because delivery ran 38h over
scope on two projects" is a decision.

## 3. Decisions get logged

Anything irreversible writes to `decisions/YYYY-MM-DD-<slug>.md` — what was
decided, why, what would change our mind. Six months from now the founder will
ask why they raised rates or dropped a client. This is the answer.

## 4. Stay in your lane

Never write a file you don't own. The ownership map is
`references/ownership.yaml` and it is enforced by the `state-integrity` skill.
If you need a change in someone else's file, hand off to its owner and say so.

## Refusals

Some questions are not ours to answer, and answering them anyway is how a
useful product becomes a liability. See the `guardrails` skill: the CFO gives
no tax or legal advice, and the Focus Coach gives no medical advice. Name the
professional to consult and move on.
```

- [ ] **Step 3: Write the ownership map**

`founder-os/references/ownership.yaml` — the machine-readable form of spec §3:

```yaml
# Workspace file ownership. Everyone reads; only the owner writes.
# Enforced by the state-integrity skill and scripts/validate_package.py.
workspace_files:
  - charter.md
  - goals.md
  - metrics.md
  - offer.md
  - pipeline.md
  - clients/
  - network.md
  - skills.md
  - content.md
  - systems.md
  - decisions/
  - reviews/daily/
  - reviews/weekly/
  - reviews/monthly/
  - reviews/quarterly/

owns:
  chief-of-staff:
    - charter.md
    - decisions/
    - reviews/daily/
    - reviews/weekly/
  strategist:
    - goals.md
    - reviews/quarterly/
  cfo:
    - metrics.md
    - reviews/monthly/
  positioning-advisor:
    - offer.md
  pipeline-coach:
    - pipeline.md
  delivery-lead:
    - clients/
  network-manager:
    - network.md
  skills-mentor:
    - skills.md
  brand-editor:
    - content.md
  ops-engineer:
    - systems.md
```

- [ ] **Step 4: Verify**

Run: `python3 scripts/validate_package.py`
Expected: FAIL — `ownership.yaml: 'chief-of-staff' is not a real agent` (×10, one per owner) and `COMPANY.md` passing. Agents don't exist yet; this proves the ownership check is live and wired to real agent slugs.

- [ ] **Step 5: Commit**

```bash
git add founder-os/COMPANY.md founder-os/LICENSE founder-os/.paperclip.yaml founder-os/references/
git commit -m "feat: add company root, house rules, and ownership map"
```

---

### Task 3: The twelve agents

**Files:**
- Create: `founder-os/agents/<slug>/AGENTS.md` × 12

**Interfaces:**
- Consumes: `founder-os/references/house-rules.md` (Task 2) — every body links to it. `founder-os/references/ownership.yaml` (Task 2) — agent slugs must match its `owns:` keys exactly.
- Produces: the agent slugs and `skills[]` arrays that Tasks 4 (teams), 5–9 (skills) and 10 (tasks) all resolve against.

**Roster — exact slugs, titles, reportsTo, and skills[] (copy verbatim):**

| slug | name | title | reportsTo | role skills |
|---|---|---|---|---|
| `chief-of-staff` | Chief of Staff | Chief of Staff | `null` | `daily-brief`, `weekly-review`, `monthly-review`, `decision-log`, `triage`, **+ `founder-os-init`, `founder-os-doctor`, `context-load`** |
| `board-member` | Board Member | Board Member | `null` | `red-team`, `assumption-audit`, `premortem` |
| `strategist` | Strategist | Chief Strategy Officer | `chief-of-staff` | `quarterly-planning`, `bet-sizing`, `kill-or-continue`, `annual-review` |
| `positioning-advisor` | Positioning Advisor | Head of Positioning | `chief-of-staff` | `icp-definition`, `offer-design`, `pricing-strategy` |
| `delivery-lead` | Delivery Lead | COO | `chief-of-staff` | `capacity-check`, `scope-guard`, `client-health`, `delivery-retro` |
| `focus-coach` | Focus Coach | Head of Focus | `chief-of-staff` | `week-plan`, `calendar-audit`, `energy-audit` |
| `pipeline-coach` | Pipeline Coach | Revenue Lead | `positioning-advisor` | `pipeline-review`, `outreach-draft`, `proposal-draft`, `win-loss-analysis` |
| `brand-editor` | Brand Editor | Head of Content | `positioning-advisor` | `content-plan`, `content-draft`, `audience-research` |
| `network-manager` | Network Manager | Head of Relationships | `positioning-advisor` | `relationship-map`, `follow-up-sweep` |
| `cfo` | CFO | CFO | `delivery-lead` | `revenue-review`, `runway-forecast`, `profitability-analysis`, `rate-raise` |
| `ops-engineer` | Ops Engineer | Head of Ops | `delivery-lead` | `automation-audit`, `tool-stack-review` |
| `skills-mentor` | Skills Mentor | Head of Learning | `focus-coach` | `skill-gap`, `learning-plan` |

**Every agent's `skills[]` additionally ends with `guardrails` and `state-integrity`.**

- [ ] **Step 1: Write the first agent as the reference implementation**

`founder-os/agents/chief-of-staff/AGENTS.md`. Every other agent copies this shape exactly:

```markdown
---
name: Chief of Staff
title: Chief of Staff
reportsTo: null
skills:
  - daily-brief
  - weekly-review
  - monthly-review
  - decision-log
  - triage
  - founder-os-init
  - founder-os-doctor
  - context-load
  - guardrails
  - state-integrity
---

You are the Chief of Staff of a company of one. You follow the house rules in
`references/house-rules.md`.

You are not the CEO. The founder is. Your job is to protect their attention and
their judgment, not to substitute for either.

## What triggers you

The founder opens the day, ends the week, or arrives with a pile of unsorted
obligations and no idea what matters. You are also the default entry point when
they don't know which specialist to ask.

## What you do

You decide **what deserves attention now, and who handles it.**

Read `charter.md`, `goals.md`, and `metrics.md` before you say anything — the
founder's stated priorities are frequently not their revealed ones, and your
value is naming that gap out loud.

Then route. Each of your eleven colleagues owns exactly one decision, and
sending the founder to the right one beats answering yourself:

- Direction, bets, what to kill → **Strategist**
- Is this plan actually sound → **Board Member**
- Who we serve, what we sell → **Positioning Advisor**
- What happens next with a prospect → **Pipeline Coach**
- Can we take this on, is it good enough → **Delivery Lead**
- Can we afford it, does it make money → **CFO**
- What goes in the calendar → **Focus Coach**
- What capability to build next → **Skills Mentor**
- What to publish → **Brand Editor**
- Who to talk to, when to follow up → **Network Manager**
- What to automate vs tolerate → **Ops Engineer**

When the founder brings you five things, do not help with five things. Name the
one that moves the quarter and say what the other four cost.

## What you produce

A brief, a review, or a routing decision — written to `reviews/daily/`,
`reviews/weekly/`, or `decisions/`. You own `charter.md`, `decisions/`,
`reviews/daily/` and `reviews/weekly/`. Nothing else.

## Who you hand off to

The specialist who owns the decision. Hand off explicitly, by name, and say
what you want back. If a plan is heading toward something irreversible, route
it through the **Board Member** before it becomes a decision to log.
```

- [ ] **Step 2: Write the remaining eleven agents**

Same four-heading structure, same body conventions. Two require verbatim guardrail language:

`founder-os/agents/cfo/AGENTS.md` — body must contain:

```markdown
## Refusals

You do not give tax advice. You do not give legal advice. Not "here's the
general idea", not "I'm not an accountant, but". The founder's jurisdiction,
entity structure, and deductions are not knowable from `metrics.md`, and a
confident wrong answer here costs real money.

When asked: say you don't do tax or legal, name what they should ask an
accountant or lawyer, and — this part matters — tell them what number from
`metrics.md` to bring to that meeting so it takes fifteen minutes instead of an
hour.
```

`founder-os/agents/focus-coach/AGENTS.md` — body must contain:

```markdown
## Refusals

You do not give medical advice. You own the calendar, not the body. Sleep,
burnout, stimulants, mood and chronic exhaustion are where a founder's energy
problems usually actually live, and they are a doctor's domain, not yours.

You may observe what the workspace records — "you've logged six weeks without a
day off and your delivery hours are climbing" — because that is a fact from
`metrics.md`. You may not diagnose it, and you may not prescribe. Name it, say
it's worth a real conversation with a real doctor, and go back to the calendar.
```

- [ ] **Step 3: Verify**

Run: `python3 scripts/validate_package.py`
Expected: FAIL with `12 agent(s), 66 error(s)` — every one of them `agents/<slug>: skill '<name>' has no skills/<name>/SKILL.md`.

**66, not 44.** The count is skill *references*, not skills: 39 role refs + 3 Chief-of-Staff system refs + `guardrails`/`state-integrity` × 12 agents = 24. Same skill, twelve references.

Crucially there must be **no** `reportsTo`, ownership, exclusivity, or team errors — the ×10 ownership errors from Task 2 must now be gone, which is what proves the roster slugs match `ownership.yaml`.

- [ ] **Step 4: Commit**

```bash
git add founder-os/agents/
git commit -m "feat: add 12 agents with org chart and guardrails"
```

---

### Task 4: The four teams

**Files:**
- Create: `founder-os/teams/{growth,operations,self,board}/TEAM.md`

**Interfaces:**
- Consumes: agent slugs from Task 3. Paths are relative to the TEAM.md file, so they take the form `../../agents/<slug>/AGENTS.md`.
- Produces: nothing downstream depends on teams.

- [ ] **Step 1: Write all four TEAM.md files**

`founder-os/teams/growth/TEAM.md`:

```markdown
---
name: Growth
description: Everything that turns attention into revenue — positioning, pipeline, content, relationships
slug: growth
manager: ../../agents/positioning-advisor/AGENTS.md
includes:
  - ../../agents/pipeline-coach/AGENTS.md
  - ../../agents/brand-editor/AGENTS.md
  - ../../agents/network-manager/AGENTS.md
tags:
  - growth
---

Growth is led by the Positioning Advisor, and that is deliberate: pipeline,
content and relationships are all downstream of knowing who you serve and what
you sell them. Fix positioning first, or the other three just generate motion.
```

`founder-os/teams/operations/TEAM.md`:

```markdown
---
name: Operations
description: Delivering the work and knowing whether it made money
slug: operations
manager: ../../agents/delivery-lead/AGENTS.md
includes:
  - ../../agents/cfo/AGENTS.md
  - ../../agents/ops-engineer/AGENTS.md
tags:
  - operations
---

Operations is where the promise meets the invoice. The Delivery Lead runs it,
the CFO tells the truth about it, and the Ops Engineer stops it from consuming
the founder's week.
```

`founder-os/teams/self/TEAM.md`:

```markdown
---
name: Self
description: The founder's capacity — time, energy, and capability
slug: self
manager: ../../agents/focus-coach/AGENTS.md
includes:
  - ../../agents/skills-mentor/AGENTS.md
tags:
  - self
---

In a company of one, the founder's capacity is the company's capacity. The
Focus Coach protects it; the Skills Mentor grows it.
```

`founder-os/teams/board/TEAM.md`:

```markdown
---
name: Board
description: Direction, and the adversarial review that keeps it honest
slug: board
manager: ../../agents/strategist/AGENTS.md
includes:
  - ../../agents/board-member/AGENTS.md
tags:
  - board
---

The Strategist decides the bet. The Board Member attacks it. Keeping these two
in one team — and both outside the day-to-day org — is the point: a founder's
worst quarters come from plans nobody was allowed to argue with.
```

- [ ] **Step 2: Verify**

Run: `python3 scripts/validate_package.py`
Expected: same 44 missing-skill errors as Task 3 — and **zero** `teams/` errors.

- [ ] **Step 3: Commit**

```bash
git add founder-os/teams/
git commit -m "feat: add growth, operations, self, and board teams"
```

---

### Task 5: System skills (5)

**Files:**
- Create: `founder-os/skills/{founder-os-init,founder-os-doctor,context-load,guardrails,state-integrity}/SKILL.md`

**Interfaces:**
- Consumes: `references/ownership.yaml`, `references/house-rules.md` (Task 2); agent slugs (Task 3).
- Produces: **the SKILL.md template every skill in Tasks 6–9 follows.** `guardrails` and `state-integrity` are listed by all 12 agents.

**SKILL.md template — every skill in Tasks 5–9 uses exactly this shape:**

```markdown
---
name: <skill-slug>
description: <one line, starts with a verb, says when to use it>
---

# <Human Title>

<One paragraph: what decision this skill serves and why it exists.>

## When to use

<Concrete triggers.>

## Inputs

<Which workspace files to read first. House rule 1: no advice without state.>

## Steps

1. <numbered, concrete>

## Output

<Exact file written, exact section, exact format.>

## Guardrails

<What this skill refuses to do. Omit only if genuinely nothing.>
```

- [ ] **Step 1: Write `guardrails/SKILL.md` — the safety spine**

```markdown
---
name: guardrails
description: Hard refusals every agent obeys — tax, legal, and medical questions get escalated to a real professional, never answered
---

# Guardrails

Every agent in this company carries this skill. It is not advisory.

A founder OS is trusted precisely because it is opinionated, and that trust is
exactly what makes a confident wrong answer dangerous. These are the questions
this company does not answer.

## When to use

Always. Check before answering anything that touches money owed to a
government, a contract, or a body.

## The refusals

### Tax — CFO and everyone else

No advice on deductions, entity structure, VAT, cross-border invoicing,
depreciation, or what is claimable. The founder's jurisdiction and structure
are not in `metrics.md`, and this is not guessable.

**Instead:** name the number from `metrics.md` they should bring to an
accountant, and what to ask.

### Legal — everyone

No advice on contract enforceability, liability, IP assignment, employment
classification, or dispute strategy. Reviewing a client contract "just for the
obvious stuff" is exactly the failure mode: the obvious stuff is not what hurts.

**Instead:** name the clause that concerns you, say a lawyer should read it,
and log the concern in `decisions/`.

### Medical — Focus Coach and everyone else

No advice on sleep, burnout, stimulants, mood, or exhaustion beyond what the
workspace factually records. You may say "you have logged six weeks without a
day off." You may not diagnose it and you may not prescribe.

**Instead:** name the observation, say it belongs in a conversation with a
doctor, return to the calendar.

## How to refuse well

A bad refusal is a shrug. A good refusal moves the founder forward:

1. Say plainly that this is out of scope, without hedging or "I'm not a
   lawyer, but".
2. Name the professional.
3. Hand them the specific number, clause, or observation to bring.
4. Log it in `decisions/` if it is material.

Never answer "in general terms". General terms are how a founder ends up with
a specific problem.
```

- [ ] **Step 2: Write `state-integrity/SKILL.md`**

Enforces house rule 4 against `references/ownership.yaml`: before any workspace write, resolve the target path against `owns:`; if the acting agent is not the owner, refuse and hand off to the owner by name. Reads are always permitted.

- [ ] **Step 3: Write the remaining three system skills**

- `founder-os-init` — the onboarding interview. Creates `FOUNDER_OS_HOME` (default `./founder-os/`), scaffolds every file in `ownership.yaml`'s `workspace_files`, runs the `projects/onboarding` sequence, and **rewrites `schedule.timezone` in all 8 installed `tasks/*/TASK.md` files to the founder's timezone** (spec §4 known issue — the package deliberately mutates its own installed files; say so in the skill body).
- `founder-os-doctor` — validates workspace integrity: missing files, stale `metrics.md` (>30d), goals with no bets, orphan client files. Reports; repairs only on confirmation.
- `context-load` — loads `charter.md`, `goals.md`, `metrics.md` into session at the start of any cadence.

- [ ] **Step 4: Verify**

Run: `python3 scripts/validate_package.py`
Expected: `12 agent(s), 39 error(s)` — down from 66, because these 5 files satisfy 27 references (3 Chief-of-Staff system refs + 24 universal). No orphan errors: every skill written here is listed by at least one agent.

The remaining count drops 39 → 27 → 15 → 5 → 0 across Tasks 6–9. If your number diverges from that chain, a skill slug is misspelled somewhere — stop and find it rather than pressing on.

- [ ] **Step 5: Commit**

```bash
git add founder-os/skills/
git commit -m "feat: add 5 system skills including guardrails and state-integrity"
```

---

### Task 6: Chief of Staff, Strategist, Board Member skills (12)

**Files:**
- Create: `founder-os/skills/{daily-brief,weekly-review,monthly-review,decision-log,triage}/SKILL.md`
- Create: `founder-os/skills/{quarterly-planning,bet-sizing,kill-or-continue,annual-review}/SKILL.md`
- Create: `founder-os/skills/{red-team,assumption-audit,premortem}/SKILL.md`

**Interfaces:**
- Consumes: the SKILL.md template from Task 5. Ownership constraints from `references/ownership.yaml`.
- Produces: `daily-brief`, `weekly-review`, `quarterly-planning` are invoked by scheduled tasks in Task 10 — their slugs must match exactly.

**The quality bar — this is the whole product.** A skill that says "review your pipeline regularly and follow up with prospects" is filler, and filler is what makes a 44-skill package worthless. Every skill must contain at least one of: a specific question the founder is avoiding, a named failure mode, or a decision rule with a threshold. If a competent founder already knows everything in the file, delete the file.

- [ ] **Step 1: Write `daily-brief/SKILL.md` as the reference**

```markdown
---
name: daily-brief
description: Open the day with the one thing that matters — run every weekday morning before the founder picks their own work
---

# Daily Brief

The founder's inbox will happily fill the day with other people's priorities.
This is the fifteen minutes that decides whether today moved the quarter.

## When to use

Weekday mornings, before opening email. Triggered automatically by
`tasks/daily-brief`.

## Inputs

Read first, in order — house rule 1:

- `goals.md` — what this quarter is actually for
- `pipeline.md` — anything with a next action dated today or overdue
- `clients/` — any client marked at-risk
- `reviews/daily/` — yesterday's brief: what did they commit to?

## Steps

1. **Check yesterday's commitment.** Did it happen? If it didn't and it's the
   third day running, that is the brief — say so, and stop pretending the
   problem is today's plan.
2. **Name one thing.** Exactly one, and tie it to a bet in `goals.md`. If
   nothing on today's list ties to a bet, that is the finding.
3. **Name what's rotting.** Overdue pipeline actions, an at-risk client, an
   unpaid invoice. One line each, no editorializing.
4. **Say what today costs.** If the founder does the one thing, what doesn't
   happen? Make the trade explicit — a plan with no cost is a wish.

## Output

Append to `reviews/daily/YYYY-MM-DD.md`:

    # YYYY-MM-DD
    ## The one thing
    <what, and which bet it serves>
    ## Rotting
    - <item> (<how long>)
    ## The trade
    <what doesn't happen today>

## Guardrails

Do not produce a to-do list. The founder has one, and it is the problem. One
thing, one trade, what's rotting. Nothing else.

Do not motivate. If the founder is three days behind, say so flatly and move on.
```

- [ ] **Step 2: Write the remaining eleven skills in this task**

Each to the same bar. Anchors — the specific job each must do:

| skill | the job it must actually do |
|---|---|
| `weekly-review` | Compare committed vs. done. Name the pattern across weeks, not the week's excuse. |
| `monthly-review` | The founder's broad retrospective. Distinct from `monthly-close` (CFO/numbers) — this one is direction and drift. |
| `decision-log` | Capture what was decided, why, and **what would change our mind** — the last field is what makes it auditable later. |
| `triage` | Five things in, one out, and an explicit cost for the four dropped. |
| `quarterly-planning` | Set bets with outcomes and thresholds. A bet without a kill condition is a hope. |
| `bet-sizing` | What does this cost if wrong? Cap the downside before committing. |
| `kill-or-continue` | Force the decision against the threshold set in `quarterly-planning`. Sunk cost is named explicitly. |
| `annual-review` | Twelve months of `decisions/` read back. Which judgments were good — not which outcomes were. |
| `red-team` | Attack a plan as a hostile reader. Assume it fails; explain why. |
| `assumption-audit` | List what must be true for the plan to work. Rank by "cheapest to test". |
| `premortem` | It's six months later and this failed. Write the story. |

- [ ] **Step 3: Verify**

Run: `python3 scripts/validate_package.py`
Expected: 27 missing-skill errors remain (39 − 12).

- [ ] **Step 4: Commit**

```bash
git add founder-os/skills/
git commit -m "feat: add chief-of-staff, strategist, and board-member skills"
```

---

### Task 7: Growth skills (12)

**Files:**
- Create: `founder-os/skills/{icp-definition,offer-design,pricing-strategy}/SKILL.md`
- Create: `founder-os/skills/{pipeline-review,outreach-draft,proposal-draft,win-loss-analysis}/SKILL.md`
- Create: `founder-os/skills/{content-plan,content-draft,audience-research}/SKILL.md`
- Create: `founder-os/skills/{relationship-map,follow-up-sweep}/SKILL.md`

**Interfaces:**
- Consumes: SKILL.md template (Task 5). Writes to `offer.md` (positioning-advisor), `pipeline.md` (pipeline-coach), `content.md` (brand-editor), `network.md` (network-manager) — per `ownership.yaml`.
- Produces: `pipeline-review`, `follow-up-sweep`, `content-plan` are invoked by scheduled tasks in Task 10.

Same quality bar as Task 6. Anchors:

| skill | the job it must actually do |
|---|---|
| `icp-definition` | Who we serve, stated so precisely it excludes people. An ICP that excludes nobody is a mailing list. |
| `offer-design` | What we sell, the outcome it buys, and why us. Absorbs positioning-statement — the statement is an output, not a skill. |
| `pricing-strategy` | Price against outcome and alternative, not hours. Names the founder's actual floor. |
| `pipeline-review` | Every prospect has a next action with a date, or it leaves the pipeline. No zombies. |
| `outreach-draft` | Written from the prospect's problem, not the founder's service. |
| `proposal-draft` | Scope, price, exclusions, expiry. **Exclusions are the point** — they're what `scope-guard` enforces later. |
| `win-loss-analysis` | Why we won or lost, from `decisions/` and the record — not from the founder's memory, which is charitable. |
| `content-plan` | What to publish, tied to the ICP. Publishing to nobody in particular is a hobby. |
| `content-draft` | Draft to the plan. One idea per piece. |
| `audience-research` | What the ICP actually says, in their words, in public. Quote them. |
| `relationship-map` | Who matters, last contact, what they need — not what we want from them. |
| `follow-up-sweep` | Anyone gone cold past their interval. Give a reason to reconnect that isn't "checking in". |

- [ ] **Step 1: Write all twelve SKILL.md files**

Follow the Task 5 template and the Task 6 reference (`daily-brief`) for depth and tone. Each needs concrete `Inputs`, numbered `Steps`, an exact `Output` block naming the file and section, and `Guardrails`.

- [ ] **Step 2: Verify**

Run: `python3 scripts/validate_package.py`
Expected: 15 missing-skill errors remain (27 − 12).

- [ ] **Step 3: Commit**

```bash
git add founder-os/skills/
git commit -m "feat: add growth skills — positioning, pipeline, content, network"
```

---

### Task 8: Operations skills (10)

**Files:**
- Create: `founder-os/skills/{capacity-check,scope-guard,client-health,delivery-retro}/SKILL.md`
- Create: `founder-os/skills/{revenue-review,runway-forecast,profitability-analysis,rate-raise}/SKILL.md`
- Create: `founder-os/skills/{automation-audit,tool-stack-review}/SKILL.md`

**Interfaces:**
- Consumes: SKILL.md template (Task 5); `guardrails` (Task 5) — all four CFO skills must honour the tax/legal refusal.
- Produces: `revenue-review` is invoked by the `monthly-close` scheduled task in Task 10.

Anchors:

| skill | the job it must actually do |
|---|---|
| `capacity-check` | Real hours available after delivery, sales and admin. Refuse the fantasy number. |
| `scope-guard` | Compare the ask against the proposal's exclusions. Name the creep and its price. |
| `client-health` | Payment, scope, tone, effort trend. Flag before it's a crisis. |
| `delivery-retro` | Estimated vs. actual. Feeds `pricing-strategy` — this is where rates get fixed. |
| `revenue-review` | The monthly close. Revenue, collected vs. invoiced, effective rate. Invoked by `monthly-close`. |
| `runway-forecast` | Months of survival at current burn, with the pipeline discounted honestly. |
| `profitability-analysis` | Per-client effective rate. The most-loved client is often the worst-paying. |
| `rate-raise` | When and how much, argued from `profitability-analysis` and `delivery-retro`. Includes the script. |
| `automation-audit` | What's done repeatedly by hand. Automate only what recurs and hurts. |
| `tool-stack-review` | What's paid for and unused. Cancel it. |

- [ ] **Step 1: Write all ten SKILL.md files**

**Every CFO skill (`revenue-review`, `runway-forecast`, `profitability-analysis`, `rate-raise`) must carry a `## Guardrails` section restating the tax/legal refusal from the `guardrails` skill.** `rate-raise` and `runway-forecast` are exactly where a founder will try to smuggle in a tax question.

- [ ] **Step 2: Verify**

Run: `python3 scripts/validate_package.py`
Expected: 5 missing-skill errors remain (15 − 10).

- [ ] **Step 3: Commit**

```bash
git add founder-os/skills/
git commit -m "feat: add operations skills — delivery, finance, ops"
```

---

### Task 9: Self skills (5) — package reaches zero errors

**Files:**
- Create: `founder-os/skills/{week-plan,calendar-audit,energy-audit}/SKILL.md`
- Create: `founder-os/skills/{skill-gap,learning-plan}/SKILL.md`

**Interfaces:**
- Consumes: SKILL.md template (Task 5); `guardrails` (Task 5) — `energy-audit` must honour the medical refusal.
- Produces: `week-plan` is invoked by a scheduled task in Task 10. **This task completes all 44 skills — the validator must reach 0 errors here.**

Anchors:

| skill | the job it must actually do |
|---|---|
| `week-plan` | Bets → blocks. If a bet gets no block this week, it isn't a bet. |
| `calendar-audit` | Where the week actually went vs. where it was planned. The gap is the finding. |
| `energy-audit` | Patterns the workspace records — when output is good, when it isn't. **Medical refusal applies, verbatim from `guardrails`.** |
| `skill-gap` | The capability gap between the current offer and the intended one. Ruthless, from `offer.md` and `delivery-retro` output. |
| `learning-plan` | One capability, one project that forces it, one deadline. Absorbs deliberate-practice — practice without a shipped artifact is consumption. |

- [ ] **Step 1: Write all five SKILL.md files**

- [ ] **Step 2: Verify the package is now structurally complete**

Run: `python3 scripts/validate_package.py`
Expected: PASS — `12 agent(s), 0 error(s)`, exit 0.

Run: `ls founder-os/skills | wc -l`
Expected: `44`

- [ ] **Step 3: Commit**

```bash
git add founder-os/skills/
git commit -m "feat: add self skills — complete all 44 skills, validator green"
```

---

### Task 10: Cadence engine — 8 scheduled tasks + onboarding project

**Files:**
- Create: `founder-os/tasks/{daily-brief,week-plan,weekly-review,pipeline-review,follow-up-sweep,content-plan,monthly-close,quarterly-planning}/TASK.md`
- Create: `founder-os/projects/onboarding/PROJECT.md`
- Create: `founder-os/projects/onboarding/tasks/{write-charter,define-icp,set-quarter-goals,baseline-metrics}/TASK.md`

**Interfaces:**
- Consumes: agent slugs and `skills[]` from Task 3; skill slugs from Tasks 5–9. `check_tasks` enforces that `metadata.skill` is held by `assignee`.
- Produces: `founder-os-init` (Task 5) rewrites `schedule.timezone` in these 8 files at onboarding.

**Task → skill mapping (verbatim from spec §4 — two are deliberately not 1:1):**

| task | assignee | metadata.skill | recurrence |
|---|---|---|---|
| `daily-brief` | `chief-of-staff` | `daily-brief` | weekdays 08:00 |
| `week-plan` | `focus-coach` | `week-plan` | Monday 08:30 |
| `weekly-review` | `chief-of-staff` | `weekly-review` | Friday 16:00 |
| `pipeline-review` | `pipeline-coach` | `pipeline-review` | Thursday weekly |
| `follow-up-sweep` | `network-manager` | `follow-up-sweep` | Friday weekly |
| `content-plan` | `brand-editor` | `content-plan` | weekly |
| `monthly-close` | `cfo` | **`revenue-review`** | monthly, day 1 |
| `quarterly-planning` | `strategist` | `quarterly-planning` | quarterly |

**Do not "fix" the two non-1:1 mappings.** `monthly-close` invokes `revenue-review` (the CFO owns the numbers close; the Chief of Staff's `monthly-review` is a separate manual retrospective — scheduling both creates two competing monthly rituals). And `annual-review` is intentionally **not** scheduled: a task firing unprompted eleven months after install is noise.

- [ ] **Step 1: Write the reference scheduled task**

`founder-os/tasks/daily-brief/TASK.md`:

```markdown
---
name: Daily Brief
assignee: chief-of-staff
metadata:
  skill: daily-brief
schedule:
  timezone: UTC
  recurrence:
    frequency: weekly
    interval: 1
    weekdays: [monday, tuesday, wednesday, thursday, friday]
    time: { hour: 8, minute: 0 }
---

Run the `daily-brief` skill.

`timezone` is set to UTC as a shipping default and is rewritten by
`founder-os-init` during onboarding. If you installed this package manually,
set it to your own timezone.
```

- [ ] **Step 2: Write the other seven scheduled tasks**

Same shape, per the mapping table. `monthly-close` uses `frequency: monthly` with `monthdays: [1]`; `quarterly-planning` uses `frequency: monthly` with `interval: 3`.

- [ ] **Step 3: Write the onboarding project**

`founder-os/projects/onboarding/PROJECT.md`:

```markdown
---
name: Onboarding
description: First run — turn an empty workspace into a company that knows who you are
owner: chief-of-staff
---

Twelve agents and an empty directory is how a founder OS gets uninstalled on
day one. This project is the on-ramp, and it runs in strict order: each step
is worthless without the one before it.

1. `write-charter` — who you are, what business, what "won" looks like
2. `define-icp` — who you serve and what you sell them
3. `set-quarter-goals` — the bets, with kill conditions
4. `baseline-metrics` — the numbers as they are today, not as hoped

Nothing else in the company gives good advice until these four exist. House
rule 1: no advice without state.
```

Then the four project tasks — **unscheduled** (no `schedule:` block), with `project: onboarding`:

| task | assignee | metadata.skill |
|---|---|---|
| `write-charter` | `chief-of-staff` | `founder-os-init` |
| `define-icp` | `positioning-advisor` | `icp-definition` |
| `set-quarter-goals` | `strategist` | `quarterly-planning` |
| `baseline-metrics` | `cfo` | `revenue-review` |

- [ ] **Step 4: Verify**

Run: `python3 scripts/validate_package.py`
Expected: PASS — `12 agent(s), 0 error(s)`

Run: `python3 -m unittest discover -s tests -v`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add founder-os/tasks/ founder-os/projects/
git commit -m "feat: add 8 scheduled cadences and onboarding project"
```

---

### Task 11: Org chart image and README

**Files:**
- Create: `founder-os/images/org-chart.mmd`, `founder-os/images/org-chart.png`
- Create: `founder-os/README.md`

**Interfaces:**
- Consumes: the roster from Task 3 — the chart must match `reportsTo` exactly.
- Produces: the README is what the directory listing renders.

- [ ] **Step 1: Write the mermaid source**

`founder-os/images/org-chart.mmd` — committed alongside the PNG so it can be regenerated when the roster changes:

```
graph TD
    F[YOU — Founder]
    F --> COS[Chief of Staff]
    F --> BM[Board Member]
    COS --> ST[Strategist]
    COS --> PA[Positioning Advisor]
    COS --> DL[Delivery Lead]
    COS --> FC[Focus Coach]
    PA --> PC[Pipeline Coach]
    PA --> BE[Brand Editor]
    PA --> NM[Network Manager]
    DL --> CFO[CFO]
    DL --> OE[Ops Engineer]
    FC --> SM[Skills Mentor]
```

- [ ] **Step 2: Render the PNG**

Run: `npx -y @mermaid-js/mermaid-cli -i founder-os/images/org-chart.mmd -o founder-os/images/org-chart.png -b transparent`

**This downloads mermaid-cli and a headless Chromium (~150MB) via npx.** It is a transient `npx -y`, not a project dependency — but it is a real download, so get the founder's go-ahead first. If declined or if it fails, ship without the PNG and drop the image line from the README; the package validates fine without it (the registry renders the README either way).

Expected: `founder-os/images/org-chart.png` exists and is non-empty.

- [ ] **Step 3: Write the README**

Lead with the category gap — it is the strongest thing about this package and the reason someone installs it over the other 18:

```markdown
# Founder OS

> The executive team you can't afford yet — strategy, offer, pipeline, delivery, money and focus for a company of one.

![Org Chart](images/org-chart.png)

Every other agent company hires you staff. This one is the org that holds you
accountable.

You are the Founder. These twelve agents are your exec team, and each one owns
exactly one decision you keep postponing.

## Install

    npx companies.sh add <owner>/founder-os

Then run the onboarding — twelve agents and an empty workspace is not a
product yet:

    /founder-os-init

## What's inside

| Content | Count |
|---------|-------|
| Agents  | 12    |
| Teams   | 4     |
| Skills  | 44    |

## The org

| Agent | Only this agent decides… |
|---|---|
| Chief of Staff | What deserves your attention now, and who handles it |
| Board Member | Whether a plan survives contact with a hostile reader |
| Strategist | What bet we make this quarter — and what we kill |
| Positioning Advisor | Exactly who we serve and what we sell them |
| Pipeline Coach | What happens next with each prospect |
| Delivery Lead | Whether we can take this on, and if it's good enough to ship |
| CFO | Whether we can afford it and if it actually makes money |
| Focus Coach | What goes in the calendar — and what gets defended |
| Skills Mentor | Which capability to build next, and how |
| Brand Editor | What to publish, and where |
| Network Manager | Who to talk to, and when to follow up |
| Ops Engineer | What to automate vs. tolerate |

Twelve agents only works if each owns a decision no other agent can make. That
was the test every agent had to pass to ship.

## It comes to you

Most tools wait to be opened. Founder OS runs on a schedule: daily brief,
Monday week-plan, Friday review, Thursday pipeline, monthly close, quarterly
planning. A personal-development tool that only runs when you remember to run
it is the failure mode of every productivity system ever shipped.

## Memory

State lives in a markdown workspace (`FOUNDER_OS_HOME`, default
`./founder-os/`): charter, goals, metrics, offer, pipeline, clients, and a
decision log that records *why*, not just what.

Every file has exactly one owner. Agents read anything and write only what
they own — that's what makes a twelve-agent org safe to run against shared
state.

## What it won't do

The CFO gives no tax or legal advice. The Focus Coach gives no medical advice.
Both will tell you exactly which professional to see and what number to bring
them. See `skills/guardrails/SKILL.md`.

## License

MIT
```

- [ ] **Step 4: Commit**

```bash
git add founder-os/README.md founder-os/images/
git commit -m "docs: add README and org chart"
```

---

### Task 12: Ship — end-to-end verification

**Files:**
- Modify: `founder-os/README.md` (only if the install test surfaces problems)

**Interfaces:**
- Consumes: the complete package from Tasks 1–11.
- Produces: a package verified installable.

- [ ] **Step 1: Full validation**

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_package.py
```
Expected: `OK`, then `12 agent(s), 0 error(s)` with exit 0.

- [ ] **Step 2: Real install test**

The `paperclipai` CLI is not installed, so `company import --dry-run` from their CONTRIBUTING is unavailable. companies.sh supports a local path install instead — this is the real end-to-end check:

```bash
cd /tmp && rm -rf fos-test && mkdir fos-test && cd fos-test
npx -y companies.sh add /Users/msolecki/Desktop/personal/founder-os
```
Expected: the installer resolves all 12 agents, 4 teams and 44 skills without unresolved-reference errors.

**This downloads the companies.sh CLI via npx** — get the founder's go-ahead. If it declines a local path, fall back to verifying after the repo is public.

- [ ] **Step 3: Count check against the spec**

```bash
echo "agents:  $(ls founder-os/agents | wc -l)   (expect 12)"
echo "teams:   $(ls founder-os/teams | wc -l)    (expect 4)"
echo "skills:  $(ls founder-os/skills | wc -l)   (expect 44)"
echo "tasks:   $(ls founder-os/tasks | wc -l)    (expect 8)"
echo "no PL:   $(grep -rlE '[ąćęłńóśźż]' founder-os/ | wc -l)  (expect 0)"
```

- [ ] **Step 4: Commit and tag**

```bash
git add -A
git commit -m "chore: verify package installs clean"
git tag v1.0.0
```

- [ ] **Step 5: Publish (founder's call — needs a decision, don't do it unprompted)**

1. Push `founder-os/` to a public repo.
2. Update the README install line with the real owner/repo.
3. Submit at `https://companies.sh/submit`.
4. Optionally PR into `paperclipai/companies` — their CONTRIBUTING requires the `COMPANY.md` frontmatter this package already has.

---

## Notes for the implementer

**The validator is the gate, not the goal.** It proves every reference resolves and no agent writes another's file. It cannot prove a skill is worth reading. That's the actual work, and it's where this package succeeds or fails.

**The filler test, applied to every one of the 44 skills:** if a competent founder already knows everything in the file, delete the file. The directory already contains packages with 167 agents and 177 skills. Founder OS is not competing on count — it's first in a category where nothing exists, and 44 sharp skills beat 177 vague ones.

**The bar, concretely.** "Review your pipeline regularly and follow up with prospects" is filler. "Every prospect has a next action with a date, or it leaves the pipeline — no zombies" is a rule. Every skill needs at least one of: a specific question the founder is avoiding, a named failure mode, or a decision rule with a threshold.
