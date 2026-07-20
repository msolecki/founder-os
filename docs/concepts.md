# Concepts

The whole package rests on a small set of ideas. Understand these five and the
rest is detail.

## 1. You are the CEO. The agents are your exec team.

Most AI setups hire you staff to do work. Founder OS is the org that holds you
accountable for decisions. There are thirteen agents, and each one owns exactly
**one decision you keep postponing** — not a topic, a decision. The Strategist
does not "help with strategy"; it decides *what bet the company makes this
quarter and what it kills*. The CFO does not "do finance"; it decides *whether
the company can afford something and whether it actually makes money*.

Thirteen agents only works because each owns a decision no other agent can make.
That was the test every agent had to pass to ship, and the reason there are
thirteen rather than a hundred and sixty-seven. A new agent that shares a
decision with an existing one is a merge, not an addition.

The agents are **role definitions, invoked when needed** — not thirteen
autonomous processes running all day. A command invokes the role that owns its
decision; a scheduled cadence invokes one at its configured time.

## 2. State lives in Markdown files, not in a chat.

Agents do not share a conversation. They share an explicit **workspace** of
Markdown files (`FOUNDER_OS_HOME`, default `./founder-os/`): `charter.md`,
`goals.md`, `metrics.md`, `pipeline.md`, `queue.md`, and so on. Every claim,
commitment, and decision is a line in a file with a heading over it, not a
message in scrollback that dies when the session closes.

This is why work does not evaporate. A brief that says "follow up with Anna"
leaves an item in `queue.md` with an id, a bet it serves, and a date — not a
feeling. Six months from now, `decisions/` can tell you *why* you raised rates
or dropped a client, because the reason was written down when it was still the
reason.

**The workspace is the entire data boundary.** Founder OS knows only what is in
its files or supplied in the current session. It does not silently read your
calendar, CRM, inbox, bank, or accounting tool. If a fact is not in the
workspace or the session, the agents do not know it.

## 3. Every file has exactly one owner.

Agents **read anything and write only what they own.** The map is
[`references/ownership.yaml`](../founder-os/references/ownership.yaml), and it is
the only map — if a file's contents and the map disagree, the map wins. The CFO
owns `metrics.md`; nobody else writes it. The Chief of Staff owns `queue.md`;
eight other cadences *propose* into it but none of them may write it.

This is enforced at write time by a hook, not just requested in prose. See
[`enforcement.md`](enforcement.md).

## 4. It drafts; you send. It never touches money.

The load-bearing rule (house rule 0): **no agent sends and no agent pays.** No
email, no message, no post, no invoice, no transfer, no signature — regardless
of which agent, however obvious the send, however explicitly you asked mid-flow.
The agents draft; you press the button.

This holds even when the tooling would allow a send. No packaged agent has a
shell, a browser, or an MCP tool — their allowlists are file tools plus, for
managers, the `Agent(...)` edges of the org chart. The capability existing is
not the permission. A wrong opinion costs an argument; a sent email costs a
client.

## 5. It comes to you, on a rhythm.

A personal-development tool that only runs when you remember to run it is the
failure mode of every productivity system ever shipped. Founder OS can run on a
schedule: a brief every weekday morning, and a cadence for every file that rots
— the week, the pipeline, the content plan, the follow-ups, the review, the
close, the quarter. `setup-cadences` writes those as cron jobs on *your* machine.
Every cadence also works typed by hand; the rhythm is the point, not the
mechanism.

---

## Glossary

**Agent** — one of the 13 role definitions in
[`founder-os/agents/`](../founder-os/agents/). Each owns one decision, a set of
skills, a tool allowlist, and (for most) a set of workspace files.

**Skill** — a workflow in `founder-os/skills/<name>/SKILL.md`, invoked as a slash
command `/<name>`. There are 49. A *role skill* belongs to one agent; a *system
skill* is cross-cutting; a *standalone skill* is run directly by the founder.

**Cadence** — one of the 10 skills that `setup-cadences` can schedule to run on
cron. Every cadence is also just a normal skill you can type by hand.

**Workspace** — the directory of Markdown state, `FOUNDER_OS_HOME` (default
`./founder-os/`). One per business.

**House rules** — the seven rules in
[`references/house-rules.md`](../founder-os/references/house-rules.md) that every
agent obeys. Rule 0 (never outbound, never money) is the one that matters most.

**Ownership map** — [`references/ownership.yaml`](../founder-os/references/ownership.yaml):
who may write each file (`owns:`) and what headings live inside it (`sections:`).

**The guard / the hook** — `hooks/ownership-guard.py`, the `PreToolUse` hook that
checks each subagent write against the ownership map and blocks outbound tools.

**Provenance** — the inline stamp on a claim that came from outside, e.g.
`(per Anna, buyer at Acme, call, 12 May)`. A file's timestamp says when it was
touched, not when a claim was last true.

**Tier** — the FACT / VALIDATE / DISREGARD label put on every claim entering a
file. See [`data-integrity.md`](data-integrity.md).

**`[[slug]]`** — an entity link. A reference to an entity that another file also
names is a `[[slug]]`, not a retyped name. See
[`data-integrity.md`](data-integrity.md).

**Portfolio / registry** — multi-business machinery: `~/.founder-os/businesses.yaml`
names the businesses, and a portfolio workspace holds `portfolio.md`, the one
decision that ranks between businesses. See [`multi-business.md`](multi-business.md).

**Fail-open** — the guard's posture: any unknown (no map, no PyYAML, unparseable
input) results in *allow*, not deny. A guard that blocks a founder's own work
because it lost its config gets uninstalled that afternoon and then protects
nobody.
