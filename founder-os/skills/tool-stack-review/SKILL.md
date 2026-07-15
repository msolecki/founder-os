---
name: tool-stack-review
description: Cancel what is paid for and unused — run quarterly, and 30 days before any annual renewal bills
metadata:
  writes:
    - systems.md
---

# Tool Stack Review

A stack that costs 4% of revenue and does 40% of the work is fine. The same stack
unused is a slow leak with a nice UI. Nobody cancels anything, because cancelling
takes ten minutes and continuing to pay takes zero.

## When to use

Quarterly. Whenever the card statement arrives with a number the founder cannot
account for. **Always 30 days before an annual renewal bills** — after it bills,
the review is a year late, and it will be a year late again.

## Inputs

Read first, in order — house rule 1:

- `systems.md` — the current stack: what each tool is for, its cost, its renewal
  date
- `metrics.md` — collected revenue, so the bill has a denominator
- `clients/` — which tools actually touch delivery. A tool in the critical path of
  client work is a different object from one the founder enjoys.

## Steps

1. **List everything that bills, including what is hiding:** annual plans
   amortised monthly, the domain registrar, per-seat tools with one seat, the LLM
   API, the thing billing to a personal card, and the free tier that quietly
   started charging. The founder's mental list is short by about a third and
   always misses the annual ones — because those do not feel like a monthly cost,
   which is exactly why they were sold that way.
2. **Ask two questions per tool. Only two:**
   - **What breaks if this is cancelled today?**
   - **When was it last opened?**
3. **Apply the rule: cannot answer either question → cancel it now.** Not
   "evaluate", not "add it to the list", not "check with the team" — there is no
   team. Cancel. **You can always resubscribe; you cannot un-pay.** "Let me think
   about it" is the mechanism by which it renews.
4. **Not opened in 30 days → cancel**, unless the answer to question one is
   something concrete that breaks. "It runs the backups" is concrete. "I might
   need it" is a subscription to a feeling.
5. **Name the annual-plan trap out loud.** The annual plan bought to "save 20%" on
   a tool used twice is not a saving — it is a twelve-month commitment made in an
   afternoon. Any annual renewal costing more than one hour of the founder's
   effective rate goes through this skill *before* it bills, not after.
6. **Compute the bill as a share of collected revenue.** Over 5% for a company of
   one → start cutting; the number is the argument, no further case needed. Under
   2% with everything used → **stop optimising this and go sell.** An afternoon
   spent shaving a bill smaller than one invoice is the same avoidance
   `automation-audit` exists to catch, just with a spreadsheet instead of a repo.
7. **Sum the cancel list monthly *and* annually.** The annual figure is the one
   that lands. "47/month" is ignorable. "564 a year — a week of runway" gets
   cancelled that afternoon.
8. **Check for duplicates.** Two tools doing one job is normal and invisible: the
   second was bought during a project and never removed. Notes, task tracking and
   scheduling are where this always is.

## Output

Replace the `## Stack` block in `systems.md`:

    ## Stack — reviewed YYYY-MM-DD
    | tool | cost/mo | renews | breaks if cancelled? | last opened |
    |---|---|---|---|---|
    Total: <amount>/mo = <n>% of collected revenue
    Cancel: <tool> — <amount>/mo — <reason>
    Cancel-list total: <amount>/mo, <amount>/yr
    Duplicates: <tool> and <tool> both do <job> — keep <tool>
    Next annual renewal to review: <tool> on <YYYY-MM-DD>

## Guardrails

Do not migrate the stack. A migration is a project with no revenue attached and it
is always proposed on a Sunday. If one is genuinely warranted, it is irreversible
far more often than it looks — hand to the **Chief of Staff** for `decisions/`.

Do not recommend a replacement for something you just cancelled. **The default
after cancelling is nothing.** If nothing hurts within a month, that was the
finding.

The tool bill's effect on runway is the **CFO's** number and belongs in
`metrics.md`. You produce the cancel list; they say what it does to the burn. Hand
off before any commitment that changes monthly burn.
