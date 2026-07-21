from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from app.plugins.manifest import PluginManifest


@dataclass(frozen=True)
class PluginContext:
    manifest: PluginManifest
    plugin_root: Path
    services: dict[str, Any]


class BackendPlugin(ABC):
    """Stable backend contract for ShieldNet plugins."""

    def __init__(self, context: PluginContext) -> None:
        self.context = context

    @property
    def key(self) -> str:
        return self.context.manifest.plugin_key

    @abstractmethod
    def router(self) -> APIRouter | None:
        """Return the plugin API router or None when the plugin has no HTTP API."""

    async def startup(self) -> None:
        """Called after the plugin instance is loaded."""

    async def shutdown(self) -> None:
        """Called before the plugin instance is unloaded."""
