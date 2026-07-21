from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.platform_access import require_platform_admin, require_superadmin
from app.db.session import get_db_session
from app.models.core import User
from app.schemas.plugins import (
    PluginManifestResponse,
    PluginRuntimeResponse,
    PluginScanResponse,
    PluginStateRequest,
)
from app.plugins.runtime import plugin_runtime
from app.services.plugin_service import PluginService

router = APIRouter(prefix="/platform/plugins", tags=["Plugin Platform"])


@router.get("", response_model=list[PluginManifestResponse])
async def list_plugins(
    _: User = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db_session),
) -> list[PluginManifestResponse]:
    return await PluginService(session).list_plugins()


@router.post("/scan", response_model=PluginScanResponse)
async def scan_plugins(
    _: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_db_session),
) -> PluginScanResponse:
    return await PluginService(session).scan()


@router.patch("/{plugin_key}", response_model=PluginManifestResponse)
async def update_plugin_state(
    plugin_key: str,
    payload: PluginStateRequest,
    _: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_db_session),
) -> PluginManifestResponse:
    try:
        return await PluginService(session).set_enabled(plugin_key, payload.enabled)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/runtime", response_model=list[PluginRuntimeResponse])
async def plugin_runtime_status(
    _: User = Depends(require_platform_admin),
) -> list[PluginRuntimeResponse]:
    return [
        PluginRuntimeResponse(
            plugin_key=item.plugin_key,
            loaded=item.loaded,
            version=item.version,
            error=item.error,
        )
        for item in plugin_runtime.snapshot()
    ]
