# Founder OS workspace

Read and follow `founder-os/CLAUDE.md` as the canonical project guidance. It is
shared by Claude Code and Codex; do not duplicate or weaken its house rules in
this file.

Prompt changes start in `.promptscript/`, never in generated plugin files.
Run `pnpm run compile:promptscript`, `python3 scripts/validate_package.py
founder-os`, and the unit tests under `tests/` before declaring the work
complete.
