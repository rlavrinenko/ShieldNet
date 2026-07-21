from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.guild_access import require_guild_management
from app.db.session import get_db_session
from app.models.core import User
from app.models.discord import Guild
from app.services.guild_registry import GuildRegistryService

router = APIRouter(prefix="/discord/guild-registry", tags=["Guild Registry"])


@router.get("/{guild_id}")
async def get_registry_entry(
    guild_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await require_guild_management(session, current_user, guild_id)
    guild = await session.get(Guild, guild_id)

    # For a superadmin the dependency may have initialized a placeholder.
    if guild is None:
        guild = await GuildRegistryService(session).ensure_management_target(
            guild_id,
            current_user,
        )

    return {
        "registered": True,
        "guild_id": guild.guild_id,
        "name": guild.name,
        "icon_url": guild.icon_url,
        "owner_discord_id": guild.owner_discord_id,
        "member_count": guild.member_count,
        "status": guild.status.value,
        "bot_status": guild.bot_status.value,
        "last_sync_at": guild.last_sync_at,
    }
