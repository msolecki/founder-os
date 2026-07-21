# Generator Robustness Batch

Completed `BUG-004`: `generate_commands.py` now rejects a plugin root without `skills/` with a clean `FAIL:` and exit code 1, covered by `tests/test_generate_commands.py`.

Evidence: validator 13/49/0, command check current, full suite 99 tests OK.
