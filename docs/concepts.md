---
title: "Concepts"
status: current
owner: Mateusz Solecki
last-verified: 2026-10-25
---

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
eleven other cadences *propose* into it but none of them may write it.

This is enforced by the local `founder-os-state` gateway at the actual write,
with the host hook as defense in depth. See
[`enforcement.md`](enforcement.md).

## 4. It drafts; you send. It never touches money.

The load-bearing rule (house rule 0): **no agent sends and no agent pays.** No
email, no message, no post, no invoice, no transfer, no signature,
no subscription cancelled — regardless of which agent, however obvious the
send, however explicitly you asked mid-flow. The agents draft; you press the
button.

This holds even when the host has a send-capable integration. Packaged roles
have no shell, browser, direct file tool, external MCP, or nested-agent edge;
the public MCP surface is the eight-tool local state gateway. Role subagents
receive six common calls; portfolio-manager alone receives the bounded
`read_portfolio_inputs` call, and only the main thread may open sessions. The capability
existing is not the permission. A wrong opinion costs an argument; a sent email
costs a client.

## 5. It comes to you, on a rhythm.

A personal-development tool that only runs when you remember to run it is the
failure mode of every productivity system ever shipped. Founder OS can run on a
schedule: a brief every weekday morning, and a cadence for every file that rots
— the week, the pipeline, the content plan, the follow-ups, the review, the
close, the quarter. `setup-cadences` installs them through cron, launchd, or a
persistent user systemd timer on *your* machine.
Every cadence also works typed by hand; the rhythm is the point, not the
mechanism.

---

## Glossary

The terms used across these pages are defined in
[`glossary.md`](glossary.md).
