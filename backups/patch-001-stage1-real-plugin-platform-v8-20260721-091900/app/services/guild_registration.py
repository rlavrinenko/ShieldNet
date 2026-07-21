from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import User
from app.models.discord import (
    BotStatus,
    Guild,
    GuildMembership,
    GuildStatus,
    MembershipRole,
    MembershipStatus,
)
from app.schemas.discord import GuildRegisterRequest
from app.services.guild_registry import GuildRegistryService


class GuildRegistrationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.registry = GuildRegistryService(session)

    async def register(self, payload: GuildRegisterRequest) -> Guild:
        guild = await self.registry.ensure_exists(
            payload.guild_id,
            name=payload.name,
            icon_url=payload.icon_url,
            owner_discord_id=payload.owner_discord_id,
            member_count=payload.member_count,
            bot_online=True,
        )
        guild.preferred_language = payload.preferred_language
        if guild.status == GuildStatus.LEFT:
            guild.status = GuildStatus.NEED_SETUP
        guild.bot_status = BotStatus.ONLINE
        guild.left_at = None
        guild.last_sync_at = datetime.now(UTC)

        owner = (
            await self.session.execute(
                select(User).where(
                    User.discord_user_id == payload.owner_discord_id
                )
            )
        ).scalar_one_or_none()

        membership = (
            await self.session.execute(
                select(GuildMembership).where(
                    GuildMembership.guild_id == payload.guild_id,
                    GuildMembership.discord_user_id
                    == payload.owner_discord_id,
                )
            )
        ).scalar_one_or_none()

        membership_status = (
            MembershipStatus.ACTIVE
            if owner
            else MembershipStatus.PENDING
        )

        if membership is None:
            self.session.add(
                GuildMembership(
                    guild_id=payload.guild_id,
                    user_id=owner.id if owner else None,
                    discord_user_id=payload.owner_discord_id,
                    role=MembershipRole.ADMIN,
                    status=membership_status,
                )
            )
        else:
            membership.user_id = owner.id if owner else None
            membership.role = MembershipRole.ADMIN
            membership.status = membership_status

        await self.session.commit()
        await self.session.refresh(guild)
        return guild

    async def mark_left(self, guild_id: int) -> None:
        guild = await self.session.get(Guild, guild_id)
        if guild:
            guild.status = GuildStatus.LEFT
            guild.bot_status = BotStatus.REMOVED
            guild.left_at = datetime.now(UTC)
            await self.session.commit()
