from __future__ import annotations

from typing import Any
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.guild_access import require_guild_management
from app.db.session import get_db_session
from app.models.core import User
from app.models.automations import AutomationRule, AutomationRun
from app.core.config import settings
from app.services.audit_service import AuditService
from app.services.automation_service import ACTIONS, TRIGGERS, AutomationService

router = APIRouter(tags=["Automation Designer"])


class Condition(BaseModel):
    field: str = Field(min_length=1, max_length=128)
    operator: str = "eq"
    value: Any = None


class Action(BaseModel):
    type: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class RuleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    trigger_type: str
    conditions: list[Condition] = Field(default_factory=list)
    actions: list[Action] = Field(min_length=1)
    stop_on_error: bool = True
    max_failures: int = Field(default=5, ge=1, le=100)


class RuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    trigger_type: str | None = None
    conditions: list[Condition] | None = None
    actions: list[Action] | None = None
    stop_on_error: bool | None = None
    max_failures: int | None = Field(default=None, ge=1, le=100)


class StatusUpdate(BaseModel):
    status: str


class DryRunRequest(BaseModel):
    context: dict[str, Any] = Field(default_factory=dict)


def rule_view(x):
    return {"id": str(x.id), "guild_id": x.guild_id, "name": x.name, "description": x.description,
            "trigger_type": x.trigger_type, "conditions": x.conditions, "actions": x.actions,
            "status": x.status, "stop_on_error": x.stop_on_error, "execution_count": x.execution_count,
            "failure_count": x.failure_count, "last_executed_at": x.last_executed_at,
            "created_at": x.created_at, "updated_at": x.updated_at, "max_failures": x.max_failures, "disabled_reason": x.disabled_reason}


def run_view(x):
    return {"id": str(x.id), "rule_id": str(x.rule_id), "guild_id": x.guild_id, "status": x.status,
            "trigger_payload": x.trigger_payload, "result": x.result, "error": x.error,
            "started_at": x.started_at, "finished_at": x.finished_at, "event_type": x.event_type,
            "event_id": x.event_id, "attempt_count": x.attempt_count}


