# Studio North — example Founder OS workspace

This is a fictional, contract-shaped workspace for a one-person strategy
studio. Every person, company, amount, and date is invented. The file headings
and cross-file relationships follow the real Founder OS ownership contract.

It is a guided tour, not an import template. `/founder-os-init` creates a
complete workspace for your own business.

## Start here

1. Open [`reviews/daily/2026-07-20.md`](reviews/daily/2026-07-20.md). The brief
   names one commitment: `q-0720a` serving bet `B1`.
2. Follow the commitment to [`queue.md`](queue.md). It is the only item in
   progress and has a start date.
3. Follow `B1` to [`goals.md`](goals.md). The bet has a threshold, judgment
   date, and downside cap.
4. Open [`week.md`](week.md). Monday has a funded block for the same commitment;
   the website redesign is explicitly traded away.
5. Open [`pipeline.md`](pipeline.md). Acme has a founder-owned next action and
   date; Northwind is overdue and therefore appears under `## Rotting` in the
   daily brief.
6. Open [`reviews/weekly/2026-W29.md`](reviews/weekly/2026-W29.md). The next
   week's commitment became `q-0720a`; the review records the cross-week pattern
   instead of narrating Friday's mood.
7. Open
   [`decisions/2026-07-18-raised-sprint-floor.md`](decisions/2026-07-18-raised-sprint-floor.md).
   It records the rejected option and the evidence that would reverse the call.

## What this demonstrates

- Agents do not share a chat transcript. They share explicit Markdown state.
- A brief is not a to-do list: one commitment, one trade, and what is rotting.
- IDs and bet references make work traceable across the queue, week, and reviews.
- Pipeline claims carry a speaker, channel, and date; founder decisions do not.
- A decision log stores the falsifier, not just the decision.

Founder OS knows only what is recorded in files like these. It does not sync a
calendar, CRM, inbox, or bank account by itself.

See [`docs/getting-started.md`](../../docs/getting-started.md) to install the
plugin and the generated [`COMMANDS.md`](../../founder-os/COMMANDS.md) for all
49 workflows.
