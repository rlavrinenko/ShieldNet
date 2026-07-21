from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.platform_access import require_superadmin
from app.db.session import get_db_session
from app.models.core import User
from app.models.discord import Guild, GuildMembership, MembershipStatus
from app.services.global_access import GlobalAccessService

router = APIRouter(prefix="/platform/access", tags=["Platform Access"])


@router.get("/me")
async def platform_access_me(
    current_user: User = Depends(get_current_user),
) -> dict:
    configured = GlobalAccessService.configured_superadmin_ids()
    return {
        "user_id": str(current_user.id),
        "discord_user_id": current_user.discord_user_id,
        "roles": GlobalAccessService.effective_role_names(current_user),
        "highest_role": (
            GlobalAccessService.highest_role(current_user).value
            if GlobalAccessService.highest_role(current_user)
            else None
        ),
        "is_superadmin": GlobalAccessService.is_superadmin(current_user),
        "superadmin_source": (
            "environment"
            if current_user.discord_user_id in configured
            else "database"
            if GlobalAccessService.is_superadmin(current_user)
            else None
        ),
    }


@router.get("/overview")
async def platform_access_overview(
    _: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    guild_count = await session.scalar(select(func.count()).select_from(Guild))
    active_memberships = await session.scalar(
        select(func.count())
        .select_from(GuildMembership)
        .where(GuildMembership.status == MembershipStatus.ACTIVE)
    )
    user_count = await session.scalar(select(func.count()).select_from(User))

    return {
        "guild_count": guild_count or 0,
        "active_memberships": active_memberships or 0,
        "user_count": user_count or 0,
        "configured_superadmins": len(
            GlobalAccessService.configured_superadmin_ids()
        ),
        "configuration_key": "SHIELDNET_SUPERADMIN_IDS",
    }
