from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
)

from app.api.dependencies.plugin_runtime import (
    get_plugin_runtime_claims,
    require_runtime_capability,
)
from app.plugin_sdk.runtime_tokens import (
    RuntimeTokenClaims,
)

router = APIRouter(
    prefix="/internal/plugin-runtime",
    tags=["Plugin Runtime Gateway"],
)


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
