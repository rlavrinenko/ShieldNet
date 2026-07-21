from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.platform_access import require_platform_admin, require_superadmin
from app.db.session import get_db_session
from app.models.core import User
from app.schemas.plugin_marketplace import (
    MarketplaceItemCreate,
    MarketplaceItemResponse,
    MarketplaceItemUpdate,
    MarketplacePageResponse,
    MarketplaceStateRequest,
    MarketplaceVersionCreate,
    MarketplaceVersionResponse,
)
from app.services.plugin_marketplace_service import (
    MarketplaceConflictError,
    PluginMarketplaceService,
)

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


@router.get("/admin", response_model=MarketplacePageResponse)
async def list_marketplace_plugins_admin(
    query: str | None = Query(default=None, max_length=160),
    category: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_db_session),
) -> MarketplacePageResponse:
    return await PluginMarketplaceService(session).list_items(
        query=query,
        category=category,
        limit=limit,
        offset=offset,
        include_unpublished=True,
    )


@router.post(
    "",
    response_model=MarketplaceItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_marketplace_plugin(
    payload: MarketplaceItemCreate,
    _: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_db_session),
) -> MarketplaceItemResponse:
    try:
        return await PluginMarketplaceService(session).create_item(payload)
    except MarketplaceConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/{plugin_key}/versions",
    response_model=MarketplaceVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_marketplace_plugin_version(
    plugin_key: str,
    payload: MarketplaceVersionCreate,
    _: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_db_session),
) -> MarketplaceVersionResponse:
    try:
        return await PluginMarketplaceService(session).add_version(plugin_key, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except MarketplaceConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.patch("/{plugin_key}/publish", response_model=MarketplaceItemResponse)
async def publish_marketplace_plugin(
    plugin_key: str,
    payload: MarketplaceStateRequest,
    _: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_db_session),
) -> MarketplaceItemResponse:
    try:
        return await PluginMarketplaceService(session).set_published(
            plugin_key,
            payload.enabled,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except MarketplaceConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.patch("/{plugin_key}/verify", response_model=MarketplaceItemResponse)
async def verify_marketplace_plugin(
    plugin_key: str,
    payload: MarketplaceStateRequest,
    _: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_db_session),
) -> MarketplaceItemResponse:
    try:
        return await PluginMarketplaceService(session).set_verified(
            plugin_key,
            payload.enabled,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete(
    "/{plugin_key}/versions/{version_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_marketplace_plugin_version(
    plugin_key: str,
    version_id: UUID,
    _: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    try:
        await PluginMarketplaceService(session).delete_version(plugin_key, version_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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


@router.patch("/{plugin_key}", response_model=MarketplaceItemResponse)
async def update_marketplace_plugin(
    plugin_key: str,
    payload: MarketplaceItemUpdate,
    _: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_db_session),
) -> MarketplaceItemResponse:
    try:
        return await PluginMarketplaceService(session).update_item(plugin_key, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete(
    "/{plugin_key}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_marketplace_plugin(
    plugin_key: str,
    _: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    try:
        await PluginMarketplaceService(session).delete_item(plugin_key)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
