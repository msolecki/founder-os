"""Executable entry point for the Founder OS local stdio MCP server."""

from __future__ import annotations

from pathlib import Path
import sys


# The state layer needs POSIX locking and dir_fd-relative opens; native
# Windows Python has neither, so stop with an actionable message instead of
# an ImportError traceback.
WINDOWS_UNSUPPORTED = (
    "Founder OS does not run on native Windows: its state server needs POSIX "
    "file locking and symlink-safe opens. Install WSL (wsl --install), open "
    "Claude Code inside the WSL shell, and run setup again there."
)
if sys.platform == "win32":
    sys.stderr.write(WINDOWS_UNSUPPORTED + "\n")
    raise SystemExit(1)


if __package__ in (None, ""):
    package_root = str(Path(__file__).resolve().parents[1])
    if package_root not in sys.path:
        sys.path.insert(0, package_root)

from mcp.protocol import serve


def main() -> int:
    """Run the line-oriented stdio server."""
    return serve(sys.stdin, sys.stdout, sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
