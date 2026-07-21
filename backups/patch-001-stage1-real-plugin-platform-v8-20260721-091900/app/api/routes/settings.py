from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.settings import ModuleSettings, SettingValue, SettingWrite
from app.services.settings import InvalidSettingName, SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


def service(db: AsyncSession = Depends(get_db_session)) -> SettingsService:
    return SettingsService(db)


@router.get("/{guild_id}/{module}", response_model=ModuleSettings)
async def list_module_settings(
    guild_id: int,
    module: str,
    settings: SettingsService = Depends(service),
) -> ModuleSettings:
    try:
        values = await settings.list_module(guild_id, module)
    except InvalidSettingName as exc:
        raise HTTPException(status_code=422, detail=f"Invalid setting name: {exc}") from exc
    return ModuleSettings(guild_id=guild_id, module=module, values=values)


@router.get("/{guild_id}/{module}/{key}", response_model=SettingValue)
async def get_setting(
    guild_id: int,
    module: str,
    key: str,
    settings: SettingsService = Depends(service),
) -> SettingValue:
    try:
        value = await settings.get(guild_id, module, key, default=None)
    except InvalidSettingName as exc:
        raise HTTPException(status_code=422, detail=f"Invalid setting name: {exc}") from exc
    if value is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    return SettingValue(guild_id=guild_id, module=module, key=key, value=value)


@router.put("/{guild_id}/{module}/{key}", response_model=SettingValue)
async def put_setting(
    guild_id: int,
    module: str,
    key: str,
    body: SettingWrite,
    settings: SettingsService = Depends(service),
) -> SettingValue:
    try:
        value = await settings.set(
            guild_id=guild_id,
            module=module,
            key=key,
            value=body.value,
        )
    except InvalidSettingName as exc:
        raise HTTPException(status_code=422, detail=f"Invalid setting name: {exc}") from exc
    return SettingValue(guild_id=guild_id, module=module, key=key, value=value)


@router.delete("/{guild_id}/{module}/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setting(
    guild_id: int,
    module: str,
    key: str,
    settings: SettingsService = Depends(service),
) -> Response:
    try:
        removed = await settings.delete(guild_id, module, key)
    except InvalidSettingName as exc:
        raise HTTPException(status_code=422, detail=f"Invalid setting name: {exc}") from exc
    if not removed:
        raise HTTPException(status_code=404, detail="Setting not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
