"""In-memory workspace bindings for explicit Founder OS state access."""

from __future__ import annotations

import os
import re
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional


_UNRESOLVED_CODE = "WORKSPACE_UNRESOLVED"
_UNRESOLVED_ACTION = "Ask for the business; make no read or write"
_SLUG_PATTERN = re.compile(r"[a-z0-9-]+")
_TOP_LEVEL_KEYS = frozenset({"businesses", "default", "portfolio"})
_BUSINESS_KEYS = frozenset({"home", "status"})


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
    workspace_kind: str


class WorkspaceResolver:
    def __init__(
        self,
        env: Optional[Mapping[str, str]] = None,
        home: Optional[Path] = None,
    ) -> None:
        self._env = dict(os.environ if env is None else env)
        self._home = Path.home() if home is None else Path(home)
        self._bindings: dict[str, WorkspaceBinding] = {}

    def resolve(
        self,
        project_dir: Path,
        business_slug: Optional[str] = None,
    ) -> WorkspaceBinding:
        try:
            project_root = Path(project_dir).resolve()
            registry = self._load_registry()
            root, slug, workspace_kind = self._select_workspace(
                registry,
                project_root,
                business_slug,
            )
        except WorkspaceResolutionError:
            raise
        except (OSError, TypeError, ValueError, KeyError):
            raise WorkspaceResolutionError()

        workspace_id = secrets.token_urlsafe(32)
        binding = WorkspaceBinding(
            workspace_id=workspace_id,
            business_slug=slug,
            display_path=str(root),
            root=root,
            workspace_kind=workspace_kind,
        )
        self._bindings[workspace_id] = binding
        return binding

    def get(self, workspace_id: str) -> WorkspaceBinding:
        try:
            return self._bindings[workspace_id]
        except (KeyError, TypeError):
            raise WorkspaceResolutionError()

    def validate_binding(
        self,
        binding: WorkspaceBinding,
    ) -> WorkspaceBinding:
        """Revalidate an issued binding against the current registry."""
        try:
            if not isinstance(binding, WorkspaceBinding):
                raise WorkspaceResolutionError()
            if self.get(binding.workspace_id) != binding:
                raise WorkspaceResolutionError()

            registry = self._load_registry()
            if binding.workspace_kind == "single-business":
                if registry is not None or binding.business_slug is not None:
                    raise WorkspaceResolutionError()
                return binding

            if registry is None or binding.business_slug is None:
                raise WorkspaceResolutionError()
            root, slug, workspace_kind = self._select_workspace(
                registry,
                binding.root,
                binding.business_slug,
            )
            if (
                root != binding.root
                or slug != binding.business_slug
                or workspace_kind != binding.workspace_kind
            ):
                raise WorkspaceResolutionError()
            return binding
        except WorkspaceResolutionError:
            raise
        except (OSError, TypeError, ValueError, KeyError):
            raise WorkspaceResolutionError()

    def portfolio_business_root(
        self,
        binding: WorkspaceBinding,
        business_slug: str,
    ) -> Path:
        """Resolve one active business through a current portfolio binding."""
        try:
            current = self.validate_binding(binding)
            if current.workspace_kind != "portfolio":
                raise WorkspaceResolutionError()
            if not self._valid_slug(business_slug):
                raise WorkspaceResolutionError()

            registry = self._load_registry()
            if registry is None:
                raise WorkspaceResolutionError()
            entry = registry["businesses"].get(business_slug)
            if entry is None or entry["status"] != "active":
                raise WorkspaceResolutionError()
            return Path(entry["home"]).resolve()
        except WorkspaceResolutionError:
            raise
        except (OSError, TypeError, ValueError, KeyError):
            raise WorkspaceResolutionError()

    def _select_workspace(
        self,
        registry: Optional[dict[str, Any]],
        project_root: Path,
        requested_slug: Optional[str],
    ) -> tuple[Path, Optional[str], str]:
        if registry is None:
            if requested_slug is not None:
                raise WorkspaceResolutionError()
            configured = self._env.get("FOUNDER_OS_HOME")
            root = (
                self._resolve_from_project(project_root, configured)
                if configured
                else (project_root / "founder-os").resolve()
            )
            return root, None, "single-business"

        businesses = registry["businesses"]
        portfolio = registry.get("portfolio")

        if requested_slug is not None:
            if requested_slug == "portfolio":
                if portfolio is None:
                    raise WorkspaceResolutionError()
                return Path(portfolio).resolve(), "portfolio", "portfolio"
            if not self._valid_slug(requested_slug):
                raise WorkspaceResolutionError()
            entry = businesses.get(requested_slug)
            if entry is None:
                raise WorkspaceResolutionError()
            return Path(entry["home"]).resolve(), requested_slug, "business"

        configured = self._env.get("FOUNDER_OS_HOME")
        if configured:
            configured_root = self._resolve_from_project(
                project_root,
                configured,
            )
            matches = [
                slug
                for slug, entry in businesses.items()
                if Path(entry["home"]).resolve() == configured_root
            ]
            if portfolio is not None and Path(portfolio).resolve() == configured_root:
                matches.append("portfolio")
            if len(matches) != 1:
                raise WorkspaceResolutionError()
            matched_slug = matches[0]
            return (
                configured_root,
                matched_slug,
                "portfolio" if matched_slug == "portfolio" else "business",
            )

        default = registry.get("default")
        if default is not None:
            if default == "portfolio":
                return Path(portfolio).resolve(), "portfolio", "portfolio"
            return (
                Path(businesses[default]["home"]).resolve(),
                default,
                "business",
            )

        active = [
            slug
            for slug, entry in businesses.items()
            if entry["status"] == "active"
        ]
        if len(active) != 1:
            raise WorkspaceResolutionError()
        slug = active[0]
        return Path(businesses[slug]["home"]).resolve(), slug, "business"

    @staticmethod
    def _resolve_from_project(project_root: Path, value: str) -> Path:
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            candidate = project_root / candidate
        return candidate.resolve()

    def _load_registry(self) -> Optional[dict[str, Any]]:
        path = self._home / ".founder-os" / "businesses.yaml"
        try:
            if not path.exists():
                return None
            if not path.is_file():
                raise WorkspaceResolutionError()
            source = path.read_text(encoding="utf-8")
            registry = self._parse_registry(source)
            self._validate_registry(registry)
            return registry
        except WorkspaceResolutionError:
            raise
        except (OSError, TypeError, ValueError):
            raise WorkspaceResolutionError()

    @classmethod
    def _parse_registry(cls, source: str) -> dict[str, Any]:
        if not isinstance(source, str) or "\t" in source:
            raise WorkspaceResolutionError()

        result: dict[str, Any] = {}
        businesses: dict[str, dict[str, str]] = {}
        in_businesses = False
        current_slug: Optional[str] = None

        for raw_line in source.splitlines():
            if not raw_line.strip() or raw_line.lstrip().startswith("#"):
                continue

            leading = len(raw_line) - len(raw_line.lstrip(" "))
            text = raw_line.strip()
            if ":" not in text:
                raise WorkspaceResolutionError()
            key, raw_value = text.split(":", 1)
            if not key or key != key.strip():
                raise WorkspaceResolutionError()
            value = cls._strip_inline_comment(raw_value.strip())

            if leading == 0:
                current_slug = None
                if key not in _TOP_LEVEL_KEYS or key in result:
                    raise WorkspaceResolutionError()
                if key == "businesses":
                    if value:
                        raise WorkspaceResolutionError()
                    result["businesses"] = businesses
                    in_businesses = True
                else:
                    result[key] = cls._parse_scalar(value)
                    in_businesses = False
                continue

            if not in_businesses:
                raise WorkspaceResolutionError()

            if leading == 2:
                if value or not cls._valid_slug(key) or key in businesses:
                    raise WorkspaceResolutionError()
                businesses[key] = {}
                current_slug = key
                continue

            if leading == 4 and current_slug is not None:
                entry = businesses[current_slug]
                if key not in _BUSINESS_KEYS or key in entry:
                    raise WorkspaceResolutionError()
                entry[key] = cls._parse_scalar(value)
                continue

            raise WorkspaceResolutionError()

        return result

    @staticmethod
    def _strip_inline_comment(value: str) -> str:
        quote: Optional[str] = None
        escaped = False

        for index, character in enumerate(value):
            if quote == '"':
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == quote:
                    quote = None
                continue

            if quote == "'":
                if character == quote:
                    quote = None
                continue

            if character in ("'", '"'):
                quote = character
            elif character == "#" and (
                index == 0 or value[index - 1].isspace()
            ):
                return value[:index].rstrip()

        return value

    @staticmethod
    def _parse_scalar(value: str) -> str:
        if not value:
            raise WorkspaceResolutionError()

        if value[0] in ("'", '"'):
            quote = value[0]
            if len(value) < 2 or value[-1] != quote:
                raise WorkspaceResolutionError()
            value = value[1:-1]
            if not value or quote in value:
                raise WorkspaceResolutionError()
        elif any(character in value for character in "[]{}"):
            raise WorkspaceResolutionError()

        if "\x00" in value or "\n" in value or "\r" in value:
            raise WorkspaceResolutionError()
        return value

    @classmethod
    def _validate_registry(cls, registry: dict[str, Any]) -> None:
        if not isinstance(registry, dict):
            raise WorkspaceResolutionError()
        if set(registry) - _TOP_LEVEL_KEYS:
            raise WorkspaceResolutionError()
        if "businesses" not in registry:
            raise WorkspaceResolutionError()

        businesses = registry["businesses"]
        if not isinstance(businesses, dict) or not businesses:
            raise WorkspaceResolutionError()

        for slug, entry in businesses.items():
            if not cls._valid_slug(slug):
                raise WorkspaceResolutionError()
            if not isinstance(entry, dict) or set(entry) != _BUSINESS_KEYS:
                raise WorkspaceResolutionError()
            home = entry["home"]
            status = entry["status"]
            if (
                not isinstance(home, str)
                or not home
                or not Path(home).is_absolute()
                or status not in ("active", "paused")
            ):
                raise WorkspaceResolutionError()

        portfolio = registry.get("portfolio")
        if portfolio is not None:
            if (
                not isinstance(portfolio, str)
                or not portfolio
                or not Path(portfolio).is_absolute()
            ):
                raise WorkspaceResolutionError()

        resolved_roots = [
            (slug, Path(entry["home"]).resolve())
            for slug, entry in businesses.items()
        ]
        if portfolio is not None:
            resolved_roots.append(("portfolio", Path(portfolio).resolve()))
        for index, (_, left_root) in enumerate(resolved_roots):
            for _, right_root in resolved_roots[index + 1:]:
                if (
                    left_root == right_root
                    or left_root in right_root.parents
                    or right_root in left_root.parents
                ):
                    raise WorkspaceResolutionError()

        default = registry.get("default")
        if default is None:
            return
        if not isinstance(default, str):
            raise WorkspaceResolutionError()
        if default == "portfolio":
            if portfolio is None:
                raise WorkspaceResolutionError()
            return
        if not cls._valid_slug(default):
            raise WorkspaceResolutionError()
        entry = businesses.get(default)
        if entry is None or entry["status"] != "active":
            raise WorkspaceResolutionError()

    @staticmethod
    def _valid_slug(value: object) -> bool:
        return isinstance(value, str) and _SLUG_PATTERN.fullmatch(value) is not None
