---
name: revenue-review
description: Close the month on booked, collected and effective rate — run on the first working day of the month, invoked by the monthly-close task
metadata:
  writes:
    - metrics.md
---

# Revenue Review

The monthly close. One job: make the number true before anybody builds a plan on
it. A founder with a record month and an empty bank account has not had a record
month — they have had a record month of paperwork.

## When to use

The first working day of each month, covering the month just ended. Triggered
automatically by `tasks/monthly-close`. Also before any decision that spends the
month's revenue: a contractor, a tool, a holiday.

## Inputs

Read first, in order — house rule 1:

- `metrics.md` — last month's close. What did the founder say was coming in?
- `clients/` — hours actually worked per engagement, including the unbilled ones
  `delivery-retro` recovered
- `pipeline.md` — what closed this month, and when the cash for it actually lands

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

## Output

Replace the `## Close — YYYY-MM` block in `metrics.md`:

    ## Close — YYYY-MM
    Booked: <amount>
    Collected: <amount>  (<n>% of booked)
    Past terms: <amount> across <n> clients — oldest <n> days
    Hours worked: <n>  (delivery <n> / sales <n> / unbilled <n>)
    Effective rate: <amount>/h vs target <amount>/h  (prev month <amount>/h)
    Largest client: <n>% of collected
    Cash on hand: <amount>  (before any tax reserve)
    Handed to: Chief of Staff for reviews/monthly/

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
