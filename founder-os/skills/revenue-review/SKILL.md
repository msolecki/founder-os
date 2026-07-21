---
name: revenue-review
description: Close the month on booked, collected and effective rate — run on the first of the month, fired by cron if the founder ran /setup-cadences
metadata:
  writes:
    - metrics.md
---

# Revenue Review

The monthly close. One job: make the number true before anybody builds a plan on
it. A founder with a record month and an empty bank account has not had a record
month — they have had a record month of paperwork.

## When to use

The first of the month, covering the month just ended — the cron line fires on
the calendar 1st, weekend or not, and a close does not mind running on a Saturday. Triggered
by cron on the 1st if the founder ran `/setup-cadences`; otherwise `/revenue-review`, by hand. Also before any decision that spends the
month's revenue: a contractor, a tool, a holiday.

A block labeled `Close type: activation-baseline` is not a prior monthly close
and never settles a recurring review. On the first real reporting run after
activation, use the recurring path below for the month that actually ended and
replace the baseline with `Close type: monthly-close` using that month's source
artifacts.

## First-run branch

Use this branch only when `/founder-os-init` invokes the skill and there is no
prior monthly close. This is a dated activation baseline, not a reconstructed
month. Every line names its source as founder onboarding on `YYYY-MM-DD` or as
arithmetic over supplied values.

| Input state | Persisted value | Required action |
|---|---|---|
| `supplied or computable` | A value supplied for the stated window, or arithmetic over those supplied values. | Write only supplied or computable values, label the window, date `YYYY-MM-DD`, name the source, state this is not a monthly close, and make no monthly-review handoff. |
| `collected unknown` | `Collected: UNKNOWN` and `Monthly average: UNKNOWN` | Never infer collected cash from booked revenue or pipeline; ask the Chief of Staff to queue the missing bank evidence. |
| `booked unknown` | `Booked: UNKNOWN` | Never zero-fill booked revenue; ask the Chief of Staff to queue the missing close input. |
| `hours unknown` | `Hours worked: UNKNOWN` and `Effective rate: UNKNOWN` | Never infer hours or rate from revenue, proposals or a quoted rate. |
| `receivables unknown` | `Receivables: UNKNOWN` | Never zero-fill receivables; ask the Chief of Staff to queue the missing invoice evidence. |
| `cash on hand unknown` | `Cash on hand: UNKNOWN` | Keep cash unknown and hand the blocking input to the Chief of Staff for the queue. |

Replace `metrics.md` `## Close` with this first-run block:

    ## Close — YYYY-MM
    Close type: activation-baseline
    Baseline: first run on YYYY-MM-DD; not a monthly close
    Source: founder onboarding, YYYY-MM-DD
    Collection window: <supplied dates, or last three months as stated>
    Booked: <supplied/computable amount, or UNKNOWN>
    Collected, supplied window: <amount, or UNKNOWN>
    Collected, monthly average: <computed amount, or UNKNOWN>  (not a monthly close)
    Receivables: <invoice-backed lines, or UNKNOWN — never 0 by absence>
    Past terms: <computed from supplied invoice lines, or UNKNOWN>
    Hours worked: <supplied total for the same window, or UNKNOWN>
    Effective rate: <collected divided by same-window hours, or UNKNOWN>
    Largest client: <computed from supplied collection lines, or UNKNOWN>
    Cash on hand: <supplied amount, or UNKNOWN>  (before any tax reserve)
    Proposed: <missing input and evidence needed> — bet: none | none
    Handed to: Chief of Staff for queue intake only; no monthly-review handoff

Do not derive booked revenue or receivables from collected cash. Do not turn an
absent pipeline, invoice list or hours ledger into zero. The Chief of Staff
chooses queue ids and dates; this skill only names each missing fact and the
evidence that would settle it. Once a real reporting month exists, leave this
branch and use the recurring Steps and Output below.

## Inputs

Read first, in order — house rule 1:

