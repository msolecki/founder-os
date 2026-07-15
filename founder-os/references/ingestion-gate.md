# The Ingestion Gate

House rule 5 states the rule. `skills/ingestion-gate/SKILL.md` is the procedure
every agent runs before a write. This file is what that procedure operates on:
the tier definitions, the ladder that settles conflicts, and worked examples of
this company getting it wrong.

`owns:` in `references/ownership.yaml` decides who may write a file. It has no
opinion whatsoever about whether the claim going in is true. This is the other
axis, and it is the one that decides whether the workspace is worth reading.

## The three tiers

### FACT

Two sources qualify, and only two.

- **First-hand.** You read it in a file, an invoice, a calendar, a bank line, a
  message that was actually sent. Not somebody's summary of the artifact — the
  artifact.
- **A counterparty describing their own situation.** Their budget, their
  timeline, their constraint, their intent. "We can't sign until the new CFO
  starts" is a fact about them. They are the only authority on it, and they are
  not flattering anyone by saying it.

The test: **could the speaker be wrong about this and still be honest?** If yes,
it is not FACT. A buyer saying "procurement takes two weeks here" describes a
process they have watched. A buyer saying "procurement will be fine" predicts
one.

The trap is the gap between the sentence and the world. "We'll pay by the 30th"
is FACT that they said it, FACT about their intent today, and a prediction about
the world on the 30th. Tier the claim you are making, not the sentence you
heard. If the line you are writing is money, the claim is about money.

### VALIDATE

Plausible, consequential, unverified. It may enter, and it enters carrying its
tier plus a validation step: the artifact that would settle it, who gets it, by
when. Without those three it is not a VALIDATE, it is a rumour with a label, and
the label survives about two reads.

**A flattering number is guilty until validated.** Not because flattery is
usually false, but because nobody in this company will ever chase it. An
unflattering claim gets tested by the founder's own anxiety within the hour. The
flattering one sits in the file being quoted.

What validates: an artifact, a first-party record, or a counterparty stating it
about themselves in a channel you can point at six weeks later. What does not:
hearing it again, hearing it louder, hearing it from someone senior, or the
quarter needing it.

### DISREGARD

Three kinds, and none of them enters the workspace at all.

- **Hearsay** — someone reporting a third party's state, intent or numbers.
  "Anna says their board has already approved it" is a fact about Anna's
  sentence and tells you nothing about the board.
- **Speculation** — a claim about a future nobody can observe today, dressed as
  a description of the present. "This market is moving to subscriptions."
- **Paid speech** — a claim whose speaker is compensated for making it. A
  vendor's benchmark, an agency's case study, a recruiter's "market rate", a
  competitor's published headcount. It may well be true. It was not said in
  order to be true.

Why DISREGARD is not simply a third label: a labelled line inside a canonical
file gets quoted without its label within two reads, after which the label's
only remaining function is making the file look rigorous. Keeping it out *is*
the enforcement. If it belongs in the conversation, say it in the conversation —
sessions are not canonical, files are.

## Incentive is part of the tier

**What a counterparty says about their own situation is fact. What you say to
win the room is positioning.** Same sentence, different tier, according to who
gains:

- Buyer: *"we have no budget until Q4."* FACT. It costs them the thing they were
  considering; nobody positions themselves into a delay.
- Buyer: *"we'd sign tomorrow if you had SOC 2."* Not a fact about a sale — a
  conditional about their own future behaviour, which is the classic feature
  request that is not one. The fact you may keep is that SOC 2 came up on
  12 May. The sale was never a fact.
- Us, in a proposal: *"we deliver in four weeks."* Positioning. The delivery
  fact lives in `clients/` and it is whatever the last three engagements
  actually took.
- The founder, about their own intent: FACT. The founder, about a number from
  memory: VALIDATE against the invoices.
- A vendor's pricing page: *"saves ten hours a week."* Paid speech. What goes in
  `systems.md` is what it saved us, measured, which is the Ops Engineer's job
  and the reason `automation-audit` exists.

## Tier is not weight

