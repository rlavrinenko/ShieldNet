from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_PLUGIN_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,95}$")
_VERSION_RE = re.compile(r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")


class PluginManifestError(ValueError):
    pass


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str, *, field_name: str = "version") -> "Version":
        match = _VERSION_RE.fullmatch(value.strip())
        if match is None:
            raise PluginManifestError(f"{field_name} must use semantic versioning (x.y.z)")
        return cls(*(int(match.group(name)) for name in ("major", "minor", "patch")))


@dataclass(frozen=True)
class PluginComponents:
    backend: bool = False
    frontend: bool = False
    bot: bool = False

    @classmethod
    def from_value(cls, value: Any) -> "PluginComponents":
        if value is None:
            return cls()
        if not isinstance(value, dict):
            raise PluginManifestError("components must be an object")
        return cls(
            backend=bool(value.get("backend", False)),
            frontend=bool(value.get("frontend", False)),
            bot=bool(value.get("bot", False)),
        )

    def as_dict(self) -> dict[str, bool]:
        return {"backend": self.backend, "frontend": self.frontend, "bot": self.bot}


@dataclass(frozen=True)
class PluginEntrypoints:
    backend: str | None = None
    bot: str | None = None
    frontend: str | None = None

    @classmethod
    def from_value(cls, value: Any) -> "PluginEntrypoints":
        if value is None:
            return cls()
        if not isinstance(value, dict):
            raise PluginManifestError("entrypoints must be an object")
        normalized: dict[str, str | None] = {}
        for key in ("backend", "bot", "frontend"):
            item = value.get(key)
            if item is None:
                normalized[key] = None
            elif isinstance(item, str) and item.strip():
                normalized[key] = item.strip()
            else:
                raise PluginManifestError(f"entrypoints.{key} must be a non-empty string")
        return cls(**normalized)

    def as_dict(self) -> dict[str, str]:
        return {
            key: value
            for key, value in {
                "backend": self.backend,
                "bot": self.bot,
                "frontend": self.frontend,
            }.items()
            if value is not None
        }


@dataclass(frozen=True)
class PluginManifest:
    plugin_key: str
    name: str
    version: str
    description: str | None = None
    author: str | None = None
    min_core_version: str | None = None
    capabilities: tuple[str, ...] = field(default_factory=tuple)
    permissions: tuple[str, ...] = field(default_factory=tuple)
    dependencies: dict[str, str | None] = field(default_factory=dict)
    components: PluginComponents = field(default_factory=PluginComponents)
    entrypoints: PluginEntrypoints = field(default_factory=PluginEntrypoints)
    raw: dict[str, Any] = field(default_factory=dict, compare=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, source: str = "plugin.json") -> "PluginManifest":
        if not isinstance(data, dict):
            raise PluginManifestError(f"{source}: manifest root must be an object")

        plugin_key = str(data.get("id") or data.get("plugin_key") or "").strip().lower()
        name = str(data.get("name") or "").strip()
        version = str(data.get("version") or "").strip()
        if not plugin_key or not name or not version:
            raise PluginManifestError(f"{source}: id, name and version are required")
        if _PLUGIN_ID_RE.fullmatch(plugin_key) is None:
            raise PluginManifestError(f"{source}: invalid plugin id")
        Version.parse(version)

        min_core = data.get("min_core") or data.get("min_core_version")
        min_core_version = str(min_core).strip() if min_core is not None else None
        if min_core_version:
            Version.parse(min_core_version, field_name="min_core_version")

        capabilities = cls._string_tuple(data.get("capabilities"), "capabilities")
        permissions = cls._string_tuple(data.get("permissions"), "permissions")
        dependencies = cls._dependencies(data.get("dependencies"))
        components = PluginComponents.from_value(data.get("components"))
        entrypoints = PluginEntrypoints.from_value(data.get("entrypoints"))

        for component_name, enabled in components.as_dict().items():
            if enabled and component_name != "frontend" and getattr(entrypoints, component_name) is None:
                raise PluginManifestError(
                    f"{source}: entrypoints.{component_name} is required when components.{component_name}=true"
                )

        normalized = dict(data)
        normalized.update(
            {
                "id": plugin_key,
                "name": name,
                "version": version,
                "components": components.as_dict(),
                "entrypoints": entrypoints.as_dict(),
                "capabilities": list(capabilities),
                "permissions": list(permissions),
                "dependencies": dependencies,
            }
        )
        if min_core_version:
            normalized["min_core"] = min_core_version

        return cls(
            plugin_key=plugin_key,
            name=name,
            version=version,
            description=cls._optional_string(data.get("description")),
            author=cls._optional_string(data.get("author")),
            min_core_version=min_core_version,
            capabilities=capabilities,
            permissions=permissions,
            dependencies=dependencies,
            components=components,
            entrypoints=entrypoints,
            raw=normalized,
        )

    @classmethod
    def from_path(cls, path: Path) -> "PluginManifest":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise PluginManifestError(f"{path}: invalid JSON: {exc.msg}") from exc
        except OSError as exc:
            raise PluginManifestError(f"{path}: cannot read manifest: {exc}") from exc
        return cls.from_dict(data, source=str(path))

    def supports_core(self, core_version: str) -> bool:
        if not self.min_core_version:
            return True
        return Version.parse(core_version, field_name="core_version") >= Version.parse(
            self.min_core_version, field_name="min_core_version"
        )


    @staticmethod
    def _dependencies(value: Any) -> dict[str, str | None]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise PluginManifestError("dependencies must be an object")
        result: dict[str, str | None] = {}
        for raw_key, raw_version in value.items():
            key = str(raw_key).strip().lower()
            if _PLUGIN_ID_RE.fullmatch(key) is None:
                raise PluginManifestError(f"dependencies contains invalid plugin id: {raw_key}")
            if raw_version is None or str(raw_version).strip() in {"", "*"}:
                result[key] = None
                continue
            version = str(raw_version).strip()
            if version.startswith(">="):
                version = version[2:].strip()
            Version.parse(version, field_name=f"dependencies.{key}")
            result[key] = version
        return result

    @staticmethod
    def _optional_string(value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @staticmethod
    def _string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
        if value is None:
            return ()
        if not isinstance(value, list):
            raise PluginManifestError(f"{field_name} must be an array")
        result: list[str] = []
        seen: set[str] = set()
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise PluginManifestError(f"{field_name} must contain non-empty strings")
            normalized = item.strip()
            if normalized not in seen:
                seen.add(normalized)
                result.append(normalized)
        return tuple(result)
