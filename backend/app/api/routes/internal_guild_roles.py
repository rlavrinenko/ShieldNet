from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.internal import verify_internal_service_token
from app.db.session import get_db_session
from app.models.guild_roles import DiscordGuildRole
from app.schemas.guild_roles import GuildRoleSyncRequest

router = APIRouter(
    prefix="/internal/discord/guilds",
    tags=["Internal Guild Roles"],
    dependencies=[Depends(verify_internal_service_token)],
)

@router.post("/{guild_id}/roles/sync")
async def sync_roles(guild_id: int, payload: GuildRoleSyncRequest, session: AsyncSession = Depends(get_db_session)):
    await session.execute(delete(DiscordGuildRole).where(DiscordGuildRole.guild_id == guild_id))
    for role in payload.roles:
        session.add(DiscordGuildRole(guild_id=guild_id, **role.model_dump()))
    await session.commit()
    return {"status": "synchronized", "count": len(payload.roles)}
