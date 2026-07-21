from datetime import UTC, datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.auth import get_current_user
from app.db.session import get_db_session
from app.models.core import GlobalRole, User
from app.models.runtime import RuntimeHeartbeat
from app.services.global_access import GlobalAccessService

router = APIRouter(prefix="/platform/runtime", tags=["Platform Runtime"])

@router.get("")
async def runtime_status(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)) -> dict:
    GlobalAccessService.require_any(current_user, (GlobalRole.SUPERADMIN, GlobalRole.ADMIN))
    rows = list((await session.scalars(select(RuntimeHeartbeat).order_by(RuntimeHeartbeat.worker_type, RuntimeHeartbeat.worker_name))).all())
    cutoff = datetime.now(UTC) - timedelta(seconds=90)
    return {
        "items": [
            {
                "worker_name": r.worker_name,
                "worker_type": r.worker_type,
                "status": "online" if r.last_seen_at >= cutoff else "stale",
                "metadata": r.metadata_json,
                "started_at": r.started_at,
                "last_seen_at": r.last_seen_at,
            }
            for r in rows
        ]
    }
