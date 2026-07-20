# House rules

Seven rules every agent in the company obeys. They are not style preferences —
they are what makes an org of agents safe to run against shared state. This page
explains them for the person relying on them; the full text is
[`references/house-rules.md`](../founder-os/references/house-rules.md), and the
`guardrails` skill is where they are enforced in a session.

Rule 0 is the one that matters if you read nothing else.

## Rule 0 — Never outbound. Never money.

**No agent sends. No agent pays.** No email, no message, no post, no invoice, no
transfer, no signature — regardless of which agent, however obvious the send
looks, however explicitly the founder asked mid-flow. You draft; the founder
sends. That is the entire boundary and it does not bend.

Why it is separate from every other rule: every other guardrail is organised by
*topic* — the CFO refuses tax, the Focus Coach refuses medical. Topic guardrails
cannot see this class of harm at all. "Send the follow-up to Anna" is not a tax,
legal, or medical question. It is simply **irreversible**, and irreversibility is
the axis that actually matters. A wrong opinion costs an argument; a sent email
costs a client.

The capability existing is not the permission. If the founder's tooling connects
a mail server, a payments MCP, or a logged-in browser session, that is precisely
the moment this rule is load-bearing rather than theoretical. This is why it is
enforced two ways below rather than merely asked for in prose:

- **Build time** — no agent's `tools:` allowlist may contain a tool that reaches
  the outside world. The validator refuses to ship a package that violates this.
- **Write time** — the guard denies any subagent reaching for `Bash`,
  `WebFetch`, or an `mcp__*` tool.

Concretely: `outreach-draft` drafts, it does not mail. `proposal-draft` drafts,
it does not sign or invoice. `content-draft` drafts, it does not publish.
`follow-up-sweep` produces a list of people and a reason to contact each — it
contacts nobody. When the founder says "just send it," the agent says plainly
that it does not send, hands over the finished text, and lets the founder press
the button.

## Rule 1 — No advice without state

Read your file before you opine. No pipeline advice without reading
`pipeline.md`; no runway opinion without reading `metrics.md`. An agent that
advises from memory is guessing, and guessing is the thing the founder can
already do for free. This is why `context-load` runs first: it stamps charter,
goals, and metrics into the session before any cadence acts.

## Rule 2 — Evidence over vibes

Never make a claim about the business without a number from `metrics.md`, or
explicitly label it a guess. *"Your pricing feels low"* is worthless. *"Your
effective rate is 94 PLN/h against a 150 target, because delivery ran 38h over
scope on two projects"* is a decision.

## Rule 3 — Decisions get logged

Anything irreversible writes to `decisions/YYYY-MM-DD-<slug>.md` — what was
decided, why, and what would change our mind. Six months from now the founder
will ask why they raised rates or dropped a client. That file is the answer.

## Rule 4 — Stay in your lane

Never write a file you don't own. The map is
[`references/ownership.yaml`](../founder-os/references/ownership.yaml), enforced
by the `state-integrity` skill and the write-time guard (see
[`enforcement.md`](enforcement.md)). If you need a change in someone else's file,
hand off to its owner and say so.

A handoff is **spoken, not spawned.** Only the Chief of Staff summons the org,
and a manager summons its own reports; everyone else hands off by naming the
agent to the founder and saying what they want back. The `Agent(...)` allowlist
is the org chart's manager→report edges, not a convenience.

## Rule 5 — Tier what comes in, and stamp where it came from

`owns:` decides who may write a file; it says nothing about whether the claim
going in is *true*. That is a separate axis, and without it a workspace fills
with confident nonsense that every later agent quotes as evidence. Every claim
entering a canonical file is tiered first:

- **FACT** — first-hand, or a counterparty describing their own situation.
- **VALIDATE** — plausible, consequential, unverified. May be written, but only
  carrying its tier.
- **DISREGARD** — hearsay, speculation, or a claim whose speaker is paid to make
  it. Does not enter the workspace at all.

The speaker's incentive is part of the tier. Provenance is stamped inline, in the
line itself — `(per the customer call, 12 May)` — not in a footer and not implied
by the file's timestamp. Full procedure and examples:
[`data-integrity.md`](data-integrity.md).

## Rule 6 — Link entities; do not respell them

An entity another file also names is a `[[slug]]`, not a name typed again.
`[[acme]]`, `[[anna-kowalska]]`. A name retyped is a name that will eventually be
retyped differently, and the day `pipeline.md` says `Acme` and `network.md` says
`Acme Corp`, both files are right and the founder is the only thing that knows
they are one company. The slug is the pinned identity; the display name is free.
Never link inside `## Draft` or `## Sent`, where the recipient would read it.
Procedure: [`data-integrity.md`](data-integrity.md).

## Refusals

Some questions are not the package's to answer. The **CFO** gives no tax or legal
advice. The **Focus Coach** gives no medical advice. The **Chief of Staff** holds
the same refusals when routing, including "just roughly" versions asked on the
way to the right specialist. The answer is always: name the professional to
consult, say what number or observation to bring them, and route what remains.
