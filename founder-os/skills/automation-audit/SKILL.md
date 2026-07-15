---
name: automation-audit
description: Decide whether a manual task is worth automating using payback arithmetic — run before building anything internal, and especially when the founder is enjoying it
metadata:
  writes:
    - systems.md
---

# Automation Audit

A technical founder's automation backlog is mostly a list of things they would
rather do than sell. This skill is the arithmetic that says no. It is the skill
most likely to be resented, which is roughly the measure of whether it is working.

## When to use

Before building anything internal. When the founder says a task is "killing them"
for the fourth time. When a Sunday is about to disappear into tooling — and
especially then, because **automation urges spike on the day a proposal follow-up
is due.** Check the calendar before you check the code.

## Inputs

Read first, in order — house rule 1:

- `systems.md` — what is already automated, what is already broken, and what was
  built once and quietly abandoned
- `clients/` — is this manual work downstream of a delivery process the **Delivery
  Lead** could reshape for free? About half of it is.
- `metrics.md` — the founder's effective hourly rate. It is the price of the build
  hours, and it is what turns this from a preference into a calculation.

## Beliefs

- **Every automation is a permanent employee with an on-call rota of one.** It
  draws no salary and it cannot be fired, but it can page the founder at 2am
  during a client deadline. The real cost is not the build; it is that a company
  of one now owns one more thing capable of failing while nobody is looking.
- **Automating an unstable process freezes it.** A task that has run the same way
  twelve times is a candidate. One that has run three times is still being
  designed, and the script will settle the design by accident — after which
  nobody revisits it, because it works.
- **The manual work that survives is the work done for the favourite client.**
  The bespoke monthly report nobody else receives, invented once as a courtesy,
  now a standing cost that appears in no proposal. It is never top of the
  automation list, because the founder does not experience it as work. Count its
  minutes with the others before deciding anything.
- **Manual and deliberate beats automated and unreviewed.** A monthly task done
  by hand is also the founder's only scheduled look at the number. Automate it
  and the looking stops — the next thing that goes wrong is discovered by a
  client, which costs more than the hours the script ever saved.

## Steps

1. **Delete, then simplify, then buy, then build. In that order, no skipping.**
   Most automation requests are for a task that should not happen at all. Ask why
   the task exists before asking how to automate it; the founder will be irritated
   by the question and it is right about half the time. **Build is last. It is
   always last for a company of one**, because the founder is also the on-call
   engineer at 2am and there is nobody to hand the pager to.
2. **Measure the task in minutes per month, honestly.** Not "it takes forever" —
   count the runs, count the minutes. Founders inflate the cost of tasks they find
   irritating by roughly an order of magnitude, and irritation is not a unit of
   time.
3. **Apply the floor: under 2 hours per month, do not automate — at any build
   cost.** A twenty-minute monthly annoyance is a rounding error wearing a costume
   that looks like a problem to an engineer with an unpleasant sales call in the
   calendar.
4. **Take the founder's build estimate, then apply their own retro variance.**
   `delivery-retro` measured exactly how wrong their estimates run on client work.
   Go read the number and apply it here. They do not get to be realistic about
   clients' projects and optimistic about their own.
5. **Count maintenance — the number everyone leaves out.** Budget **20% of build
   hours, per month, forever.** APIs change, credentials expire, formats shift.
   Omitting this is precisely how a company of one accumulates nine broken
   scripts, each now costing more than the task it replaced.
6. **Compute the payback:**

       payback months = build hours ÷ (hours saved per month − maintenance hours per month)

   - **If the denominator is zero or negative, the automation costs more than the
     task, forever.** This happens far more often than founders expect, and
     surfacing it is the most valuable thing this skill does.
   - **If payback is over 3 months, do not build it.** Say it plainly, even when
     the founder is enjoying themselves. Especially then.
7. **Price the build in the founder's rate, not in hours.** "16 hours" sounds
   free. "16 hours at your 140/h effective rate is 2,240 of unbillable time —
   about a third of what Acme pays you in a month" is a decision.
8. **Name what is not happening while this gets built.** Every automation hour is
   a sales hour or a delivery hour. Name the specific one, not the category.

## Output

Append to `systems.md` under `## Automation decisions`:

    ### YYYY-MM-DD — <task>
    Task cost: <n> min × <n> runs/mo = <n> h/month
    Order check: delete? <y/n — why> | simplify? <y/n> | buy? <amount>/mo | build
    Build: <n> h  (founder estimate <n> h × retro variance <n>%)
    Maintenance: <n> h/month  (20% of build)
    Payback: <n> months
    Build cost at founder rate: <amount>
    Not happening instead: <the specific thing>
    Verdict: <delete | simplify | buy <tool> | build | leave it manual>

## Guardrails

Do not build it because the founder wants to. This skill exists to be the
friction. If they build it anyway, that is their call — write the payback number
into `systems.md` first, so the next review has something to convict with.

Do not automate a task the **Delivery Lead** could delete by reshaping delivery.
Scripting a bad process makes it permanent and attaches a maintenance bill to it.

If the real problem is that the founder is slow at the task rather than repeating
it, that is the **Skills Mentor's**. No tool fixes that, and building one buries
the evidence under a repo.

The tool bill's effect on runway is the **CFO's** to write in `metrics.md`, not
yours. Hand off before any commitment that changes monthly burn.