Tier asks *is it true*. Weight asks *does it matter*. They are independent, and
collapsing them is how a workspace ends up holding forty true irrelevant lines
and one load-bearing guess.

Weight is three questions:

- **Whose book does it touch?** Money (`metrics.md`), capacity (`clients/`,
  `week.md`), reputation (`voice.md`, `content.md`). A claim touching none of
  them is trivia.
- **Does it touch a live bet in `goals.md`?** A claim that could kill or confirm
  this quarter's bet is heavy even when it is small.
- **One-off, or the third time?** Three of anything is a pattern, and the
  pattern outweighs any single instance of it. The Pipeline Coach already reads
  losses this way.

The grid:

- **FACT, no weight** — true, irrelevant, do not write it. Files have a budget
  and every line spends it.
- **FACT, weight** — write it, stamped. The common case, and the boring one.
- **VALIDATE, no weight** — do not write it and do not validate it. You will
  never chase it, and it will be quoted anyway.
- **VALIDATE, weight** — the actual work. Tier label, validation step, owner,
  date; if the step needs a human it belongs in `queue.md` via the Chief of
  Staff.
- **DISREGARD, any weight** — still DISREGARD. **Weight is a reason a claim is
  worth checking. It is never a reason to count it as checked.**

## The precedence ladder

When two sources disagree, rank them:

1. **Signed document** — contract, SOW, PO, invoice, an accepted quote.
2. **First-party record** — a bank credit, a sent email, a calendar entry, a
   commit log. The thing actually happening, recorded as it happened.
3. **CRM and notes** — `pipeline.md`, `clients/`, meeting notes. Somebody's
   transcription of a conversation: a real source, and a lossy one.
4. **Outward positioning** — their deck, our deck, a website, a case study, a
   LinkedIn post. Written to be read by someone who is being sold to, and that
   includes ours.

The rules:

- Higher rank takes the line. The lower-ranked claim is not deleted — it becomes
  the conflict note attached to it. "The file changed and nobody knows why" is
  the failure this whole package exists to prevent.
- **The OS never picks a winner silently.** Even when the ladder is unambiguous,
  the conflict is named — in the line and to the founder. The ladder decides
  what the line says. It does not decide that the founder need not know there
  was an argument.
- Same rank, both credible: nobody wins. Write both, name the conflict, hand it
  to the file's owner. If it is material it is a `decision-log` entry, and what
  the founder chose is then itself a FACT with a stamp.
- A conflict crossing an ownership boundary goes to the owner by name
  (`state-integrity`). Discovering a conflict does not make you the agent who
  settles it.
- A conflict with a signed document at the top is usually not an ingestion
  problem at all — somebody is about to work outside scope. That is
  `scope-guard` and the Delivery Lead, today, not at the retro.

## Provenance stamps

A stamp has three parts: **who** — a person, with their relationship to us;
**where** — the channel; **when** — the date. `(per Anna, buyer at Acme, call,
12 May)`. Not `(per Acme)`: companies do not speak. Not `(per the call)`: which
call.

It goes inline, in the line carrying the claim. Not a footer — footers are read
once, at the bottom, by nobody. And not the file's timestamp: **the mtime says
when someone last touched the file, which is a different fact from when the
claim was last true.** The two diverge exactly when it matters, because the file
was touched on Tuesday to fix a typo underneath a number from March.

Staleness is therefore read inside the line. `context-load` puts a date on the
file; this puts a date on the claim, and a freshly-touched file full of March is
the state that actually kills a decision. Staleness is per claim, not per file:
a buyer's timeline goes stale when their quarter turns, a signed rate does not
go stale at all, and an ICP attribute goes stale when the client it cites stops
paying.

**A line with no stamp is VALIDATE**, whoever wrote it and however confident it
reads. That is not an insult to the past; it is the only rule that makes
adopting this gate mean anything. Restamp such lines when you next touch the
file, or leave them and quote them as guesses out loud. Do not promote one by
reading it twice.

## Worked examples

### The CFO and a promise to pay

`metrics.md`, at the month close. The buyer's email says: "we'll get the invoice
paid by the 30th."

- **Speaker:** named, first-party, describing their own intent. What they gain
  by your believing it: three more weeks of not paying.
