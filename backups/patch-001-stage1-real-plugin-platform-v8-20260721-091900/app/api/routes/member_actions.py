from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.guild_access import require_guild_management
from app.db.session import get_db_session
from app.models.core import User
from app.schemas.member_actions import MemberActionCreate, MemberActionResponse
from app.services.member_action_service import MemberActionService

router = APIRouter(tags=["Member Actions"])


@router.post(
    "/discord/guilds/{guild_id}/members/{discord_user_id}/actions",
    response_model=MemberActionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_action(
    guild_id: int,
    discord_user_id: int,
    payload: MemberActionCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await require_guild_management(session, current_user, guild_id)
    return await MemberActionService(session).create(
        guild_id, discord_user_id, current_user.id, payload
    )
