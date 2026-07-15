---
name: state-integrity
description: Resolve every workspace write against the ownership map before making it — refuse and hand off by name when the acting agent is not the owner
---

# State Integrity

Every agent in this company carries this skill. It is house rule 4 — *stay in
your lane* — turned from a preference into a check that runs before the write.

Twelve agents sharing one markdown workspace has exactly one failure mode worth
engineering against, and it is not conflict. It is silence: two agents write the
same file, the second one wins, and nobody notices until the founder acts on a
number that was quietly replaced three weeks ago. There is no merge conflict, no
error, and no way to reconstruct what was true. Single ownership prevents that.
This skill is where single ownership is actually enforced.

## When to use

Before every write to a workspace file. Every one — a new file, an appended
section, a corrected typo in someone else's file.

Not before reads. Reads are always permitted, and an agent that hasn't read the
file has nothing to say anyway (house rule 1).

Also use it the moment the founder asks an agent directly to edit a file it does
not own. *"Just update `metrics.md` while you're in there"* is how this rule
actually gets broken — not by an agent going rogue, but by an agent being
helpful. The founder asking does not make you the owner. It makes the handoff
one sentence long.

## Inputs

- `references/ownership.yaml` — the `owns:` map is the only authority.

Not your agent body, not this skill, not what the map said last session. This
skill deliberately does not restate the map: a copy in prose is a second map,
and second maps go stale silently, which is the exact failure this skill exists
to prevent. Read the file.

## Steps

1. **Resolve the target path against `owns:`.** Directory entries end in `/` and
   match by prefix — `clients/acme.md` resolves to `clients/`,
   `reviews/monthly/2026-07.md` resolves to `reviews/monthly/`. Exact file
   entries match exactly. Longest match wins.
2. **Compare the resolved owner to the agent running right now.** If they match,
   write. Stop here; this is the common case and it costs one lookup.
3. **If no entry matches, refuse.** An unmapped path is not a free path. A file
   nobody owns is a file everybody eventually overwrites — that is how the
   workspace rots back into a folder of notes. Say the path is absent from
   `ownership.yaml`, and that the map changes deliberately, not by whichever
   agent first needed somewhere to put something.
4. **If the owner is another agent, refuse and hand off by name.** State the
   file, its owner, and the change you wanted — concretely enough that the owner
   can act without re-deriving it. A handoff that says "the CFO should look at
   this" is a shrug with extra steps.
5. **Never route around the refusal.** Do not write the content into a file you
   do own and call it a note. Do not paste the intended edit into the founder's
   lap and let them do it manually. Both produce the same divergence single
   ownership exists to prevent, and the second one is worse because it looks
   like cooperation.

## Output

No file. This skill is a gate, and a passing gate is silent.

When it blocks, say exactly this to the founder:

    Blocked: <path> is owned by <owner-agent>.
    I wanted to write: <the concrete change>
    Handing to: <Agent Name> — <what you want back>

## Guardrails

**Owning nothing is a valid state.** For an agent absent from `owns:` this skill
refuses every write, always, and that is correct rather than broken — it advises
the founder and hands to owners. An agent that owns nothing and finds itself
writing something has misread its own role, not this map. Which agents those are
is a question for `ownership.yaml` and not for this file: naming them here would
be the second map this skill just told you not to keep.

**Creating a file is not writing a file.** `founder-os-init` and
`founder-os-doctor` are the only skills that may bring a missing file into
existence across an ownership boundary, and only as an empty stub carrying the
headings `ownership.yaml` `sections:` declares for it. The same two may restore a
section heading that has gone missing from a file that already exists — empty,
and only one the map declares. An absent heading is what makes the owning skill
invent a second spelling for it, and two spellings of one section is this skill's
failure mode wearing a smaller hat: both exist, one gets read, the other is
wallpaper nobody notices. Neither skill may put a line of content into a file its
holder does not own. Scaffolding is lifecycle; content is ownership. No other
skill gets this exemption, and these two do not get it extended by analogy.

**This skill never edits `ownership.yaml`.** An agent that can rewrite the map
that binds it is not bound. Changing ownership is a founder decision, and a
material one — it goes through `decision-log` like any other.

**This applies to agents, not to the founder.** The founder owns everything and
may edit anything. If they hand-edit a file, the owning agent reads what they
wrote and works from it. Do not revert the founder. Do not lecture them about
the map.
