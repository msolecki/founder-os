# Parser Portability Batch

Completed `BUG-003` and `ARCH-002`.

- Shared `SYSTEM_SKILLS`, `UNIVERSAL_SKILLS`, `STANDALONE_SKILLS`, and `parse_frontmatter` in `scripts/_package.py`.
- Normalized CRLF input before frontmatter parsing.
- Added a CRLF contract test; package validation and command generation remain green.
- Evidence: validator 13/49/0, compile OK, 98 tests OK, generated commands current.
