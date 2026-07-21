import uuid
from datetime import UTC, datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.internal import require_internal_token
from app.db.session import get_db_session
from app.models.leadership import LeadershipApplication, LeadershipApplicationSettings, LeadershipLanguageRole
from app.schemas.leadership import LeadershipSyncResult
router=APIRouter(tags=["Internal leadership"],dependencies=[Depends(require_internal_token)])
@router.get("/internal/leadership/pending-role-sync")
async def pending(limit:int=20,session:AsyncSession=Depends(get_db_session)):
    rows=(await session.execute(select(LeadershipApplication).where(LeadershipApplication.status=="approved",LeadershipApplication.role_sync_status=="pending").order_by(LeadershipApplication.role_sync_requested_at).limit(min(max(limit,1),100)))).scalars().all();result=[]
    for a in rows:
        s=(await session.execute(select(LeadershipApplicationSettings).where(LeadershipApplicationSettings.guild_id==a.guild_id))).scalar_one_or_none();lang=(await session.execute(select(LeadershipLanguageRole).where(LeadershipLanguageRole.guild_id==a.guild_id,LeadershipLanguageRole.language_code==a.language_code,LeadershipLanguageRole.leadership_rank==a.requested_rank))).scalar_one_or_none();result.append({"application_id":str(a.id),"guild_id":a.guild_id,"discord_user_id":a.discord_user_id,"alliance_tag":a.alliance_tag,"game_nickname":a.game_nickname,"requested_rank":a.requested_rank,"rank_role_id":s.r5_role_id if s and a.requested_rank=="R5" else s.r4_role_id if s else None,"language_role_id":lang.role_id if lang else None})
    return result
@router.post("/internal/leadership/applications/{application_id}/sync-result")
async def sync_result(application_id:uuid.UUID,payload:LeadershipSyncResult,session:AsyncSession=Depends(get_db_session)):
    a=(await session.execute(select(LeadershipApplication).where(LeadershipApplication.id==application_id))).scalar_one_or_none()
    if not a:raise HTTPException(404,"Application not found")
    a.role_sync_status=payload.status;a.processing_error=payload.message;a.role_sync_completed_at=datetime.now(UTC)
    if payload.status=="completed":a.status="completed"
    else:a.status="failed"
    await session.commit();return {"status":a.status}
