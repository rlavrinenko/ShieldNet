import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.guild_access import require_guild_management
from app.db.session import get_db_session
from app.models.core import User
from app.schemas.member_evidence import (
    CaseAppealCreate,
    CaseAppealResponse,
    CaseAppealUpdate,
    CaseEvidenceCreate,
    CaseEvidenceResponse,
)
from app.services.member_evidence_service import MemberEvidenceService

router = APIRouter(tags=["Case evidence and appeals"])
BASE = "/discord/guilds/{guild_id}/members/{discord_user_id}/cases/{case_id}"


@router.get(f"{BASE}/evidence", response_model=list[CaseEvidenceResponse])
async def list_evidence(guild_id: int, discord_user_id: int, case_id: uuid.UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    return await MemberEvidenceService(session).list_evidence(guild_id, discord_user_id, case_id)


@router.post(f"{BASE}/evidence", response_model=CaseEvidenceResponse, status_code=201)
async def create_evidence(guild_id: int, discord_user_id: int, case_id: uuid.UUID, payload: CaseEvidenceCreate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    return await MemberEvidenceService(session).create_evidence(guild_id, discord_user_id, case_id, current_user.id, payload)


@router.delete(f"{BASE}/evidence/{{evidence_id}}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evidence(guild_id: int, discord_user_id: int, case_id: uuid.UUID, evidence_id: uuid.UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    await MemberEvidenceService(session).delete_evidence(guild_id, discord_user_id, case_id, evidence_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(f"{BASE}/appeals", response_model=list[CaseAppealResponse])
async def list_appeals(guild_id: int, discord_user_id: int, case_id: uuid.UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    return await MemberEvidenceService(session).list_appeals(guild_id, discord_user_id, case_id)


@router.post(f"{BASE}/appeals", response_model=CaseAppealResponse, status_code=201)
async def create_appeal(guild_id: int, discord_user_id: int, case_id: uuid.UUID, payload: CaseAppealCreate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    return await MemberEvidenceService(session).create_appeal(guild_id, discord_user_id, case_id, current_user.id, payload)


@router.patch(f"{BASE}/appeals/{{appeal_id}}", response_model=CaseAppealResponse)
async def update_appeal(guild_id: int, discord_user_id: int, case_id: uuid.UUID, appeal_id: uuid.UUID, payload: CaseAppealUpdate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    return await MemberEvidenceService(session).update_appeal(guild_id, discord_user_id, case_id, appeal_id, current_user.id, payload)
