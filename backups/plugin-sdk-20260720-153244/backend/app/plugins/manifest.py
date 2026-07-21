from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

_PLUGIN_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,95}$")
_ENTRYPOINT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*:[A-Za-z_][A-Za-z0-9_]*$")


class PluginManifestError(ValueError):
    pass


class PluginComponents(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backend: bool = False
    frontend: bool = False
    bot: bool = False


class PluginManifest(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str = Field(alias="plugin_key")
    name: str = Field(min_length=1, max_length=160)
    version: str = Field(min_length=1, max_length=40)
    description: str | None = None
    author: str | None = Field(default=None, max_length=160)
    min_core_version: str | None = Field(default=None, alias="min_core")
    components: PluginComponents = Field(default_factory=PluginComponents)
    capabilities: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    backend_entrypoint: str | None = None

    @field_validator("id", mode="before")
    @classmethod
    def normalize_id(cls, value: Any) -> str:
        plugin_key = str(value or "").strip().lower()
        if not _PLUGIN_KEY_RE.fullmatch(plugin_key):
            raise ValueError("plugin id must match ^[a-z0-9][a-z0-9_-]{1,95}$")
        return plugin_key

    @field_validator("name", "version", mode="before")
    @classmethod
    def strip_required_text(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator("capabilities", "permissions", mode="before")
    @classmethod
    def normalize_string_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("must be an array")
        result: list[str] = []
        seen: set[str] = set()
        for item in value:
            normalized = str(item).strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                result.append(normalized)
        return result

    @field_validator("backend_entrypoint")
    @classmethod
    def validate_backend_entrypoint(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not _ENTRYPOINT_RE.fullmatch(normalized):
            raise ValueError("backend_entrypoint must use module.path:ClassName")
        return normalized

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "PluginManifest":
        normalized = dict(data)
        if "plugin_key" not in normalized and "id" in normalized:
            normalized["plugin_key"] = normalized["id"]
        if "min_core" not in normalized and "min_core_version" in normalized:
            normalized["min_core"] = normalized["min_core_version"]
        try:
            return cls.model_validate(normalized)
        except ValidationError as exc:
            raise PluginManifestError(str(exc)) from exc

    def registry_payload(self) -> dict[str, Any]:
        payload = self.model_dump(by_alias=False, exclude_none=True)
        payload["id"] = payload.pop("plugin_key", self.id)
        payload["min_core"] = payload.pop("min_core_version", self.min_core_version)
        payload["components"] = self.components.model_dump()
        return payload


def load_plugin_manifest(path: Path) -> tuple[PluginManifest, bytes, str]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise PluginManifestError(f"{path}: unable to read manifest: {exc}") from exc

    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PluginManifestError(f"{path}: invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise PluginManifestError(f"{path}: manifest root must be an object")

    try:
        manifest = PluginManifest.from_mapping(data)
    except PluginManifestError as exc:
        raise PluginManifestError(f"{path}: {exc}") from exc

    checksum = hashlib.sha256(raw).hexdigest()
    return manifest, raw, checksum
