from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.automations import AutomationRule, AutomationRun


TRIGGERS = {
    "member.joined": "Member joins the server",
    "member.left": "Member leaves the server",
    "member.verified": "Member is verified",
    "member.role_added": "Role is added to a member",
    "moderation.case_created": "Moderation case is created",
    "security.finding_created": "Security finding is detected",
    "schedule.daily": "Daily schedule",
}

ACTIONS = {
    "member.add_role": "Add Discord role",
    "member.remove_role": "Remove Discord role",
    "member.send_dm": "Send direct message",
    "channel.send_message": "Send channel message",
    "member.set_nickname": "Set member nickname",
    "audit.write": "Write Audit Log event",
    "webhook.call": "Call outgoing webhook",
}

OPERATORS = {"eq", "neq", "contains", "not_contains", "exists", "gt", "gte", "lt", "lte"}


class AutomationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self, guild_id: int) -> list[AutomationRule]:
        return list((await self.session.execute(
            select(AutomationRule).where(AutomationRule.guild_id == guild_id).order_by(AutomationRule.updated_at.desc())
        )).scalars().all())

    async def get(self, guild_id: int, rule_id: UUID) -> AutomationRule | None:
        return (await self.session.execute(select(AutomationRule).where(
            AutomationRule.guild_id == guild_id, AutomationRule.id == rule_id
        ))).scalar_one_or_none()

    def validate(self, trigger_type: str, conditions: list[dict[str, Any]], actions: list[dict[str, Any]]) -> None:
        if trigger_type not in TRIGGERS:
            raise ValueError("Unsupported trigger type")
        if not actions:
            raise ValueError("At least one action is required")
        for condition in conditions:
            if not condition.get("field"):
                raise ValueError("Condition field is required")
            if condition.get("operator", "eq") not in OPERATORS:
                raise ValueError("Unsupported condition operator")
        for action in actions:
            if action.get("type") not in ACTIONS:
                raise ValueError("Unsupported action type")

    async def create(self, guild_id: int, payload: dict[str, Any], user_id: UUID | None) -> AutomationRule:
        self.validate(payload["trigger_type"], payload.get("conditions", []), payload.get("actions", []))
        item = AutomationRule(
            guild_id=guild_id,
            name=payload["name"].strip(),
            description=payload.get("description"),
            trigger_type=payload["trigger_type"],
            conditions=payload.get("conditions", []),
            actions=payload.get("actions", []),
            stop_on_error=payload.get("stop_on_error", True),
            max_failures=payload.get("max_failures", 5),
            status="draft",
            created_by=user_id,
            updated_by=user_id,
        )
        self.session.add(item)
        await self.session.flush()
        return item

    async def update(self, item: AutomationRule, payload: dict[str, Any], user_id: UUID | None) -> AutomationRule:
        trigger_type = payload.get("trigger_type", item.trigger_type)
        conditions = payload.get("conditions", item.conditions)
        actions = payload.get("actions", item.actions)
        self.validate(trigger_type, conditions, actions)
        for field in ("name", "description", "trigger_type", "conditions", "actions", "stop_on_error", "max_failures"):
            if field in payload:
                setattr(item, field, payload[field])
        item.updated_by = user_id
        item.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return item

    async def set_status(self, item: AutomationRule, status: str, user_id: UUID | None) -> AutomationRule:
        if status not in {"draft", "enabled", "disabled"}:
            raise ValueError("Invalid rule status")
        if status == "enabled":
            self.validate(item.trigger_type, item.conditions, item.actions)
        item.status = status
        item.updated_by = user_id
        item.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return item

    async def remove(self, guild_id: int, rule_id: UUID) -> bool:
        result = await self.session.execute(delete(AutomationRule).where(
            AutomationRule.guild_id == guild_id, AutomationRule.id == rule_id
        ))
        return bool(result.rowcount)

    @staticmethod
    def _value(context: dict[str, Any], path: str) -> Any:
        value: Any = context
        for part in path.split("."):
            if not isinstance(value, dict) or part not in value:
                return None
            value = value[part]
        return value

    @staticmethod
    def _matches(actual: Any, operator: str, expected: Any) -> bool:
        if operator == "exists": return actual is not None
        if operator == "eq": return actual == expected
        if operator == "neq": return actual != expected
        if operator == "contains": return expected in actual if isinstance(actual, (str, list, tuple, set)) else False
        if operator == "not_contains": return expected not in actual if isinstance(actual, (str, list, tuple, set)) else True
        try:
            if operator == "gt": return actual > expected
            if operator == "gte": return actual >= expected
            if operator == "lt": return actual < expected
            if operator == "lte": return actual <= expected
        except TypeError:
            return False
        return False

    async def dry_run(self, item: AutomationRule, context: dict[str, Any], user_id: UUID | None) -> AutomationRun:
        evaluations = []
        matched = True
        for condition in item.conditions:
            actual = self._value(context, str(condition.get("field", "")))
            operator = str(condition.get("operator", "eq"))
            expected = condition.get("value")
            passed = self._matches(actual, operator, expected)
            evaluations.append({**condition, "actual": actual, "passed": passed})
            matched = matched and passed
        planned = []
        if matched:
            for index, action in enumerate(item.actions, start=1):
                planned.append({"step": index, "type": action.get("type"), "parameters": action.get("parameters", {}), "would_execute": True})
        run = AutomationRun(
            rule_id=item.id,
            guild_id=item.guild_id,
            status="dry_run_matched" if matched else "dry_run_skipped",
            trigger_payload=context,
            result={"matched": matched, "conditions": evaluations, "planned_actions": planned, "executed": False},
            initiated_by=user_id,
            finished_at=datetime.now(timezone.utc),
        )
        self.session.add(run)
        await self.session.flush()
        return run

    async def runs(self, guild_id: int, rule_id: UUID, limit: int = 30) -> list[AutomationRun]:
        return list((await self.session.execute(select(AutomationRun).where(
            AutomationRun.guild_id == guild_id, AutomationRun.rule_id == rule_id
        ).order_by(AutomationRun.started_at.desc()).limit(limit))).scalars().all())
