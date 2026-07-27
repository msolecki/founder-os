"""In-memory workspace bindings for explicit Founder OS state access."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional


_UNRESOLVED_CODE = "WORKSPACE_UNRESOLVED"
_UNRESOLVED_ACTION = "Ask for the business; make no read or write"


class WorkspaceResolutionError(Exception):
    def __init__(self) -> None:
        super().__init__(_UNRESOLVED_CODE)
        self.code = _UNRESOLVED_CODE
        self.action = _UNRESOLVED_ACTION


@dataclass(frozen=True)
class WorkspaceBinding:
    workspace_id: str
    business_slug: Optional[str]
    display_path: str
    root: Path


class WorkspaceResolver:
    """Resolve a workspace and issue an opaque, process-local binding."""

    def __init__(
        self,
        env: Optional[Mapping[str, str]] = None,
        home: Optional[Path] = None,
    ) -> None:
        self._env = dict(os.environ if env is None else env)
        self._home = Path.home() if home is None else Path(home)
        self._bindings = {}

    def resolve(
        self,
        project_dir: Path,
        business_slug: Optional[str] = None,
    ) -> WorkspaceBinding:
        project_root = Path(project_dir).resolve()
        registry = self._load_registry()
        try:
            root, slug = self._select_workspace(
                registry,
                project_root,
                business_slug,
            )
        except (OSError, TypeError, ValueError, KeyError):
            raise WorkspaceResolutionError()

        workspace_id = secrets.token_urlsafe(32)
        binding = WorkspaceBinding(
            workspace_id=workspace_id,
            business_slug=slug,
            display_path=str(root),
            root=root,
        )
        self._bindings[workspace_id] = binding
        return binding

    def get(self, workspace_id: str) -> WorkspaceBinding:
        try:
            return self._bindings[workspace_id]
        except (KeyError, TypeError):
            raise WorkspaceResolutionError()

    def _select_workspace(
        self,
        registry: Optional[Mapping[str, Any]],
        project_root: Path,
        requested_slug: Optional[str],
    ) -> tuple[Path, Optional[str]]:
        if registry is None:
            if requested_slug:
                raise WorkspaceResolutionError()
            configured = self._env.get("FOUNDER_OS_HOME")
            root = (
                self._resolve_from_project(project_root, configured)
                if configured
                else (project_root / "founder-os").resolve()
            )
            return root, None

        businesses = registry["businesses"]
        portfolio = registry.get("portfolio")
        if requested_slug:
            if requested_slug == "portfolio":
                if not isinstance(portfolio, str) or not Path(portfolio).is_absolute():
                    raise WorkspaceResolutionError()
                return Path(portfolio).resolve(), "portfolio"
            entry = businesses.get(requested_slug)
            if not isinstance(entry, Mapping):
                raise WorkspaceResolutionError()
            return self._business_root(entry), requested_slug

        configured = self._env.get("FOUNDER_OS_HOME")
        if configured:
            configured_root = self._resolve_from_project(project_root, configured)
            matches = [
                slug
                for slug, entry in businesses.items()
                if isinstance(entry, Mapping)
                and self._business_root(entry) == configured_root
            ]
            if isinstance(portfolio, str) and Path(portfolio).is_absolute():
                if Path(portfolio).resolve() == configured_root:
                    matches.append("portfolio")
            if len(matches) != 1:
                raise WorkspaceResolutionError()
            return configured_root, matches[0]

        default = registry.get("default")
        if isinstance(default, str):
            if default == "portfolio":
                if not isinstance(portfolio, str) or not Path(portfolio).is_absolute():
                    raise WorkspaceResolutionError()
                return Path(portfolio).resolve(), "portfolio"
            entry = businesses.get(default)
            if not isinstance(entry, Mapping):
                raise WorkspaceResolutionError()
            return self._business_root(entry), default

        active = [
            slug
            for slug, entry in businesses.items()
            if isinstance(entry, Mapping) and entry.get("status") == "active"
        ]
        if len(active) != 1:
            raise WorkspaceResolutionError()
        slug = active[0]
        return self._business_root(businesses[slug]), slug

    @staticmethod
    def _resolve_from_project(project_root: Path, value: str) -> Path:
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            candidate = project_root / candidate
        return candidate.resolve()

    @staticmethod
    def _business_root(entry: Mapping[str, Any]) -> Path:
        home = entry.get("home")
        status = entry.get("status")
        if not isinstance(home, str) or status not in ("active", "paused"):
            raise WorkspaceResolutionError()
        return Path(home).expanduser().resolve()

    def _load_registry(self) -> Optional[Mapping[str, Any]]:
        path = self._home / ".founder-os" / "businesses.yaml"
        try:
            if not path.exists():
                return None
            if not path.is_file():
                raise WorkspaceResolutionError()
            source = path.read_text(encoding="utf-8")
            parsed = self._parse_yaml(source)
            if not isinstance(parsed, Mapping):
                raise WorkspaceResolutionError()
            businesses = parsed.get("businesses")
            if not isinstance(businesses, Mapping):
                raise WorkspaceResolutionError()
            return parsed
        except (OSError, TypeError, ValueError):
            raise WorkspaceResolutionError()

    @staticmethod
    def _parse_yaml(source: str) -> Mapping[str, Any]:
        try:
            import yaml  # type: ignore
        except ImportError:
            return WorkspaceResolver._parse_simple_registry(source)

        try:
            parsed = yaml.safe_load(source)
        except Exception:
            raise WorkspaceResolutionError()
        if not isinstance(parsed, Mapping):
            raise WorkspaceResolutionError()
        return parsed

    @staticmethod
    def _parse_simple_registry(source: str) -> Mapping[str, Any]:
        """Parse the deliberately small canonical registry shape without PyYAML."""
        result = {}
        businesses = {}
        in_businesses = False
        current_slug = None

        for raw_line in source.splitlines():
            if not raw_line.strip() or raw_line.lstrip().startswith("#"):
                continue
            indent = len(raw_line) - len(raw_line.lstrip(" "))
            text = raw_line.strip()
            if ":" not in text:
                raise WorkspaceResolutionError()
            key, value = text.split(":", 1)
            value = value.strip().strip("'\"")

            if indent == 0:
                current_slug = None
                if key == "businesses" and not value:
                    in_businesses = True
                    result["businesses"] = businesses
                elif key in ("default", "portfolio") and value:
                    in_businesses = False
                    result[key] = value
                else:
                    raise WorkspaceResolutionError()
            elif in_businesses and indent == 2 and not value:
                current_slug = key
                if not current_slug or current_slug in businesses:
                    raise WorkspaceResolutionError()
                businesses[current_slug] = {}
            elif in_businesses and indent == 4 and current_slug and value:
                if key not in ("home", "status") or key in businesses[current_slug]:
                    raise WorkspaceResolutionError()
                businesses[current_slug][key] = value
            else:
                raise WorkspaceResolutionError()

        if not businesses:
            raise WorkspaceResolutionError()
        return result
