from __future__ import annotations

from collections.abc import Iterable

from fastapi import HTTPException, status

from app.core.config import settings
from app.models.core import GlobalRole, User


ROLE_PRIORITY: tuple[GlobalRole, ...] = (
    GlobalRole.SUPERADMIN,
    GlobalRole.ADMIN,
    GlobalRole.MODERATOR,
    GlobalRole.ADVERTISING_PARTNER,
)


class GlobalAccessService:
    """Resolve platform-wide roles from both the database and trusted env config."""

    @staticmethod
    def configured_superadmin_ids() -> set[int]:
        return settings.superadmin_id_set

    @classmethod
    def effective_roles(cls, user: User) -> set[GlobalRole]:
        roles = {item.role for item in user.roles}
        if (
            user.discord_user_id is not None
            and user.discord_user_id in cls.configured_superadmin_ids()
        ):
            roles.add(GlobalRole.SUPERADMIN)
        return roles

    @classmethod
    def effective_role_names(cls, user: User) -> list[str]:
        roles = cls.effective_roles(user)
        return [role.value for role in ROLE_PRIORITY if role in roles]

    @classmethod
    def highest_role(cls, user: User) -> GlobalRole | None:
        roles = cls.effective_roles(user)
        return next((role for role in ROLE_PRIORITY if role in roles), None)

    @classmethod
    def is_superadmin(cls, user: User) -> bool:
        return GlobalRole.SUPERADMIN in cls.effective_roles(user)

    @classmethod
    def require_any(cls, user: User, allowed: Iterable[GlobalRole]) -> None:
        allowed_set = set(allowed)
        if cls.effective_roles(user).isdisjoint(allowed_set):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient platform privileges",
            )

    @classmethod
    def require_superadmin(cls, user: User) -> None:
        if not cls.is_superadmin(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="SuperAdmin access required",
            )
