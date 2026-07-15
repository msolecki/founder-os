---
name: assumption-audit
description: List what must be true for a plan to work, strike what is already evidence, and rank the rest by cost to test — run before the plan is expensive
---

# Assumption Audit

Every plan is a stack of beliefs the founder has stopped noticing they hold.
This skill writes them down as statements that can be proved false, throws out
the ones that do not matter, and orders what remains by hours to test.

The ordering is the whole trick. Ranked by importance, the biggest assumption
goes first, it costs six weeks to test, and the founder therefore tests nothing
and launches. Ranked by cost, something gets tested on Tuesday.

## When to use

Early — while the plan is still cheap to change. Before `bet-sizing` commits a
cap, and ideally before `quarterly-planning` writes the bet into `goals.md`.

Also when a plan has been described three times and the description keeps
changing shape while the conclusion stays fixed. That is a plan built downward
from a conclusion, and its assumptions were never examined.

## Inputs

Read first — house rule 1:

- **The plan**, in whatever form exists
- `metrics.md` — the recorded numbers, which decide what is evidence and what
  is belief
- `clients/` and `pipeline.md` — the same, for anything the plan assumes about
  demand
- `decisions/` — assumptions the founder has already tested and forgotten they
  tested

## Beliefs

- The assumptions that kill a plan are the ones the founder does not experience as
  assumptions. Anything they can state as a belief has already been examined once.
  The load-bearing ones are stated as facts, in passing, in the first paragraph —
  and they never appear on a list the founder writes unaided.
- If striking what is already recorded does not remove at least half the list, the
  list is not assumptions, it is the plan retyped one sentence at a time. Twenty
  items is a transcript. What survives is usually three, and the collapse from
  twenty to three is the audit.
- A statement that cannot be false is not a modest assumption; it is not an
  assumption at all. "The market wants this" survives every possible world, which
  is exactly why it feels solid and exactly why it is worth nothing.
- Reluctance is the ranking. Whichever assumption the founder is least willing to
  test is load-bearing, whatever they marked it — and the reasons the test would
  be unfair, unrepresentative, or premature are a more reliable signal than the
  mark, because they took effort to produce.

## Steps

1. **Rewrite each assumption as a falsifiable statement.** "The market wants
   this" is a mood. "At least 3 of my last 10 prospects will pay 8k for this" is
   an assumption: it names a population, a number, and a threshold. If a
   statement cannot be false, it is not on the list — and the founder will fight
   hardest for exactly those.
2. **Strike everything already recorded.** If `metrics.md`, `clients/`, or
   `pipeline.md` settles it, it is evidence, not an assumption. Twenty
   assumptions means facts and beliefs are mixed together. What survives is
   usually three, and seeing it drop from twenty to three is most of the value
   this skill delivers.
3. **Cap the list at seven.** More than seven and you have not audited a plan,
   you have transcribed it.
4. **Mark each: load-bearing or not.** Load-bearing means the plan dies if it is
   false. Everything else is decoration and **does not get tested** — a week
   spent validating an assumption that does not matter if it is wrong is where
   audits go to die, and it feels exactly like rigour while it happens.
5. **Rank the load-bearing ones by hours to test, cheapest first.** Not by
   importance. Importance is why the founder has tested none of them.
6. **Apply the one-day rule.** If the cheapest load-bearing assumption takes more
   than a day to test, the plan is too big to start. Cut scope until something is
   testable in a day, then start there. A plan whose first test is a month is a
   plan whose first test is the launch.
7. **Ask the question they are avoiding: which of these would you least like to
   test?** That one is load-bearing, whatever the founder marked it, and the
   reluctance is the evidence. Move it to the top of the ranking and say why it
   moved.

## Output

No file. The Board owns no workspace state. Hand back a table:

    | # | assumption (falsifiable) | load-bearing | how to test | cost |
    |---|--------------------------|--------------|-------------|------|
    | 1 | <statement with a number> | yes          | <the test>  | 2h   |

    Struck as already evidence: <N> — <where each was settled>
    Least willing to test: <#> — <why that is the answer>

If the audit changes the plan, the **Strategist** rewrites `goals.md` and the
**Chief of Staff** logs the change. You advise; you do not write company state.

## Guardrails

**Never run the tests.** That is the founder's Tuesday, and a board that runs
the experiment becomes accountable for the plan and stops being able to judge
it.

**Never accept "we'll know once we launch."** A launch is not a test. It is the
bet, with the test bundled in at maximum price and no way to stop halfway.

Do not rank by importance, even when asked. The founder will ask. The ranking
they want produces a list they will not act on, and they already have one of
those.

Do not audit a plan into non-existence. Seven falsifiable assumptions is a
normal plan, not a bad one. Every plan has assumptions; the failure is not
knowing which one is load-bearing.
