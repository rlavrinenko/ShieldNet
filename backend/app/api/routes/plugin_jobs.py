from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.platform_access import require_superadmin
from app.db.session import get_db_session
from app.models.core import User
from app.schemas.plugin_jobs import (
    PluginJobCreate,
    PluginJobDetailResponse,
    PluginJobPageResponse,
    PluginJobResponse,
)
from app.services.plugin_job_service import PluginJobConflictError, PluginJobService

router = APIRouter(prefix="/platform", tags=["Plugin Installation Jobs"])


async def _enqueue(
    plugin_key: str,
    action: str,
    payload: PluginJobCreate,
    user: User,
    session: AsyncSession,
) -> PluginJobResponse:
    try:
        return await PluginJobService(session).enqueue(
            plugin_key=plugin_key,
            action=action,
            payload=payload,
            requested_by_user_id=getattr(user, "id", None),
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PluginJobConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/plugin-marketplace/{plugin_key}/install",
    response_model=PluginJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def install_plugin(
    plugin_key: str,
    payload: PluginJobCreate,
    user: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_db_session),
) -> PluginJobResponse:
    return await _enqueue(plugin_key, "install", payload, user, session)


@router.post(
    "/plugin-marketplace/{plugin_key}/update",
    response_model=PluginJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def update_plugin(
    plugin_key: str,
    payload: PluginJobCreate,
    user: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_db_session),
) -> PluginJobResponse:
    return await _enqueue(plugin_key, "update", payload, user, session)


@router.post(
    "/plugin-marketplace/{plugin_key}/rollback",
    response_model=PluginJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def rollback_plugin(
    plugin_key: str,
    payload: PluginJobCreate,
    user: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_db_session),
) -> PluginJobResponse:
    return await _enqueue(plugin_key, "rollback", payload, user, session)


@router.post(
    "/plugin-marketplace/{plugin_key}/uninstall",
    response_model=PluginJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def uninstall_plugin(
    plugin_key: str,
    payload: PluginJobCreate,
    user: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_db_session),
) -> PluginJobResponse:
    return await _enqueue(plugin_key, "uninstall", payload, user, session)


@router.get("/plugin-jobs", response_model=PluginJobPageResponse)
async def list_plugin_jobs(
    status_filter: str | None = Query(default=None, alias="status", max_length=24),
    plugin_key: str | None = Query(default=None, max_length=96),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_db_session),
) -> PluginJobPageResponse:
    return await PluginJobService(session).list_jobs(
        status=status_filter,
        plugin_key=plugin_key,
        limit=limit,
        offset=offset,
    )


@router.get("/plugin-jobs/{job_id}", response_model=PluginJobDetailResponse)
async def get_plugin_job(
    job_id: UUID,
    _: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_db_session),
) -> PluginJobDetailResponse:
    try:
        return await PluginJobService(session).get_job(job_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
