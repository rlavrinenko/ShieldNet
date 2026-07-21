from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.guild_access import require_guild_management
from app.db.session import get_db_session
from app.models.core import User
from app.schemas.security import SecurityFindingOut, SecuritySummaryOut
from app.services.security_service import SecurityService

router = APIRouter(tags=["Security"])


@router.get("/discord/guilds/{guild_id}/security", response_model=SecuritySummaryOut)
async def security_summary(guild_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await require_guild_management(session, current_user, guild_id)
    snapshot, findings, counts, score = await SecurityService(session).latest(guild_id)
    return SecuritySummaryOut(
        guild_id=guild_id,
        snapshot_id=snapshot.id if snapshot else None,
        collected_at=snapshot.collected_at if snapshot else None,
        role_count=snapshot.role_count if snapshot else 0,
        channel_count=snapshot.channel_count if snapshot else 0,
        webhook_count=snapshot.webhook_count if snapshot else 0,
        risk_score=score,
        counts=counts,
        findings=[SecurityFindingOut.model_validate(item, from_attributes=True) for item in findings],
    )
