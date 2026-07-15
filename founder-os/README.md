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
| Skills  | 44    |

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

Most tools wait to be opened. Founder OS runs on a schedule: daily brief,
Monday week-plan, Thursday pipeline, Friday review and follow-up sweep, monthly
close, quarterly planning.

A personal-development tool that only runs when you remember to run it is the
failure mode of every productivity system ever shipped. That's the part this
package refuses to repeat.

## Memory

State lives in a markdown workspace (`FOUNDER_OS_HOME`, default
`./founder-os/`): charter, goals, metrics, offer, pipeline, clients, network,
week — and a decision log that records *why*, not just what. Six months from
now you will want to know why you raised rates or dropped a client. That's the
file that answers.

Every file has exactly one owner. Agents read anything and write only what they
own — that's what makes a twelve-agent org safe to run against shared state,
and it's enforced mechanically, not by good intentions.

## What it won't do

The CFO gives no tax or legal advice. The Focus Coach gives no medical advice.
Both will tell you exactly which professional to see and what number or
observation to bring them, so the meeting takes fifteen minutes instead of an
hour.

This is deliberate. A founder OS is trusted because it is opinionated, and that
trust is exactly what makes a confident wrong answer expensive. See
`skills/guardrails/SKILL.md`.

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
