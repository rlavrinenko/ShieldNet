import uuid
from datetime import UTC, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.guild_access import require_guild_management
from app.db.session import get_db_session
from app.models.core import User
from app.models.leadership import LeadershipApplication, LeadershipApplicationDecision, LeadershipApplicationSettings, LeadershipLanguageRole
from app.schemas.leadership import LeadershipApplicationCreate, LeadershipAssignInput, LeadershipDecisionInput, LeadershipLanguageRoleInput, LeadershipSettingsInput
from app.services.audit_service import AuditService

router = APIRouter(tags=["R5/R4 Applications"])

def dump(a):
    return {"id":str(a.id),"guild_id":a.guild_id,"discord_user_id":a.discord_user_id,"alliance_tag":a.alliance_tag,"game_nickname":a.game_nickname,"requested_rank":a.requested_rank,"language_code":a.language_code,"evidence_url":a.evidence_url,"applicant_comment":a.applicant_comment,"status":a.status,"assigned_to":str(a.assigned_to) if a.assigned_to else None,"decision_reason":a.decision_reason,"decided_by":str(a.decided_by) if a.decided_by else None,"decided_at":a.decided_at,"processing_error":a.processing_error,"role_sync_status":a.role_sync_status,"created_at":a.created_at,"updated_at":a.updated_at}

async def access(session,user,guild_id):
    await require_guild_management(session,user,guild_id)

@router.get("/discord/guilds/{guild_id}/leadership/settings")
async def get_settings(guild_id:int,current_user:User=Depends(get_current_user),session:AsyncSession=Depends(get_db_session)):
    await access(session,current_user,guild_id)
    item=(await session.execute(select(LeadershipApplicationSettings).where(LeadershipApplicationSettings.guild_id==guild_id))).scalar_one_or_none()
    if item is None:
        item=LeadershipApplicationSettings(guild_id=guild_id);session.add(item);await session.commit();await session.refresh(item)
    return {"enabled":item.enabled,"review_channel_id":item.review_channel_id,"r5_role_id":item.r5_role_id,"r4_role_id":item.r4_role_id,"require_evidence":item.require_evidence,"language_role_mode":item.language_role_mode}

@router.put("/discord/guilds/{guild_id}/leadership/settings")
async def save_settings(guild_id:int,payload:LeadershipSettingsInput,current_user:User=Depends(get_current_user),session:AsyncSession=Depends(get_db_session)):
    await access(session,current_user,guild_id)
    item=(await session.execute(select(LeadershipApplicationSettings).where(LeadershipApplicationSettings.guild_id==guild_id))).scalar_one_or_none() or LeadershipApplicationSettings(guild_id=guild_id)
    session.add(item)
    for k,v in payload.model_dump().items():setattr(item,k,v)
    item.updated_by=current_user.id
    await session.commit();return {"status":"saved"}

@router.get("/discord/guilds/{guild_id}/leadership/language-roles")
async def list_language_roles(guild_id:int,current_user:User=Depends(get_current_user),session:AsyncSession=Depends(get_db_session)):
    await access(session,current_user,guild_id)
    rows=(await session.execute(select(LeadershipLanguageRole).where(LeadershipLanguageRole.guild_id==guild_id).order_by(LeadershipLanguageRole.language_code,LeadershipLanguageRole.leadership_rank))).scalars().all()
    return [{"id":str(x.id),"language_code":x.language_code,"leadership_rank":x.leadership_rank,"role_id":x.role_id} for x in rows]

@router.post("/discord/guilds/{guild_id}/leadership/language-roles")
async def add_language_role(guild_id:int,payload:LeadershipLanguageRoleInput,current_user:User=Depends(get_current_user),session:AsyncSession=Depends(get_db_session)):
    await access(session,current_user,guild_id)
    code=payload.language_code.strip().lower()
    item=(await session.execute(select(LeadershipLanguageRole).where(LeadershipLanguageRole.guild_id==guild_id,LeadershipLanguageRole.language_code==code,LeadershipLanguageRole.leadership_rank==payload.leadership_rank))).scalar_one_or_none()
    if item is None:item=LeadershipLanguageRole(guild_id=guild_id,language_code=code,leadership_rank=payload.leadership_rank,role_id=payload.role_id);session.add(item)
    else:item.role_id=payload.role_id
    await session.commit();return {"status":"saved"}

@router.delete("/discord/guilds/{guild_id}/leadership/language-roles/{item_id}")
async def delete_language_role(guild_id:int,item_id:uuid.UUID,current_user:User=Depends(get_current_user),session:AsyncSession=Depends(get_db_session)):
    await access(session,current_user,guild_id)
    item=(await session.execute(select(LeadershipLanguageRole).where(LeadershipLanguageRole.id==item_id,LeadershipLanguageRole.guild_id==guild_id))).scalar_one_or_none()
    if not item:raise HTTPException(404,"Language role mapping not found")
    await session.delete(item);await session.commit();return {"status":"deleted"}

@router.post("/discord/guilds/{guild_id}/leadership/applications")
async def create_application(guild_id:int,payload:LeadershipApplicationCreate,current_user:User=Depends(get_current_user),session:AsyncSession=Depends(get_db_session)):
    await access(session,current_user,guild_id)
    settings=(await session.execute(select(LeadershipApplicationSettings).where(LeadershipApplicationSettings.guild_id==guild_id))).scalar_one_or_none()
    if settings and settings.require_evidence and not payload.evidence_url:raise HTTPException(400,"Evidence is required")
    active=(await session.execute(select(LeadershipApplication).where(LeadershipApplication.guild_id==guild_id,LeadershipApplication.discord_user_id==payload.discord_user_id,LeadershipApplication.status.in_(["pending","in_review","approved","processing"])))).scalar_one_or_none()
    if active:raise HTTPException(409,"An active leadership application already exists")
    item=LeadershipApplication(guild_id=guild_id,discord_user_id=payload.discord_user_id,alliance_tag=payload.alliance_tag.strip().upper(),game_nickname=payload.game_nickname.strip(),requested_rank=payload.requested_rank,language_code=payload.language_code.strip().lower(),evidence_url=payload.evidence_url,applicant_comment=payload.applicant_comment)
    session.add(item);await session.commit();await session.refresh(item);return dump(item)

