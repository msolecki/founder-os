# Founder OS Threat Model

Version: 1.0.0
Last updated: 2026-08-14

## 1. System Overview

Founder OS is a local plugin package compiled from PromptScript sources. The
repository contains canonical `.promptscript/` declarations, native skill
resources, generated Claude Code and Codex adapters, Python hook programs, and
an MCP server that exposes bounded workspace state operations over stdio.

The normal flow is:

1. A maintainer edits canonical PromptScript or native skill sources.
2. The local PromptScript CLI resolves and validates imports, then emits
   target-specific instructions and adapters.
3. The sync script copies only owned generated files into `founder-os/`.
4. Claude Code or Codex starts the plugin and invokes hooks and the
   `founder-os-state` MCP server.
5. Role agents read or write local Markdown workspace state through the
   gateway, subject to role capabilities and ownership rules.

The package is local-first. The gateway uses JSON-RPC over standard input and
output, and the package does not provide an outbound messaging or payment
service. Runtime references and workspace data are intended to stay on the
founder's machine.

## 2. Trust Boundaries

### Maintainer and repository boundary

PromptScript files, native skills, generated files, build tools, and tests are
repository content. A maintainer or CI process is trusted to review source
changes. Generated files are less trusted than canonical sources and are
reconciled by the sync script.

### Host and plugin boundary

Claude Code and Codex load generated instructions, hooks, and MCP
configuration. The host controls process execution, tool permissions,
environment variables, and plugin installation. `PLUGIN_ROOT` and
`CLAUDE_PLUGIN_ROOT` are host-provided paths and must not be treated as
untrusted content after path resolution without validating the installed
package.

### Agent and gateway boundary

Role agents are intentionally restricted to the Founder OS state gateway.
The ownership guard denies direct file and outbound capabilities for known
roles. Generic agents remain under the host permission model and receive only
path ownership protections from the hook.

### Gateway and workspace boundary

The gateway reads and writes files under the resolved Founder OS workspace.
Workspace content is user-controlled and may be stale, malformed, or
attacker-influenced if another local process can write to it. Ownership maps,
path containment checks, stale-write checks, and role capabilities protect
writes.

### Local overlay boundary

The `_local/` workspace overlay is founder-controlled and can extend ownership
data. It is additive to the packaged map and must not silently remove packaged
ownership constraints.

## 3. Critical Assets

| Asset | Sensitivity | Required protection |
| --- | --- | --- |
| Founder workspace Markdown | High | Path containment, ownership checks, stale-write protection |
| Ownership maps and role capabilities | High | Integrity, fail-closed behavior for known roles |
| Founder instructions and native skill content | High | Source integrity, generated-output ownership markers |
| MCP protocol and tool schemas | High | Strict request validation, bounded allowlist |
| Plugin manifests and hook configuration | High | Review, package validation, no unexpected tools |
| Local registry and business routing data | High | Parse safely, avoid cross-business disclosure |
| Dependency lockfile and compiler | Medium | Pin versions, validate before release |
| Diagnostics and test output | Medium | Avoid secrets and user workspace content |

## 4. Attack Surface

- PromptScript imports and local fragment paths.
- Native skill frontmatter and adjacent Codex adapter YAML.
- The PromptScript compiler and generated plugin files.
- The sync script's source and destination path handling.
- Claude and Codex hook JSON configuration.
- Hook input received from host tool events.
- The stdio MCP JSON-RPC transport.
- MCP tool names and arguments.
- Workspace paths, ownership maps, and local overlays.
- Environment variables used to locate the installed plugin and workspace.
- Python and Node dependencies used during build and validation.
- Installed package copies and release artifacts.

## 5. Threat Analysis

### Spoofing

- A forged role identity could obtain another role's gateway capability.
  Mitigations include exact role allowlists, normalized host namespaces,
  capability hashes, session correlation, and expiry checks. Residual risk is
  host-level compromise, which is outside the plugin boundary.
- A malicious plugin path could make hooks load attacker-controlled guidance.
  The installed package must be validated and the host must provide the
  expected plugin root. Runtime checks should treat missing or invalid guidance
  as a warning and must not invent replacement policy.

### Tampering

- A repository or local process could replace generated files with content that
  is later shipped. The sync process uses ownership markers, detects unmarked
  destination conflicts, refuses source symlinks, and removes only owned stale
  outputs.
- PromptScript imports could introduce unexpected declarations or duplicate
  agent definitions. Strict validation, explicit manifests, canonical agent
  completeness checks, and duplicate-fragment rejection mitigate this risk.
