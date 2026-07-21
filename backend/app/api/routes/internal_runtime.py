from datetime import UTC, datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.internal import verify_internal_service_token
from app.db.session import get_db_session
from app.models.runtime import RuntimeHeartbeat
from app.schemas.runtime import RuntimeHeartbeatIn

router = APIRouter(prefix="/internal/runtime", tags=["Internal Runtime"], dependencies=[Depends(verify_internal_service_token)])

@router.post("/heartbeat")
async def heartbeat(payload: RuntimeHeartbeatIn, session: AsyncSession = Depends(get_db_session)) -> dict:
    item = await session.get(RuntimeHeartbeat, payload.worker_name)
    now = datetime.now(UTC)
    if item is None:
        item = RuntimeHeartbeat(
            worker_name=payload.worker_name,
            worker_type=payload.worker_type,
            status=payload.status,
            metadata_json=payload.metadata,
            started_at=now,
            last_seen_at=now,
        )
        session.add(item)
    else:
        item.worker_type = payload.worker_type
        item.status = payload.status
        item.metadata_json = payload.metadata
        item.last_seen_at = now
    await session.commit()
    return {"ok": True, "worker_name": payload.worker_name, "last_seen_at": now}
