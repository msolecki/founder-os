# Contributing

Thanks for looking under the hood. This repo is both the plugin marketplace
and the source repo — the [root README](README.md) explains how the machine
works, and its *Adding a skill* / *Adding an agent* sections are the actual
contribution guide. This file is the short version.

## Reporting something without opening a PR

Most useful feedback is not a pull request, and until now this file did not say
where it goes. It goes to one of three forms in
[`.github/ISSUE_TEMPLATE`](.github/ISSUE_TEMPLATE), and each exists because the
reports it collects are different:

- **[Workflow feedback](https://github.com/msolecki/founder-os/issues/new?template=workflow-feedback.yml)**
  — a workflow ran and did the wrong thing, or the right thing badly. This is
  the report almost nobody sends, because nothing is broken enough to feel worth
  the form, and it is the one that says the product is wrong rather than broken.
- **[Bug](https://github.com/msolecki/founder-os/issues/new?template=bug.yml)** —
  a failed write, a wrong owner, a hook that denies what it should allow. Bring
  the `/founder-os-doctor` output; it reports structure, never file contents.
- **[Idea](https://github.com/msolecki/founder-os/issues/new?template=idea.yml)**
  — one field is required and it is *which decision does this improve*. Without
  it the backlog fills with features that have no decision behind them, which is
  the failure mode this package is built against.

Anything else — a question, a workspace worth showing, an idea that is not a
proposal yet — starts in
[Discussions](https://github.com/msolecki/founder-os/discussions).

`/founder-os-feedback` fills any of the three in from the session that went
wrong and hands you a prefilled link. It sends nothing: you read what it wrote
and post it from your own account. It also never quotes your workspace —
**neither should you.** Paths are useful in a public issue; your revenue, your
clients and your rates are not.

## Before you open a PR

```bash
pip install pyyaml
python3 scripts/validate_package.py founder-os   # 13 agent(s), 56 skill(s), 0 error(s)
python3 scripts/generate_commands.py founder-os  # regenerate COMMANDS.md if frontmatter changed
python3 scripts/smoke_installed_copy.py          # copied local gateway lifecycle
python3 -m unittest discover -s tests            # OK
node --test tests/*.behavior.test.js              # landing behavior
python3 scripts/check_local_links.py              # local docs and anchors
```

CI runs all six on every push and PR, and a red build is a no from the
machine before it is a review comment from a human.

Adding a skill or an agent moves counts that are published in a dozen places.
Do not type the new number from memory — run the validator, read the number it
gives you, and write that one. `check_readme_counts` fails the build with the
exact figure, and the issue-template workflow dropdown is pinned to the skills
directory by `tests/test_feedback_channels.py` for the same reason.

## The rules the validator cannot read

The build checks structure; review holds the bar. The three that matter:

1. **One agent = one decision no other agent can make.** That is the test
   every existing agent had to pass, and the reason there are thirteen rather
   than a hundred and sixty-seven. A new agent that shares a decision with an
   existing one is a merge, not an addition.
2. **Beliefs must be contestable.** Every role skill states at least three
   principles a competent generic advisor would *not* say. The count and
   placement are machine-checked; whether they are actual beliefs rather than
   platitudes with a heading over them is what review is for. See
   `founder-os/references/skill-template.md`.
3. **House rule 0 is not negotiable.** No agent gets a tool that can reach
   the outside world, and no PR that loosens an allowlist will be merged —
   agents draft, the founder sends.
4. **One host-independent role contract.** Claude Code and Codex adapters may
   differ, but the role file, workflow, bounded sibling handoff, role
   capability, ownership rule, and persisted result may not.

## Scope

Bug fixes, sharper beliefs, new checks for the validator or the doctor, and
skills that pass the one-decision test are all welcome. A workflow that only
your business needs is not a PR — it is `/skill-forge` and the local overlay
(`founder-os/references/extensibility.md`), which exists so you never have to
fork to get it. Integrations that
send, pay, or post are out of scope by design — see *What it won't do* in
[`founder-os/README.md`](founder-os/README.md).
