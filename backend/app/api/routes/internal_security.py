from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.internal import verify_internal_service_token
from app.db.session import get_db_session
from app.schemas.security import SecuritySnapshotIn
from app.services.guild_registry import GuildRegistryService
from app.services.security_service import SecurityService

router = APIRouter(tags=["Internal Security"], dependencies=[Depends(verify_internal_service_token)])


@router.post("/internal/security/snapshot")
async def ingest_security_snapshot(payload: SecuritySnapshotIn, session: AsyncSession = Depends(get_db_session)):
    await GuildRegistryService(session).ensure_exists(payload.guild_id)
    snapshot = await SecurityService(session).ingest(payload)
    return {"ok": True, "snapshot_id": str(snapshot.id)}
