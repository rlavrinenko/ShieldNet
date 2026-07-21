from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.guild_access import require_guild_management
from app.db.session import get_db_session
from app.models.core import User
from app.schemas.moderation_operations import ModerationCaseList, ModerationStats, ModeratorWorkload
from app.services.moderation_operations_service import ModerationOperationsService

router = APIRouter(tags=["Moderation operations"])


@router.get("/discord/guilds/{guild_id}/moderation/cases", response_model=ModerationCaseList)
async def moderation_cases(
    guild_id: int,
    query: str | None = None,
    status_filter: str = "all",
    priority: str = "all",
    assignee: str = "all",
    overdue_only: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await require_guild_management(session, current_user, guild_id)
    return await ModerationOperationsService(session).list_cases(
        guild_id, query=query, status_filter=status_filter, priority=priority,
        assignee=assignee, overdue_only=overdue_only, page=page, page_size=page_size,
    )


@router.get("/discord/guilds/{guild_id}/moderation/stats", response_model=ModerationStats)
async def moderation_stats(guild_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    return await ModerationOperationsService(session).stats(guild_id)


@router.get("/discord/guilds/{guild_id}/moderation/workload", response_model=list[ModeratorWorkload])
async def moderation_workload(guild_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    return await ModerationOperationsService(session).workload(guild_id)
