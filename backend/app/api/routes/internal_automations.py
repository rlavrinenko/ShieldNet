from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.api.dependencies.internal import verify_internal_service_token
from app.services.automation_runtime import AutomationRuntimeService
from app.models.automations import AutomationRule, AutomationRun, AutomationSchedule
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/internal/automations", tags=["Internal Automations"], dependencies=[Depends(verify_internal_service_token)])


class EventRequest(BaseModel):
    guild_id: int
    event_type: str = Field(min_length=2, max_length=64)
    event_id: str = Field(min_length=1, max_length=160)
    context: dict[str, Any] = Field(default_factory=dict)


class CompleteRequest(BaseModel):
    status: str
    result: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


@router.post("/events")
async def dispatch_event(payload: EventRequest, session: AsyncSession = Depends(get_db_session)):
    jobs = await AutomationRuntimeService(session).dispatch(payload.guild_id, payload.event_type, payload.event_id, payload.context)
    await session.commit()
    return {"jobs": jobs, "count": len(jobs)}


@router.post("/runs/{run_id}/complete")
async def complete_run(run_id: UUID, payload: CompleteRequest, session: AsyncSession = Depends(get_db_session)):
    if payload.status not in {"succeeded", "failed", "partial"}:
        raise HTTPException(422, "Invalid run status")
    run = await AutomationRuntimeService(session).complete(run_id, payload.status, payload.result, payload.error)
    if run is None:
        raise HTTPException(404, "Automation run not found")
    await session.commit()
    return {"id": str(run.id), "status": run.status}


@router.post("/schedules/tick")
async def schedule_tick(session: AsyncSession = Depends(get_db_session)):
    now = datetime.now(timezone.utc)
    rows = (await session.execute(
        select(AutomationSchedule, AutomationRule).join(AutomationRule, AutomationRule.id == AutomationSchedule.rule_id).where(
            AutomationSchedule.enabled.is_(True), AutomationSchedule.next_run_at <= now,
            AutomationRule.status == "enabled"
        ).order_by(AutomationSchedule.next_run_at).limit(100)
    )).all()
    jobs=[]
    for schedule, rule in rows:
        event_id=f"schedule:{schedule.id}:{int(schedule.next_run_at.timestamp())}"
        context={"schedule":{"id":str(schedule.id),"scheduled_for":schedule.next_run_at.isoformat(),"timezone":schedule.timezone}}
        run=AutomationRun(rule_id=rule.id,guild_id=rule.guild_id,status="queued",trigger_payload=context,result={"scheduled":True,"actions":[]},event_type="schedule",event_id=event_id,attempt_count=0)
        session.add(run); await session.flush()
        jobs.append({"run_id":str(run.id),"rule_id":str(rule.id),"rule_name":rule.name,"guild_id":rule.guild_id,"stop_on_error":rule.stop_on_error,"actions":rule.actions,"context":context})
        schedule.last_run_at=now
        if schedule.schedule_type=="interval": schedule.next_run_at=now+timedelta(minutes=schedule.interval_minutes or 60)
        else:
            step=timedelta(days=1)
            candidate=schedule.next_run_at+step
            if schedule.schedule_type=="weekly":
                days=set(schedule.days_of_week or [0])
                while candidate.weekday() not in days: candidate+=step
            schedule.next_run_at=candidate
    await session.commit()
    return {"jobs":jobs,"count":len(jobs)}
