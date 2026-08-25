"""Access to the two maps the dashboard reads: ownership, and the registry.

Both are parsed by the modules the gateway already uses. This file exists so
exactly one place in the dashboard knows where the plugin lives and how to reach
those parsers — everything downstream receives plain values.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Tuple


def plugin_root() -> Path:
    """The packaged `founder-os/` directory containing this file's grandparent."""
    return Path(__file__).resolve().parents[2]


def _load_sibling(name: str, relative: str):
    """Load one of the gateway's modules by path, under a private name.

    Registered in `sys.modules` before it executes because `dataclass` resolves
    a class's annotations through `sys.modules[cls.__module__]`, and a module
    absent from that table makes the decorator raise on import.
    """
    key = "fos_dashboard_dep_%s" % name
    cached = sys.modules.get(key)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(key, plugin_root() / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        del sys.modules[key]
        raise
    return module


@dataclass(frozen=True)
class OwnershipView:
    workspace_files: Tuple[str, ...]
    portfolio_files: Tuple[str, ...]
    derived_paths: Tuple[str, ...]
    sections: Mapping[str, Tuple[str, ...]]
    owners: Mapping[str, str]


def load_ownership(path: Optional[Path] = None) -> OwnershipView:
    ownership = _load_sibling("ownership", "mcp/ownership.py")
    target = Path(path) if path else plugin_root() / "references" / "ownership.yaml"
    document = ownership.load_document(target)
    owners = {}
    for role, paths in document["owns"].items():
        for owned in paths:
            owners[owned] = role
    sections = {
        key: tuple(values) for key, values in document["sections"].items()}
    return OwnershipView(
        workspace_files=tuple(document["workspace_files"]),
        portfolio_files=tuple(document["portfolio_files"]),
        derived_paths=tuple(document["derived_files"]),
        sections=sections,
        owners=owners,
    )


@dataclass(frozen=True)
class Business:
    slug: str
    home: Path
    status: str


def active_businesses(
    home: Optional[Path] = None,
    cwd: Optional[Path] = None,
    env: Optional[Mapping[str, str]] = None,
) -> Tuple[Tuple[Business, ...], Optional[Path], int]:
    """Every active business, the portfolio root, and how many were paused.

    Falls back to the classic single-workspace resolution when no registry
    exists, which is every install that predates the registry and every founder
    running one company.
    """
    workspaces = _load_sibling("workspaces", "mcp/workspaces.py")
    environment = dict(os.environ if env is None else env)
    registry = workspaces.load_registry(Path.home() if home is None else Path(home))
    if registry is None:
        declared = environment.get("FOUNDER_OS_HOME")
        base = Path(cwd or Path.cwd())
        root = Path(declared).expanduser() if declared else base / "founder-os"
        return ((Business(slug="", home=root, status="active"),), None, 0)

    businesses = []
    paused = 0
    for slug in sorted(registry["businesses"]):
        entry = registry["businesses"][slug]
        status = entry.get("status", "active")
        if status != "active":
            paused += 1
            continue
        businesses.append(
            Business(slug=slug, home=Path(entry["home"]), status=status))
    portfolio = registry.get("portfolio")
    return (tuple(businesses),
            Path(portfolio) if portfolio else None,
            paused)
