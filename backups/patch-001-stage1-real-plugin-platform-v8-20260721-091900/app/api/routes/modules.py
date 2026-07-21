from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.guild_access import require_guild_management
from app.db.session import get_db_session
from app.models.core import User
from app.schemas.modules import (
    BotModuleStateResponse,
    ModuleResponse,
    ModuleUpdateRequest,
    ModuleUpdateResponse,
)
from app.services.module_service import ModuleService

router = APIRouter(tags=["Modules"])


@router.get(
    "/discord/guilds/{guild_id}/modules",
    response_model=list[ModuleResponse],
)
async def list_guild_modules(
    guild_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[ModuleResponse]:
    await require_guild_management(session, current_user, guild_id)
    return await ModuleService(session).list_for_guild(guild_id)


@router.patch(
    "/discord/guilds/{guild_id}/modules/{module_key}",
    response_model=ModuleUpdateResponse,
)
async def update_guild_module(
    guild_id: int,
    module_key: str,
    payload: ModuleUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ModuleUpdateResponse:
    await require_guild_management(session, current_user, guild_id)

    try:
        module = await ModuleService(session).update(
            guild_id=guild_id,
            module_key=module_key,
            enabled=payload.enabled,
            configuration=payload.configuration,
            changed_by=current_user.id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ModuleUpdateResponse(
        guild_id=guild_id,
        sync_required=True,
        **module.model_dump(),
    )
