---
name: relationship-map
description: Map who the founder actually knows by category and days since real contact — run quarterly, before any conference, and whenever cold outreach is proposed with the warm list untouched
metadata:
  writes:
    - network.md
---

# Relationship Map

A founder's mental model of their network is the twelve people they saw most
recently. The next client is almost always someone else — a past client,
delighted eighteen months ago, who has since forgotten what the founder does.

Forgetting is the default, not a judgement. This map exists because the number
that predicts the next contract is not warmth. It is **days since last real
contact**, and it is a number nobody keeps.

## When to use

Quarterly. Before a conference. When the founder needs an introduction, a
reference, or a second opinion and "doesn't know who to ask" — which almost
always means they know, and have not thought about that person since 2023. Also
whenever cold outreach is proposed while the warm list sits untouched, which is
the most expensive form of procrastination available to a solo founder.

## Inputs

Read first, in order — house rule 1:

- `network.md` — the current map, and how stale it is
- `clients/` — every past client. This is the highest-converting group in any
  company of one and the most neglected, in that order, causally.
- `pipeline.md` — who is a live deal. They are the **Pipeline Coach's**; they
  do not belong in the map's cadence.
- `offer.md` — the ICP, for who among the network could plausibly refer
- `ingestion-gate` — "what they need" is a claim about another person's
  situation, which is the gate's hardest case. Heard from them, it is FACT.
  Heard *about* them from a third party, it is hearsay and does not enter. Run
  the gate on every cell before the row exists.

## Beliefs

- Relationships decay from asymmetry, not from neglect. Someone contacted only
  when they are needed is not being neglected, they are being used, and the
  interval on the calendar looks identical either way.
- Referrals do not come from the people who like the founder most. They come
  from whoever most recently had a reason to describe them out loud to somebody
  else. That is a fact about frequency, not about affection, and it is why the
  delighted client at 640 days refers nobody.
- The founder's network is smaller than they believe and warmer than they fear.
  Both errors have one cause: they are counting people who never think about
  them, and avoiding the ones who do.

## Steps

1. **Start from `clients/`, not from memory.** Every person who ever paid, and
   everyone who was in the room while they did. The founder's recall is
   recency-ordered and it will skip the best entries in the file.
2. **Sort into the four categories. They behave differently, so they get
   different cadences:**
   - **Past clients** — quarterly. Highest conversion, most neglected.
   - **Referred once** — quarterly. They already took a social risk on the
     founder and nothing was done with it.
   - **Could refer, never has** — twice a year. Usually because they do not know
     what the founder does now, which is not their fault.
   - **Peers** — twice a year.
3. **Record days since last *real* contact.** A conversation. Not a LinkedIn
   reaction, not a like, not a conference nod. If the founder cannot name what
   was actually said, it did not happen.
4. **Cut anyone with no dateable contact.** No date you can name means they are
   a contact, not a relationship. Contacts belong in the phone; a map that
   includes them is a database of strangers with a warm-sounding title.
5. **Fill in "what they need" — about them.** Mandatory. What are they working
   on, hiring for, stuck on, trying to prove. If the only thing you can write is
   "could send me work", **that is not a relationship and it does not go in the
   map.** It is a lead: hand it to the **Pipeline Coach**, or leave it out. This
   test is what keeps the map from quietly becoming a CRM.
6. **Sort by days since contact, descending.** The top of the list is
   embarrassing and that is the entire point of building it. The most valuable
   line in this file is the delighted client from two years ago at 640 days.
7. **Cap the map.** A solo founder maintains about forty relationships, not two
   hundred, and a map of two hundred is maintained at zero. If it is over forty,
   the question is not who to cut — it is which forty the founder would actually
   be glad to hear from.
8. **Ask the question they are avoiding: when did you last talk to the client
   who was delighted with you?** Then let the number sit there.

## Named failure modes

- **The CRM of hope.** Every "what they need" blank, every "what I want" full.
  It produces messages that feel like invoices and it teaches the network to
  stop replying.
- **The LinkedIn mirage.** Counting reactions as contact. Five hundred
  connections and four relationships, with no way to tell them apart — which is
  what this map is for.

## Output

Write to `network.md`, replacing `## Map`:

    ## Map — updated YYYY-MM-DD
    <n> people (cap 40) | Overdue: <n>

    ### Past clients — quarterly
    | slug | person | company | last real contact | days | what they need | per | next contact |
    |------|--------|---------|-------------------|------|----------------|-----|--------------|
    |      |        |         |                   |      |                | <them, channel, YYYY-MM-DD> \| guess — last heard YYYY | |

    ### Referred once — quarterly
    ### Could refer, never has — 2×/year
    ### Peers — 2×/year

    ## Not in the map
    - <name> — no contact I can date → a contact, not a relationship
    - <name> — only reason to write is to ask for work → handed to Pipeline Coach

`follow-up-sweep` reads the `days` and `next contact` columns. A row with a
blank "what they need" cannot be swept, because there is nothing to send that
isn't an ask.

The `slug` column is this table's other job. Every `[[slug]]` in the workspace that
is not a file resolves to a row here — house rule 6, procedure in
`references/linking.md`. Lowercase, hyphenated, from the person's name:
`anna-kowalska`. A row with a blank slug is unreachable: `pipeline.md` can point at
it and nothing arrives.

**The `per` column is what stops "what they need" ageing into fiction.** It is
the only stamp slot in the table because it is the only cell that is a claim —
`days` is arithmetic, `last real contact` is a date the founder can name or the
row does not exist, and `next contact` is a decision. Two values are legal:
either they told you themselves, in a channel, on a date, or it is `guess` with
the year attached — the label the Guardrails below already demand, given a column
so it cannot be dropped when the row is rewritten. A third party's account of
what someone needs is hearsay and does not get a cell; it is not that the stamp
would be ugly, it is that the row would be false. Unstamped, a `what they need`
from 2024 reads exactly like one from last week, and `follow-up-sweep` will
cheerfully draft against it — which is how the founder writes to someone about a
job they left.

## Guardrails

Never write `pipeline.md`. The moment money and a decision are in play, the
person is a deal and the **Pipeline Coach** owns the next step. Hand them over
and take them off your cadence.

Never fill "what they need" with a guess presented as fact. Label it: `guess —
last heard 2024`. An agent inventing a person's motivations produces messages
that are confidently about the wrong thing.

Never rank people by revenue potential. That produces a lead list, and a lead
list is how a founder burns fifteen years of goodwill in one quarter — silently,
because nobody tells you they've written you off.

Friends stay out. If the founder feels obliged to contact someone monthly, they
are either a friend — in which case this system stays out of it entirely — or a
deal, in which case they are not yours.

**The slug is the identity and this skill owns it.** Every other file points at
`## Map` with `[[slug]]`, so a slug you change is a link you broke somewhere you
are not looking. Pick it once, from the person's name, lowercase and hyphenated,
and leave it alone — the display name in the `person` column is free to change
when they marry, rebrand or correct you.
