from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.guild_access import require_guild_management
from app.db.session import get_db_session
from app.models.core import User
from app.schemas.member_actions import MemberActionResponse
from app.schemas.members import MemberDetailResponse, MemberListResponse, MemberProfileUpdate, MemberStatsResponse
from app.services.member_action_service import MemberActionService
from app.services.member_service import MemberService

router = APIRouter(tags=["Members"])


@router.get("/discord/guilds/{guild_id}/members", response_model=MemberListResponse)
async def list_members(
    guild_id: int,
    query: str | None = Query(default=None, max_length=255), page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200), member_type: str = Query(default="all", pattern="^(all|human|bot)$"),
    status_filter: str = Query(default="active", pattern="^(active|pending|timed_out|blocked|inactive|watchlist|review_due|left)$"),
    role_id: int | None = None, tag: str | None = Query(default=None, max_length=64),
    sort: str = Query(default="activity", pattern="^(activity|name|joined|oldest)$"),
    current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session),
):
    await require_guild_management(session, current_user, guild_id)
    return await MemberService(session).list(guild_id, query, page, page_size, member_type, status_filter, role_id, tag, sort)


@router.get("/discord/guilds/{guild_id}/members/stats", response_model=MemberStatsResponse)
async def member_stats(guild_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    return await MemberService(session).stats(guild_id)


@router.get("/discord/guilds/{guild_id}/members/{discord_user_id}", response_model=MemberDetailResponse)
async def member_detail(guild_id: int, discord_user_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    return await MemberService(session).get(guild_id, discord_user_id)


@router.patch("/discord/guilds/{guild_id}/members/{discord_user_id}/profile", response_model=MemberDetailResponse)
async def update_member_profile(guild_id: int, discord_user_id: int, payload: MemberProfileUpdate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    return await MemberService(session).update_profile(guild_id, discord_user_id, current_user.id, payload)


@router.get("/discord/guilds/{guild_id}/members/{discord_user_id}/actions", response_model=list[MemberActionResponse])
async def member_action_history(guild_id: int, discord_user_id: int, limit: int = Query(default=50, ge=1, le=200), current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    actions = await MemberService(session).action_history(guild_id, discord_user_id, limit)
    return [MemberActionService.serialize(a) for a in actions]
