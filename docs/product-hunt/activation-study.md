# Founder OS activation study

This is an empty operational worksheet, not proof that a study happened. Use it
only with people who voluntarily agree to test the clean installation. Assign a
consented participant ID; do not record names, contact details, or company data.

**Do not paste workspace contents.** Record whether the promised outcome was
reached, how long it took, and the first break—not the founder's answers.

## Cohort record

| Consented participant ID | First brief persisted | Elapsed minutes | Resume preserved protected sections | Integrity incident | First confusion | Outcome useful | Seven-day return |
|---|---|---:|---|---|---|---|---|
| P-01 |  |  |  |  |  |  |  |
| P-02 |  |  |  |  |  |  |  |
| P-03 |  |  |  |  |  |  |  |
| P-04 |  |  |  |  |  |  |  |
| P-05 |  |  |  |  |  |  |  |

## Interruption assignment

Each participant gets one Assigned interruption boundary. End the session only
after the named checkpoint is visibly persisted, then let the participant use
the printed resume command in a new session.

| Consented participant ID | Assigned interruption boundary | Protected populated sections | Expected post-resume write |
|---|---|---|---|
| P-01 | after Business checkpoint, before Customer | populated charter sections and the install target checkpoint | persist `offer.md` |
| P-02 | after offer checkpoint, before Quarter | prior protected sections plus the populated `offer.md` sections | persist the ready `goals.md` `## Bets` section |
| P-03 | after ready-bet checkpoint, before Money | prior protected sections plus the ready `## Bets` section | persist the activation close, then runway, in `metrics.md` |
| P-04 | after activation close, before runway | prior protected sections plus the existing `## Close — YYYY-MM` block | append `## Runway — as of YYYY-MM-DD` to the same `metrics.md` |
| P-05 | after runway checkpoint, before first brief | prior protected sections, both financial blocks, and unrelated existing queue records | persist or update only the chosen queue item, then write the daily review |

## Observation protocol

1. Confirm voluntary participation and assign the pseudonymous ID.
2. Start from a clean Claude Code install and an empty disposable workspace.
3. Do not rescue the participant; record only the first confusing instruction.
4. At the assigned boundary, hash each protected populated section or record
   locally, from its heading or record identifier to its boundary. Do not hash
   the whole file: an expected append can correctly change `metrics.md` or
   `queue.md`. Do not copy paths, hashes or contents into this worksheet.
5. End the session, then observe the participant resume from the generated
   command in a new session.
6. Compare only the protected sections or records after resume, and separately
   confirm the expected post-resume write. Record `yes` only when every protected
   value is byte-for-byte unchanged. Under Integrity incident, record `none`,
   `overwrite`, `ownership breach`, or `false completion`.
7. Stop the activation timer when a valid first brief is persisted in the
   resolved workspace. Do not include the seven-day wait in elapsed minutes.
8. Ask whether its `## The one thing` is useful without copying the answer.
9. Seven days later, record whether the participant ran `/weekly-review` as a
   separate outcome.

## Separate Codex clean-install check

Codex status before this test is **beta/manual**. Run one separate clean install
and record only the operational result; a passing run is evidence for a later
host-status decision, not an automatic parity claim.

| Codex status | First brief persisted | Elapsed minutes | Resume preserved protected sections | Integrity incident | First break |
|---|---|---:|---|---|---|
| beta/manual |  |  |  |  |  |

Do not count the Codex result toward the five-person Claude Code gate. If it
fails, keep Codex labeled beta/manual everywhere and record the first break.

## Go/no-go calculation

- Activation: at least 4/5 persist a valid first brief.
- Speed: P50 at most 10 minutes; target P90 at most 15 minutes.
- Integrity: 0 overwrites, ownership breaches, or false completions, and every
  resumed participant preserves every protected populated section or record
  byte-for-byte while the expected new write succeeds.
- Return: at least 3/5 run `/weekly-review` within seven days.

If a changed step misses a threshold, do not reinterpret the result. Fix that
step, rerun its tests, and repeat the cohort with new consented participants.

## Launch cohort summary

Record aggregate counts only: consented testers, confirmed activations, P50,
P90, seven-day returns, and the first repeated blocker. Product Hunt visits,
ranking, repository traffic, stars, and reactions are supporting indicators;
they are not activation.
