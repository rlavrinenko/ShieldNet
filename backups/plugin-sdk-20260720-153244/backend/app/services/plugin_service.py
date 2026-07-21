from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plugins import PluginEvent, PluginRegistry
from app.plugins.manifest import PluginManifest, PluginManifestError, load_plugin_manifest
from app.schemas.plugins import PluginManifestResponse, PluginScanResponse

PLUGIN_ROOT = Path("/opt/shieldnet/plugins")


class PluginService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_plugins(self) -> list[PluginManifestResponse]:
        result = await self.session.execute(select(PluginRegistry).order_by(PluginRegistry.name))
        return [self._response(item) for item in result.scalars().all()]

    async def scan(self) -> PluginScanResponse:
        PLUGIN_ROOT.mkdir(parents=True, exist_ok=True)
        result = await self.session.execute(select(PluginRegistry))
        existing = {item.plugin_key: item for item in result.scalars().all()}
        seen: set[str] = set()
        discovered = 0
        updated = 0
        errors: list[str] = []

        for path in sorted(PLUGIN_ROOT.glob("*/plugin.json")):
            try:
                manifest, _, checksum = load_plugin_manifest(path)
                key = manifest.id
                seen.add(key)
                item = existing.get(key)
                if item is None:
                    item = PluginRegistry(
                        plugin_key=key,
                        name=manifest.name,
                        version=manifest.version,
                        manifest_path=str(path),
                    )
                    self.session.add(item)
                    discovered += 1
                else:
                    updated += 1
                payload = manifest.registry_payload()
                item.name = manifest.name
                item.version = manifest.version
                item.description = manifest.description
                item.author = manifest.author
                item.min_core_version = manifest.min_core_version
                item.manifest_path = str(path)
                item.manifest = payload
                item.checksum = checksum
                item.healthy = True
                item.last_error = None
            except PluginManifestError as exc:
                errors.append(str(exc))
            except Exception as exc:  # third-party plugin must not stop registry scan
                errors.append(f"{path}: unexpected scan error: {exc}")

        missing = 0
        for key, item in existing.items():
            if key not in seen:
                item.healthy = False
                item.enabled = False
                item.last_error = "Plugin manifest is missing from disk"
                missing += 1

        self.session.add(
            PluginEvent(
                plugin_key="core",
                event_type="registry.scan",
                status="success" if not errors else "warning",
                message=f"Discovered {discovered}, updated {updated}, missing {missing}",
                metadata_json={"errors": errors},
            )
        )
        await self.session.commit()
        return PluginScanResponse(discovered=discovered, updated=updated, missing=missing, errors=errors)

    async def set_enabled(self, plugin_key: str, enabled: bool) -> PluginManifestResponse:
        result = await self.session.execute(
            select(PluginRegistry).where(PluginRegistry.plugin_key == plugin_key)
        )
        item = result.scalar_one_or_none()
        if item is None:
            raise LookupError("Plugin not found")
        if enabled and not item.healthy:
            raise ValueError("Plugin cannot be enabled while unhealthy")
        if enabled:
            manifest_path = Path(item.manifest_path)
            manifest, _, checksum = load_plugin_manifest(manifest_path)
            if manifest.id != item.plugin_key:
                raise ValueError("Plugin manifest id no longer matches registry")
            if item.checksum and checksum != item.checksum:
                raise ValueError("Plugin files changed; scan registry before enabling")
            if manifest.components.backend and not manifest.backend_entrypoint:
                raise ValueError("Backend plugin has no backend_entrypoint")
        item.enabled = enabled
        self.session.add(
            PluginEvent(
                plugin_key=plugin_key,
                event_type="plugin.enabled" if enabled else "plugin.disabled",
                message=f"Plugin {'enabled' if enabled else 'disabled'}",
            )
        )
        await self.session.commit()
        await self.session.refresh(item)
        return self._response(item)

    @staticmethod
    def _response(item: PluginRegistry) -> PluginManifestResponse:
        manifest = item.manifest or {}
        components = manifest.get("components") or {
            "backend": bool(manifest.get("backend")),
            "frontend": bool(manifest.get("frontend")),
            "bot": bool(manifest.get("bot")),
        }
        capabilities = manifest.get("capabilities") or []
        return PluginManifestResponse(
            plugin_key=item.plugin_key,
            name=item.name,
            version=item.version,
            description=item.description,
            author=item.author,
            min_core_version=item.min_core_version,
            manifest_path=item.manifest_path,
            signature_status=item.signature_status,
            enabled=item.enabled,
            healthy=item.healthy,
            last_error=item.last_error,
            capabilities=[str(value) for value in capabilities],
            components={str(key): bool(value) for key, value in components.items()},
            manifest=manifest,
            updated_at=item.updated_at,
        )
