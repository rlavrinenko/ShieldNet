from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.internal import verify_internal_service_token
from app.db.session import get_db_session
from app.schemas.permissions import PermissionCheckRequest, PermissionCheckResponse
from app.services.permission_service import PermissionService

router = APIRouter(
    prefix="/internal/permissions",
    tags=["Internal Permissions"],
    dependencies=[Depends(verify_internal_service_token)],
)


@router.post("/check", response_model=PermissionCheckResponse)
async def check_permission(payload: PermissionCheckRequest, session: AsyncSession = Depends(get_db_session)):
    return await PermissionService(session).check_discord_user(
        payload.guild_id,
        payload.module_key,
        payload.permission,
        payload.discord_user_id,
        payload.discord_role_ids,
    )
