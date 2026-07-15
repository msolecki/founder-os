# Founder OS

> The executive team you can't afford yet — strategy, offer, pipeline, delivery, money and focus for a company of one.

![Org Chart](images/org-chart.png)

Every other agent company hires you staff. This one is the org that holds you
accountable.

You are the Founder. These twelve agents are your exec team, and each one owns
exactly one decision you keep postponing.

## Install

```
npx companies.sh add <owner>/founder-os
```

Then run onboarding — twelve agents and an empty workspace is not a product
yet:

```
/founder-os-init
```

## What's inside

| Content | Count |
|---------|-------|
| Agents  | 12    |
| Teams   | 4     |
| Skills  | 47    |
| Cadences | 8    |

## The org

| Agent | Only this agent decides… |
|---|---|
| Chief of Staff | What deserves your attention now, and who handles it |
| Board Member | Whether a plan survives contact with reality |
| Strategist | What bet we make this quarter — and what we kill |
| Positioning Advisor | Exactly who we serve and what we sell them |
| Pipeline Coach | What happens next with each prospect |
| Delivery Lead | Whether we can take this on, and if it's good enough to ship |
| CFO | Whether we can afford it and if it actually makes money |
| Focus Coach | What goes in the calendar — and what comes out |
| Skills Mentor | Which capability to build next, and how |
| Brand Editor | What to publish, and where |
| Network Manager | Who to talk to, and when to follow up |
| Ops Engineer | What to automate vs. tolerate |

Twelve agents only works if each owns a decision no other agent can make. That
was the test every agent had to pass to ship — and the reason there are twelve
of them rather than a hundred and sixty-seven.

## It comes to you

Most tools wait to be opened. Founder OS runs on a schedule: a brief every
weekday morning, and a cadence for every file that rots — the week, the
pipeline, the content plan, the follow-ups, the review, the close, the quarter.

A personal-development tool that only runs when you remember to run it is the
failure mode of every productivity system ever shipped. That's the part this
package refuses to repeat.

## Memory

State lives in a markdown workspace (`FOUNDER_OS_HOME`, default
`./founder-os/`): charter, goals, metrics, offer, pipeline, clients, network,
week, queue, voice — and a decision log that records *why*, not just what. Six
months from now you will want to know why you raised rates or dropped a client.
That's the file that answers.

Every file has exactly one owner. Agents read anything and write only what they
own — that's what makes a twelve-agent org safe to run against shared state.
A validator enforces it at build time, so it's a contract rather than an
intention.

**Work doesn't evaporate.** A brief that says "follow up with Anna" leaves an
item in `queue.md`, not a feeling. It has an id, a bet it serves, and a date —
and if it sits for 21 days it is dropped automatically, with a reason. An item
nobody started in 15 working days was passed over by 15 daily briefs; the queue
just writes down a decision you already made fifteen times. A queue that only
grows is a to-do list, and you already have one of those.

**Nothing is written just because someone said it.** The eight skills that write
down what someone outside told you — pipeline, revenue, client health, win/loss,
ICP, audience, network, profitability — tier the claim before it reaches a file:
fact, validate, or disregard. What a counterparty says about their own situation
is a fact; what you say to win the room is positioning; what someone tells you
about a third party does not get written at all. Their output templates carry the
stamp slot, so provenance lands in the line itself (`per Anna, buyer at Acme,
call, 12 May`) — a file's timestamp tells you when someone touched it, not when
the claim was last true, and those diverge exactly when it matters.

Every other skill does not run the gate, because it does not ingest: a skill
doing arithmetic over files already in the workspace has no speaker to name, and
making it recite a tier anyway would be the ceremony this package exists to
avoid.

**It writes like you, or it says it can't.** `voice.md` holds real samples of
your writing — not adjectives about it. "Friendly but professional" describes
90% of all business writing and constrains nothing; three real emails beat any
adjective. Every draft is checked against it, and your edits before sending are
harvested back, because that's you correcting the machine.

## What it won't do

**It never sends. It never pays.** No email, no post, no invoice, no signature —
whatever the agent, however obvious the send, however explicitly you asked
mid-flow. It drafts; you press the button. If your setup connects a mailbox or
a payment tool, the capability existing is not the permission — that is exactly
when the rule matters. A wrong opinion costs an argument; a sent email costs a
client.

**The CFO gives no tax or legal advice. The Focus Coach gives no medical
advice.** Both will tell you which professional to see and what number or
observation to bring them, so the meeting takes fifteen minutes instead of an
hour.

This is deliberate. A founder OS is trusted because it is opinionated, and that
trust is exactly what makes a confident wrong answer expensive. See
`skills/guardrails/SKILL.md`.

## It has opinions

Every role skill states at least three principles a competent generic advisor
would not say. The section is required and machine-checked; the bar itself was
held by review — no regex reaches "would a generic advisor say this?". Without
them you get Wikipedia advice the moment you step off the script, which is
precisely when you needed an opinion.

A sample of what that means in practice:

> *"Continuing has no invoice. Killing feels like the loss because it comes
> with a date and a number attached, while a bet running at 20% for another
> quarter costs more and never sends a bill."*

> *"Your price is not low because you undervalue your work. It is low because a
> low price is an effective way of not being rejected, and it is working."*

> *"Over 40% of revenue is not a client, it is an employer."*

You are meant to disagree with some of them. That is the point — an argued
position can be improved, a platitude can only be nodded at.

## Extending it

`references/skill-template.md` is the template every skill follows, and
`references/ownership.yaml` is the file-ownership map — both who owns each file
and which sections live inside it. If you add a skill, declare what it writes and
make sure its agent owns that path.

The validator that enforces all of this (`scripts/validate_package.py`) is build
tooling and lives in the source repo alongside the tests, not in the installed
package — clone the repo and run it there before opening a pull request.

## License

MIT
