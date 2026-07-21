from __future__ import annotations
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.guild_access import require_guild_management
from app.db.session import get_db_session
from app.models.core import User
from app.models.automations import AutomationRule, AutomationSchedule
from app.services.audit_service import AuditService

router=APIRouter(tags=["Workflow Scheduler"])
class SchedulePayload(BaseModel):
    schedule_type:str=Field(default="daily", pattern="^(daily|weekly|interval)$")
    timezone:str="UTC"
    hour:int=Field(default=9,ge=0,le=23)
    minute:int=Field(default=0,ge=0,le=59)
    days_of_week:list[int]=Field(default_factory=list)
    interval_minutes:int|None=Field(default=None,ge=5,le=10080)
    enabled:bool=True

def next_run(payload:SchedulePayload, now:datetime|None=None)->datetime:
    now=now or datetime.now(timezone.utc)
    if payload.schedule_type=="interval": return now+timedelta(minutes=payload.interval_minutes or 60)
    try: tz=ZoneInfo(payload.timezone)
    except ZoneInfoNotFoundError as exc: raise HTTPException(422,"Unknown timezone") from exc
    local=now.astimezone(tz)
    candidate=local.replace(hour=payload.hour,minute=payload.minute,second=0,microsecond=0)
    if payload.schedule_type=="daily":
        if candidate<=local: candidate+=timedelta(days=1)
    else:
        days=set(payload.days_of_week or [0])
        if any(d<0 or d>6 for d in days): raise HTTPException(422,"days_of_week values must be 0..6")
        for offset in range(8):
            c=candidate+timedelta(days=offset)
            if c.weekday() in days and c>local: candidate=c; break
        else: raise HTTPException(422,"Unable to calculate weekly schedule")
    return candidate.astimezone(timezone.utc)

def view(x):
    return {"id":str(x.id),"rule_id":str(x.rule_id),"guild_id":x.guild_id,"schedule_type":x.schedule_type,"timezone":x.timezone,"hour":x.hour,"minute":x.minute,"days_of_week":x.days_of_week,"interval_minutes":x.interval_minutes,"enabled":x.enabled,"next_run_at":x.next_run_at,"last_run_at":x.last_run_at}

@router.get("/discord/guilds/{guild_id}/automation-schedules")
async def list_schedules(guild_id:int,current_user:User=Depends(get_current_user),session:AsyncSession=Depends(get_db_session)):
    await require_guild_management(session,current_user,guild_id)
    rows=(await session.execute(select(AutomationSchedule,AutomationRule.name).join(AutomationRule,AutomationRule.id==AutomationSchedule.rule_id).where(AutomationSchedule.guild_id==guild_id).order_by(AutomationSchedule.next_run_at))).all()
    return [{**view(s),"rule_name":name} for s,name in rows]

@router.put("/discord/guilds/{guild_id}/automations/{rule_id}/schedule")
async def save_schedule(guild_id:int,rule_id:UUID,payload:SchedulePayload,current_user:User=Depends(get_current_user),session:AsyncSession=Depends(get_db_session)):
    await require_guild_management(session,current_user,guild_id)
    rule=(await session.execute(select(AutomationRule).where(AutomationRule.id==rule_id,AutomationRule.guild_id==guild_id))).scalar_one_or_none()
    if not rule: raise HTTPException(404,"Automation rule not found")
    item=(await session.execute(select(AutomationSchedule).where(AutomationSchedule.rule_id==rule_id))).scalar_one_or_none()
    values=payload.model_dump(); values["next_run_at"]=next_run(payload)
    if item is None:
        item=AutomationSchedule(rule_id=rule_id,guild_id=guild_id,created_by=current_user.id,**values); session.add(item)
    else:
        for k,v in values.items(): setattr(item,k,v)
    await AuditService(session).record(event_type="automation.schedule_saved",guild_id=guild_id,actor_user_id=current_user.id,target_type="automation_schedule",target_id=str(item.id),payload={"rule_id":str(rule_id)})
    await session.commit(); await session.refresh(item); return view(item)

@router.delete("/discord/guilds/{guild_id}/automations/{rule_id}/schedule",status_code=204)
async def delete_schedule(guild_id:int,rule_id:UUID,current_user:User=Depends(get_current_user),session:AsyncSession=Depends(get_db_session)):
    await require_guild_management(session,current_user,guild_id)
    item=(await session.execute(select(AutomationSchedule).where(AutomationSchedule.rule_id==rule_id,AutomationSchedule.guild_id==guild_id))).scalar_one_or_none()
    if item: await session.delete(item); await session.commit()
