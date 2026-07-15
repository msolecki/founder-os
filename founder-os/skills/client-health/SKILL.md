---
name: client-health
description: Score an engagement on payment, scope, tone and effort before it becomes a crisis — run monthly per active client, and always before a renewal
metadata:
  writes:
    - clients/
---

# Client Health

Engagements do not fail suddenly. They fail for six weeks and get discovered at
renewal — the one moment when nothing can be repaired and the founder's only
remaining move is a discount.

## When to use

Monthly, per active engagement. Immediately when a client goes quiet mid-project
or an invoice slips. Before every renewal conversation, never during one.

## Inputs

Read first, in order — house rule 1:

- `clients/<client>.md` — the engagement log: scope asks, hours, invoice dates,
  response times
- `metrics.md` — the invoice terms and this client's actual days-to-pay history
- `pipeline.md` — is a renewal or expansion pending? It changes what silence
  means
- `ingestion-gate` — the four signals are computed from dates in the log and need
  no gate. What the client *said* about them does: "cashflow is tight this
  quarter", "we're restructuring, it's not you". Those explain a red or excuse it,
  and which one they are is the gate's question, not this skill's.

## Beliefs

- **A client who has stopped complaining is not satisfied.** Complaints are
  engagement. The quiet ones have already had the conversation about you
  internally and reached a conclusion nobody sent. Rising friction is a
  healthier signal than a relationship that has gone smooth.
- **Health is a property of the deal's shape, not the client's personality.**
  Most "difficult clients" were priced, scoped or sequenced badly at the start,
  and the same person on a better-shaped engagement would have been fine. This
  matters because personalities cannot be fixed and deals can.
- **The founder is one of the signals, and they are not scoring themselves.**
  A large share of failing engagements went quiet from the founder's end first:
  latency is bidirectional, and a client's tone frequently tracks the founder's
  own avoidance of them by about three weeks. Before scoring tone red, check who
  stopped replying.
- **Renewal rewards the client having felt in control, not the work having been
  good.** A client who cannot say what they got this month will not renew a
  project that went perfectly. The founder reads that as ingratitude; it is a
  reporting failure and it is fixable.

## Steps

Score four signals. Green, amber, or red — not out of ten. Scores out of ten
launder judgment into arithmetic and let a 6 mean whatever the founder needs it
to mean that day.

1. **Payment.** Days-to-pay against terms. **Red at 15+ days past terms, or at
   the second consecutive late invoice.** A client who paid in five days for six
   months and now takes forty has told you something they have not said yet.
2. **Scope.** The absorbed-ask count `scope-guard` keeps. **Red at 3+ this
   engagement**, and red on the trend regardless of count. Rising asks usually
   mean the client feels they are not getting value and is trying to get it by
   volume.
3. **Tone.** Response latency against *this client's own baseline*, not against
   other clients. **Red when it doubles.** Also red: the CC list grew. Someone
   was added to the thread for a reason nobody stated, and it is never a good one.
4. **Effort trend.** Hours per delivered unit across the engagement. **Red at 30%
   above the first month's rate.** Work getting harder over time is usually the
   relationship, not the task.

Then:

5. **Apply the rule: two reds is a failing engagement.** Not "monitor it" — a
   direct conversation this week, started by the founder, naming the thing
   plainly. One red is `at-risk`: a note in the log, not an action. Three reds
   means the founder already knew and has been managing their own feelings
   instead of the client.

   The verdict is arithmetic on the reds, and the vocabulary is fixed: **zero
   reds `healthy`, one red `at-risk`, two or more `failing`.** These three words
   are the only ones this skill emits, because `daily-brief` reads them every
   weekday morning and a synonym is invisible to it — a client the founder would
   call "a bit wobbly" is a client no other agent will ever hear about.
6. **Ask the question the founder is avoiding: if this client emailed tomorrow to
   end the engagement, would the first feeling be panic or relief?** Relief is
   diagnostic, and it shows up months before any of the four signals move. Write
   the answer down. It is the only subjective input in this skill and it is the
   most predictive thing in it.

## Output

Append to `clients/<client>.md` under `## Health`:

    ### YYYY-MM-DD
    Payment: <G/A/R> — <days to pay vs <n>-day terms>
    Scope: <G/A/R> — <n> absorbed asks, trend <up/flat>
    Tone: <G/A/R> — latency <n>d vs <n>d baseline
    Effort: <G/A/R> — <n> h/unit vs <n> at start
    What they said about it: <their explanation, verbatim> (per <person, role at
      client>, <channel>, YYYY-MM-DD) | none — nobody has said anything
    Relief test: <panic | relief>
    Verdict: <healthy | at-risk | failing>
    Action this week: <the specific conversation, and who opens it>

`Verdict:` is this skill's only published output and `daily-brief` is its reader.
Those three tokens, spelled exactly that way, or the morning brief goes quiet
about a client that is on fire.

The four signal lines are dates and counts out of the log, so they carry no
stamp — there is no speaker to name. **`What they said about it:` is the one line
here that came from a mouth, and it is the line that will be used to argue the
verdict down**, so it carries who said it, where, and when, or it is not written.
`none` is a real and common value, and a red with nobody explaining it is worse
news than a red with an excuse, not better. The stamp is also what stops the
excuse ageing into a fact: "cashflow is tight" from March is not a description of
July, and in six weeks the stamp is the only thing that says so.

## Guardrails

Do not diagnose the client's motives. "They're probably just busy" and "they're
shopping around" are both stories, and the founder already has a preferred one.
Report the four signals and the trend; the story is theirs to pick.

Do not soften a red because the founder likes them. The **CFO** will separately
find that the best-liked client is the worst-paying one, and being liked is not a
health signal — it is frequently a symptom, because pleasant clients get free
hours.

You do not fire clients. You produce the case; the founder decides and the
**Chief of Staff** logs it in `decisions/`.

No medical read on the founder's dread. "You seem burned out by this client" is
not yours — `guardrails` is explicit. Say the latency number, say the relief
answer, stop there.