- **Tier:** two claims in one sentence. That they intend to pay — FACT. That the
  money arrives on the 30th — VALIDATE. Only the bank line settles the second.
- **Weight:** money, and it moves runway. Heavy, so the VALIDATE gets a
  validation step or it does not get written.
- **The line:**

      Receivable 18,000 PLN, expected 30 May [VALIDATE] (per Marek, finance at
      Acme, email, 12 May — validate: bank credit, CFO, by 2 Jun)

- **What the CFO does not do:** book it as collected, or quote runway from it
  with the tag quietly dropped. Revenue booked is not revenue collected — the
  CFO's own agent body says so, and this gate is the mechanism that makes that
  sentence survive contact with a friendly email.

### The Pipeline Coach and "they're keen"

`pipeline.md`, `## Live`. The founder, after a call: "they're really keen."

- **Speaker:** the founder, describing a third party's state of mind. Hearsay
  about an internal state — DISREGARD. That it is the founder saying it changes
  nothing; they cannot see inside the buyer either.
- **What is FACT underneath it,** and it is better material anyway: they took a
  45-minute call on 12 May, asked what onboarding looks like, said they would
  take it to their CTO. Three observable events with a date.
- **The line:**

      Acme — next: send onboarding outline, 15 May. Asked about onboarding,
      taking it to their CTO (per founder, call, 12 May).

- Keenness has no next action and no date, which are the only two fields
  `pipeline.md` requires. Not a coincidence: those fields exist because they are
  the two parts nobody can vibe.
- **Said out loud, not written:** "keen" is a description of someone else's
  mind, and eight keen people is how a pipeline of three deals reads as eleven.

### The Positioning Advisor and one flattering call

`offer.md`, `## ICP`. A prospect on a first call: "honestly, this is exactly
what every agency our size needs."

- **Speaker:** a prospect being pleasant at zero cost to themselves, and
  describing a market rather than their own situation. Speculation about third
  parties — DISREGARD.
- **What is FACT:** one person, at one company, said the problem is real for
  them, on 12 May. n = 1.
- **Weight:** high, and that is the danger. `offer.md` is quoted downstream by
  every outreach, proposal and post. High weight is why it must not be promoted,
  not permission to promote it.
- **The line:** none. `## ICP` attributes cite paid clients — `icp-definition`,
  and this is not one. If it is worth pursuing it is a hypothesis with a test
  date, and the honest test is whether one of them pays.
- **The cost of getting it wrong is a quarter:** the ICP widens to a segment
  nobody has invoiced, the Pipeline Coach prospects into it, the Brand Editor
  writes for it, and it surfaces two quarters later as "our content stopped
  working".

### A conflict, and what the ladder does not do

`clients/acme.md`. The SOW says onboarding is billed separately. The client's PM
says on a call: "we always assumed onboarding was included — it was in your
deck."

- **Rank:** signed document (1) against a conversation (3), and the evidence
  behind the conversation is our own deck (4). The ladder is unambiguous: the
  SOW takes the line.
- **What the ladder does not do is end it.** The deck said what it said, we
  wrote it to win the room, and a paying client read it and believed it. Naming
  the conflict is the entire output here:

      Onboarding billed separately (per SOW, signed 3 Mar) [CONFLICT: PM says
      it was implied by our deck (call, 12 May) — founder to settle]

- Then it leaves this skill. The money question is the founder's, the scope
  conversation is `scope-guard` and the Delivery Lead's, the deck that caused it
  is the Brand Editor's. A silent win for the SOW is the worst outcome on the
  table: technically correct, and the client finds out via an invoice.

## When nothing is FACT

Pre-revenue, or a new segment: `clients/` is empty and every claim you hold came
from a conversation. The honest state is that the workspace contains hypotheses,
so say that, and let the files say it too — a `[VALIDATE]` tag on every line
that deserves one is not clutter, it is the accurate picture.

What you must not do is promote the best conversation you had to FACT because
the file looks thin without one. A thin file is a true description of a young
company. A confident file is a young company that will spend a quarter acting on
a sentence somebody said to be nice.
