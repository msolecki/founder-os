---
name: audience-research
description: Collect what the ICP actually says about their problem, verbatim and sourced — run before a content plan, and whenever the founder is about to write about a topic instead of a question
metadata:
  writes:
    - content.md
---

# Audience Research

Research that produces topics is useless. "They care about scalability" is a
topic; it cannot be written from, argued with, or headlined. "We rewrote it
twice and I'm not doing that again" is a sentence a real person said, and it is
the piece.

So this skill collects sentences, verbatim, with a source and a date. A
paraphrase is the founder's words wearing the audience's clothes — and the
founder's words are the problem, since they are the reason prospects say "I
didn't really understand what you do".

## When to use

Before `content-plan`, and whenever the plan starts filling with topics. Also
when the founder is about to open a keyword tool, which is a distant fourth
source and the only one that never argues back.

## Inputs

Read first, in order — house rule 1. The ranking is the method:

1. **`pipeline.md`** — what prospects actually asked on calls, and the objection
   the founder answers every single time. This is the best data in the company
   and it is already in the workspace, unread.
2. **`clients/`** — what buyers said before they bought, and what they complained
   about after
3. **Public writing by ICP-fitting people** — their posts, their forum threads,
   and their job ads. Job ads are the most underrated source in existence: the
   ICP describes their own pain, publicly, in their own words, with a budget
   attached, in a document written to be read.
4. **Keyword tools** — last, and only to check volume on a phrase you already
   heard a human say.

- `offer.md` — the ICP. A quote from someone outside it is noise, and it is
  attractive noise, because there is much more of it.
- `ingestion-gate` — every line this skill writes is a sentence a person said,
  so the gate is not an extra step here, it is the ranking above restated as a
  rule. Source 3 is where it bites: a public post is the ICP describing their own
  situation, which is FACT, right up until it is a vendor describing a market,
  which is paid speech and does not enter.

## Beliefs

- A survey is a machine for converting the founder's assumptions into numbers.
  Ask a person what they want and they report what a reasonable person would
  want; ask what already happened to them and they cannot help being specific.
- Nobody has an opinion about your category until something is broken. What an
  ICP-fitting person says while nothing is wrong is entertainment and forecasts
  nothing — which is why a job ad, written under pressure with a budget
  attached, outranks everything they have ever posted about the industry.
- The founder's fluency in their own field is a liability. Jargon is not a list
  of technical words; it is any word that has stopped being confusing to you,
  which makes it structurally invisible from the inside and is exactly why the
  founder is certain their message is already clear.

## Steps

1. **Mine the calls first.** Go through `pipeline.md` and write down what
   prospects asked, in their words. If the founder did not record the questions,
   that is finding number one and it is worth more than this month's plan.
2. **Collect ten verbatim quotes minimum.** Under ten, say the sample is too
   small and label every conclusion a guess (house rule 2). Four quotes and a
   theory is not research; it is the founder's existing opinion with citations
   attached.
3. **Keep the exact words.** Including the ugly phrasing, the wrong terminology,
   and the swearing. The founder's instinct is to tidy the quote into
   professional language, and the tidying deletes the only thing that made it
   useful.
4. **Count the repeats.** Anything said three or more times is not an objection
   — it is the headline of the next piece. Anything the founder answers on every
   call is a piece that should have been published a year ago, and the fact that
   it hasn't been is costing them the same twenty minutes per call, forever.
5. **Build the translation table.** The founder's word on the left, their word
   on the right. Every founder has a vocabulary their buyers do not use; the
   mismatch is invisible from the inside, because the founder's words feel
   precise to the founder.
6. **Ask the question they are avoiding: what is the sentence you say on every
   sales call to explain what you do — and why has it never been published?**
   That sentence has been A/B tested against real buyers dozens of times. It is
   the best-performing content the company owns and it exists only as speech.
7. **Escalate the pattern.** If the repeated objection is "I don't understand
   what you do", that is not a content problem you can research your way out of.
   Hand to the **Positioning Advisor**.

## Named failure modes

- **The persona.** A composite buyer with a name, a photo, and invented
  preferences. It is fiction, every decision downstream inherits the fiction, and
  nobody ever revisits it because it is so pleasant to have.
- **The paraphrase drift.** Quotes lightly cleaned up, then cleaned up again next
  quarter, until the "audience research" is the founder talking to themselves in
  someone else's font.

## Output

Write to `content.md`, replacing `## Audience`:

    ## Audience — updated YYYY-MM-DD
    Sample: <n> quotes from <n> people (min 10 — below that, GUESS)

    ### What they say — verbatim
    - "<exact quote, ugly phrasing intact>" (per <role, ICP-fitting company>,
      <channel>, YYYY-MM-DD)

    ### Repeats — said 3+ times
    - "<the question>" — heard <n>× (per <role> <date>; <role> <date>; <role> <date>)
      → planned as <piece> | handed to Positioning Advisor

    ### The sentence that works on calls
    "<the founder's own spoken explanation>" — published: <yes | NO>
    (per the founder, <channel>, YYYY-MM-DD)

    ### Translation table
    | founder says | they say | first heard from | when |
    |--------------|----------|------------------|------|

Every row in this file is a stamp with a sentence attached — that is not
ceremony, it is the skill. **`Repeats` names all three speakers and all three
dates, not just the count.** `heard 3×` is one integer standing in for three
tiers, and the whole argument of step 4 is that three is a pattern: three people
is a pattern, one person on three calls is a customer with a bugbear, and the
integer cannot tell them apart. If the three dates are all one week, that is not a
pattern either — it is a news cycle.

The translation table gains `first heard from` and `when` for the same reason: a
buyer vocabulary from 2023 is how a founder ends up carefully translating into
words nobody uses any more.

**Never invent a quote and never invent a person.** Not as an illustration, not
as a placeholder, not "roughly what they'd say". A fabricated quote is
indistinguishable from a real one in the file, and it will be published as
evidence within a month.

Never paraphrase into the quote block. If you do not have the exact words, you
have a note — file it as a note.

Never publish a quote from a private call without the founder confirming
permission. Public writing is public; a sales call is not, and that distinction
may also be a contract question. See `guardrails`.

If `pipeline.md` is thin, say the sample is too small rather than filling the
gap from what similar companies say. The gap is the finding: the founder has not
spoken to enough of their ICP, and no amount of desk research substitutes for
that.
