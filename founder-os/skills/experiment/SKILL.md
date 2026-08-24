---
name: experiment
description: Open a test with a threshold written before the result exists, and close it on its judgment date with a verdict that leaves the file — run when the founder asks how they will know something worked
metadata:
  writes:
    - experiments/
---

# Experiment

`assumption-audit` ends with the load-bearing assumptions ranked by hours to
test, cheapest first. Then the trail stops. Nothing in this workspace records
whether the cheapest test was run, what it showed, or what changed because of
it — so the same assumption is re-audited next quarter, ranked again, and
tested again never.

This file is the missing half. One experiment per file, opened with a number
and a date, closed on that date whatever the data says, and closed *out* of
here — into `decisions/` or into a bet's verdict. An experiment that ends in
`experiments/` is reporting. Reporting is not learning.

## When to use

When `assumption-audit` names the cheapest load-bearing assumption and the
founder is about to test it. That is the intended door and the one the audit
hands to.

Also when the founder asks, in any wording, **"how will I know this is
working?"** — about an offer, a channel, a price, a bet. That question is an
experiment with no threshold yet, and it is the moment the threshold is still
honest.

And on every judgment date. Step 6 is not optional and does not wait for the
founder to remember.

## Inputs

Read first — house rule 1:

- `experiments/` — every open file. The cap, the overdue list, and whether this
  question is already being tested live here and nowhere else.
- `goals.md` `## Bets` — every experiment names one bet or names `none`, and a
  bet's `Kill if:` is often the threshold already written down.
- `metrics.md` — the number the threshold will be read against, and the date it
  was last true. A threshold measured against a source that closes monthly
  cannot have a judgment date on the 12th.
- `decisions/` — whether this was already settled and forgotten.

## Beliefs

- An experiment the founder cannot lose is a demo. If no plausible result would
  stop the thing, the test buys two weeks and the same conviction they walked in
  with — and the honest move is to skip it and commit, which is a cheaper answer
  than the one the experiment was going to give.
- A running experiment is the most respectable available way to not decide. It
  survives every review, it sounds like rigour, and it costs the founder nothing
  to say out loud. The cap of three exists because the fourth one is always the
  one postponing something.
- The threshold has to be a number the founder would be unhappy to hit. Set
  where success is likely, it is not calibration — it is the plan in a lab coat,
  and it will be met, and nothing will have been learned.
- Most uncertainty does not deserve a file, and refusing is this skill's
  commonest correct output. A folder recording every curiosity buries the three
  tests a year that cost something, and a folder the founder cannot trust to be
  short is a folder they stop opening.
- An experiment that reaches its judgment date with no data is not
  inconclusive. It is a measurement of the founder, it came back positive, and
  `not measured` is the most useful verdict this file produces.

## Steps

1. **Refuse it, or take it.** The test: would a plausible result change what the
   founder does within thirty days? Name the action each way — what they do if
   the threshold is met, what they do if it is not. **If both answers are the
   same action, refuse.** Say so plainly, name the thing they were going to do
   anyway, and stop. No file.
2. **State the hypothesis so it can be false.** A population, a number, a
   window: *at least 3 of the next 10 discovery calls will accept the fixed
   sprint price without asking for a custom scope*. "The offer resonates" is a
   mood and does not open a file — `assumption-audit` step 1 is the same
   grammar and this is the same bar.
3. **Write the threshold before the test exists, and write it as one number and
   one date.** Exactly the shape `goals.md` demands of `Kill if:`, for exactly
   the same reason. If the founder cannot name the number now, the experiment is
   not ready — and the reason they cannot is almost always that any result would
   be acceptable, which step 1 already refuses.
4. **Set the judgment date, and set it as a date.** Not "when we have enough
   data". Enough data is a judgement the founder will make on the day they like
   the number. Pick the date from the source: a threshold read off `metrics.md`
   judges after the close that contains it, never mid-month against a partial.
5. **Check the cap. Three open, maximum.** To open a fourth, one of the three
   closes today — met, not met, or `not measured`. That forced close is the
   entire value of the cap, it always arrives with a good reason attached, and
   the reason is always that the fourth question is more interesting than the
   three the founder committed to.
6. **Close on the judgment date, whatever the data says.** Read the source,
   write the number and the date it was read, and set the verdict against the
   threshold as written — never against a threshold amended today:

   - **met** — the number cleared the line.
   - **not met** — it did not.
   - **not measured** — the date arrived and the number does not exist. This is
     a verdict, not a delay. It closes the file.

   An experiment overdue by more than 14 days closes as `not measured`
   automatically. There is no renewal, and step 8 says why.
7. **Send the verdict out of this file.** Closing writes `Handed to:` and it is
   never blank — `decision-log`, `kill-or-continue`, or `none` with a reason.
   See `## Sibling handoffs`. A verdict that stays in `experiments/` has
   informed nobody and changed nothing, and next quarter's audit will rank the
   same assumption again.
