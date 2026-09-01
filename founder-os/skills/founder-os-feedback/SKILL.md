---
name: founder-os-feedback
description: Compose a Founder OS bug report or workflow complaint locally and hand the founder a prefilled GitHub link to send themselves — run right after a workflow does the wrong thing
---

# Founder OS Feedback

A workflow did the wrong thing, and the founder is the only person who will ever
know. There is no telemetry in this package and there is not going to be — the
whole claim in the trust center is that nothing leaves the machine, and an
opt-in exception would still be network code in a product sold on not having
any. So the only path from a bad run to a fix is a person choosing to describe
it, and the friction on that path is where the feedback dies.

This skill removes the friction and none of the choice. It assembles the report
from the session that just happened, prints it, and hands over a URL. **It sends
nothing.** The founder reads what it wrote, clicks if they agree, and posts it
from their own account.

## When to use

Immediately after a workflow does something wrong — while what was expected is
still in the room. A report written on Sunday about Wednesday reconstructs the
expectation from the outcome, and the reconstruction is always more reasonable
than the surprise was.

Also when a workflow is technically correct and still useless. That is the more
valuable report and the one nobody sends, because nothing is broken enough to
feel worth the form.

Not for a question — that is Discussions, and this skill says so and stops.

## Inputs

Read first — house rule 1, and note how little of it there is:

- The session itself: which workflow ran, what the founder expected, what
  happened.
- `.codex-plugin/plugin.json` — the `version` field, through
  `read_reference`, which allows both host manifests for exactly this. From the
  package, never from memory; a version quoted from memory is the version at
  training time.
- Which host is running — Claude Code or Codex.

**No workspace file is read.** Not `metrics.md`, not `pipeline.md`, not the file
the failing workflow was writing. This is the only skill in the package that
opens none of them, and the next section is why.

## Beliefs

- A report that leaks the founder's revenue onto a public issue ends this
  product faster than any bug in it, so this skill never quotes workspace
  contents — not a number, not a client name, not an amount, not a line of a
  draft. Naming the path is the whole permitted vocabulary: `metrics.md`,
  `pipeline.md ## Live`. The founder can paste more if they choose; that is
  their call to make on their own account, and it is not made on their behalf by
  something helpfully assembling context.
- The reports worth having are the boring ones. A crash gets reported anyway
  because it blocks the founder; a workflow that ran cleanly and produced advice
  they ignored gets reported by nobody, and it is the one that says the product
  is wrong rather than broken.
- Prefilling is not sending, and the gap between them is not friction to be
  optimized away. The moment this skill acquires the ability to post, house rule
  0 stops being a property of the package and starts being a setting.
- A feedback form that asks for everything gets filled in by nobody. Five fields,
  three of which this skill answers by itself, is the difference between a report
  and an intention to write one.

## Steps

1. **Sort it first, in one question.** Broken → `bug.yml`. Ran but wrong or
   useless → `workflow-feedback.yml`. Something should exist and does not →
   `idea.yml`. **A question about how to use Founder OS is none of these** — send
   them to Discussions and stop, because a question filed as an issue gets
   answered once and helps one person.
2. **Fill in what the machine knows.** The workflow slug, the version read out
   of `.codex-plugin/plugin.json` with `read_reference`, and the host. Do not
   ask the founder for any of the three. If that read fails, say the version is
   unknown and ask for it — do not supply one from memory.
3. **Ask for the two the machine does not know**, in this order and no others:
   what did you expect it to do, and what did it do instead. Take them in the
   founder's words; do not tidy the expectation into something the outcome makes
   look reasonable.
4. **For a bug, ask them to run `/founder-os-doctor` and paste the report.**
   Doctor output names paths and structural findings, never file contents, which
   is why it is the one artifact this skill will carry. Say that out loud when
   you ask — a founder who does not know what is in it will either paste it
   blind or refuse, and both are the wrong reason.
5. **For an idea, ask the one question the form requires: which decision does
   this improve?** If the answer is that it would be useful, say plainly that
   this is not a decision and offer `/skill-forge` instead — a workflow only one
   business needs belongs in that business's `_local/` overlay, and saying so is
   a better answer than an issue nobody will close.
6. **Scan what you wrote before you print it.** Any digit that came out of the
   founder's business, any proper noun that is a client's, any currency amount:
   strike it and say you struck it. The founder can put it back. This scan is
   the step, not a caution attached to one.
7. **Build the URL by field id, never as one `body`.** These are YAML issue
   forms, and a form ignores `body=` — the canonical prefill key is each field's
   `id`, so the parameters are `workflow`, `host`, `version`, `expected`,
   `actual` and, for a bug, `doctor`. A link built the old way opens an empty
   form and the founder retypes everything, which is the exact friction this
   skill exists to remove. Percent-encode every value.

   **The two dropdowns are best-effort.** `workflow` and `host` prefill by their
   option label where the host accepts it; if the form opens with either unset,
   that is one click and not a bug. Every free-text field is reliable and those
   are the ones carrying the founder's words.
8. **Print the body, then the URL, in that order.** The body first so it is read
   as a draft rather than as a link. Then the URL, and one line saying it opens a
   prefilled form on GitHub and posts nothing until they submit it.

## Output

No file. Nothing is written to the workspace, and nothing is written anywhere
else.

Print the assembled body, then the link — one parameter per form field, all
percent-encoded:

    https://github.com/msolecki/founder-os/issues/new?template=workflow-feedback.yml
      &title=<title>
      &workflow=<slug>&host=<Claude%20Code|Codex|Both>&version=<x.y.z>
      &expected=<what they expected>&actual=<what happened>

`template=bug.yml` takes the same parameters plus `&doctor=<report>`.
`template=idea.yml` takes `&decision=`, `&today=` and `&existing=`.

**There is no `body` parameter here and adding one does nothing.** A YAML issue
form is prefilled by field `id`; `body=` belongs to the old Markdown templates
and is silently dropped, which produces an empty form and a founder who assumes
the skill is broken. An unencoded `#` or `&` truncates a value the same way, and
both failures are discovered after the click rather than before.

Close with exactly one line:

    Opens a prefilled GitHub form. Nothing is sent until you press Submit.

## Guardrails

**Never open the URL, never fetch it, never post it.** House rule 0, and this is
the skill where it is least abstract: the report is written, the destination is
known, and one request would finish the job. That adjacency is the reason the
line is drawn here rather than one step further along. If the host offers a
browser tool, a GitHub MCP, or an authenticated `gh`, that is capability and not
permission.

**Never read a workspace file to enrich the report**, however much better it
would make it. Reproducing a bug against real state is the maintainer's problem
and they can ask; publishing the founder's book to make an issue easier to triage
is not a trade this skill gets to make on their behalf.

**Never quote a number, a client, or an amount.** Paths only. If the report is
incomprehensible without the number, say so in the report — *the effective rate
line was wrong by roughly a factor of ten* — and let the founder decide whether
to add the figure.

**Never file the same report twice.** If the founder has already been handed a
link this session, say so and offer to amend the body rather than producing a
second one.

**Never write to the workspace**, including a note that feedback was given.
There is no owner for that and no file it belongs in, and a skill that invents
one has created state nobody maintains.
