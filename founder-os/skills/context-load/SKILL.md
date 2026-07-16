---
name: context-load
description: Load charter, goals and metrics with their dates stamped before any cadence runs — the house-rule-1 check that starts every session
---

# Context Load

Agents have amnesia. Every cadence starts cold, and a cold agent that opines
anyway is doing the one thing house rule 1 forbids: guessing, which is a service
the founder can already perform for free.

The dangerous state is not missing context. Missing context is loud — the file
is empty and the agent stops. The dangerous state is **stale context that reads
as fresh**: a runway figure from a close that happened seven weeks ago, quoted
today with full confidence and no date attached. This skill exists to put the
date on the number.

## When to use

At the start of every cadence — daily brief, week plan, weekly review, monthly
close, quarterly planning — and at the start of any session where an agent is
about to make a claim about the business.

Also whenever a session has been running long enough that a number was quoted
earlier in the conversation. Re-read the file. "As we established above" is
memory, and memory is exactly what this package does not trust.

## Inputs

Three files, always, in this order. The order is the point:

1. **`charter.md`** — what this business is. Read first because it tells you
   what to *ignore*. Everything after this is filtered through it.
2. **`goals.md`** — this quarter's bets and their kill conditions. What is
   currently being attempted, and what would end it.
3. **`metrics.md`** — the numbers, and the date they were last true.

Then, and only then, the one file your decision owns.

## Steps

1. **Load the three, in order, with their last-modified dates.** The dates are
   not metadata. They are the confidence interval on everything you are about to
   say.
2. **Stop if `charter.md` is empty.** There is no business described, so there
   is nothing to advise on. Run `founder-os-init`. Do not proceed on the
   assumption that you can infer the business from the other files.
3. **Apply the staleness rule to `metrics.md`:**
   - **≤ 30 days** — quote the numbers plainly, with the date.
   - **> 30 days** — quote them, and label every downstream claim a guess, out
     loud, exactly as house rule 2 requires. Not a hedge. A label.
   - **> 60 days** — say the close is overdue and hand to the **CFO** before
     advising on anything the numbers touch. Advising on nine-week-old runway is
     not caution, it is fiction with a decimal point.
4. **Load your own file.** The one your decision writes to — `pipeline.md` for
   the Pipeline Coach, `clients/` for the Delivery Lead. That is the fourth
   file, and for most cadences it is the last.
5. **Stop loading.** At most one additional file, and only if the founder's
   question is explicitly about it — so two files beyond the three, counting your
   own. This is a rule with a cost attached: an agent holding every file in the
   workspace does not become better informed, it becomes an averager —
   everything is a little bit relevant, nothing outranks anything, and the output
   is a summary of the workspace instead of a decision about it. The founder can
   read their own files. They summoned you to say which one matters today.

   **One skill is exempt, and it is named here so the exemption is not something
   it granted itself.** `triage` (Chief of Staff) may open one file per item, five
   maximum, because its input is five items that each live in a different agent's
   file — a cap of two would make it guess about three of them. Its exemption is
   bounded in `triage` and the bounds are the price of it: **sections, not files**;
   one question per section — *is this real and is it dated?*; and an item that
   needs the whole file to judge is not a triage item at all, it is a session with
   that specialist, so it gets routed rather than read.

   **`daily-brief` (Chief of Staff) is the second exemption, and it is the last
   one.** It reads the three, its own `reviews/daily/`, `queue.md`, `pipeline.md`,
   `clients/` `## Health`, `offer.md` `## ICP` `### Not this`, `metrics.md`
   `## Close` (the receivable lines and the `Proposed:` lines, nothing else), and
   the `Proposed:` line in `content.md` and `network.md`. That is well past the cap and it is
   deliberate, because **the brief is the one cadence whose decision is the
   ranking across books.** Every other cadence answers a question inside one book
   — is this deal real, does this month clear, is this client dying — and for
   those, breadth is how the answer gets averaged into a summary. The brief's
   entire output is *which book matters today*, and it cannot produce that from
   two of them. Denying it the sixth file does not make it disciplined, it makes
   it a pipeline review that runs at 8am.

   The bounds are the price, and they are the same bounds as `triage`'s:
   **sections, not files.** Only `goals.md`, `queue.md` and yesterday's brief are
   read whole. Everything else is one named section, read for one question — is
   anything here rotting, and is anything here proposed. A brief that reads
   `metrics.md` whole and comments on the effective rate has stopped being a brief
   and become the averager this step describes. `daily-brief` states the same
   bounds on its own side; neither file may widen this alone.

   **No other skill has either exemption**, and neither gets extended by analogy
   to any other cadence the Chief of Staff runs. `week-plan`, `weekly-review`,
   `monthly-review` and `triage` beyond its own bounds all live under step 5.
6. **Stamp the context before your first sentence.** The founder sees what you
   read and how old it was, every time, before they read your conclusion.

## Output

No file. One line, first, before anything else:

    Context: charter <date> | goals <quarter>, <N> bets | metrics <date> (<N>d old)<, STALE if >30d>

Then the cadence proceeds.

## Guardrails

Never quote a number without the date it was written. A number without a date is
a claim about the present, and `metrics.md` is a record of the past.

Never carry state across sessions. If the last session's brief is relevant, it is
in `reviews/daily/` — read it from there. An agent that remembers is an agent
that will eventually remember wrong, and it will do so with no file to check it
against.

Never fill a gap from training data or inference. If `goals.md` is empty, the
finding is that there are no goals — hand to the **Strategist**. Do not
reconstruct what the goals probably are from the pipeline. That reconstruction
will be plausible, it will be wrong, and it will be quoted back for a quarter.

This skill loads. It does not write, ever — not even the file the calling agent
owns. That is the cadence's job.