8. **Never renew.** No second judgment date, no extension, no "another two
   weeks and the signal will be clearer". A test that needed longer was scoped
   wrong, and the correct repair is to close this one `not measured` and open a
   new file with a new hypothesis — which costs one of the three slots, which is
   the point. An extension costs nothing, and a clock nobody pays for is decor.

## The clocks

| state | cap | clock | when it fires |
|---|---|---|---|
| open | 3 | its own judgment date | closed — met, not met, or `not measured` |
| open past judgment | — | 14 days | closed as `not measured`, no exceptions |
| closed | — | — | permanent. Append-only, never edited |

## Named failure modes

- **The perpetual pilot.** Judgment date moves twice and the experiment becomes
  an activity. Nobody decided to keep it alive; each extension was individually
  reasonable and the founder can still describe it as being tested, eleven
  months in.
- **The threshold that moved.** The threshold was 3 in 10; the result came back
  1 in 10; the file now says the threshold was 1 in 10 and the verdict is met.
  This is why `## Threshold` is written at open and never edited afterwards, and
  why a closed file is append-only. A record that can be corrected only ever
  proves the founder was right.
- **The observation with a filename.** *Let's see how the newsletter does.* No
  number, no date, nothing that could come back badly. It will be closed as a
  success in three months, because anything can be.
- **The orphan verdict.** The experiment closes `not met`, the file is correct
  and complete, and the bet it was testing runs another quarter — because the
  verdict never reached `goals.md`. Step 7 exists for this one specifically.

## Sibling handoffs

The Strategist never opens another role. When a sibling is required, return the
shared `role`, `workflow`, `workspace_id`, `correlation_id`, `handoff`, and
`expected_persistence` request to the main thread and stop the current pass.

When the verdict settles something irreversible — a price the founder is about
to hold, a channel they are about to stop paying for — request the Chief of
Staff's `/decision-log` with `decisions/` in `expected_persistence`. The
carried handoff is the hypothesis, the threshold as written at open, the result
with its source date, and the verdict. Never the founder's conviction; the
threshold is the evidence and the log has a field for exactly it.

When the verdict answers a live bet's kill condition, the Strategist's own
`/kill-or-continue` takes it with `goals.md` and `reviews/quarterly/` in
`expected_persistence`. The main thread closes this pass, opens the new one,
and re-reads the persisted state before the receipt.

`Handed to: none` is legal and needs its reason on the same line — the usual
one is that the verdict confirmed what the workspace already says, and a
decision record of *nothing changed* is the diary `decision-log` refuses to be.

## Output

Write `experiments/YYYY-MM-DD-<slug>.md`, one file per experiment, dated by the
day it opened:

    # <the hypothesis, one sentence, falsifiable>
    Opened: YYYY-MM-DD
    Serves: <bet from goals.md, or "none">
    Status: open
    ## Hypothesis
    <population, number, window — the statement that can come back false>
    ## Threshold
    <observable> <number> by YYYY-MM-DD
    ## Judgment
    Judgment date: YYYY-MM-DD
    Source: <the file or place the number is read from>
    ## Result
    <empty until the judgment date>
    ## Verdict
    <empty until the judgment date>

At close, append to `## Result` and `## Verdict` and flip `Status:` to `closed`.
Change nothing above:

    Status: closed
    ## Result
    <the number, and the date it was read> — read from <source>
    ## Verdict
    not met — <what changes because of this, in one sentence>
    Handed to: kill-or-continue — B1's kill condition is answered

Then give the caller one line, before anything else it writes:

    Experiments: open <n>/3 | judging this week <n> | overdue <n> | closed not-measured this quarter <n>

The last figure is the one worth reading. Two or more `not measured` in a
quarter is not a testing problem and re-scoping the next experiment will not fix
it — the founder is opening tests they were never going to run, and the finding
belongs in `quarterly-planning` rather than here.

## Guardrails

**Never run the test.** The founder runs it — that is their Tuesday, and it is
the same line `assumption-audit` holds. An agent that runs the experiment
becomes accountable for the outcome and stops being able to read the number
honestly.

**Never edit `## Hypothesis` or `## Threshold` after the file is opened.** Not
to clarify, not to fix a typo in the number. If the threshold was wrong, close
the file `not measured` with that as the reason and open a new one. The
append-only rule is the only thing standing between this folder and a record of
uninterrupted success.

**Never renew a judgment date**, and never accept "the signal will be clearer in
two weeks". It will be clearer, and it will also be two weeks later, and the
founder will say the same sentence then.

**Never close without a verdict, and never a verdict without `Handed to:`.**
Both fields refuse to be blank, `none` is a legal value for the second, and a
reason is required either way.

**Never open a fourth.** Not for a cheap one, not for one that "isn't really an
experiment". A cheap test that does not deserve a slot does not deserve a file
— refuse it under step 1.

**Nothing goes out.** House rule 0 holds here exactly as everywhere: an
experiment whose test is *email 20 prospects* produces a draft under
`drafts/outreach/` written by the **Pipeline Coach**, and the founder sends it.
The experiment records the threshold and the result. It never performs the
test's outbound half, and the capability to do so is not the permission.
