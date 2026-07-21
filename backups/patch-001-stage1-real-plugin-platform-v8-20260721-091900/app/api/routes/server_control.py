from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.guild_access import require_guild_management
from app.db.session import get_db_session
from app.models.audit import AuditEvent
from app.models.core import User
from app.models.discord import Guild
from app.models.members import DiscordMember
from app.models.verification import VerificationRequest

router = APIRouter(prefix="/discord/guilds", tags=["Server Control"])


@router.get("/{guild_id}/control-center")
async def control_center(
    guild_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await require_guild_management(session, current_user, guild_id)

    guild = (
        await session.execute(
            select(Guild).where(Guild.guild_id == guild_id)
        )
    ).scalar_one_or_none()

    if guild is None:
        raise HTTPException(status_code=404, detail="Server not found.")

    members = (
        await session.execute(
            select(func.count(DiscordMember.id)).where(
                DiscordMember.guild_id == guild_id,
                DiscordMember.is_active.is_(True),
            )
        )
    ).scalar_one()

    roles = (
        await session.execute(
            text(
                """
                SELECT COUNT(*)
                FROM discord.guild_roles
                WHERE guild_id = :guild_id
                """
            ),
            {"guild_id": guild_id},
        )
    ).scalar_one()

    rows = await session.execute(
        select(
            VerificationRequest.status,
            func.count(VerificationRequest.id),
        )
        .where(VerificationRequest.guild_id == guild_id)
        .group_by(VerificationRequest.status)
    )
    verification = dict(rows.all())

    since = datetime.now(UTC) - timedelta(hours=24)
    audit_24h = (
        await session.execute(
            select(func.count(AuditEvent.id)).where(
                AuditEvent.guild_id == guild_id,
                AuditEvent.created_at >= since,
            )
        )
    ).scalar_one()

    return {
        "generated_at": datetime.now(UTC),
        "guild": {
            "guild_id": guild.guild_id,
            "name": guild.name,
            "icon_url": guild.icon_url,
            "owner_discord_id": guild.owner_discord_id,
            "status": guild.status.value,
            "bot_status": guild.bot_status.value,
            "member_count": members,
            "role_count": roles,
            "channel_count": getattr(guild, "channel_count", 0),
            "category_count": getattr(guild, "category_count", 0),
            "last_sync_at": guild.last_sync_at,
        },
        "verification": {
            "pending": verification.get("pending", 0),
            "processing": verification.get("processing", 0),
            "completed": verification.get("completed", 0),
            "failed": verification.get("failed", 0),
        },
        "audit": {"events_24h": audit_24h},
        "services": {
            "backend": "online",
            "database": "online",
            "bot": guild.bot_status.value,
        },
    }
