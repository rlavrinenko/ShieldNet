import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.guild_access import require_guild_management
from app.db.session import get_db_session
from app.models.core import User
from app.schemas.member_cases import MemberCaseCreate, MemberCaseResponse, MemberCaseUpdate
from app.services.member_case_service import MemberCaseService

router = APIRouter(tags=["Member cases"])


@router.get("/discord/guilds/{guild_id}/members/{discord_user_id}/cases", response_model=list[MemberCaseResponse])
async def list_member_cases(guild_id: int, discord_user_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    return await MemberCaseService(session).list(guild_id, discord_user_id)


@router.post("/discord/guilds/{guild_id}/members/{discord_user_id}/cases", response_model=MemberCaseResponse, status_code=201)
async def create_member_case(guild_id: int, discord_user_id: int, payload: MemberCaseCreate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    return await MemberCaseService(session).create(guild_id, discord_user_id, current_user.id, payload)


@router.patch("/discord/guilds/{guild_id}/members/{discord_user_id}/cases/{case_id}", response_model=MemberCaseResponse)
async def update_member_case(guild_id: int, discord_user_id: int, case_id: uuid.UUID, payload: MemberCaseUpdate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    return await MemberCaseService(session).update(guild_id, discord_user_id, case_id, payload)
