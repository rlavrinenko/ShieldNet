from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.internal import verify_internal_service_token
from app.db.session import get_db_session
from app.schemas.members import MemberActivityRequest, MemberBatchSyncRequest, MemberLeftRequest
from app.services.member_service import MemberService

router = APIRouter(
    prefix="/internal/discord/guilds",
    tags=["Internal Members"],
    dependencies=[Depends(verify_internal_service_token)],
)

@router.post("/{guild_id}/members/sync")
async def sync_members(guild_id: int, payload: MemberBatchSyncRequest, session: AsyncSession = Depends(get_db_session)):
    count = await MemberService(session).batch_sync(guild_id, payload)
    return {"status": "synchronized", "count": count}

@router.post("/{guild_id}/members/activity")
async def activity(guild_id: int, payload: MemberActivityRequest, session: AsyncSession = Depends(get_db_session)):
    await MemberService(session).activity(guild_id, payload.discord_user_id, payload.activity_at)
    return {"status": "updated"}

@router.post("/{guild_id}/members/left")
async def left(guild_id: int, payload: MemberLeftRequest, session: AsyncSession = Depends(get_db_session)):
    await MemberService(session).left(guild_id, payload.discord_user_id, payload.left_at)
    return {"status": "updated"}
