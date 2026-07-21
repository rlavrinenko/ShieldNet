from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db_session
from app.models.audit import AuditEvent
from app.models.core import User
from app.models.discord import Guild, GuildMembership, MembershipStatus
from app.models.members import DiscordMember
from app.models.verification import VerificationRequest

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/overview")
async def dashboard_overview(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    if getattr(current_user, "is_superadmin", False):
        guild_query = (
            select(Guild)
            .order_by(Guild.name)
        )
    else:
        guild_query = (
            select(Guild)
            .join(
                GuildMembership,
                GuildMembership.guild_id == Guild.guild_id,
            )
            .where(
                GuildMembership.user_id == current_user.id,
                GuildMembership.status == MembershipStatus.ACTIVE,
            )
            .order_by(Guild.name)
        )

    guilds = list(
        (
            await session.execute(guild_query)
        ).scalars().unique().all()
    )

    guild_ids = [guild.guild_id for guild in guilds]

    if not guild_ids:
        return {
            "generated_at": datetime.now(UTC),
            "services": {
                "backend": "online",
                "database": "online",
            },
            "totals": {
                "guilds": 0,
                "members": 0,
                "verification_pending": 0,
                "verification_failed": 0,
                "audit_24h": 0,
            },
            "guilds": [],
        }

    member_rows = await session.execute(
        select(
            DiscordMember.guild_id,
            func.count(DiscordMember.id),
        )
        .where(
            DiscordMember.guild_id.in_(guild_ids),
            DiscordMember.is_active.is_(True),
        )
        .group_by(DiscordMember.guild_id)
    )
    members = dict(member_rows.all())

    verification_rows = await session.execute(
        select(
            VerificationRequest.guild_id,
            VerificationRequest.status,
            func.count(VerificationRequest.id),
        )
        .where(
            VerificationRequest.guild_id.in_(guild_ids),
        )
        .group_by(
            VerificationRequest.guild_id,
            VerificationRequest.status,
        )
    )

    verification: dict[int, dict[str, int]] = {}

    for guild_id, status, count in verification_rows.all():
        verification.setdefault(guild_id, {})[status] = count

    audit_since = datetime.now(UTC) - timedelta(hours=24)

    audit_rows = await session.execute(
        select(
            AuditEvent.guild_id,
            func.count(AuditEvent.id),
        )
        .where(
            AuditEvent.guild_id.in_(guild_ids),
            AuditEvent.created_at >= audit_since,
        )
        .group_by(AuditEvent.guild_id)
    )
    audit_counts = dict(audit_rows.all())

    await session.execute(text("SELECT 1"))

    guild_items = []

    for guild in guilds:
        statuses = verification.get(guild.guild_id, {})

        guild_items.append({
            "guild_id": guild.guild_id,
            "name": guild.name,
            "icon_url": guild.icon_url,
            "status": guild.status.value,
            "bot_status": guild.bot_status.value,
            "member_count": members.get(
                guild.guild_id,
                guild.member_count,
            ),
            "verification_pending": statuses.get("pending", 0),
            "verification_processing": statuses.get(
                "processing",
                0,
            ),
            "verification_failed": statuses.get("failed", 0),
            "audit_24h": audit_counts.get(guild.guild_id, 0),
            "last_sync_at": guild.last_sync_at,
        })

    return {
        "generated_at": datetime.now(UTC),
        "services": {
            "backend": "online",
            "database": "online",
        },
        "totals": {
            "guilds": len(guild_items),
            "members": sum(
                item["member_count"]
                for item in guild_items
            ),
            "verification_pending": sum(
                item["verification_pending"]
                for item in guild_items
            ),
            "verification_failed": sum(
                item["verification_failed"]
                for item in guild_items
            ),
            "audit_24h": sum(
                item["audit_24h"]
                for item in guild_items
            ),
        },
        "guilds": guild_items,
    }
