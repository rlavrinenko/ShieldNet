from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.guild_access import require_guild_management
from app.db.session import get_db_session
from app.models.core import User
from app.schemas.audit import AuditListResponse
from app.services.audit_service import AuditService

router = APIRouter(tags=["Audit"])


@router.get("/discord/guilds/{guild_id}/audit", response_model=AuditListResponse)
async def list_audit(
    guild_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> AuditListResponse:
    await require_guild_management(session, current_user, guild_id)
    return await AuditService(session).list_for_guild(guild_id, page, page_size)
