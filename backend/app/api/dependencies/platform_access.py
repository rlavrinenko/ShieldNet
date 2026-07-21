from typing import Annotated

from fastapi import Depends

from app.api.dependencies.auth import get_current_user
from app.models.core import GlobalRole, User
from app.services.global_access import GlobalAccessService


async def require_platform_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    GlobalAccessService.require_any(
        user,
        (GlobalRole.SUPERADMIN, GlobalRole.ADMIN),
    )
    return user


async def require_superadmin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    GlobalAccessService.require_superadmin(user)
    return user
