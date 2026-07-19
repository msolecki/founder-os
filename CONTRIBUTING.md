# Contributing

Thanks for looking under the hood. This repo is both the plugin marketplace
and the source repo — the [root README](README.md) explains how the machine
works, and its *Adding a skill* / *Adding an agent* sections are the actual
contribution guide. This file is the short version.

## Before you open a PR

```bash
pip install pyyaml
python3 scripts/validate_package.py founder-os   # 13 agent(s), 49 skill(s), 0 error(s)
python3 scripts/generate_commands.py founder-os  # regenerate COMMANDS.md if frontmatter changed
python3 -m unittest discover -s tests            # OK
```

CI runs all three on every push and PR, and a red build is a no from the
machine before it is a review comment from a human.

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

## Scope

Bug fixes, sharper beliefs, new checks for the validator or the doctor, and
skills that pass the one-decision test are all welcome. Integrations that
send, pay, or post are out of scope by design — see *What it won't do* in
[`founder-os/README.md`](founder-os/README.md).
