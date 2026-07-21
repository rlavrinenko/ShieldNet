from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.platform_access import require_platform_admin
from app.db.session import get_db_session
from app.models.core import User
from app.schemas.plugin_marketplace import MarketplaceItemResponse, MarketplacePageResponse
from app.services.plugin_marketplace_service import PluginMarketplaceService

router = APIRouter(
    prefix="/platform/plugin-marketplace",
    tags=["Plugin Marketplace"],
)


@router.get("", response_model=MarketplacePageResponse)
async def list_marketplace_plugins(
    query: str | None = Query(default=None, max_length=160),
    category: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db_session),
) -> MarketplacePageResponse:
    return await PluginMarketplaceService(session).list_items(
        query=query,
        category=category,
        limit=limit,
        offset=offset,
    )


@router.get("/{plugin_key}", response_model=MarketplaceItemResponse)
async def get_marketplace_plugin(
    plugin_key: str,
    _: User = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db_session),
) -> MarketplaceItemResponse:
    try:
        return await PluginMarketplaceService(session).get_item(plugin_key)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