- A concurrent workspace writer could overwrite a role's update. Gateway writes
  use an expected digest or equivalent stale-write check and should report
  conflict rather than silently overwrite.

### Repudiation

- A local process could deny changing workspace state if writes are not
  attributable. Role session correlation, owner identity, and decision logs
  provide local audit context. The package does not claim tamper-proof audit
  history against a user with filesystem access.

### Information disclosure

- A role could read or write another role's state. Gateway tool schemas,
  ownership maps, role capabilities, and packaged tool allowlists constrain
  access. Cross-business routing must resolve the business before reading
  state.
- Secrets could enter generated instructions, skills, or diagnostics. Source
  review, package validation, and safe-reference checks reduce exposure.
  Credentials must remain in host secret stores or environment configuration,
  not in `.prs`, Markdown, or logs.
- Malformed JSON-RPC or filesystem errors could reveal local paths. Error
  responses are bounded, but stderr and host debug logs may still contain
  local paths and must not be shared as public artifacts.

### Denial of service

- Very large JSON-RPC messages, workspace trees, or recursive state inputs
  could consume local memory or CPU. The stdio server validates message shape,
  and callers should impose host-level request and output limits.
- A broken or malicious import graph could make compilation expensive or
  fail release builds. Strict validation, lockfiles, and bounded local imports
  reduce this risk.
- A malformed ownership overlay could disable useful operations. The hook
  prefers a safe no-op or explicit diagnostic over guessing ownership.

### Elevation of privilege

- A role with shell, web, arbitrary MCP, or nested-agent access could bypass
  the no-outbound and one-level orchestration rules. Package validation rejects
  outbound tools and the guard denies nested-agent tools for recognized roles.
- Path traversal or symlink escape could grant writes outside the workspace.
  Canonical source checks, path containment, symlink refusal, and ownership
  validation are required at each file boundary.
- Host tools may still be more powerful than the plugin can observe. The
  ownership guard is defense in depth, not a sandbox for hostile host
  processes.

## 6. Vulnerability Pattern Library

### Path traversal and symlink escape

Reject absolute paths, parent traversal, unexpected path segments, symlink
components, and resolved paths outside the configured workspace. Do not use
string prefix checks as the only containment test.

### Command injection

Do not interpolate workspace or user content into shell commands. Prefer
argument arrays and fixed interpreters. Never add outbound tools to a role's
allowlist.

### Unsafe deserialization

Parse JSON with the standard decoder and validate object shape before use.
Parse YAML with a safe loader and do not construct arbitrary Python objects.

### Authorization bypass

Use exact allowlists for role names, gateway servers, tools, and ownership
entries. Check the role capability and workspace binding on every role-bound
operation rather than trusting a prior request.

### Race and stale write

Require an expected content digest for updates to shared state. Re-read and
reconcile on mismatch. Do not delete or replace an unmarked destination file.

### Secret exposure

Keep credentials out of PromptScript, native skills, manifests, diagnostics,
and generated files. Redact or bound errors before displaying them to an
assistant or writing them to a log.

## 7. Security Testing Strategy

- Run strict PromptScript validation on every source change.
- Compile every configured target and verify generated outputs are current.
- Run package validation, command catalog checks, local-link checks, and
  installed-copy smoke tests.
- Run the complete Python unit test suite, including gateway, hook, ownership,
  sync, and release metadata contracts.
- Test malformed JSON-RPC, unknown tools, invalid lifecycle transitions,
  invalid paths, symlinks, stale writes, duplicate imports, and duplicate
  declarations.
- Review changes to role tool lists, MCP manifests, hook commands, ownership
  maps, and dependency lockfiles as security-sensitive.
- Scan uncommitted or committed changes with the repository security skill
  before release.

## 8. Assumptions and Accepted Risks

- The host application and the local operating system are trusted to launch
  the intended plugin files and to enforce their own permission prompts.
- A user with write access to the repository, plugin directory, or workspace
  can alter local behavior. This model does not protect against that user.
- The plugin is not an internet-facing service and does not provide durable
  tamper-proof audit storage.
- Generic non-role agents may retain host-authorized capabilities. The hook
  protects ownership paths but is not a complete sandbox around arbitrary
  shell access.
- Optional local tools and dependency availability can reduce enforcement or
  validation coverage. Release checks must fail rather than silently skipping
  required gates.

## 9. Changelog

- 1.0.0: Initial local-first STRIDE model for the PromptScript-built Founder
  OS plugin and its bounded state gateway.
