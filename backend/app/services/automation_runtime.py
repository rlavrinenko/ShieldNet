from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.automations import AutomationRule, AutomationRun
from app.services.automation_service import AutomationService


class AutomationRuntimeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.rules = AutomationService(session)

    @staticmethod
    def event_key(guild_id: int, event_type: str, event_id: str, rule_id: UUID) -> str:
        raw = f"{guild_id}:{event_type}:{event_id}:{rule_id}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def dispatch(self, guild_id: int, event_type: str, event_id: str, context: dict[str, Any]) -> list[dict[str, Any]]:
        rules = list((await self.session.execute(
            select(AutomationRule).where(
                AutomationRule.guild_id == guild_id,
                AutomationRule.status == "enabled",
                AutomationRule.trigger_type == event_type,
            ).order_by(AutomationRule.created_at.asc())
        )).scalars().all())
        jobs: list[dict[str, Any]] = []
        for rule in rules:
            evaluations = []
            matched = True
            for condition in rule.conditions:
                actual = self.rules._value(context, str(condition.get("field", "")))
                operator = str(condition.get("operator", "eq"))
                expected = condition.get("value")
                passed = self.rules._matches(actual, operator, expected)
                evaluations.append({**condition, "actual": actual, "passed": passed})
                matched = matched and passed
            if not matched:
                continue
            idem = self.event_key(guild_id, event_type, event_id, rule.id)
            existing = (await self.session.execute(select(AutomationRun.id).where(AutomationRun.idempotency_key == idem))).scalar_one_or_none()
            if existing is not None:
                continue
            run = AutomationRun(
                rule_id=rule.id,
                guild_id=guild_id,
                status="queued",
                trigger_payload=context,
                result={"conditions": evaluations, "actions": []},
                idempotency_key=idem,
                event_type=event_type,
                event_id=event_id,
                attempt_count=0,
            )
            self.session.add(run)
            await self.session.flush()
            jobs.append({
                "run_id": str(run.id),
                "rule_id": str(rule.id),
                "rule_name": rule.name,
                "stop_on_error": rule.stop_on_error,
                "actions": rule.actions,
                "context": context,
            })
        return jobs

    async def complete(self, run_id: UUID, status: str, result: dict[str, Any], error: str | None = None) -> AutomationRun | None:
        run = (await self.session.execute(select(AutomationRun).where(AutomationRun.id == run_id))).scalar_one_or_none()
        if run is None:
            return None
        run.status = status
        run.result = result
        run.error = error
        run.finished_at = datetime.now(timezone.utc)
        run.attempt_count = int(run.attempt_count or 0) + 1
        rule = (await self.session.execute(select(AutomationRule).where(AutomationRule.id == run.rule_id))).scalar_one_or_none()
        if rule is not None:
            rule.execution_count = int(rule.execution_count or 0) + 1
            rule.last_executed_at = datetime.now(timezone.utc)
            if status != "succeeded":
                rule.failure_count = int(rule.failure_count or 0) + 1
                if rule.failure_count >= int(rule.max_failures or 5):
                    rule.status = "disabled"
                    rule.disabled_reason = f"Automatically disabled after {rule.failure_count} failed runs"
        await self.session.flush()
        return run
