from __future__ import annotations

from abc import ABC

from app.plugins.context import PluginContext


class ShieldNetPlugin(ABC):
    """Base contract for backend plugins."""

    def __init__(self, context: PluginContext) -> None:
        self.context = context

    async def startup(self) -> None:
        return None

    async def shutdown(self) -> None:
        return None

    async def healthcheck(self) -> dict[str, object]:
        return {"status": "healthy"}
