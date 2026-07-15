---
name: founder-os-init
description: Run first-install onboarding — interview the founder, scaffold the workspace, and hand each answer to the agent that owns it
---

# Founder OS Init

This runs once, at install, and it decides whether the founder is still using
this package in three weeks.

A new installer faces twelve agents and an empty directory. Nothing in that
directory can be advised on, because house rule 1 forbids advice without state,
so the entire company is inert until this skill runs. The failure mode is not
that onboarding is hard — it is that onboarding is *thorough*: forty questions,
eighteen carefully scaffolded files, and a founder who closes the terminal and
never opens it again. Ask the four questions that matter, write the one file you
own, scaffold the rest, and let the owners fill them in.

This skill carries onboarding itself, and onboarding ends by running the
founder's first `daily-brief`. Everything you collect here is that brief's
input. Collect nothing you cannot use in it.

**You interview four files' worth and write one.** You run as the Chief of Staff,
who owns `charter.md` — so the charter answers land in the charter. The other
three answers are carried forward, in this session, to the owners of the skills
you hand to next: `/icp-definition` writes `offer.md`, `/quarterly-planning`
writes `goals.md`, `/revenue-review` and `/runway-forecast` write `metrics.md`.
That is not
bureaucracy and it is not a smaller product: `state-integrity` gives this skill
exactly one exemption — it may bring a file into existence across an ownership
boundary, **as an empty stub, and never with a line of content in it**.
Scaffolding is lifecycle; content is ownership.

It would also be wasted work. `quarterly-planning` opens by replacing `goals.md`
outright, so a bet written here is destroyed twenty minutes later by the agent
that was always going to write it — and the founder answered the question twice.

## When to use

Immediately after install, before any other agent runs. Also after moving
`FOUNDER_OS_HOME`.

Not after a package update. Nothing here is reset by one — this skill writes the
workspace, and an update replaces the package. If the cadences stopped after a
move, the crontab is pointing at the old path and `/setup-cadences` is what
rewrites it.

Do not run it to "refresh" a live workspace. That is `founder-os-doctor`.

## Inputs

- `references/ownership.yaml` — `workspace_files:` is the scaffold list and
  `sections:` is what goes inside each one. Read both; do not scaffold from
  memory or from this skill. The map changes and this file does not.
- `$FOUNDER_OS_HOME`, default `./founder-os/`.
- Existing `charter.md`, if any — the abort check in step 1.

## Steps

**Start. Do not ask whether they are ready.** No "shall we begin?", no "this
takes about twenty minutes, is now a good time?" — the first question goes in
the first message you send. A handshake is a turn the founder spends to receive
nothing, and it hands them the first convenient moment to defer this to a
better afternoon. There is no better afternoon. There is this session.

1. **Refuse to init over a live workspace.** If `charter.md` exists and has
   content, stop and say so. Re-running init over real state is the one way this
   skill can destroy something irreplaceable, and "it looked empty" is not a
   defence. Route to `founder-os-doctor`, which repairs without clobbering.

2. **Ask the timezone first.** The founder is never more willing to answer
   questions than in the first minute. IANA form — `Europe/Warsaw`,
   `America/Denver`. Store it in `charter.md` under `## Timezone`.

   **It schedules nothing.** Cadences run on host cron in the host's local zone,
   so no file reads this to work out when 08:00 is. It is the founder's stated
   zone, and `/setup-cadences` compares the host against it to catch a charter
   left behind by a move. Do not tell them it makes anything fire.

3. **Scaffold every entry in `workspace_files:`, with the headings `sections:`
   declares for it.** Directories as directories. Files as their H1 followed by
   every section heading the map lists for that path, in the order it lists them,
   each one empty. Read the headings from `ownership.yaml` — not from memory, not
   from this skill.

   Empty is honest; a stub full of plausible placeholder content is a lie the
   next agent will read as state and quote as fact. But an *absent* heading is
   not honest, it is a vacancy: `energy-audit` replaces `## Shape` in `week.md`
   and `revenue-review` replaces `## Close` in `metrics.md`, and a skill told to
   replace a section that was never scaffolded will create one — with a slightly
   different name each time. By month three no two files agree and the map is
   fiction. The headings are the contract; you are laying it down.