@router.get("/discord/guilds/{guild_id}/leadership/applications")
async def list_applications(guild_id:int,status:str|None=Query(None),query:str|None=Query(None),current_user:User=Depends(get_current_user),session:AsyncSession=Depends(get_db_session)):
    await access(session,current_user,guild_id)
    stmt=select(LeadershipApplication).where(LeadershipApplication.guild_id==guild_id)
    if status:stmt=stmt.where(LeadershipApplication.status==status)
    if query:
        q=f"%{query.strip()}%";stmt=stmt.where(LeadershipApplication.alliance_tag.ilike(q)|LeadershipApplication.game_nickname.ilike(q))
    rows=(await session.execute(stmt.order_by(LeadershipApplication.created_at.desc()).limit(500))).scalars().all();return [dump(x) for x in rows]

@router.get("/discord/guilds/{guild_id}/leadership/summary")
async def summary(guild_id:int,current_user:User=Depends(get_current_user),session:AsyncSession=Depends(get_db_session)):
    await access(session,current_user,guild_id)
    rows=(await session.execute(select(LeadershipApplication.status,func.count()).where(LeadershipApplication.guild_id==guild_id).group_by(LeadershipApplication.status))).all();data={k:v for k,v in rows};return {"pending":data.get("pending",0),"in_review":data.get("in_review",0),"approved":data.get("approved",0),"completed":data.get("completed",0),"rejected":data.get("rejected",0),"failed":data.get("failed",0)}

@router.post("/discord/guilds/{guild_id}/leadership/applications/{application_id}/assign")
async def assign(guild_id:int,application_id:uuid.UUID,payload:LeadershipAssignInput,current_user:User=Depends(get_current_user),session:AsyncSession=Depends(get_db_session)):
    await access(session,current_user,guild_id);item=await get_item(session,guild_id,application_id);item.assigned_to=payload.assigned_to or current_user.id;item.status="in_review";await decision(session,item,"assigned",None,current_user.id);await session.commit();return dump(item)

async def get_item(session,guild_id,item_id):
    item=(await session.execute(select(LeadershipApplication).where(LeadershipApplication.id==item_id,LeadershipApplication.guild_id==guild_id))).scalar_one_or_none()
    if not item:raise HTTPException(404,"Leadership application not found")
    return item

async def decision(session,item,action,reason,actor):
    session.add(LeadershipApplicationDecision(application_id=item.id,guild_id=item.guild_id,action=action,reason=reason,actor_user_id=actor))

@router.post("/discord/guilds/{guild_id}/leadership/applications/{application_id}/approve")
async def approve(guild_id:int,application_id:uuid.UUID,payload:LeadershipDecisionInput,current_user:User=Depends(get_current_user),session:AsyncSession=Depends(get_db_session)):
    await access(session,current_user,guild_id);item=await get_item(session,guild_id,application_id)
    if item.status not in {"pending","in_review"}:raise HTTPException(409,"Application cannot be approved")
    item.status="approved";item.decision_reason=payload.reason;item.decided_by=current_user.id;item.decided_at=datetime.now(UTC);item.role_sync_status="pending";item.role_sync_requested_at=datetime.now(UTC)
    await decision(session,item,"approved",payload.reason,current_user.id);await AuditService(session).record(guild_id=guild_id,actor_user_id=current_user.id,event_type="leadership.application.approved",target_type="leadership_application",target_id=str(item.id),payload={"rank":item.requested_rank,"language":item.language_code},result="approved");await session.commit();return dump(item)

@router.post("/discord/guilds/{guild_id}/leadership/applications/{application_id}/reject")
async def reject(guild_id:int,application_id:uuid.UUID,payload:LeadershipDecisionInput,current_user:User=Depends(get_current_user),session:AsyncSession=Depends(get_db_session)):
    await access(session,current_user,guild_id);item=await get_item(session,guild_id,application_id);reason=(payload.reason or "").strip()
    if not reason:raise HTTPException(400,"Rejection reason is required")
    if item.status not in {"pending","in_review"}:raise HTTPException(409,"Application cannot be rejected")
    item.status="rejected";item.decision_reason=reason;item.decided_by=current_user.id;item.decided_at=datetime.now(UTC);await decision(session,item,"rejected",reason,current_user.id);await session.commit();return dump(item)

@router.get("/discord/guilds/{guild_id}/leadership/applications/{application_id}/history")
async def history(guild_id:int,application_id:uuid.UUID,current_user:User=Depends(get_current_user),session:AsyncSession=Depends(get_db_session)):
    await access(session,current_user,guild_id);await get_item(session,guild_id,application_id);rows=(await session.execute(select(LeadershipApplicationDecision).where(LeadershipApplicationDecision.application_id==application_id).order_by(LeadershipApplicationDecision.created_at.desc()))).scalars().all();return [{"id":str(x.id),"action":x.action,"reason":x.reason,"actor_user_id":str(x.actor_user_id) if x.actor_user_id else None,"created_at":x.created_at} for x in rows]