- `metrics.md` — last month's close. What did the founder say was coming in?
- `clients/` — hours actually worked per engagement, including the unbilled ones
  `delivery-retro` recovered
- `pipeline.md` — what closed this month, and when the cash for it actually lands
- `ingestion-gate` — a bank credit is first-hand and needs no gate. Everything
  else here arrived in a sentence: "we'll pay by the 30th", the founder's
  recollection of a figure, a client's explanation for the delay. The gate's
  first named failure mode is the promise written as a receivable, in this file,
  by this skill. Run it before every expected-payment line.

## Beliefs

- **A record month is a warning until proven otherwise.** Revenue arriving in a
  spike was delivered in a spike, and the hours that produced it were taken from
  the weeks that would have sold the next quarter. Read a great month as a hole
  sixty days out and check `pipeline.md` before celebrating.
- **A company of one dies of a fortnight, not of a year.** Timing kills before
  volume does: there is no credit line, no finance function and nobody who
  notices before the founder does. A profitable month with the cash landing
  three weeks late is a worse month than a smaller one that cleared.
- **The friendliest client is the cheapest source of credit in the business, and
  they never asked to be.** Warm invoices get chased last, because chasing
  someone pleasant costs the founder something that chasing a stranger does not.
  Age the receivables before looking at the names, or the ageing gets edited by
  affection.
- **A client who pays late is not short of money — they are short of a reason to
  pay you first.** Payment order is a ranking of suppliers, and the founder is
  ranked in it every month whether or not they ever look at the result.

## Steps

1. **Split booked from collected, before anything else.** Invoiced is not
   revenue; it is a hope with a due date on it. Report both numbers, and never
   let the larger one stand alone in a sentence — the founder will remember only
   that one.
2. **Age the receivables per client.** Days outstanding against terms. **If more
   than 30% of the month's booked revenue is past terms, the month has not
   happened yet.** Say exactly that, and stop the founder spending it. It is the
   single most useful sentence this skill produces, and the least welcome.
3. **Compute the effective rate.** Collected revenue divided by *every* hour that
   touched the work — delivery, sales, revisions, account admin. Not the invoiced
   rate: the invoiced rate is a number the founder made up in a proposal, and the
   effective rate is what actually happened to them.
4. **Compare to target and to last month.** One month is a data point, three is a
   trend, and the trend is the finding. **A rate falling while revenue rises means
   the founder is buying revenue with their own time** — that is the report, not
   the growth.
5. **Name the concentration.** What share of collected revenue came from the
   largest client? **Over 40% is not a client, it is an employer** — one who can
   fire the founder without notice, severance, or a conversation. Report the
   number every single month; it creeps, and it creeps in good months.
6. **Hand off the meaning.** You close the month; you do not narrate it. Write the
   numbers to `metrics.md`, then hand to the **Chief of Staff**, who owns
   `reviews/monthly/` and writes what it means. Say the handoff out loud so it
   happens.
7. **Propose the chases in the same handoff.** `metrics.md` holds the ageing —
   *past terms: 12k across two clients, oldest 47 days* — and an ageing is a
   number, not an obligation. Nobody in this company owns *chase the 47-day
   invoice from X*: it is not a deal, so it is not the Pipeline Coach's; it is not
   a relationship, so it is not the Network Manager's; and this file records that
   it is late without anyone ever being asked to fix it. That is precisely why it
   is 47 days old, and it is the class `queue.md` exists for.

   One item per client past terms, with `bet: none` where it serves no bet — an
   overdue invoice serves no bet and still has to be paid. **If more than three
   clients are past terms, do not propose four items.** Four invoice chases is not
   a queue, it is step 2's finding wearing ids: the month has not happened yet,
   and the founder has a collections problem that fifteen slots and a 21-day clock
   will not solve one chase at a time.

   Hand them to the **Chief of Staff**. You do not write `queue.md` — what
   deserves attention is decided across every cadence, and this review only sees
   money. Propose; do not append. And do not close one: a chase is a send, the
   founder sends, and this skill cannot know whether it went.

