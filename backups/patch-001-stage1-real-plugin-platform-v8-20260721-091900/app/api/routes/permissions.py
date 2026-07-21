import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.guild_access import require_guild_management
from app.db.session import get_db_session
from app.models.core import User
from app.models.permissions import GuildPermissionRule, PermissionName
from app.schemas.permissions import PermissionRuleResponse, PermissionRuleUpsert

router = APIRouter(tags=["Permissions"])


def serialize(rule: GuildPermissionRule) -> PermissionRuleResponse:
    return PermissionRuleResponse(
        id=rule.id,
        guild_id=rule.guild_id,
        module_key=rule.module_key,
        permission=rule.permission,
        effect=rule.effect,
        subject_type=rule.subject_type,
        subject_value=rule.subject_value,
        enabled=rule.enabled,
        priority=rule.priority,
    )


@router.get("/discord/guilds/{guild_id}/permissions", response_model=list[PermissionRuleResponse])
async def list_permissions(guild_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    result = await session.execute(
        select(GuildPermissionRule).where(GuildPermissionRule.guild_id == guild_id)
        .order_by(GuildPermissionRule.module_key, GuildPermissionRule.permission, GuildPermissionRule.priority.desc())
    )
    return [serialize(rule) for rule in result.scalars().all()]


@router.put("/discord/guilds/{guild_id}/permissions/{module_key}/{permission}", response_model=PermissionRuleResponse)
async def upsert_permission(guild_id: int, module_key: str, permission: PermissionName, payload: PermissionRuleUpsert, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    result = await session.execute(
        select(GuildPermissionRule).where(
            GuildPermissionRule.guild_id == guild_id,
            GuildPermissionRule.module_key == module_key,
            GuildPermissionRule.permission == permission,
            GuildPermissionRule.subject_type == payload.subject_type,
            GuildPermissionRule.subject_value == payload.subject_value,
        )
    )
    rule = result.scalar_one_or_none()
    if rule is None:
        rule = GuildPermissionRule(
            guild_id=guild_id,
            module_key=module_key,
            permission=permission,
            subject_type=payload.subject_type,
            subject_value=payload.subject_value,
            created_by=current_user.id,
        )
        session.add(rule)
    rule.effect = payload.effect
    rule.enabled = payload.enabled
    rule.priority = payload.priority
    await session.commit()
    await session.refresh(rule)
    return serialize(rule)


@router.delete("/discord/guilds/{guild_id}/permissions/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(guild_id: int, rule_id: uuid.UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    result = await session.execute(
        delete(GuildPermissionRule).where(
            GuildPermissionRule.id == rule_id,
            GuildPermissionRule.guild_id == guild_id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Permission rule not found")
    await session.commit()
