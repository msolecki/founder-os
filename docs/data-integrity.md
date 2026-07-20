# Data integrity

Ownership decides *who may write* a file. It has no opinion about whether the
claim going in is *true*, or *who it is about*. Those are two more axes, and
without them a workspace fills with confident nonsense that every later agent
quotes as evidence — house rule 2 turned into a laundering machine. Three
mechanisms keep the workspace worth reading: the **ingestion gate**, **entity
linking**, and the **voice / drafts** loop.

## 1. The ingestion gate — tier every claim

Every claim entering a canonical file is tiered first (house rule 5). The full
procedure and worked examples are in
[`references/ingestion-gate.md`](../founder-os/references/ingestion-gate.md); the
skill that runs it is `/ingestion-gate`. Three tiers:

### FACT
Two sources qualify, and only two:
- **First-hand** — you read it in the artifact itself (an invoice, a calendar, a
  sent message, a bank line), not somebody's summary of it.
- **A counterparty describing their own situation** — their budget, timeline,
  constraint, intent. "We can't sign until the new CFO starts" is a fact about
  them.

The test: **could the speaker be wrong about this and still be honest?** If yes,
it is not FACT. Tier the claim *you are making*, not the sentence you heard —
"We'll pay by the 30th" is a fact that they said it and a prediction about the
world on the 30th.

### VALIDATE
Plausible, consequential, unverified. It may enter, but only carrying its tier
plus a validation step: the artifact that would settle it, who gets it, by when.
**A flattering number is guilty until validated** — not because flattery is
usually false, but because nobody will ever chase it, while an unflattering claim
gets tested by the founder's own anxiety within the hour.

### DISREGARD
Does not enter the workspace at all: **hearsay** (reporting a third party's
state), **speculation** (a claim about an unobservable future dressed as the
present), and **paid speech** (a vendor benchmark, a recruiter's "market rate").
It may be true; it was not said in order to be true. Keeping it out *is* the
enforcement — a labelled DISREGARD line gets quoted without its label within two
reads.

### Stamp provenance inline
Provenance goes in the line itself: `(per Anna, buyer at Acme, call, 12 May)` —
not in a footer, not implied by the file's timestamp. A file's mtime tells you
when someone touched the file, which is a different fact from when the claim was
last true. Six weeks later the stamp is what tells you the number is stale.

## 2. Entity linking — `[[slug]]`, not a retyped name

`Anna at Acme` appears in `pipeline.md`, in `network.md` `## Map`, and in
`clients/acme.md`. Until they are linked, those are three strings that happen to
look alike, and nothing can tell you they are one company — or notice when they
stop being spelled the same way. That is not a tidiness problem: the day
`pipeline.md` says `Acme` and `network.md` says `Acme Corp`, both are correct,
both are confident, and two agents advise on two companies forever. Full rule:
[`references/linking.md`](../founder-os/references/linking.md).

**The rule:** every reference to an entity another file also names is a
`[[slug]]`. A slug is lowercase, hyphenated, and resolves to exactly one of:

- **A file**, workspace-relative, without extension or directory: `[[acme]]` →
  `clients/acme.md`; `[[2026-07-15-anna-acme]]` →
  `drafts/outreach/2026-07-15-anna-acme.md`.
- **A row in `network.md` `## Map`**, matched on its `slug` column:
  `[[anna-kowalska]]` → that row. People have no file, so the Map row is their
  definition — which is why the Network Manager owns the identity of every
  person.

Anything else is a broken link, and `founder-os-doctor` reports it.

**What does *not* get a link:**
- A person or company named once, in passing, in a file nobody joins on. A link
  is a claim that two files talk about the same thing; if only one file is
  talking, the brackets are decoration.
- **Anything inside `## Draft` or `## Sent`.** A prospect who receives
  `Hi [[anna-kowalska]]` is receiving evidence they are a row in a database.
- A slug you would have to invent. If the entity has no file and no Map row, name
  it in prose and hand it to the Network Manager — that row is its decision.

**Renaming:** the slug is the identity, so changing it breaks every file pointing
at it. `[[acme]]` does not become `[[acme-corp]]` because the founder started
saying "Acme Corp" — the display name is free, the slug is pinned. A genuine
rename is a workspace-wide edit, not one made on the way past.

## 3. Voice and drafts — write like the founder, or say it can't

Two files and one loop keep everything published under the founder's name
sounding like them.

- **`voice.md`** holds *real samples of the founder's writing* — not adjectives
  about it. "Friendly but professional" describes 90% of business writing and
  constrains nothing; three real emails beat any adjective. Its sections:
  `## Samples`, `## Tells`, `## Never`, `## Register`. If the founder already
  keeps a style guide or a banned-phrases list, `init` offers to import it rather
  than making them teach it twice.
- **`drafts/{outreach,proposals,content}/`** hold `## Draft` (the body), and
  `## Sent` (what actually went out). `## Sent` is the only place the founder's
  own edit to the machine's prose survives the session.
- **The loop:** `voice-capture` reads the diff between `## Draft` and `## Sent` —
  the founder's edits before sending — and folds it back into `voice.md`. That is
  the founder correcting the machine, harvested. `content-draft` will not ship
  under the founder's name until `voice.md` has real samples; it says it can't
  rather than inventing a voice.

## Language: pinned headings, free content

The section headings are **pinned English** — they are the machine contract. But
everything *under* them is the founder's: a Polish founder gets a Polish
workspace under English headings, and no skill translates their pipeline at them.
