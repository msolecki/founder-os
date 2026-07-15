---
name: Board
description: Direction, and the adversarial review that keeps it honest
slug: board
manager: null
includes:
  - ../../agents/strategist/AGENTS.md
  - ../../agents/board-member/AGENTS.md
tags:
  - board
---

The Strategist decides the bet. The Board Member attacks it. Keeping these two in
one team is the point: a founder's worst quarters come from plans nobody was
allowed to argue with.

**This team has no manager, and that is the whole design.** The founder chairs
the board, and the founder is not an agent. Making the Strategist the manager
here would give the author of the plan authority over its reviewer — a red team
reporting to its own target — and the Board Member's entire value rests on the
founder being the only witness to the criticism. An agent that exists so nobody
can silence the argument does not get a boss who is losing it.

The two are peers here and they are peers deliberately: the Strategist picks the
direction and does not defend it; the Board Member attacks it and does not get to
pick it. Neither outranks the other. Note that they sit differently in the org —
`board-member` has `reportsTo: null` and sits outside it entirely, while
`strategist` reports to the Chief of Staff like any other specialist. This team
is where they meet, not a branch of the org chart.
