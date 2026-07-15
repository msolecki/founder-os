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
   plainly. One red is a note in the log. Three reds means the founder already
   knew and has been managing their own feelings instead of the client.
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
    Relief test: <panic | relief>
    Verdict: <healthy | watch | failing>
    Action this week: <the specific conversation, and who opens it>

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
