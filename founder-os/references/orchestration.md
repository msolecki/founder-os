# Founder OS orchestration

This reference is the canonical host-independent contract for role execution. The main thread owns orchestration; role subagents are one-level workers and never dispatch another role.

## Main-thread protocol

The main thread resolves the workspace, selects exactly one role and exactly one `skills/{workflow}/SKILL.md`, opens the role session, and passes exactly one capability with exactly one bounded handoff. It reads the role definition from the one literal path `agents/{role}.md`.

When the host documents a named native role, the main thread selects it;
otherwise it selects the generic fallback under the identical envelope below.

If a role returns a delegation request, the main thread validates it, closes or retains the current session as appropriate, and performs the next dispatch itself. No role-to-role edge is permitted.

## Role execution envelope

Every native or generic execution envelope carries one `role`, one `role_file`, byte-for-byte `role_instructions`, one `workflow`, one bounded `handoff`, and one `capability`. The role uses only the six declared Founder OS state-gateway tools. `open_role_session` remains a main-thread operation and is never exposed to a role.

## Delegation request

A role that needs another role returns a request to the main thread with exactly these six fields: `role`, `workflow`, `workspace_id`, `correlation_id`, `handoff`, and `expected_persistence`.

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

After the role returns, the main thread re-reads every path named in `expected_persistence`. It verifies the expected state before closing the session or advancing the workflow. A missing, stale, or wrongly owned write stops the transition and is reported as a bounded handoff; it is never silently treated as persisted.
