from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discord import GuildMembership, MembershipRole, MembershipStatus
from app.models.permissions import GuildPermissionRule, PermissionEffect, PermissionName
from app.schemas.permissions import PermissionCheckResponse


class PermissionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def check_discord_user(self, guild_id: int, module_key: str, permission: PermissionName, discord_user_id: int, discord_role_ids: list[int]) -> PermissionCheckResponse:
        membership = (await self.session.execute(
            select(GuildMembership).where(
                GuildMembership.guild_id == guild_id,
                GuildMembership.discord_user_id == discord_user_id,
                GuildMembership.status == MembershipStatus.ACTIVE,
            )
        )).scalar_one_or_none()

        if membership and membership.role == MembershipRole.ADMIN:
            return PermissionCheckResponse(allowed=True, reason="Server Admin")

        subjects = {("everyone", "*"), ("discord_user", str(discord_user_id))}
        subjects.update(("discord_role", str(role_id)) for role_id in discord_role_ids)
        if membership:
            subjects.add(("shieldnet_role", membership.role.value))

        result = await self.session.execute(
            select(GuildPermissionRule)
            .where(
                GuildPermissionRule.guild_id == guild_id,
                GuildPermissionRule.module_key.in_([module_key, "*"]),
                GuildPermissionRule.permission == permission,
                GuildPermissionRule.enabled.is_(True),
            )
            .order_by(GuildPermissionRule.priority.desc(), GuildPermissionRule.created_at)
        )
        matched = [r for r in result.scalars().all() if (r.subject_type, r.subject_value) in subjects]

        deny = next((r for r in matched if r.effect == PermissionEffect.DENY), None)
        if deny:
            return PermissionCheckResponse(allowed=False, matched_rule_id=deny.id, reason="Explicit deny rule")

        allow = next((r for r in matched if r.effect == PermissionEffect.ALLOW), None)
        if allow:
            return PermissionCheckResponse(allowed=True, matched_rule_id=allow.id, reason="Explicit allow rule")

        return PermissionCheckResponse(allowed=False, reason="No matching allow rule")
