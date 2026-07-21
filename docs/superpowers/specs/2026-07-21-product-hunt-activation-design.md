# Product Hunt Activation Launch — Design Specification

**Status:** approved by the founder on 2026-07-21  
**Product:** Founder OS  
**Launch outcome:** activation, not Product Hunt rank  
**Candidate release:** `2.4.0`

## Objective

Prepare Founder OS for a Product Hunt launch that converts a new visitor into a
founder with a useful, locally persisted first daily brief. The product must
make the value legible before it explains the thirteen-agent architecture, and
the activation path must preserve the existing ownership, evidence, local-state
and never-outbound rules.

Activation is complete only when a valid first brief exists at
`reviews/daily/YYYY-MM-DD.md`. Installing the plugin, opening the landing page,
or scaffolding an empty workspace is not activation.

## Decisions already made

- Keep the marketing name, marketplace name, plugin id and command namespace as
  `founder-os`. Accept the known collision risk; do not migrate to an
  `msolecki-*` id.
- `/founder-os-init` must carry the user through to the first daily brief in one
  continuous flow.
- Position the launch around activation plus trust.
- Keep product telemetry out. Measure activation through observed cohorts and
  voluntary user reports.
- Preserve local Markdown state, explicit file ownership, source/date
  provenance and the hard `never outbound, never money` boundary.
- Do not add integrations, new agents, more skills, voice operation or
  autonomous actions for this launch.
- Treat Codex support as beta/manual until a clean-install test proves the same
  activation experience as Claude Code.

## Problem and evidence

### Product problem

The current package has a strong operating model but exposes the machinery
before the outcome. The landing page leads with thirteen agents and dozens of
skills. The current onboarding text says it ends with a daily brief, but the
implementation instructs `/founder-os-init` to stop after scaffolding and hand
the founder three more commands. A user can therefore complete the advertised
command without reaching the advertised result.

### Audience language

Public founder discussions repeatedly describe:

- no clear path through scattered advice;
- cognitive load from holding the whole business in one head;
- inability to decide what to prioritize;
- distrust of autonomous agents with stale or conflicting context.

The product's internal language is “agents, ownership map, persistent
decisions.” The audience's language is “tell me what matters today without
creating more work.” Launch copy must translate the former into the latter.

This research is directional rather than definitive: it used public founder
discussions because no internal customer-interview or win/loss corpus was
available. The five-person activation study is therefore part of the release
gate, not post-launch polish.

### Competitive findings

Direct Founder OS plugins and adjacent executive-assistant products commonly
use fast onboarding, a setup verifier, visible progress, a small first-actions
list and clear repair/update instructions. Adjacent successful products also
make trust visible through permissions, source confidence, approval queues or
local-first state.

Adopt for this launch:

1. read-only install preflight;
2. one continuous path to first value;
3. visible onboarding progress;
4. five concrete next actions;
5. update, repair and uninstall guidance;
6. visible provenance and permission boundaries.

Reject for this launch:

- Gmail, Slack and Notion integrations;
- automatic sending or other outbound side effects;
- invisible git automation;
- voice operation;
- feature-count competition.

Representative competitor references:

