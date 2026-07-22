from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.platform_access import require_platform_admin, require_superadmin
from app.db.session import get_db_session
from app.models.core import User
from app.schemas.plugin_control import ActivationResponse, MaintenanceRequest, PermissionItem, PermissionUpdate, SecretCreate, SecretMetadata, VersionHistoryItem
from app.services.plugin_control_service import PluginControlService

router = APIRouter(prefix="/platform/plugins", tags=["Plugin Control"])

def actor_id(user: User): return getattr(user, "id", None)

def activation(row):
    return ActivationResponse(plugin_key=row.plugin_key, state=row.state, enabled=row.enabled, maintenance=row.maintenance, restart_count=row.restart_count, pid=row.pid, last_heartbeat_at=row.last_heartbeat_at, last_error=row.last_error, updated_at=row.updated_at)

@router.get("/{plugin_key}/permissions", response_model=list[PermissionItem])
async def get_permissions(plugin_key: str, _: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db_session)):
    return await PluginControlService(session).permissions(plugin_key)

@router.put("/{plugin_key}/permissions", response_model=list[PermissionItem])
async def put_permissions(plugin_key: str, payload: PermissionUpdate, user: User = Depends(require_superadmin), session: AsyncSession = Depends(get_db_session)):
    try: return await PluginControlService(session).update_permissions(plugin_key, payload.permissions, actor_id(user))
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc

@router.get("/{plugin_key}/secrets", response_model=list[SecretMetadata])
async def list_secrets(plugin_key: str, _: User = Depends(require_superadmin), session: AsyncSession = Depends(get_db_session)):
    return [SecretMetadata(secret_name=x.secret_name, scope=x.scope, scope_key=x.scope_key, key_version=x.key_version, created_at=x.created_at, updated_at=x.updated_at) for x in await PluginControlService(session).list_secrets(plugin_key)]

@router.post("/{plugin_key}/secrets", response_model=SecretMetadata)
async def create_secret(plugin_key: str, payload: SecretCreate, user: User = Depends(require_superadmin), session: AsyncSession = Depends(get_db_session)):
    try: x = await PluginControlService(session).put_secret(plugin_key, payload.secret_name, payload.value, payload.scope, payload.scope_key, actor_id(user))
    except RuntimeError as exc: raise HTTPException(503, str(exc)) from exc
    return SecretMetadata(secret_name=x.secret_name, scope=x.scope, scope_key=x.scope_key, key_version=x.key_version, created_at=x.created_at, updated_at=x.updated_at)

@router.delete("/{plugin_key}/secrets/{secret_name}", status_code=204)
async def remove_secret(plugin_key: str, secret_name: str, scope: str = Query("plugin"), scope_key: str = Query(""), user: User = Depends(require_superadmin), session: AsyncSession = Depends(get_db_session)):
    try: await PluginControlService(session).delete_secret(plugin_key, secret_name, scope, scope_key, actor_id(user))
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc
    return Response(status_code=204)

@router.get("/{plugin_key}/status", response_model=ActivationResponse)
async def status(plugin_key: str, _: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db_session)):
    return activation(await PluginControlService(session).activation(plugin_key))

@router.post("/{plugin_key}/{action}", response_model=ActivationResponse)
async def action(plugin_key: str, action: str, user: User = Depends(require_superadmin), session: AsyncSession = Depends(get_db_session)):
    if action not in {"start", "stop", "restart", "enable", "disable"}: raise HTTPException(404, "Unknown plugin action")
    try: return activation(await PluginControlService(session).transition(plugin_key, action, actor_id(user)))
    except ValueError as exc: raise HTTPException(409, str(exc)) from exc

@router.put("/{plugin_key}/maintenance", response_model=ActivationResponse)
async def maintenance(plugin_key: str, payload: MaintenanceRequest, user: User = Depends(require_superadmin), session: AsyncSession = Depends(get_db_session)):
    return activation(await PluginControlService(session).maintenance(plugin_key, payload.enabled, actor_id(user)))

@router.get("/{plugin_key}/versions", response_model=list[VersionHistoryItem])
async def versions(plugin_key: str, _: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db_session)):
    return [VersionHistoryItem(plugin_key=x.plugin_key, version=x.version, previous_version=x.previous_version, action=x.action, status=x.status, checksum_sha256=x.checksum_sha256, metadata_json=x.metadata_json, created_at=x.created_at) for x in await PluginControlService(session).versions(plugin_key)]
