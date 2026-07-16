# Linking

`Anna at Acme` appears in `pipeline.md`, in `network.md` `## Map`, and in
`clients/acme.md`. Until this file existed those were three strings that happened
to look alike, and nothing in the package could tell you they were one company —
or notice when they stopped being spelled the same way.

That is not a tidiness problem. `follow-up-sweep` reads `network.md` and
`pipeline-review` reads `pipeline.md`, and the day one of them says `Acme` and the
other says `Acme Corp`, both are correct, both are confident, and the founder is
the only thing joining them. Six weeks later `Acme` is a dead deal and `Acme Corp`
is a client being delivered to, and no agent can see it.

## The rule

**Every reference to an entity another file also names is a `[[slug]]`.**

A slug is lowercase, hyphenated, and resolves to exactly one of two things:

- **A file**, workspace-relative, without its extension or directory:
  `[[acme]]` → `clients/acme.md`. `[[2026-07-15-anna-acme]]` →
  `drafts/outreach/2026-07-15-anna-acme.md`.
- **A row in `network.md` `## Map`**, matched on its `slug` column:
  `[[anna-kowalska]]` → the row that carries that slug.

Nothing else. A `[[slug]]` that resolves to neither is a broken link, and
`founder-os-doctor` reports it.

## Why the Map row counts as a target

People have no file. `network.md` is one table with one owner, and a `people/`
directory would be a different package — fifty files, fifty mtimes, and a
`follow-up-sweep` that reads fifty of them to build the table it currently reads
in one. That trade may be worth making one day. It is not this change.

So the row is the definition. `## Map` grows a `slug` column, the slug is the
canonical name of that person, and every other file points at it. The Network
Manager owns the row and therefore owns the identity — which is correct, because
"who is this person" is exactly the decision that agent exists to make.

## What does not get a link

- **A person or company named once, in passing, in a file nobody joins on.** A
  link is a claim that two files are talking about the same thing. If only one
  file is talking, there is nothing to join and the brackets are decoration.
- **Anything inside `## Draft` or `## Sent`.** Those sections hold text the founder
  is about to send or has sent, verbatim. A prospect who receives
  `Hi [[anna-kowalska]]` is receiving evidence that they are a row in a database.
  Provenance goes in `## Provenance`, where the founder is the only reader.
- **A slug you would have to invent.** If the entity has no file and no `## Map`
  row, do not link it and do not create the row on the way past — that row is the
  Network Manager's decision. Name it in prose and hand it over.

## Renaming

The slug is the identity, so changing it breaks every file that points at it.
`[[acme]]` does not become `[[acme-corp]]` because the founder started saying
"Acme Corp" — the display name is free, the slug is pinned. If a slug genuinely
must change, that is a workspace-wide edit and `founder-os-doctor` will report
every link you missed. It is not an edit to make on the way past.
