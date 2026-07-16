---
name: setup-cadences
description: Turn the eight cadences into real scheduled jobs on the founder's own machine — run once, after their first brief, so the package stops waiting to be opened
---

# Setup Cadences

Every skill in this package is inert until somebody types its name. That is the
whole problem. The eight cadences are the only thing that makes this an OS
rather than a folder of prompts, and a cadence that fires when the founder
remembers to fire it is not a cadence — it is a reminder they are already
ignoring. This skill is how eight skills become a schedule on the founder's own
machine, once, in one confirmation.

**Claude Code cannot ship a schedule inside a plugin.** Not a gap to work around
later — a fact to design against now:

- `/loop` is session-scoped and **auto-expires seven days after creation**. A
  quarterly cadence that dies in a week is not a quarterly cadence.
- Cloud routines need a claude.ai account, run at a one-hour minimum interval,
  are research-preview — and have **no local file access**. That last one ends
  it: the workspace is local markdown, and a daily brief that cannot read
  `goals.md` is not a brief, it is a horoscope.
- Desktop scheduled tasks work, and every user has to build their own set. That
  is the work this skill does for them.

So the schedule lives on the host: the founder's own crontab, calling Claude
Code headless from the workspace directory. **Cron reads the host's local
timezone.** There is nothing to rewrite and no zone to carry — 08:00 in the
crontab is 08:00 where the founder is sitting, and it stays 08:00 through their
own DST changes. That was the old runtime's problem. It is not inherited.

## When to use

Once, **after** onboarding has ended on the founder's first `daily-brief` — not
during it. A founder who has never seen a brief has no reason to want eight of
them, and onboarding is arranged to end on a payoff. A machine-modification
confirmation is not a payoff.

Run it again when the ground moves underneath the crontab, because the crontab
does not notice:

- `FOUNDER_OS_HOME` moved. Every line now `cd`s somewhere that isn't there.
- Claude Code was reinstalled elsewhere. The absolute binary path is now fiction.
- A Node major upgrade, if the binary resolves through `nvm` — see step 2.

Not to check whether the cadences are still firing. That is `founder-os-doctor`,
which already has the check: *cadence gone quiet*, no file in `reviews/daily/`
for five weekdays.

## Inputs

House rule 1 says no advice without state. **The state this skill reads is the
host, not the workspace** — that is the one thing that makes it different from
every other skill here, and it is why it reads almost nothing you own:

- `uname -s` — `Darwin`, `Linux`, or something you must be honest about (step 1).
- `command -v claude` — the binary. If this is empty, the skill stops (step 2).
- `crontab -l` — what is already there. It exits `1` with *no crontab for user*
  when there is nothing, which is not an error, it is an empty answer.
- The **absolute** path of `$FOUNDER_OS_HOME`, default `./founder-os/`. Resolve
  it with `pwd`. Step 3 is about why a relative default is a landmine here.
- `charter.md` `## Timezone` — read only, to compare against the host's zone. The
  Chief of Staff owns that file. You do not edit it.

## The three ways a cron cadence fails silently

Read these before the steps, because every step below exists to close one of
them. **A cron job that fails silently is worse than no cron job at all** — no
cron job is a gap the founder can feel, and a silently broken one is a gap they
believe is covered. It fails every weekday at 08:00 forever and nobody ever
finds out. It has no error to notice. It has no output to miss. It just isn't
there, and by the time `founder-os-doctor` says *cadence gone quiet*, that is
five days late and it cannot say why.

1. **The binary doesn't resolve.** `claude` is on the founder's PATH because
   their shell profile put it there. Cron does not run their shell and does not
   read their profile: it runs `/bin/sh` with `PATH=/usr/bin:/bin`. A bare
   `claude -p "/daily-brief"` works perfectly in the terminal you test it in and
   is `command not found` at 08:00. Step 2.
2. **The output goes nowhere.** Cron mails stdout to the local user. On a
   typical macOS or desktop Linux box there is no MTA configured, so an expired
   auth token prints its error into a spool nobody has ever opened. Step 6.
3. **The machine was asleep.** Cron does not catch up. A laptop with its lid
   shut at 08:00 skips the brief entirely and leaves no trace that it was
   skipped — no log line, no error, no file. Step 4 is the decision rule for
   this one, and on a laptop it is the failure that actually happens.

## The schedule

