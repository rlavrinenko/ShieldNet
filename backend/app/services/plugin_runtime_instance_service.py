from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.plugins import GuildPluginInstallation, PluginRuntimeInstance, PluginRuntimeState
from app.schemas.plugin_runtime_instances import PluginRuntimeInstanceResponse

class PluginRuntimeConflictError(Exception):
    pass

class PluginRuntimeInstanceService:
    def __init__(self, session: AsyncSession):
        self.session=session

    async def list_for_guild(self, guild_id:int):
        rows=list((await self.session.execute(
            select(PluginRuntimeInstance).where(
                PluginRuntimeInstance.guild_id==guild_id
            ).order_by(PluginRuntimeInstance.plugin_key.asc())
        )).scalars().all())
        return [self._response(x) for x in rows]

    async def start(self,guild_id:int,plugin_key:str):
        install=(await self.session.execute(
            select(GuildPluginInstallation).where(
                GuildPluginInstallation.guild_id==guild_id,
                GuildPluginInstallation.plugin_key==plugin_key,
                GuildPluginInstallation.enabled.is_(True),
            )
        )).scalar_one_or_none()
        if install is None:
            raise LookupError("plugin must be installed and enabled for this server")
        prepared=(await self.session.execute(
            select(PluginRuntimeState).where(
                PluginRuntimeState.plugin_key==plugin_key,
                PluginRuntimeState.state=="validated",
            )
        )).scalar_one_or_none()
        if prepared is None or not prepared.package_path or not prepared.prepared_version:
            raise LookupError("validated plugin package is not prepared")
        item=await self._instance(guild_id,plugin_key)
        now=datetime.now(timezone.utc)
        if item and item.state=="running":
            raise PluginRuntimeConflictError("plugin runtime is already running")
        if item is None:
            item=PluginRuntimeInstance(
                id=uuid4(), guild_id=guild_id, plugin_key=plugin_key,
                state="running", generation=1,
                package_version=prepared.prepared_version,
                package_path=prepared.package_path,
                manifest_json=prepared.manifest_json or {},
                started_at=now,last_heartbeat_at=now,
                created_at=now,updated_at=now,
            )
            self.session.add(item)
        else:
            item.state="running"; item.generation+=1
            item.package_version=prepared.prepared_version
            item.package_path=prepared.package_path
            item.manifest_json=prepared.manifest_json or {}
            item.started_at=now; item.stopped_at=None
            item.last_heartbeat_at=now; item.last_error=None; item.updated_at=now
        await self.session.commit(); await self.session.refresh(item)
        return self._response(item)

    async def stop(self,guild_id:int,plugin_key:str):
        item=await self._require(guild_id,plugin_key)
        now=datetime.now(timezone.utc)
        item.state="stopped"; item.stopped_at=now; item.updated_at=now
        await self.session.commit(); await self.session.refresh(item)
        return self._response(item)

    async def heartbeat(self,guild_id:int,plugin_key:str):
        item=await self._require(guild_id,plugin_key)
        if item.state!="running":
            raise PluginRuntimeConflictError("runtime is not running")
        item.last_heartbeat_at=datetime.now(timezone.utc)
        item.updated_at=item.last_heartbeat_at
        await self.session.commit(); await self.session.refresh(item)
        return self._response(item)

    async def _instance(self,guild_id,plugin_key):
        return (await self.session.execute(
            select(PluginRuntimeInstance).where(
                PluginRuntimeInstance.guild_id==guild_id,
                PluginRuntimeInstance.plugin_key==plugin_key,
            )
        )).scalar_one_or_none()

    async def _require(self,guild_id,plugin_key):
        item=await self._instance(guild_id,plugin_key)
        if item is None: raise LookupError("plugin runtime instance not found")
        return item

    @staticmethod
    def _response(x):
        return PluginRuntimeInstanceResponse(
            id=x.id,guild_id=x.guild_id,plugin_key=x.plugin_key,state=x.state,
            generation=x.generation,package_version=x.package_version,
            package_path=x.package_path,manifest_json=x.manifest_json or {},
            started_at=x.started_at,stopped_at=x.stopped_at,
            last_heartbeat_at=x.last_heartbeat_at,last_error=x.last_error,
            created_at=x.created_at,updated_at=x.updated_at,
        )
