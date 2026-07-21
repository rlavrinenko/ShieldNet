from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.platform_access import require_platform_admin
from app.db.session import get_db_session
from app.models.core import User
from app.models.plugins import PluginEvent

router = APIRouter(prefix="/platform/plugin-events", tags=["Plugin Platform"])


class PluginEventItem(BaseModel):
    id: str
    plugin_key: str
    event_type: str
    status: str
    message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class PluginEventPage(BaseModel):
    items: list[PluginEventItem]
    total: int
    limit: int
    offset: int


class PluginEventSummary(BaseModel):
    total: int
    success: int
    warning: int
    error: int
    latest_at: datetime | None = None


def _item(row: PluginEvent) -> PluginEventItem:
    return PluginEventItem(
        id=str(row.id),
        plugin_key=row.plugin_key,
        event_type=row.event_type,
        status=row.status,
        message=row.message,
        metadata=row.metadata_json or {},
        created_at=row.created_at,
    )


@router.get("", response_model=PluginEventPage)
async def list_plugin_events(
    plugin_key: str | None = Query(default=None, min_length=1, max_length=96),
    event_type: str | None = Query(default=None, min_length=1, max_length=64),
    status: Literal["success", "warning", "error"] | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db_session),
) -> PluginEventPage:
    filters = []
    if plugin_key:
        filters.append(PluginEvent.plugin_key == plugin_key)
    if event_type:
        filters.append(PluginEvent.event_type == event_type)
    if status:
        filters.append(PluginEvent.status == status)

    total_stmt = select(func.count(PluginEvent.id))
    items_stmt = select(PluginEvent).order_by(PluginEvent.created_at.desc())
    if filters:
        total_stmt = total_stmt.where(*filters)
        items_stmt = items_stmt.where(*filters)

    total = int((await session.execute(total_stmt)).scalar_one())
    result = await session.execute(items_stmt.limit(limit).offset(offset))
    items = [_item(row) for row in result.scalars().all()]
    return PluginEventPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/summary", response_model=PluginEventSummary)
async def plugin_event_summary(
    plugin_key: str | None = Query(default=None, min_length=1, max_length=96),
    _: User = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db_session),
) -> PluginEventSummary:
    stmt = select(
        func.count(PluginEvent.id),
        func.count(PluginEvent.id).filter(PluginEvent.status == "success"),
        func.count(PluginEvent.id).filter(PluginEvent.status == "warning"),
        func.count(PluginEvent.id).filter(PluginEvent.status == "error"),
        func.max(PluginEvent.created_at),
    )
    if plugin_key:
        stmt = stmt.where(PluginEvent.plugin_key == plugin_key)

    total, success, warning, error, latest_at = (await session.execute(stmt)).one()
    return PluginEventSummary(
        total=int(total or 0),
        success=int(success or 0),
        warning=int(warning or 0),
        error=int(error or 0),
        latest_at=latest_at,
    )
