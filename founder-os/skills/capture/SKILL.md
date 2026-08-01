---
name: capture
description: Capture one unstructured thought in the inbox without classifying it — use when the founder needs to remember one thing now and decide what it means later
metadata:
  writes:
    - inbox.md
---

# Capture

This is the lowest-ceremony door into Founder OS: one founder-supplied line goes
into the inbox, and no agent pretends to know what it means yet.

## When to use

Use when the founder has one thought, obligation, or observation to retain but
does not want to stop and route it. Use `triage` when the input is already a
pile, and `queue` only after an obligation has actually been classified.

## Inputs

Resolve exactly one business workspace. Read the full `inbox.md` through
`read_state`; do not read another business file to classify or enrich the line.

Accept one raw command argument. It must be one nonblank logical line of at
most 2048 UTF-8 bytes. Whitespace-only input is blank. Reject NUL, newline, and
carriage return characters before any write. Do not trim or normalize the
accepted argument, and do not split rejected multiline input into several
captures.

## Beliefs

- Capture that asks for a priority is prioritization wearing an intake label;
  the moment belongs to remembering, not deciding.
- A timestamp added by the system is false precision: it records when the tool
  ran, not when the founder first knew the thought mattered.
- An inbox line that becomes a queue item before triage has silently allowed
  arrival order to decide the company.

## Steps

1. Validate the raw argument against the input contract before mutation. On
   rejection, name the violated limit and stop without calling
   `write_owned_state`.
2. Resolve the business. An ambiguous workspace stops with
   `WORKSPACE_UNRESOLVED`; never guess another business and perform no read or
   write there.
3. Use `read_state` to read the full `inbox.md` and retain its observed SHA-256.
   Require its one declared `## Inbox` heading.
4. Build one proposed full document in memory. Preserve every existing byte and
   append exactly one Markdown list item under `## Inbox`: prefix `- `, then the
   founder's accepted bytes unchanged, then the document's line ending. The
   safe list prefix prevents input such as `## Urgent` from becoming a document
   heading.
5. Call `write_owned_state` with the active capability, `inbox.md`, the proposed
   full document, and the observed SHA-256 as the expected hash in the gateway's
   `expected_sha256` field; never omit it on an existing inbox. Apply the shared
   `STALE_WRITE` recovery at most once; every final failure stops without a
   success receipt.
6. After a successful write, re-read the full file. Verify the exact appended
   list item and that the earlier bytes remain intact. Only that re-read may
   produce the workflow result below.

## Output

Return the shared structured workflow result from
`references/orchestration.md`. The decision is exactly:

> Captured in `inbox.md`. The next `/daily-brief` or `/triage` will decide what it becomes.

Evidence names the re-read `inbox.md` and its source date, gaps and human action
are `none`, the return point is the next daily brief or triage, and
`expected_persistence` is only `inbox.md`. The main thread populates `Changed`
from its verified re-read.

## Guardrails

Add no ID, date, priority, owner, classification, bet, or inferred wording.
Never turn the line into a task, advice, or a claim about the business. The
founder's accepted bytes after the safe list marker stay unchanged.

Only `/daily-brief` and `/triage` drain `inbox.md`. Capture appends one item and
does not empty, route, or rewrite another item.

On validation or gateway write failure, the capture attempt leaves the original
inbox unchanged. If the independent post-write re-read fails, persistence is
uncertain: omit the success receipt, do not roll back over an unobserved file,
and show the shared error experience without claiming either outcome.
