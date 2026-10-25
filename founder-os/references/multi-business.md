# Multi-business

One founder can run more than one company of one. The model does not change to
accommodate that — it repeats. **One workspace per business, each a complete,
ordinary Founder OS workspace**, plus one small portfolio workspace that holds
the single decision no per-business file can: how the founder's hours and cash
split across businesses.

Nothing here is required. A single-business install never touches any of it,
and every skill behaves exactly as before when the registry is absent.

## The registry

`~/.founder-os/businesses.yaml` — the one file that says which businesses
exist. It lives outside every workspace because it is *about* the workspaces,
and it is config, not company state: no agent owns it, the founder edits it (or
`founder-os-init` does, with the founder watching).

```yaml
# One entry per business. The slug is the identity — it names scheduler state,
# the log directory, and the business everywhere the package needs a name.
# Slugs are [a-z0-9-], and renaming one is a migration, not an edit.
businesses:
  acme:
    home: /Users/x/work/acme/founder-os
    status: active        # active | paused
  nordwind:
    home: /Users/x/work/nordwind/founder-os
    status: active
default: acme             # which business a session means when it doesn't say
portfolio: /Users/x/.founder-os/portfolio   # scaffolded with the 2nd business
```

- **`status: paused`** keeps the workspace and its history but drops the
  business from cadence scheduling and from portfolio ranking. Pausing is an
  edit; deleting an entry orphans a workspace and its scheduler state — pause
  first, delete when the workspace is archived.
- **`default:`** is what an unqualified session works on. With one active
  business it is redundant; with two it is mandatory, because "whichever
  workspace the cwd happens to resolve to" is how advice lands in the wrong
  company. It names a business, never the portfolio: `default: portfolio`
  makes the registry unreadable, because every business role would resolve to
  a workspace it is refused in.
- **`portfolio`** is a reserved selector, not a slug: no business may take it,
  and naming it (as the business in the invocation, or as the gateway's
  `business_slug`) selects the `portfolio:` workspace. Only the
  Portfolio Manager may open a session there.

## How a session picks a business

Precedence, most explicit wins:

1. **Named in the invocation** — `/founder-os:daily-brief acme`, or the
   founder says "for acme" in the session; `portfolio` names the portfolio
   workspace. Every cadence accepts the slug as its first argument and passes
   it to `context-load`.
2. **`FOUNDER_OS_HOME`** — set in the environment; each scheduled job carries
   its business's absolute home. The registry maps the path back to a slug for
   display.
3. **Registry `default:`** — when nothing above says otherwise, and only while
   that business is `active`. A paused `default:` is ignored, not refused:
   with exactly one active business that one is used; with more than one, name
   the business (1).
4. **No registry** — the classic single-business resolution: `FOUNDER_OS_HOME`
   or `./founder-os/`. This is every install before the registry existed, and
   it keeps working untouched.

`context-load` step 0 applies this order and **stamps the business into the
context line** — `Context: [acme] charter <date> | …` — so the founder sees
which company is being advised before they read the advice. With more than one
active business and no signal from 1–3, it asks. One question, one word of
answer; guessing which company a question is about is not a time saving.

## Second business: what init does differently

`founder-os-init` on a machine that already has a workspace does not clobber
it — it registers. The flow:

1. Ask for the slug and the new workspace path.
2. Scaffold the new workspace exactly as ever: the Chief of Staff's own
   `workspace_files:` entries, with every other owner creating its own file on
   its first write (`founder-os-init`, Stage 0).
3. Create or update `~/.founder-os/businesses.yaml` — adding the *existing*
   workspace under a slug too, if the registry is being created now, and asking
   which is `default:`.
4. If this is the second **active** business: create the portfolio workspace
   directory at `portfolio:` and name `/portfolio-review` as the cadence that now
   has a reason to exist. `portfolio.md` (from `portfolio_files:` in
   `ownership.yaml`) is the Portfolio Manager's, and its first `portfolio-review`
   creates it — the Chief of Staff does not write it, not even empty.

The portfolio workspace holds `portfolio.md` and nothing else. It is owned by
the **portfolio-manager** like any owned file — the ownership hook resolves it
through the registry's `portfolio:` path.

## Cadences: one fence per business

`setup-cadences` on a multi-business install runs **per business**. The
packaged `scripts/cadence_manager.py` renders and updates each exact identity;
do not edit fences with `sed` or a prefix regular expression:

```
# BEGIN founder-os:acme — cadence-manager YYYY-MM-DD
…ten lines, each carrying FOUNDER_OS_HOME=<acme's absolute home>…
# END founder-os:acme
```

- Re-running for `acme` replaces **only** the `founder-os:acme`
  fence. Another business's fence, and everything outside all fences, survives
  byte for byte. This is why the slug is in the marker: the legacy unslugged
  fence made the second business's setup silently delete the first's schedule.
- Logs split the same way: `~/.founder-os/logs/<slug>/<cadence>.log`. *Which
  business's* cadence stopped is the first question; a shared log answers the
  wrong one.
- `/portfolio-review` is scheduled **once**, in its own
  `# BEGIN founder-os:portfolio` fence, only when the registry lists two or
  more active businesses — Monday before the earliest `week-plan`, because the
  split is that plan's input.
- A legacy unslugged fence (`# BEGIN founder-os` … `# END founder-os`) is
  migrated only when preview uses `--migrate-legacy`: the manager removes that
  exact identity and rewrites the selected business under its slug. The
  preview and backup make the migration visible before confirmation.
- Preview and snapshot digests bind apply to the scheduler state the founder
  inspected. A sibling schedule added during confirmation makes apply stop;
  it is never silently overwritten.

## What deliberately does not change

- **The ownership map is one map.** The same `ownership.yaml` governs every
  workspace; `charter.md` has the same owner and the same sections in every
  business. A per-business map would be N maps drifting apart — the exact
  disease this package exists to prevent.
- **No agent reads across businesses except the portfolio-manager**, and it
  reads only the sections `portfolio-review` licenses (`goals.md` `## Bets`,
  `metrics.md` `## Close`/`## Runway`). A pipeline-coach with two pipelines
  open is advising a company that does not exist.
- **`[[slug]]` links do not cross workspaces.** `[[acme]]` in one business's
  files and the business slug `acme` in the registry are different namespaces;
  a client called Acme in business A and the founder's business acme are not
  the same entity and must never resolve to each other.
- **House rules bind everywhere**, portfolio workspace included. Rule 0 has no
  per-business exception; nothing about a second company makes anything
  sendable.
