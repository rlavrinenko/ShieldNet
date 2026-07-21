from fastapi import APIRouter

from app.core.events import event_bus

router = APIRouter(prefix="/runtime/events", tags=["Runtime"])


@router.get("")
async def event_bus_status() -> dict[str, object]:
    snapshot = await event_bus.snapshot()
    return {
        "status": "ok" if snapshot.started else "stopped",
        "started": snapshot.started,
        "subscribers": snapshot.subscribers,
        "event_names": snapshot.event_names,
        "published": snapshot.published,
        "delivered": snapshot.delivered,
        "failed": snapshot.failed,
        "active_dispatches": snapshot.active_dispatches,
        "average_dispatch_ms": snapshot.average_dispatch_ms,
    }
