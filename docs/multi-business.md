# Multi-business

One founder can run more than one company of one. The model does not change to
accommodate that — it **repeats**. One workspace per business, each a complete,
ordinary Founder OS workspace, plus one small portfolio workspace holding the
single decision no per-business file can: how the founder's hours and cash split
across businesses.

**Nothing here is required.** A single-business install never touches any of it,
and every skill behaves exactly as before when the registry is absent. The
canonical procedure is
[`references/multi-business.md`](../founder-os/references/multi-business.md); this
page is the operator's summary.

## The registry

`~/.founder-os/businesses.yaml` is the one file that says which businesses exist.
It lives *outside* every workspace because it is *about* the workspaces, and it is
config, not company state — no agent owns it; the founder edits it (or
`founder-os-init` does, with the founder watching).

```yaml
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

- The **slug** is the identity. It names the cron fence, the log directory, and
  the business everywhere the package needs a name. Slugs are `[a-z0-9-]`, and
  renaming one is a migration, not an edit.
- **`status: paused`** keeps the workspace and its history but drops the business
  from cadence scheduling and portfolio ranking. Pause first, delete only once
  the workspace is archived — deleting an entry orphans its crontab lines.
- **`default:`** is what an unqualified session works on. Redundant with one
  active business, mandatory with two — "whichever workspace the cwd resolves to"
  is how advice lands in the wrong company.

## How a session picks a business

Precedence, most explicit wins:

1. **Named in the invocation** — `/founder-os:daily-brief acme`, or "for acme" in
   the session. Every cadence accepts the slug as its first argument.
2. **`FOUNDER_OS_HOME`** — set in the environment (this is what cron lines do;
   each carries its business's absolute home).
3. **Registry `default:`** — when nothing above says otherwise.
4. **No registry** — the classic single-business resolution: `FOUNDER_OS_HOME`
   or `./founder-os/`. Every install before the registry existed keeps working
   untouched.

`context-load` step 0 applies this order and **stamps the business into the
context line** — `Context: [acme] charter <date> | …` — so the founder sees which
company is being advised before they read the advice. With more than one active
business and no signal from 1–3, it asks. One question, one word of answer;
guessing which company a question is about is not a time saving.

## The portfolio workspace

The portfolio workspace (default `~/.founder-os/portfolio/`) holds `portfolio.md`
and nothing else. It is owned by the **Portfolio Manager** like any owned file —
the ownership hook resolves it through the registry's `portfolio:` path.

`portfolio.md`'s sections:

- `## Businesses` — the map (slug, status, one line each).
- `## Allocation` — the current split of hours and cash, with a date on it.
- `## Starving` — what the split is underfeeding, with the number that says so.
- `## Review` — the last `portfolio-review` verdict.

`/portfolio-review` is the one cadence that crosses workspace boundaries. It ranks
the businesses against each other, sets this week's split, and names what the
split is starving. It runs Monday 08:15, before the earliest `week-plan`, because
the split is that plan's input.

## What a second business does to `init`

`founder-os-init` on a machine that already has a workspace does not clobber it —
it **registers**:

1. Ask for the slug and the new workspace path.
2. Scaffold the new workspace exactly as ever (from `workspace_files:`).
3. Create or update `~/.founder-os/businesses.yaml` — adding the *existing*
   workspace under a slug too if the registry is being created now, and asking
   which is `default:`.
4. If this is the **second active** business: scaffold the portfolio workspace
   from `portfolio_files:` and name `/portfolio-review` as the cadence that now
   has a reason to exist.

## What deliberately does not change

- **The ownership map is one map.** The same `ownership.yaml` governs every
  workspace; `charter.md` has the same owner and sections in every business. A
  per-business map would be N maps drifting apart — the exact disease the package
  exists to prevent.
- **No agent reads across businesses except the Portfolio Manager**, and it reads
  only the sections `portfolio-review` licenses (`goals.md` `## Bets`,
  `metrics.md` `## Close`/`## Runway`). A pipeline-coach with two pipelines open
  is advising a company that does not exist.
- **`[[slug]]` links do not cross workspaces.** `[[acme]]` in one business's
  files and the business slug `acme` in the registry are different namespaces; a
  client called Acme in business A and the founder's business `acme` are not the
  same entity and must never resolve to each other.
- **House rules bind everywhere**, portfolio workspace included. Rule 0 has no
  per-business exception; nothing about a second company makes anything sendable.

## The doctor's multi-business check

`founder-os-doctor` check #14, *Portfolio dark*: two active businesses with a
missing, drifted, or 21-days-silent `portfolio.md`. See
[`troubleshooting.md`](troubleshooting.md).