- [NaluForge Founder OS getting started](https://fos.naluforge.com/docs/getting-started)
- [ARCASSystems Founder OS](https://arcassystems.com/)
- [ARCASSystems listing](https://www.claudepluginhub.com/plugins/arcassystems-founder-os)
- [thecloudtips Founder OS listing](https://www.claudepluginhub.com/plugins/thecloudtips-founder-os-plugin)

## Activation experience

### Stage 0 — preflight

`/founder-os-init` performs read-only checks before the first workspace write:

- plugin manifest and required references are present;
- the target workspace resolves unambiguously;
- the target is writable;
- a multi-business registry, if present, resolves safely;
- the current workspace is new, partially onboarded or already activated;
- the session has the canonical Founder OS context injected.

A preflight failure stops before mutation and reports the failed check, why it
matters and the exact repair path. The founder is not sent through a separate
setup command on the happy path.

### Stages 1–4 — interview

The founder sees progress labels and answers four question groups:

1. **Business:** timezone, the business in one sentence and the five-year
   north star.
2. **Customer:** two clients or companies they would take again, one they
   would not, and the observable difference.
3. **Quarter:** one result that must be true in 90 days, the numeric failure
   threshold, and the hours/cash available to pursue it.
4. **Money:** cash on hand, revenue collected over the last three months and
   real monthly burn including founder pay.

Unknown values remain unknown. They become owned queue items; the system never
fills them from inference. The interview targets a median activation time of ten
minutes and retains a hard stop at fifteen minutes. Anything that is not needed
to produce the first brief moves to progressive setup after activation.

### Stage 5 — owner-safe delegation

The Chief of Staff orchestrates but writes only its own files. Carried answers
are delegated in the same session:

- Positioning Advisor writes an evidence-backed ICP or an explicitly dated
  first-run hypothesis to `offer.md`.
- Strategist writes one sized partial-quarter bet with a numeric outcome and
  kill condition to `goals.md`.
- CFO writes the truthful first-run financial baseline and runway to
  `metrics.md`; missing close inputs remain labeled gaps.
- Chief of Staff creates queue items for missing data and accepts or refuses
  the first move proposed by the Strategist.

Each downstream skill receives a bounded first-run branch. It may produce a
thin result; it may not call that result a full ICP audit, quarterly close or
monthly revenue review.

### Stage 6 — first brief

The orchestrator validates that the minimum state is present, then invokes
`daily-brief`. The brief must:

- select exactly one thing tied to the first bet, or state that the missing
  financial fact is the one thing;
- persist that item in `queue.md`;
- name the trade;
- name up to three genuinely rotting items without inventing day-one history;
- write `reviews/daily/YYYY-MM-DD.md`.

Only a successful, validated write of that review produces
`Activation complete`.

### Stage 7 — activation receipt

The receipt is local and human-readable:

- the one thing for today;
- the path of the persisted brief;
- the files written and their owners;
- any honest gaps queued for later;
- the first five actions: `daily-brief`, write to `inbox.md`,
  `pipeline-review`, `weekly-review`, and ask the Chief of Staff where to route
  an uncategorized decision.

No event is sent. A voluntary feedback link may be displayed, but opening it is
the founder's action.

## Resume and failure model

Onboarding is resumable without a hidden tracker:

- no daily review plus an initialized charter means activation is incomplete;
- existing, populated sections are preserved;
- the next run validates and continues from the first missing stage;
- a daily review means activation already occurred and routes a repeat init to
  `founder-os-doctor`;
- failure in a delegated stage reports completed and incomplete stages and the
  exact resume command;
- no failure path prints `Activation complete`;
- a live workspace is never reset, re-scaffolded destructively or silently
  converted into a different business.

The completion condition and validation condition are identical: the same
resolved workspace must contain the valid first brief. A brief written to one
workspace cannot validate activation for another.

## Positioning and launch copy

### Message hierarchy

Hero:

> Know what matters today.

Supporting line:

> Founder OS turns your goals, cash, pipeline and commitments into one daily
> decision — stored locally and traceable to its source.

Primary CTA: `Install Founder OS`  
Secondary CTA: `See the first brief`

Proof line:

> Local Markdown · No automatic sending · Explicit ownership · No hidden actions

The page must not claim that no data leaves the computer. Workspace files stay
local, while prompts and context remain subject to the data-handling terms of
the user's Claude Code or Codex environment.

### Information order

1. the finished daily brief;
2. empty folder to brief in one command;
3. local state, sources, dates and owners;
4. the daily-to-weekly operating loop;
5. the agent architecture and full skill catalogue.

The organization chart remains available but no longer carries the first-screen
value proposition.

## Product Hunt package

- Name: `Founder OS`.
- Tagline: `Know what matters today — before opening your inbox`.
- At least four gallery images at `1270×760`: outcome, onboarding, trust model,
  operating loop.
- Thumbnail at `240×240`.
- A 45–60 second demo: public install, four onboarding stages, saved first
  brief. No mocked success state presented as a real run.
- Maker comment: problem, origin, trust boundaries, who it is for, and a request
  to test activation and report where it breaks. Never ask for an upvote.
- Three or fewer precise Product Hunt topics/tags selected at submission time.

Product Hunt allows scheduling up to 30 days ahead, recommends complete gallery
assets and maker participation, and prohibits vote manipulation. Ranking also
incorporates meaningful engagement rather than raw upvotes alone. Sources:

- [Preparing for launch](https://www.producthunt.com/launch/preparing-for-launch)
- [Before launch](https://www.producthunt.com/launch/before-launch)
- [Sharing your launch](https://www.producthunt.com/launch/sharing-your-launch)
- [Product of the Day, Week and Month](https://help.producthunt.com/en/articles/11751186-product-of-the-day-week-month)

Recommend a Saturday launch only if the tester cohort is available then. The
official guide reports more visit clicks for smaller weekend launches, but
there is no universally best day. Activation quality outranks reduced ranking
competition.

## Measurement without telemetry

### Release-gate cohort

Five people who have not worked on the repository perform a clean install while
the observer does not rescue them. Record voluntarily:

- whether a first brief was persisted;
- elapsed time to the persisted brief;
- the first confusing instruction;
- whether the result names a useful one thing;
- whether the person returns for `weekly-review` within seven days.

Go/no-go thresholds:

- at least four of five activate;
- median activation time at most ten minutes;
- P90 target at most fifteen minutes;
- no data loss, ownership breach or false completion;
- at least three of the first five return for weekly review.

### Launch cohort

Recruit a named, consented Product Hunt cohort and ask for voluntary activation
confirmation. The first seven-day target is:

- ten confirmed activations;
- at least 60% activation among people who explicitly agreed to test;
- P50 at most ten minutes and P90 at most fifteen minutes;
- at least three of the first five activations return for weekly review.

Product Hunt visits, repository traffic, installs, stars, upvotes and ranking
are reported only as supporting indicators. They are not activation.

## Technical findings to close

At the design snapshot (`4a1ba55`, 2026-07-21), the earlier repository audit had
been largely implemented. The remaining recorded feature-list failure was
`TEST-010`: landing controllers were still extracted from inline HTML by
string-slicing and `eval`. The launch work must re-audit current HEAD and close
that item if it is still open; it must not resurrect audit items already closed
by concurrent work.

Additional launch findings:

- onboarding promise and actual stopping point contradict each other;
- no end-to-end activation contract or resume path is pinned;
- CI validates internal structure but not a clean installed-copy lifecycle;
- official `claude plugin validate` passes with warnings that require either a
  manifest fix or an explicit hook test;
- manifest version `2.3.0` has no matching observed git tag;
- launch page has no activation measurement design and lacks the complete
  Product Hunt asset set;
- Codex package compatibility exists locally, but public turnkey distribution
  is unverified.

## Release scope

### In scope

- activation and resume behavior;
- first-run branches for the owner skills;
- preflight and repair instructions;
- contract, hook, installed-copy, validator and landing behavior tests;
- activation-led landing copy and information architecture;
- Product Hunt assets, copy and launch runbook;
- version, changelog and tag only after all gates pass.

### Out of scope

- authentication or middleware changes;
- outbound integrations and telemetry;
- new agents or skills;
- autonomous sending, payments, subscriptions or signatures;
- a cloud backend;
- feature-count parity with competing Founder OS products;
- claiming Codex parity before evidence exists.

## Acceptance criteria

The release is ready only when all of the following are true:

1. A clean `/founder-os-init` produces and persists a truthful first brief.
2. A partial init can resume without overwriting populated state.
3. Re-running init on an activated workspace refuses and routes to the doctor.
4. Every workspace write is performed by the owner declared in
   `references/ownership.yaml`.
5. Unknown values remain explicit and reach `queue.md` under the correct
   priority branch.
6. The installed package injects canonical guidance in a realistic
   `SessionStart` fixture.
7. Package validation, generated-command check, unit tests, behavior tests and
   clean installed-copy checks pass.
8. Official Claude plugin validation passes without an unaddressed warning.
9. Five-person activation study clears the go/no-go thresholds.
10. Landing and Product Hunt materials lead with the daily outcome, accurately
    describe data handling and include the required asset dimensions.
11. `2.4.0` manifests, changelog and tag agree.
12. Codex claims match the evidence from its own clean-install test.

## Risks and mitigations

- **The four questions are still too heavy.** Observe time per stage; move any
  input not used by the first brief to progressive setup.
- **Thin first-run state looks authoritative.** Label hypotheses, unknowns and
  incomplete closes inline with dates and sources.
- **Multi-agent orchestration fails midway.** Derive resume state from persisted
  outputs and never validate completion before the daily review exists.
- **Same-name plugin collision occurs.** Keep the founder-approved `founder-os`
  identity, document the qualified command form and test a clean install. Do not
  imply the collision risk has been eliminated.
- **No telemetry hides launch activation.** Use explicit cohorts and voluntary
  reports; never convert installs into claimed activations.
- **Launch pressure expands scope.** Freeze new features at D-7 and accept only
  activation, data-loss, security or packaging blockers.
- **Concurrent repository work changes the baseline.** Re-run the audit at the
  start of implementation, preserve unrelated changes and update the execution
  plan with the new HEAD before editing.
