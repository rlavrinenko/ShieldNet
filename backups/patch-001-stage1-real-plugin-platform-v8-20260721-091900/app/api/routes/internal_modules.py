from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.internal import verify_internal_service_token
from app.db.session import get_db_session
from app.schemas.modules import BotModuleStateResponse
from app.services.module_service import ModuleService

router = APIRouter(
    prefix="/internal/modules",
    tags=["Internal Modules"],
    dependencies=[Depends(verify_internal_service_token)],
)


@router.get(
    "/guilds/{guild_id}",
    response_model=BotModuleStateResponse,
)
async def bot_guild_modules(
    guild_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> BotModuleStateResponse:
    service = ModuleService(session)

    return BotModuleStateResponse(
        guild_id=guild_id,
        modules=await service.list_for_guild(guild_id),
        configuration_revision=await service.configuration_revision(guild_id),
    )
