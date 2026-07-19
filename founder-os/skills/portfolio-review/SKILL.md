---
name: portfolio-review
description: Rank the businesses against each other, set this week's split of the founder's hours and cash, and name what the split is starving — the one cadence that crosses workspace boundaries
metadata:
  writes:
    - portfolio.md
---

# Portfolio Review

Every cadence in this package answers a question inside one business. This is
the one that answers the question between them: the founder has one calendar
and N companies, and the split is a decision whether or not anyone makes it.
Unmade, it is still made — by whichever business had the loudest Tuesday — and
the record of it is nowhere. This skill makes it on purpose, weekly, with a
number, and writes it where next week can read it.

## When to use

Monday morning, before any business's `week-plan` runs — the split is that
plan's input, not its output. Also whenever a new business enters the registry,
one is paused, or the founder says "I don't know which business to work on" —
which is this question wearing plain clothes.

On a single-business install: say in one line that a portfolio of one has
nothing to allocate, and stop. Do not produce a review of one business ranked
against nothing; that file already exists and it is called `reviews/weekly/`.

## Inputs

- `~/.founder-os/businesses.yaml` — the registry: which businesses exist,
  which are active. If it is missing or lists one business, stop (see above).
- `portfolio.md` — your own file: last week's split, last review's verdict.
- Per active business, exactly two reads, **sections not files**:
  `goals.md` `## Bets` (what is being attempted and its kill conditions) and
  `metrics.md` `## Close` and `## Runway` (what the money says, and when it was
  last true). This is the cross-book exemption `context-load` step 5 grants
  period reviews: the licence is this list, fixed in the package, never widened
  in the moment. A portfolio review that reads a business's `pipeline.md` has
  started re-running that business's cadences from the wrong chair.

## Beliefs

- **An unallocated week is an allocation — to whoever shouted last.** The split
  happens every week whether it is decided or not; the only choice is whether
  there is a record of it and a date on it. "I'll see what each week needs" is
  not flexibility, it is the loudest business writing your calendar.
- **The starving business never complains in its own files.** Its pipeline
  grades on its own curve, its weekly review compares it to its own last week,
  and every number it holds looks fine at four hours a week. Starvation is only
  visible from the chair that sees both books — which is why no per-business
  agent ever catches it and no per-business file ever records it.
- **Two businesses at 50/50 is usually one decision postponed.** An even split
  is what "I haven't chosen" looks like when it is written down. Sometimes it is
  right — two genuinely independent engines — but it is guilty until the
  arithmetic proves it, because it is also exactly what a founder writes to
  avoid the kill-or-continue question one of the businesses is due.
- **Runway is portfolio-level even when the books are separate.** The founder
  eats from one fridge. A business with eight months of runway subsidising a
  founder whose other business has three weeks of it is not two runways, it is
  one, and only this file can say the real number.

## Steps

1. **Load the registry, then `portfolio.md`.** If the registry lists one active
   business, stop per *When to use*. Stamp what you read and how old it was —
   `context-load` rules apply across workspaces exactly as within one.
2. **Read each active business: `goals.md` `## Bets`, `metrics.md` `## Close`
   and `## Runway`.** With dates. A business whose close is more than 60 days
   old gets ranked on a guess, and the review says so in the line that ranks it
   — that staleness is itself a starvation signal, because a business nobody
   closes is a business nobody is running.
3. **Do the hours arithmetic first.** Founder's workable hours this week
   (from them, or last review's number carried with its date) versus the sum of
   what the split promised last week. If the promises exceed the hours, the
   review's first sentence is that gap, in hours, before any ranking — a split
   of hours that do not exist is fiction with a ratio in it.
4. **Set the split.** Hours per business, cash moves if any, one line of *why*
   per business quoting that business's own number. Replace `## Allocation`
   with the new split, dated. The founder can overrule it in a sentence — but
   now they are overruling a written number, not drifting from an unwritten one.
5. **Name what the split starves.** Every split underfeeds something; the
   honest review says which business, what number shows it, and what would have
   to be true for the split to change. Replace `## Starving`. If a business has
   been in `## Starving` for three consecutive reviews, the finding is no longer
   an allocation finding — hand it to that business's **Strategist** as
   `kill-or-continue` evidence, by name, and say so in the review.
6. **Write the verdict.** Replace `## Review`: date, the one-line split, the
   starvation call, and anything handed off. Update `## Businesses` only if the
   registry changed — it is the map, not the commentary.

## Output

`portfolio.md` in the portfolio workspace, exactly four sections per
`ownership.yaml`: `## Businesses` (the map — slug, status, one line each),
`## Allocation` (this week's split, dated, one *why* line per business),
`## Starving` (the underfed business, the number, the change condition), and
`## Review` (dated verdict). On screen: the split and the starvation call, two
or three lines — the founder decides in the calendar, not in this file.

## Guardrails

Never write inside a business workspace. Your entire authority comes from
owning none of the books you rank — the first cross-boundary write ends it.
`portfolio.md` is the only file you touch, and it lives outside every business.

Never rank on feel. Every comparative claim quotes each business's own
`metrics.md` with its date, or is labelled a guess out loud — house rule 2,
across all books at once.

Never answer the kill question. "Starving for three reviews" is the strongest
sentence this skill may say about a business's future; killing it is that
business's Strategist's decision, with this file as evidence. A portfolio
review that closes businesses is a Strategist with no kill conditions and
worse context.

No investment, tax or legal advice. Splitting the founder's own hours is an
operating call; valuing a business, selling one, or moving money between legal
entities is a professional's — name which professional and what number to
bring them.