@router.get("/discord/guilds/{guild_id}/automations/catalog")
async def catalog(guild_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    return {"triggers": [{"key": k, "label": v} for k, v in TRIGGERS.items()],
            "actions": [{"key": k, "label": v} for k, v in ACTIONS.items()],
            "operators": ["eq", "neq", "contains", "not_contains", "exists", "gt", "gte", "lt", "lte"]}


@router.get("/discord/guilds/{guild_id}/automations")
async def list_rules(guild_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    return [rule_view(x) for x in await AutomationService(session).list(guild_id)]


@router.post("/discord/guilds/{guild_id}/automations", status_code=status.HTTP_201_CREATED)
async def create_rule(guild_id: int, payload: RuleCreate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    try:
        item = await AutomationService(session).create(guild_id, payload.model_dump(), current_user.id)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    await AuditService(session).record(event_type="automation.created", guild_id=guild_id, actor_user_id=current_user.id, target_type="automation_rule", target_id=str(item.id), payload={"name": item.name})
    await session.commit()
    return rule_view(item)


@router.put("/discord/guilds/{guild_id}/automations/{rule_id}")
async def update_rule(guild_id: int, rule_id: UUID, payload: RuleUpdate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    service = AutomationService(session); item = await service.get(guild_id, rule_id)
    if not item: raise HTTPException(404, "Automation rule not found")
    try: await service.update(item, payload.model_dump(exclude_unset=True), current_user.id)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
    await AuditService(session).record(event_type="automation.updated", guild_id=guild_id, actor_user_id=current_user.id, target_type="automation_rule", target_id=str(item.id))
    await session.commit(); return rule_view(item)


@router.post("/discord/guilds/{guild_id}/automations/{rule_id}/status")
async def set_status(guild_id: int, rule_id: UUID, payload: StatusUpdate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    service = AutomationService(session); item = await service.get(guild_id, rule_id)
    if not item: raise HTTPException(404, "Automation rule not found")
    try: await service.set_status(item, payload.status, current_user.id)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
    await AuditService(session).record(event_type="automation.status_changed", guild_id=guild_id, actor_user_id=current_user.id, target_type="automation_rule", target_id=str(item.id), payload={"status": item.status})
    await session.commit(); return rule_view(item)


@router.post("/discord/guilds/{guild_id}/automations/{rule_id}/dry-run")
async def dry_run(guild_id: int, rule_id: UUID, payload: DryRunRequest, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    service = AutomationService(session); item = await service.get(guild_id, rule_id)
    if not item: raise HTTPException(404, "Automation rule not found")
    run = await service.dry_run(item, payload.context, current_user.id)
    await AuditService(session).record(event_type="automation.dry_run", guild_id=guild_id, actor_user_id=current_user.id, target_type="automation_rule", target_id=str(item.id), payload={"matched": run.result.get("matched")})
    await session.commit(); return run_view(run)


@router.get("/discord/guilds/{guild_id}/automations/{rule_id}/runs")
async def list_runs(guild_id: int, rule_id: UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    return [run_view(x) for x in await AutomationService(session).runs(guild_id, rule_id)]


@router.delete("/discord/guilds/{guild_id}/automations/{rule_id}", status_code=204)
async def delete_rule(guild_id: int, rule_id: UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    if not await AutomationService(session).remove(guild_id, rule_id): raise HTTPException(404, "Automation rule not found")
    await AuditService(session).record(event_type="automation.deleted", guild_id=guild_id, actor_user_id=current_user.id, target_type="automation_rule", target_id=str(rule_id))
    await session.commit()


@router.get("/discord/guilds/{guild_id}/automations-monitor/summary")
async def monitor_summary(guild_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    rows = (await session.execute(
        select(AutomationRun.status, func.count(AutomationRun.id)).where(
            AutomationRun.guild_id == guild_id, AutomationRun.started_at >= since
        ).group_by(AutomationRun.status)
    )).all()
    counts = {str(status): int(count) for status, count in rows}
    active_rules = int((await session.execute(select(func.count(AutomationRule.id)).where(
        AutomationRule.guild_id == guild_id, AutomationRule.status == "enabled"
    ))).scalar_one())
    queued = counts.get("queued", 0)
    completed = sum(counts.get(x, 0) for x in ("succeeded", "failed", "partial"))
    succeeded = counts.get("succeeded", 0)
    return {"window_hours": 24, "active_rules": active_rules, "queued": queued,
            "succeeded": succeeded, "failed": counts.get("failed", 0), "partial": counts.get("partial", 0),
            "success_rate": round((succeeded / completed) * 100, 1) if completed else 100.0}


@router.get("/discord/guilds/{guild_id}/automations-monitor/runs")
async def monitor_runs(guild_id: int, status_filter: str | None = None, limit: int = 100,
                       current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    query = select(AutomationRun, AutomationRule.name).join(AutomationRule, AutomationRule.id == AutomationRun.rule_id).where(
        AutomationRun.guild_id == guild_id
    )
    if status_filter:
        query = query.where(AutomationRun.status == status_filter)
    rows = (await session.execute(query.order_by(AutomationRun.started_at.desc()).limit(min(max(limit, 1), 250)))).all()
    return [{**run_view(run), "rule_name": name} for run, name in rows]


@router.post("/discord/guilds/{guild_id}/automations-monitor/runs/{run_id}/retry", status_code=202)
async def retry_run(guild_id: int, run_id: UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    original = (await session.execute(select(AutomationRun).where(
        AutomationRun.id == run_id, AutomationRun.guild_id == guild_id
    ))).scalar_one_or_none()
    if original is None:
        raise HTTPException(404, "Automation run not found")
    if original.status not in {"failed", "partial"}:
        raise HTTPException(409, "Only failed or partial runs can be retried")
    rule = (await session.execute(select(AutomationRule).where(
        AutomationRule.id == original.rule_id, AutomationRule.guild_id == guild_id
    ))).scalar_one_or_none()
    if rule is None:
        raise HTTPException(404, "Automation rule not found")
    retry = AutomationRun(rule_id=rule.id, guild_id=guild_id, status="queued",
        trigger_payload=original.trigger_payload, result={"retry_of": str(original.id), "actions": []},
        event_type=original.event_type, event_id=f"manual-retry:{original.id}", attempt_count=0,
        initiated_by=current_user.id)
    session.add(retry)
    await session.flush()
    job = {"job": "automation_execute", "guild_id": guild_id, "automation": {
        "run_id": str(retry.id), "rule_id": str(rule.id), "rule_name": rule.name,
        "stop_on_error": rule.stop_on_error, "actions": rule.actions, "context": original.trigger_payload}}
    redis = Redis.from_url(settings.redis_url, decode_responses=True,
        health_check_interval=30, socket_keepalive=True, retry_on_timeout=True)
    try:
        await redis.lpush(settings.discord_job_queue, json.dumps(job))
    except Exception as exc:
        retry.status = "failed"; retry.error = f"Queue unavailable: {exc}"; retry.finished_at = datetime.now(timezone.utc)
        await session.commit()
        raise HTTPException(503, "Discord worker queue is unavailable") from exc
    finally:
        await redis.aclose()
    await AuditService(session).record(event_type="automation.run_retried", guild_id=guild_id,
        actor_user_id=current_user.id, target_type="automation_run", target_id=str(retry.id),
        payload={"retry_of": str(original.id), "rule_id": str(rule.id)})
    await session.commit()
    return {**run_view(retry), "rule_name": rule.name}
