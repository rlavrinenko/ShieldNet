from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from sqlalchemy import select

from app.db.session import AsyncSessionFactory
from app.models.plugins import PluginEvent, PluginRegistry
from app.plugins.dependencies import PluginDependencyError, PluginDependencyResolver
from app.plugins.loader import BackendPluginLoader, PluginLoadError
from app.plugins.manifest import PluginManifest, PluginManifestError

logger = logging.getLogger(__name__)
PLUGIN_ROOT = Path("/opt/shieldnet/plugins")
CORE_VERSION = "7.0.0"


@dataclass(frozen=True)
class PluginRuntimeStatus:
    plugin_key: str
    loaded: bool
    version: str
    error: str | None = None


class PluginRuntime:
    def __init__(self) -> None:
        self.loader = BackendPluginLoader()
        self.statuses: dict[str, PluginRuntimeStatus] = {}

    async def start(self, app: FastAPI) -> None:
        async with AsyncSessionFactory() as session:
            records = list(
                (
                    await session.execute(
                        select(PluginRegistry).where(
                            PluginRegistry.enabled.is_(True),
                            PluginRegistry.healthy.is_(True),
                        )
                    )
                ).scalars().all()
            )

            manifests: list[PluginManifest] = []
            roots: dict[str, Path] = {}
            for record in records:
                try:
                    path = Path(record.manifest_path)
                    manifest = PluginManifest.from_path(path)
                    if not manifest.supports_core(CORE_VERSION):
                        raise PluginLoadError(
                            f"Plugin requires ShieldNet {manifest.min_core_version} or newer"
                        )
                    manifests.append(manifest)
                    roots[manifest.plugin_key] = path.parent
                except (PluginManifestError, PluginLoadError) as exc:
                    await self._record_failure(session, record, str(exc))

            try:
                plan = PluginDependencyResolver().resolve(manifests)
            except PluginDependencyError as exc:
                logger.exception("Plugin dependency resolution failed")
                for manifest in manifests:
                    record = next(item for item in records if item.plugin_key == manifest.plugin_key)
                    await self._record_failure(session, record, str(exc))
                await session.commit()
                return

            for manifest in plan.ordered:
                if not manifest.components.backend:
                    self.statuses[manifest.plugin_key] = PluginRuntimeStatus(
                        plugin_key=manifest.plugin_key,
                        loaded=False,
                        version=manifest.version,
                    )
                    continue
                record = next(item for item in records if item.plugin_key == manifest.plugin_key)
                try:
                    loaded = await self.loader.load(roots[manifest.plugin_key], manifest)
                    router = loaded.instance.router()
                    if router is not None:
                        app.include_router(
                            router,
                            prefix=f"/api/v1/plugins/{manifest.plugin_key}",
                            tags=[f"Plugin: {manifest.name}"],
                        )
                    self.statuses[manifest.plugin_key] = PluginRuntimeStatus(
                        plugin_key=manifest.plugin_key,
                        loaded=True,
                        version=manifest.version,
                    )
                    record.last_error = None
                    session.add(
                        PluginEvent(
                            plugin_key=manifest.plugin_key,
                            event_type="runtime.loaded",
                            message=f"Plugin {manifest.version} loaded",
                        )
                    )
                except Exception as exc:
                    logger.exception("Unable to load plugin %s", manifest.plugin_key)
                    await self._record_failure(session, record, str(exc))
            await session.commit()

    async def stop(self) -> None:
        for plugin_key in reversed(tuple(self.loader.loaded)):
            try:
                await self.loader.unload(plugin_key)
            except Exception:
                logger.exception("Unable to unload plugin %s", plugin_key)
        self.statuses.clear()

    def snapshot(self) -> list[PluginRuntimeStatus]:
        return sorted(self.statuses.values(), key=lambda item: item.plugin_key)

    async def _record_failure(
        self,
        session: Any,
        record: PluginRegistry,
        error: str,
    ) -> None:
        record.healthy = False
        record.last_error = error
        self.statuses[record.plugin_key] = PluginRuntimeStatus(
            plugin_key=record.plugin_key,
            loaded=False,
            version=record.version,
            error=error,
        )
        session.add(
            PluginEvent(
                plugin_key=record.plugin_key,
                event_type="runtime.failed",
                status="error",
                message=error,
            )
        )


plugin_runtime = PluginRuntime()