| skill | when | cron |
|---|---|---|
| `/daily-brief` | weekdays 08:00 | `0 8 * * 1-5` |
| `/week-plan` | Monday 08:30 | `30 8 * * 1` |
| `/weekly-review` | Friday 16:00 | `0 16 * * 5` |
| `/pipeline-review` | Thursday 10:00 | `0 10 * * 4` |
| `/follow-up-sweep` | Friday 14:00 | `0 14 * * 5` |
| `/content-plan` | Wednesday 10:00 | `0 10 * * 3` |
| `/revenue-review` | 1st of month 09:00 | `0 9 1 * *` |
| `/quarterly-planning` | Jan/Apr/Jul/Oct 1st 11:00 | `0 11 1 1,4,7,10 *` |

Eight, and not nine. `monthly-review` and `annual-review` are deliberately
unscheduled and adding them is not an improvement: `revenue-review` is already
the monthly close, and scheduling a second monthly ritual gives the founder two
competing ones and a reason to skip both. `annual-review` firing unprompted
eleven months after install is noise — the founder invokes that one on purpose
or not at all.

`0 11 1 1,4,7,10 *` names the months, so the quarterly lands on 1 Jan / 1 Apr /
1 Jul / 1 Oct from any install date. There is no start date to carry and no
drift to patch.

## Steps

1. **Detect the OS. Say what you found, and stop if it isn't one you can write.**
   `uname -s` → `Darwin` is macOS, `Linux` is Linux. Both get a crontab.

   Anything else — `MINGW*`, `MSYS*`, `CYGWIN*`, or no `crontab` binary at all —
   is where you stop guessing. Print the eight lines from the table, say plainly
   that Windows Task Scheduler is where they go and that you cannot write them
   from here, and stop. A wrong cron line on a machine you guessed at is the
   silent failure in section 1, installed by the tool that promised to prevent it.

   **WSL reports `Linux` and is the trap.** If `/proc/version` contains
   `microsoft`, say so before writing anything: the cron daemon does not start on
   boot in a WSL distro, and WSL2 shuts the VM down when the last terminal
   closes. The crontab will be flawless and will never fire once. That is
   honest-and-stop territory, not a `service cron start` you talk them into.

2. **Resolve `claude` to an absolute path — or write nothing.**
   `command -v claude`. Empty means Claude Code is not on this PATH under this
   shell, and the correct move is to stop and say so. Eight cron lines pointing
   at a binary that does not exist is not a partial success, it is failure mode 1
   pre-installed.

   Then **throw the PATH away and hardcode the result.** `/usr/local/bin/claude`,
   `~/.local/bin/claude` — whatever it resolved to, that literal string goes in
   the cron line. This is the single edit that separates a cadence that fires
   from one that doesn't, and testing it in your terminal proves nothing, because
   your terminal has the PATH and cron never will.

   **If the path contains `/.nvm/`, say so now.** It resolved to something like
   `~/.nvm/versions/node/v22.1.0/bin/claude`, and that pins the cadences to a
   Node version the founder will upgrade without ever connecting the two events.
   Every cadence stops that day. They are two lines: pin it and know that a Node
   major is what breaks it, or reinstall Claude Code natively so the path stops
   moving. Name the trade; let them pick; do not silently write the shim.

3. **Resolve the workspace to an absolute path — `pwd`, never `./`.**
   `FOUNDER_OS_HOME` defaults to `./founder-os/`, and cron's working directory is
   `$HOME`. So a relative default in a cron line does not error: it resolves
   against the wrong directory and finds either nothing, or — worse and not rare —
   some other `~/founder-os/` that an earlier init scaffolded and nobody filled
   in.

   That is the nastiest failure this skill can ship, because it produces no error
   at all. It produces a brief. A perfectly formatted brief every weekday about
   an empty company, written to a `reviews/daily/` the founder never opens,
   while the real workspace goes untouched for a month. Every line gets
   `cd <absolute path> && ...`.

4. **Pick the mechanism, and pick it by whether the machine is awake.**
   The rule, and it has one threshold:

   > **Does this machine sleep at any hour in the table? Laptop → `launchd`.
   > Always-on desktop or server → `crontab`.**

   Cron skips a missed run and never mentions it. launchd
   `StartCalendarInterval` runs the job when the machine next wakes — late, but
   run. For a founder on a MacBook that is shut at 08:00 three mornings a week,
   that difference is the entire product: cron gives them five briefs a fortnight
   and no explanation for the gaps.

   On macOS, launchd is one `~/Library/LaunchAgents/com.founder-os.<slug>.plist`
   per cadence — `ProgramArguments` (the absolute binary, `-p`,
   `/founder-os:<slug>`, `--permission-mode`, `acceptEdits`, `--max-turns`,
   `50`), `EnvironmentVariables` carrying `FOUNDER_OS_HOME` (launchd agents get
   no shell profile either), `WorkingDirectory` (the workspace *parent*, step
   3's path), `StandardOutPath` / `StandardErrorPath` (step 6's log), and
   `StartCalendarInterval` with `Hour`/`Minute`/`Weekday` (0 and 7 are both
   Sunday). The quarterly is an *array* of four dicts, one per `Month`. Load
   with `launchctl bootstrap gui/$(id -u) <plist>`. Same eight
   schedules, same three resolved paths, different file format — everything
   below about backup, confirmation and the smoke test applies unchanged.

   On Linux the same laptop problem exists and the same answer is a systemd user
   timer with `Persistent=true`. Say that in one line if they are on a laptop.
   Do not build it unless they ask.