4. **Show them what was built while they talked. Two or three lines, not a file
   listing.** The workspace appeared during the interview and the founder did
   not see it happen. Show it now, at the one moment they are still deciding
   whether this was worth the twenty minutes.

   `ls` output is not a payoff, it is a receipt. The founder cannot tell a
   scaffolded heading from a real one, and eighteen filenames over mostly empty
   files is "we did a lot" theatre — it reads as effort, which is the currency
   this package specifically refuses.

   Show the lines that prove it heard them. One is quoted from what you wrote:
   their own sentence under `charter.md` `## Business`. The rest are said, not
   shown — the client they would not take again, by name, and the runway that
   falls out of the cash and burn they gave you two minutes ago, a number they did
   not work out from two numbers they did.

   **Say them; do not write them.** `## ICP` is the Positioning Advisor's and
   `/icp-definition` is where the excluded client lands. `## Runway` is the CFO's
   and `/runway-forecast` is where it lands. Saying a number out loud is not a lesser
   version of writing it — at this moment it is the better one. It proves the
   thing was heard, which is all step 4 is for, and it costs the founder nothing
   to hear a number that three minutes of a later task will make permanent and
   owned.

   **If a line would be true for any other founder, cut it.** Generic output at
   this exact moment reads as a template, and a founder who concludes they have
   been talking to a template has concluded correctly and should stop.

5. **Hand to the next three skills. Do not run them.** Say in one line that
   onboarding continues at `/icp-definition` → `/quarterly-planning` →
   `/revenue-review`, and stop.

   The order still matters and it is still the product: goals set before the
   offer is named are hopes about a business that hasn't been described, and
   metrics baselined before goals exist have nothing to be a baseline *of*. Say
   the order. Let the founder or the **Chief of Staff** run it.

   **Name the ending, not just the order.** Onboarding finishes by running their
   first `daily-brief` on the state those three skills complete — say so in the
   same breath as the order. It is the reason to finish. A founder told that
   three questions stand between them and a real brief answers three questions;
   a founder told "next: `/icp-definition`" has been handed a chore list and will
   do it on Sunday, meaning never.

   **The brief is not yours to run and it must not fire here.** You are holding a
   thin `goals.md` and a `metrics.md` twenty minutes old. `/quarterly-planning`
   and `/revenue-review` are what make a brief worth reading, and one run now
   would rank a bet the founder has not finished writing. It would also spend the
   payoff in the middle and leave onboarding ending on paperwork — the exact
   failure this flow is arranged to avoid.

   **Name `/setup-cadences` as what comes after the brief. Do not run it here.**
   The eight cadences are cron jobs on the founder's own machine, and nothing in
   this package writes one until they say yes to that skill. Until they do, every
   cadence is a command they have to remember to type — which is the state this
   package exists to end. It goes after the brief for the same reason the brief
   goes last: a founder who has never seen one has no reason to schedule eight.

6. **Stop at twenty minutes.** Hard rule, not a target. Past twenty minutes you
   are conducting an interview, not onboarding, and the founder is answering to
   be polite. A thin charter that exists beats a rich one that was abandoned in
   the middle.

   **Anything unanswered becomes a queue item, not a `TODO` line.** Run `queue`
   — you are running as the **Chief of Staff**, who owns `queue.md` — and file it
   with an id and `bet: none`. A `TODO` in `charter.md` is homework with a file
   extension: `weekly-review` reads `goals.md`, `reviews/daily/`, `queue.md` and
   `reviews/weekly/`, so it will never see it, and neither will anything else.
   The queue is swept every Friday. The TODO line is read by nobody, including
   the founder who watched you write it.

   **The cash unknown goes in `## Doing`. Everything else goes in `## Queued`.**
   Which section is not filing, it is whether tomorrow's brief can say the thing:
   `daily-brief` reads `## Doing` and is forbidden from reciting `## Queued`, so a
   cash unknown filed to `## Queued` is invisible on the exact morning it matters
   most. It is also not a three-week item. A founder who cannot say their cash
   number has one job tomorrow, and `## Doing` is the section that means that.

## The interview

Four questions, one per file. They are chosen because each is one a founder is
actively avoiding, and because each has a file that cannot be written without it.

