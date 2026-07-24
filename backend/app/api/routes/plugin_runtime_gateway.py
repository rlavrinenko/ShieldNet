from __future__ import annotations

from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select

from app.api.dependencies.plugin_runtime import (
    get_plugin_runtime_claims,
    require_runtime_capability,
)
from app.db.session import AsyncSessionFactory
from app.models.plugins import PluginRuntimeInstance
from app.plugin_sdk.capabilities import ALL_CAPABILITIES
from app.plugin_sdk.runtime_tokens import (
    RuntimeTokenClaims,
    create_runtime_token,
)

router = APIRouter(
    prefix="/internal/plugin-runtime",
    tags=["Plugin Runtime Gateway"],
)


def _manifest_permissions(
    manifest: dict[str, Any] | None,
) -> frozenset[str]:
    manifest = manifest or {}
    raw_permissions = manifest.get("permissions", [])

    if not isinstance(raw_permissions, list) or any(
        not isinstance(permission, str)
        for permission in raw_permissions
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Runtime manifest permissions are invalid",
        )

    permissions = frozenset(raw_permissions)
    unknown = sorted(permissions - ALL_CAPABILITIES)

    if unknown:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Runtime manifest contains unknown capabilities: "
                + ", ".join(unknown)
            ),
        )

    return permissions


@router.get("/context")
async def runtime_context(
    claims: Annotated[
        RuntimeTokenClaims,
        Depends(get_plugin_runtime_claims),
    ],
) -> dict:
    return {
        "authenticated": True,
        "plugin_key": claims.plugin_key,
        "guild_id": claims.guild_id,
        "generation": claims.generation,
        "permissions": sorted(claims.permissions),
        "token_id": claims.token_id,
        "issued_at": claims.issued_at,
        "expires_at": claims.expires_at,
    }


@router.post("/token/refresh")
async def refresh_runtime_token(
    claims: Annotated[
        RuntimeTokenClaims,
        Depends(get_plugin_runtime_claims),
    ],
) -> dict:
    async with AsyncSessionFactory() as session:
        runtime = (
            await session.execute(
                select(PluginRuntimeInstance).where(
                    PluginRuntimeInstance.guild_id
                    == claims.guild_id,
                    PluginRuntimeInstance.plugin_key
                    == claims.plugin_key,
                )
            )
        ).scalar_one_or_none()

    if runtime is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Plugin runtime no longer exists",
        )

    if runtime.state != "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Plugin runtime is not running",
        )

    if runtime.generation != claims.generation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Plugin runtime generation changed; "
                "process restart is required"
            ),
        )

    permissions = _manifest_permissions(
        runtime.manifest_json
    )

    token = create_runtime_token(
        plugin_key=runtime.plugin_key,
        guild_id=runtime.guild_id,
        generation=runtime.generation,
        permissions=permissions,
    )

    return {
        "token": token,
        "token_type": "Bearer",
        "plugin_key": runtime.plugin_key,
        "guild_id": runtime.guild_id,
        "generation": runtime.generation,
        "permissions": sorted(permissions),
    }


@router.post("/test/runtime-read")
async def test_runtime_read(
    claims: Annotated[
        RuntimeTokenClaims,
        Depends(
            require_runtime_capability(
                "runtime.read"
            )
        ),
    ],
) -> dict:
    return {
        "allowed": True,
        "capability": "runtime.read",
        "plugin_key": claims.plugin_key,
        "guild_id": claims.guild_id,
    }


@router.post("/test/send-message")
async def test_send_message(
    claims: Annotated[
        RuntimeTokenClaims,
        Depends(
            require_runtime_capability(
                "discord.send.message"
            )
        ),
    ],
) -> dict:
    return {
        "allowed": True,
        "capability": "discord.send.message",
        "plugin_key": claims.plugin_key,
        "guild_id": claims.guild_id,
    }