5. **Back up the crontab before you touch it, and say where in the same breath.**

       mkdir -p ~/.founder-os
       crontab -l > ~/.founder-os/crontab-backup-$(date +%Y%m%d-%H%M%S).txt 2>/dev/null || true

   The `|| true` is not sloppiness — `crontab -l` exits `1` when there is no
   crontab, and without it the `&&` chain aborts on a founder whose crontab was
   simply empty. The backup path goes in the confirmation, before they say yes,
   not in a summary afterwards. Clobbering somebody's existing cron is
   unforgivable and it is one careless `crontab <file>` away.

   **The backup lives in `~/.founder-os/`, outside the workspace, on purpose.**
   Every file in the workspace has exactly one owner and this one has none —
   dropping it in `$FOUNDER_OS_HOME` would create an unowned file that
   `state-integrity` refuses to write for the rest of the package's life.

6. **Show the exact block. Ask once. One question, not eight.**
   Print it fenced, with all three resolved paths substituted in, exactly as it
   will be written:

       # BEGIN founder-os — /setup-cadences, YYYY-MM-DD. Do not remove these markers.
       0 8 * * 1-5        cd /Users/x/work && FOUNDER_OS_HOME=/Users/x/work/founder-os /Users/x/.local/bin/claude -p "/founder-os:daily-brief" --permission-mode acceptEdits --max-turns 50 >> /Users/x/.founder-os/logs/daily-brief.log 2>&1
       30 8 * * 1         cd /Users/x/work && FOUNDER_OS_HOME=/Users/x/work/founder-os /Users/x/.local/bin/claude -p "/founder-os:week-plan" --permission-mode acceptEdits --max-turns 50 >> /Users/x/.founder-os/logs/week-plan.log 2>&1
       0 16 * * 5         cd /Users/x/work && FOUNDER_OS_HOME=/Users/x/work/founder-os /Users/x/.local/bin/claude -p "/founder-os:weekly-review" --permission-mode acceptEdits --max-turns 50 >> /Users/x/.founder-os/logs/weekly-review.log 2>&1
       0 10 * * 4         cd /Users/x/work && FOUNDER_OS_HOME=/Users/x/work/founder-os /Users/x/.local/bin/claude -p "/founder-os:pipeline-review" --permission-mode acceptEdits --max-turns 50 >> /Users/x/.founder-os/logs/pipeline-review.log 2>&1
       0 14 * * 5         cd /Users/x/work && FOUNDER_OS_HOME=/Users/x/work/founder-os /Users/x/.local/bin/claude -p "/founder-os:follow-up-sweep" --permission-mode acceptEdits --max-turns 50 >> /Users/x/.founder-os/logs/follow-up-sweep.log 2>&1
       0 10 * * 3         cd /Users/x/work && FOUNDER_OS_HOME=/Users/x/work/founder-os /Users/x/.local/bin/claude -p "/founder-os:content-plan" --permission-mode acceptEdits --max-turns 50 >> /Users/x/.founder-os/logs/content-plan.log 2>&1
       0 9 1 * *          cd /Users/x/work && FOUNDER_OS_HOME=/Users/x/work/founder-os /Users/x/.local/bin/claude -p "/founder-os:revenue-review" --permission-mode acceptEdits --max-turns 50 >> /Users/x/.founder-os/logs/revenue-review.log 2>&1
       0 11 1 1,4,7,10 *  cd /Users/x/work && FOUNDER_OS_HOME=/Users/x/work/founder-os /Users/x/.local/bin/claude -p "/founder-os:quarterly-planning" --permission-mode acceptEdits --max-turns 50 >> /Users/x/.founder-os/logs/quarterly-planning.log 2>&1
       # END founder-os

   The `>> …log 2>&1` is failure mode 2 and it is not optional. Without it the
   only record of six weeks of auth errors is a mail spool with no reader. Eight
   logs rather than one, because *which* cadence stopped is the question, and a
   shared log buries the quarterly failure under sixty daily successes.

   **Four parts of that line are not decoration, and each one is a cadence that
   silently never works without it:**

   - `FOUNDER_OS_HOME=<absolute workspace>` — cron runs `/bin/sh` with a bare
     environment and reads no shell profile. A variable set in `.zshrc` never
     reaches this line, the skill falls back to `./founder-os/`, and the founder
     gets a perfectly formatted brief about an empty company. Embed it.
   - `cd <workspace parent>`, not the workspace itself — `cd` into the workspace
     and any relative fallback resolves to `<workspace>/founder-os/`, a nested
     phantom that scaffolds itself on first write.
   - `/founder-os:<slug>`, the namespaced form — bare `/daily-brief` works only
     while no other plugin or user command claims the name. This line is written
     once and must survive whatever gets installed next year; the day it
     collides, the log says "unknown command" forever and nobody reads the log.
   - `--permission-mode acceptEdits --max-turns 50` — a headless session cannot
     approve its own `Write`. Without the flag, every cadence runs, is denied
     its one output file, and produces a folder of permission denials shaped
     exactly like briefs. `--max-turns` is the backstop that stops a wedged run
     from stacking onto the next one. `acceptEdits` accepts *file edits* — it
     does not grant Bash, WebFetch or MCP, so House Rule 0 stands exactly where
     it stood. The founder's own main thread was always allowed to write; this
     flag only lets the machine say so at 08:00 with nobody watching.

   **Then ask one question, and offer the opt-out in the same message.** Not
   eight confirmations, not a walkthrough. They see the block, they see the
   backup path, they say yes or they don't.