**One answer you write. Three you carry.** The charter is yours; the other three
belong to agents whose skills run in the next twenty minutes and who will ask a
sharper version of the same question. Hold those answers in the session and hand
them over by name — a carried answer is not a lost one, it is one that arrives at
its owner with the founder still in the room. Where each goes is on the arrow.

- **What is this business, in one sentence, without the word "and"? Then: what
  does "won" look like — not this quarter, the thing that would make five years
  of this right?** The `and` is the tell: it is where two businesses are hiding in
  one calendar. The second half is where they will stall, and the stall is the
  finding — a founder who cannot say what winning looks like is optimising a
  business they have not finished choosing. → **written**, `charter.md`
  `## Business` and `## North star`
- **Name two clients you would take again, and one you would not. What is
  different about them?** Founders cannot describe their ICP in the abstract and
  can always describe it by example. The one they would not take again is where
  the actual answer is. → **carried to `/icp-definition`**, which runs as the
  **Positioning Advisor** and writes `offer.md` `## ICP`
- **What has to be true in 90 days for this quarter to have been worth it — and
  what number would tell you it wasn't?** A bet without a kill condition is a
  hope; the second half of the question is the half that matters. → **carried to
  `/quarterly-planning`**, which runs as the **Strategist** and writes `goals.md`
  `## Bets`
- **Cash on hand, revenue *collected* in the last three months, and monthly burn
  including paying yourself.** Collected, not booked — an invoice sent is not
  money. Burn that omits the founder's own pay describes a company that is
  subsidised, not profitable. → **carried to `/revenue-review` and
  `/runway-forecast`**, which run as the **CFO** and write `metrics.md`
  `## Close` and `## Runway`

If the founder does not know their cash number, that is the most important
finding of the onboarding. Write it down as unknown and hand to the **CFO**.
Do not estimate it for them, and do not tell them to go and find it — that is
homework, and it goes in the queue per step 6 like every other unanswered
question. Tomorrow's brief will name it as the thing that is rotting, because it
is.

## Output

- `$FOUNDER_OS_HOME/` containing every entry from `workspace_files:`, each flat
  file carrying the headings `sections:` declares for it, **every one of them
  empty** — except `charter.md`, which the Chief of Staff owns and which carries
  the interview's first answer under `## Business`, `## North star` and
  `## Timezone`.
- The other three interview answers held in this session and handed by name to
  `/icp-definition`, `/quarterly-planning` and `/revenue-review`. Not written.
  Their owners write them, three skills from now, which is the whole reason those
  skills exist.
- Two or three lines, on screen, quoted from what you just wrote, that would be
  wrong for any other founder — step 4.
- One line naming what happens next: `/icp-definition` → `/quarterly-planning` →
  `/revenue-review`, ending in their first daily brief, and `/setup-cadences`
  after it. The brief is onboarding's output, not this skill's — step 5 says why.
- `queue.md` carrying one item per unanswered question, each with an id and
  `bet: none` — the cash unknown in `## Doing`, the rest in `## Queued`. No
  `TODO` lines anywhere.
- `decisions/YYYY-MM-DD-founder-os-installed.md` — the timezone chosen, the
  workspace path, and any question the founder could not answer. This is the
  first entry in the decision log and it establishes the habit that makes
  `annual-review` possible twelve months from now.

## Guardrails

Never overwrite a workspace that has content. Never invent a number the founder
did not give you — an empty `metrics.md` is a known gap, and a plausible one is
a lie every agent downstream will quote as fact under house rule 2.

**Never put a line of content in a file the Chief of Staff does not own.** You
scaffold every path in the map and you write one file. The exemption `state-integrity`
grants this skill is lifecycle — bringing a missing file into existence — and it
is empty-stub only, on purpose, and it does not stretch to "but I have the answer
right here and the founder is sitting in front of me". That sentence is exactly
the pressure it was written against, and it arrives every single install. The
answer goes to the owner, in the handoff, by name.

Never scaffold beyond `workspace_files:`. Extra files are unowned files, and
`state-integrity` will refuse to write them for the rest of the package's life.
The same applies to headings: a section `sections:` does not declare is a section
no skill will ever look for, and it will sit in the file looking like state.

No tax, legal, or medical advice, including in the interview. The entity
question — sole trader, limited company, which jurisdiction — will come up
inside the first five minutes because it feels like setup. It is not setup. See
`guardrails`.