## Output

Replace the `## Close — YYYY-MM` block in `metrics.md`:

    ## Close — YYYY-MM
    Close type: monthly-close
    Booked: <amount>
    Collected: <amount>  (<n>% of booked)
    Receivables — one line per invoice, never rolled up before it is stamped:
    - <client> — <amount> — invoiced YYYY-MM-DD — terms <n>d — <n> days past —
      expected YYYY-MM-DD [VALIDATE] (per <person, role at client>, <channel>,
      YYYY-MM-DD — validate: bank credit, CFO, by YYYY-MM-DD)
    - <client> — <amount> — invoiced YYYY-MM-DD — terms <n>d — <n> days past —
      no date given, nobody asked
    Past terms: <amount> across <n> clients — oldest <n> days
      (sum of the lines above; carries the weakest tier among them)
    Hours worked: <n>  (delivery <n> / sales <n> / unbilled <n>)
    Effective rate: <amount>/h vs target <amount>/h  (prev month <amount>/h)
    Largest client: <n>% of collected
    Cash on hand: <amount>  (before any tax reserve)
    Proposed: chase <client> — <n> days past terms — bet: none | none
    Proposed: write the monthly review for <YYYY-MM> — bet: none
    Handed to: Chief of Staff for reviews/monthly/

**`Proposed:` is how step 7's handoff survives the 1st of the month at 09:00 with
nobody in the room.** This cadence fires on a schedule and the Chief of Staff is
not there to take the handoff, so it goes in the line, in the file you own, and
the next `daily-brief` drains it. One line per client past terms, up to three;
`none` written explicitly when there is nothing, because an absent line and a
forgetful cadence look identical to the brief.

The second `Proposed:` line is how `monthly-review` ever runs. Its trigger is
"after the close lands", the close lands at 09:00 on the 1st with nobody in the
room, and `Handed to:` is a fact, not an obligation — nothing drains it. The
line makes the review an item the next brief must take or refuse; refusing it
is allowed and recorded, which is the difference between a skipped ritual and a
silently dead one.

`Booked`, `Collected`, `Hours worked`, `Effective rate`, `Largest client` and
`Cash on hand` are computed from invoices, `clients/` and the bank, and carry no
stamp because there is no speaker — they are arithmetic over artifacts, which is
the case `ingestion-gate` explicitly exempts.

**The receivable lines are the exception, and they are why the ageing is a list
before it is a total.** Each one is a promise somebody made in a sentence, and
each one is a different tier: an invoice with a signed PO behind it and an
invoice with "we'll sort it next week" behind it are not the same object.
`Past terms: 18k across 3 clients` is one integer that looks computed and is not
— it is three tiers averaged into a number, which is the laundering
`ingestion-gate` names outright: *averaging does not launder; it hides the tier
inside a number that looks computed*. Write the lines, then sum them. The total
is still useful — it is step 2's 30% test — and it now inherits its weakest line
instead of hiding it.

## Guardrails

**No tax advice. No legal advice.** Not deductions, not entity structure, not
VAT, not cross-border invoicing, not depreciation, not what is claimable. Not
"here's the general idea", not "I'm not an accountant, but". The founder's
jurisdiction and structure are not in `metrics.md` and are not guessable, and a
confident wrong answer here costs real money.

The close is a natural place for this to arrive, because the founder is staring
at a revenue figure and wondering what they actually keep. That is a question for
an accountant. Say so plainly, hand them the booked figure, the collected figure
and the receivables ageing, tell them to ask what is owed and when — and log it
in `decisions/` if it is material.

Do not write `reviews/monthly/`. It belongs to the **Chief of Staff**. Your job is
that the number is true, not that it is narrated.

Never adjust a number to match what the founder forecast. If last month's plan
said 40k and 22k arrived, the gap is the finding, not an error to be reconciled
away.
