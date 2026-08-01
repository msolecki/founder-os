# Founder OS orchestration

This reference is the canonical host-independent contract for role execution,
workflow results, receipts, and recovery. The main thread owns orchestration;
role subagents are one-level workers and never dispatch another role.

## Main-thread protocol

The main thread resolves the workspace, selects exactly one role and exactly one
`skills/{workflow}/SKILL.md`, opens the role session, and passes exactly one
capability with exactly one bounded handoff. It reads the role definition from
the one literal path `agents/{role}.md`.

When the host documents a named native role, the main thread selects it;
otherwise it selects the generic fallback under the identical envelope below.

If a role returns a delegation request, the main thread validates it, closes or
retains the current session as appropriate, and performs the next dispatch
itself. No role-to-role edge is permitted. If a role returns a workflow result,
the main thread applies the persistence gate, renders the receipt, and then
closes the session.

## Role execution envelope

Every native or generic execution envelope carries one `role`, one `role_file`,
byte-for-byte `role_instructions`, one `workflow`, one bounded `handoff`, and one
`capability`. The role uses only the six declared Founder OS state-gateway
tools. `open_role_session` remains a main-thread operation and is never exposed
to a role.

## Workflow result

A completed role returns exactly these structured inputs to the main thread:
`decision`, `evidence`, `gaps`, `return_point`, `human_action`, and
`expected_persistence`.

- `decision` is the bounded verdict or result, not a transcript.
- `evidence` names every workspace path and source date used. Each item may add
  a freshness state only under the vocabulary below.
- `gaps` names missing or stale state that constrained the result, or `none`.
- `return_point` names the cadence or date that will revisit the decision, or
  `none`.
- `human_action` is exactly one founder action still required, or `none`. A
  draft may require the founder to review and send it; it never claims a send.
- `expected_persistence` is the path list the active workflow expects the main
  thread to verify. It is empty for a read-only workflow.

This workflow result is separate from a delegation request. A result never
adds fields to, substitutes for, or relaxes the exact delegation shape below.
The role supplies structured receipt inputs; it does not render a success
receipt or assert that its own write persisted.

## User-facing receipt

After a successfully completed workflow, render exactly one compact receipt in
this order:

- **Decision:** the verdict or result.
- **Evidence:** the workspace paths and source dates used.
- **Changed:** only paths the main thread re-read and verified after the role
  returned.
- **Gaps:** missing or stale state that constrained the answer, or `none`.
- **Returns:** the cadence or date that will revisit the decision, or `none`.
- **Your move:** exactly one human action, or `none`.

For a read-only workflow, **Changed:** is `none`. The re-read path list, never
the role's prose, populates **Changed:**. Failed or uncertain persistence
produces an error receipt and never a success receipt. A draft receipt may say
the founder must review and send; it never says the draft was sent.

The receipt is conversational output. It creates no workspace file, history
record, receipt log, or second state store.

## Freshness vocabulary

Use only these three explicit states:

- `current` only when the active workflow already defines a freshness
  threshold and the source is inside that threshold;
- `stale` only when a named workflow or doctor threshold has been crossed;
- `unknown` when a required value is absent.

When there is no threshold, show the source date without assigning a freshness
state. Do not invent one global freshness period. Use no AI confidence
percentage.

## First-week guidance

First-week guidance appears only in the workflow receipt's **Your move:** field
and creates no progress file. Select exactly one action from the first matching
rule, in this order:

1. When no valid first brief exists, resume the host-specific
   `founder-os-init` skill.
2. When the current flow has just completed activation, show one `/capture`
   example.
3. On a later run with no current pipeline review, recommend
   `/pipeline-review` before the next Thursday cadence.
4. When no weekly review exists, name the next Friday `/weekly-review`.
5. Otherwise derive the one next action from the workflow result, or show
   `none`.

Do not repeat the complete first-five-actions list after each run.

## Error experience

The stable gateway code remains the machine contract. The main thread wraps it
in a human-facing error receipt containing these five facts:

1. whether any write occurred;
2. whether the original file is preserved;
3. the canonical owner or unresolved context;
4. what the system will do next;
5. whether the founder must act.

| Code | User-facing action |
|---|---|
| `WORKSPACE_UNRESOLVED` | Ask which business is active; perform no read or write. |
| `ROLE_SESSION_INVALID` | Stop the role run and return control to the main thread. |
| `PATH_OUTSIDE_WORKSPACE` | Refuse the path and name the resolved workspace boundary. |
| `ROLE_NOT_OWNER` | Name the canonical owner and request one bounded handoff. |
| `INVALID_DOCUMENT_STRUCTURE` | Preserve the file, name the structural mismatch, and route to the owner or doctor. |
| `STALE_WRITE` | Re-read, reconcile deliberately, and retry once. |
| `STATE_IO_ERROR` | Preserve the original file, stop, and surface the concrete recovery step. |

The first line must describe user impact. No error message may imply that a
failed write was persisted. The raw code may follow as technical detail.

## Delegation request

A role that needs another role returns a request to the main thread with exactly
these six fields: `role`, `workflow`, `workspace_id`, `correlation_id`,
`handoff`, and `expected_persistence`.

The target `role` must be real. `workflow` must be one non-system workflow held
by that role. `workspace_id` must equal the workspace the main thread resolved
before the first role session, and `correlation_id` must equal the active
main-thread flow; both are nonblank and NUL-free, and the main thread rejects
rather than replaces either value. `handoff` is a nonblank, NUL-free UTF-8
string of at most 4096 bytes. `expected_persistence` is a unique list of at most
16 safe relative paths owned by the target role; an empty list is valid only
when the selected workflow declares no writes.

## Native and generic parity

Native dispatch and generic fallback both read byte-identical instructions from
`agents/{role}.md`. The generic fallback must not rewrite, summarize, or copy
the role definition, and it must not use a fallback-specific role path. Both
modes load the same single `skills/{workflow}/SKILL.md` and carry the same
single capability and bounded handoff.

## Persistence gate

After the role returns, the main thread re-reads every path named in
`expected_persistence`. It verifies the expected state before closing the
session, rendering success, or advancing the workflow. A missing, stale, or
wrongly owned write stops the transition and receives the error experience
above; it is never silently treated as persisted.