7. **Write it. The fence is what makes a second run safe.**

       crontab -l 2>/dev/null | sed '/# BEGIN founder-os/,/# END founder-os/d' > "$tmp"
       cat block >> "$tmp"
       crontab "$tmp"

   Strip the old fence, append the new one, install. Everything outside the
   markers survives byte for byte, which is what the diff in step 6 promised.

   **Without the fence, the second run is the bug.** Sixteen lines, two daily
   briefs racing at 08:00 into the same `reviews/daily/` file, and a founder
   whose fix is `crontab -r` — deleting their own cron along with ours to make it
   stop. Re-running this skill has to be boring.

8. **Prove it fires under cron's environment, not yours.** Do not learn at 08:00
   tomorrow. Reproduce what cron actually hands the job:

       env -i HOME="$HOME" PATH=/usr/bin:/bin SHELL=/bin/sh /bin/sh -c \
         'cd /Users/x/work && FOUNDER_OS_HOME=/Users/x/work/founder-os /Users/x/.local/bin/claude -p "/founder-os:daily-brief" --permission-mode acceptEdits --max-turns 50'

   `env -i` is the point. Your shell's PATH is exactly what makes a broken line
   look fine, so strip it to the four variables cron sets and run the real
   cadence. It writes a real brief, which is a payoff and not a test artifact —
   `daily-brief` is the Chief of Staff's write, not this skill's.

   Also verify the flags exist before writing a single cron line:
   `<binary> --help | grep -q -- --permission-mode` — an older claude that does
   not know the flag would otherwise fail every scheduled job with an argument
   error, in the logs, forever. If it is missing, stop and say the binary is
   too old for scheduled cadences; hand-invocation still works.

   **On macOS this test passes and cron still fails, if the workspace is under
   `~/Desktop`, `~/Documents`, `~/Downloads`, or iCloud Drive.** You are running
   under the terminal's TCC grants; `/usr/sbin/cron` has its own, and it has
   none. It cannot prompt, so it does not — it gets a permission error at 08:00
   and mails it nowhere. If step 3's path is under a protected directory: either
   grant `/usr/sbin/cron` Full Disk Access in System Settings → Privacy &
   Security, or use `launchd` from step 4, which runs in the founder's session
   and can actually ask. Say which one applies before they close the terminal.

   **Failure mode: credentials.** A cron job runs outside the login session.
   If the claude binary stores its credential in the macOS keychain, the first
   post-reboot run before the founder logs in can fail auth — once, then work
   after login. The log will say so; the doctor cannot. If every line of a log
   is an auth error, the fix is to run any interactive `claude` session once
   and let the keychain unlock, not to edit the crontab.

9. **Check the host zone against `charter.md` `## Timezone`, and only say it.**
   Cron is host-local, so the host is right about when 08:00 is — a mismatch does
   not break a single cadence. It means the charter is stale, which is the Chief
   of Staff's file and their problem. One line, and hand it over. Do not edit it,
   and do not "fix" the crontab to match a stale charter.

