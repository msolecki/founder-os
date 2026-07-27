"""Executable entry point for the Founder OS local stdio MCP server."""

from __future__ import annotations

from pathlib import Path
import sys


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
