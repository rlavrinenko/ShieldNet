from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.guild_access import require_guild_management
from app.db.session import get_db_session
from app.models.core import User
from app.schemas.plugin_runtime_instances import PluginRuntimeInstanceResponse
from app.services.plugin_runtime_instance_service import PluginRuntimeConflictError,PluginRuntimeInstanceService

router=APIRouter(tags=["Plugin Runtime Instances"])

@router.get("/discord/guilds/{guild_id}/plugin-runtime",response_model=list[PluginRuntimeInstanceResponse])
async def list_runtime(guild_id:int,current_user:User=Depends(get_current_user),session:AsyncSession=Depends(get_db_session)):
    await require_guild_management(session,current_user,guild_id)
    return await PluginRuntimeInstanceService(session).list_for_guild(guild_id)


@router.get(
    "/discord/guilds/{guild_id}/plugin-runtime/{plugin_key}",
    response_model=PluginRuntimeInstanceResponse,
)
async def get_runtime_instance(
    guild_id: int,
    plugin_key: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await require_guild_management(
        session,
        current_user,
        guild_id,
    )

    instances = await PluginRuntimeInstanceService(
        session
    ).list_for_guild(guild_id)

    for instance in instances:
        if instance.plugin_key == plugin_key:
            return instance

    raise HTTPException(
        status_code=404,
        detail="Plugin runtime instance not found",
    )


@router.post("/discord/guilds/{guild_id}/plugin-runtime/{plugin_key}/start",response_model=PluginRuntimeInstanceResponse)
async def start_runtime(guild_id:int,plugin_key:str,current_user:User=Depends(get_current_user),session:AsyncSession=Depends(get_db_session)):
    await require_guild_management(session,current_user,guild_id)
    try:return await PluginRuntimeInstanceService(session).start(guild_id,plugin_key)
    except LookupError as e: raise HTTPException(404,str(e)) from e
    except PluginRuntimeConflictError as e: raise HTTPException(409,str(e)) from e

@router.post("/discord/guilds/{guild_id}/plugin-runtime/{plugin_key}/stop",response_model=PluginRuntimeInstanceResponse)
async def stop_runtime(guild_id:int,plugin_key:str,current_user:User=Depends(get_current_user),session:AsyncSession=Depends(get_db_session)):
    await require_guild_management(session,current_user,guild_id)
    try:return await PluginRuntimeInstanceService(session).stop(guild_id,plugin_key)
    except LookupError as e: raise HTTPException(404,str(e)) from e

@router.post("/discord/guilds/{guild_id}/plugin-runtime/{plugin_key}/heartbeat",response_model=PluginRuntimeInstanceResponse)
async def heartbeat_runtime(guild_id:int,plugin_key:str,current_user:User=Depends(get_current_user),session:AsyncSession=Depends(get_db_session)):
    await require_guild_management(session,current_user,guild_id)
    try:return await PluginRuntimeInstanceService(session).heartbeat(guild_id,plugin_key)
    except LookupError as e: raise HTTPException(404,str(e)) from e
    except PluginRuntimeConflictError as e: raise HTTPException(409,str(e)) from e
