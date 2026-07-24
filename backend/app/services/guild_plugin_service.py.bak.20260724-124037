from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.plugins import GuildPluginInstallation, PluginMarketplaceItem
from app.schemas.guild_plugins import GuildPluginInstallationResponse, GuildPluginMarketplaceItemResponse

class GuildPluginConflictError(Exception):
    pass

class GuildPluginService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def marketplace(self, guild_id: int):
        plugins = list((await self.session.execute(
            select(PluginMarketplaceItem).where(
                PluginMarketplaceItem.status == "published",
                PluginMarketplaceItem.published.is_(True),
            ).order_by(PluginMarketplaceItem.verified.desc(), PluginMarketplaceItem.name.asc())
        )).scalars().all())
        installs = list((await self.session.execute(
            select(GuildPluginInstallation).where(GuildPluginInstallation.guild_id == guild_id)
        )).scalars().all())
        by_key = {x.plugin_key: x for x in installs}
        return [GuildPluginMarketplaceItemResponse(
            plugin_key=p.plugin_key, name=p.name, summary=p.summary,
            category=p.category, icon_url=p.icon_url, verified=p.verified,
            installed=p.plugin_key in by_key,
            enabled=bool(by_key.get(p.plugin_key) and by_key[p.plugin_key].enabled),
            installation_status=by_key[p.plugin_key].status if p.plugin_key in by_key else None,
        ) for p in plugins]

    async def list_installed(self, guild_id: int):
        rows = list((await self.session.execute(
            select(GuildPluginInstallation).where(
                GuildPluginInstallation.guild_id == guild_id
            ).order_by(GuildPluginInstallation.created_at.asc())
        )).scalars().all())
        return [self._response(x) for x in rows]

    async def install(self, guild_id: int, plugin_key: str, user_id: UUID | None):
        plugin = (await self.session.execute(select(PluginMarketplaceItem).where(
            PluginMarketplaceItem.plugin_key == plugin_key,
            PluginMarketplaceItem.status == "published",
            PluginMarketplaceItem.published.is_(True),
        ))).scalar_one_or_none()
        if plugin is None:
            raise LookupError("published Marketplace plugin not found")
        if await self._find(guild_id, plugin_key):
            raise GuildPluginConflictError("plugin is already installed for this server")
        now = datetime.now(timezone.utc)
        row = GuildPluginInstallation(
            id=uuid4(), guild_id=guild_id, plugin_key=plugin_key,
            status="installed", enabled=False, configuration={},
            installed_by_user_id=user_id, installed_at=now,
            created_at=now, updated_at=now,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return self._response(row)

    async def set_enabled(self, guild_id: int, plugin_key: str, enabled: bool):
        row = await self._required(guild_id, plugin_key)
        now = datetime.now(timezone.utc)
        row.enabled = enabled
        row.status = "enabled" if enabled else "disabled"
        row.enabled_at = now if enabled else row.enabled_at
        row.disabled_at = None if enabled else now
        row.last_error = None
        row.updated_at = now
        await self.session.commit()
        await self.session.refresh(row)
        return self._response(row)

    async def update_configuration(self, guild_id: int, plugin_key: str, configuration: dict):
        row = await self._required(guild_id, plugin_key)
        row.configuration = configuration
        row.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(row)
        return self._response(row)

    async def uninstall(self, guild_id: int, plugin_key: str):
        row = await self._required(guild_id, plugin_key)
        await self.session.delete(row)
        await self.session.commit()

    async def _find(self, guild_id: int, plugin_key: str):
        return (await self.session.execute(select(GuildPluginInstallation).where(
            GuildPluginInstallation.guild_id == guild_id,
            GuildPluginInstallation.plugin_key == plugin_key,
        ))).scalar_one_or_none()

    async def _required(self, guild_id: int, plugin_key: str):
        row = await self._find(guild_id, plugin_key)
        if row is None:
            raise LookupError("plugin is not installed for this server")
        return row

    @staticmethod
    def _response(x):
        return GuildPluginInstallationResponse(
            id=x.id, guild_id=x.guild_id, plugin_key=x.plugin_key,
            status=x.status, enabled=x.enabled,
            configuration=x.configuration or {},
            installed_by_user_id=x.installed_by_user_id,
            installed_at=x.installed_at, enabled_at=x.enabled_at,
            disabled_at=x.disabled_at,
            last_health_check_at=x.last_health_check_at,
            last_error=x.last_error,
            created_at=x.created_at, updated_at=x.updated_at,
        )