10. **End on the schedule, not on a chore.** They confirmed once and it is
    installed. Say what fires next and when — *tomorrow 08:00, `daily-brief`* —
    and stop. Do not close with a checklist, do not ask them to watch a log, do
    not suggest a monthly review of the cron lines. There is nothing left for
    them to do, and saying so is the deliverable.

## The opt-out is a real answer

Offer it in step 6, in the same message as the diff, and offer it straight — not
as the thing you say before talking them round.

**The cadence is the point. Cron is a mechanism.** A calendar reminder at 08:00
that says *run `/daily-brief`* is a legitimate implementation of this entire
skill, and on some machines it is the better one. A laptop that sleeps through
every cadence hour gets more from a reminder than from a crontab. And a reminder
has the one property cron structurally lacks: **it fails loudly.** A founder who
ignores a calendar alert knows they ignored it. A founder whose cron broke in
week two believes for a month that the system is running.

If they say no, say the eight skills work exactly as well typed by hand, tell
them the hours from the table so the reminder lands on the right ones, and stop.
No degraded-mode framing, no asking again next session. This is not a downgrade
and treating it as one is how a tool that modifies machines gets uninstalled.

## Removal

Uninstalling the plugin does not touch the crontab — the fence outlives the
package and keeps firing a claude that no longer knows the skills. The removal
is one command, and it is the founder's to run:

    crontab -l | sed '/# BEGIN founder-os/,/# END founder-os/d' | crontab -

On launchd: `launchctl bootout gui/$(id -u)/com.founder-os.<slug>` per cadence,
then delete the plists. Say this at install time, in the confirmation — a tool
that modifies a machine owes the founder the way back *before* they say yes.

## Output

- The founder's crontab (or eight LaunchAgent plists), carrying the eight lines
  fenced by `# BEGIN founder-os` / `# END founder-os`, with the absolute binary
  path, the absolute workspace path, and a per-cadence log redirect. Everything
  outside the fence untouched.
- `~/.founder-os/crontab-backup-<timestamp>.txt` — the crontab as it was, named
  out loud before the founder said yes.
- `~/.founder-os/logs/` — eight append-only logs, the only place a failure will
  ever be visible. When `founder-os-doctor` reports *cadence gone quiet*, this
  is what answers *why*.
- One line on screen naming the next cadence and its hour. Nothing else.
- Nothing written to `$FOUNDER_OS_HOME`. This skill owns no workspace file and
  declares no `metadata.writes`, because it writes the host, not the company —
  except through `daily-brief`, which step 8 runs and which writes as its own
  owner.

## Guardrails

**One confirmation, and it is not a formality.** House Rule 0 is *never
outbound, never money*, and a local crontab is neither — nothing is sent and
nothing is spent, so the rule does not reach this. What does reach it is that
this is the one skill in the package that changes something outside the
workspace. Show the exact block, name the backup path, ask, then act. Never
write a crontab the founder has not read.

**Scope is the fence, the backup, and the log directory. Nothing else on that
machine.** Being permitted to write a crontab is not a general licence to
administer a host. Never `sudo`. Never touch `/etc/crontab`, `/etc/cron.d/`, or
another user's crontab — the user crontab or nothing. If it cannot be written
without elevation, stop and say so.

**Never reorder, rewrite, or drop a line outside the markers**, including one
that looks obsolete or duplicated. It is not yours, you do not know what it does,
and the diff you showed them said it would survive.

Never write a line whose binary path you did not resolve, or whose workspace path
is relative. Both produce a cadence that reports nothing and does nothing, which
is the exact outcome this skill exists to prevent — and shipping it under this
skill's name is worse than never running, because the founder now believes it is
handled.

Do not schedule a ninth cadence. Do not schedule `monthly-review` or
`annual-review`. See *The schedule*.

**A `%` in a crontab line is a newline, not a percent sign.** Everything after
the first unescaped one becomes stdin to the command. This matters the day
someone improves a log path to `…/daily-brief-$(date +%F).log` and turns one
working line into two broken ones. Escape it as `\%` or leave it out.

**Do not restrict day-of-month and day-of-week in the same line.** Cron ORs them
rather than ANDing them — the one trap in the syntax that a competent person
walks into. The eight lines above dodge it by never constraining both, but the
edit that breaks it is the obvious one: *first Monday of the month* written as
`0 9 1-7 * 1` fires every day of the first week **and** every Monday of the year,
which is a monthly close that runs eleven times a month.
