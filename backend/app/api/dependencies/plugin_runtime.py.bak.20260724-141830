from __future__ import annotations

from typing import Annotated

from fastapi import (
    Depends,
    Header,
    HTTPException,
    status,
)

from app.plugin_sdk.runtime_tokens import (
    RuntimeTokenClaims,
    RuntimeTokenError,
    decode_runtime_token,
)


async def get_plugin_runtime_claims(
    authorization: Annotated[
        str | None,
        Header(),
    ] = None,
) -> RuntimeTokenClaims:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Plugin runtime token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, separator, token = authorization.partition(" ")

    if (
        separator != " "
        or scheme.lower() != "bearer"
        or not token
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return decode_runtime_token(token)
    except RuntimeTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def require_runtime_capability(
    capability: str,
):
    async def dependency(
        claims: Annotated[
            RuntimeTokenClaims,
            Depends(get_plugin_runtime_claims),
        ],
    ) -> RuntimeTokenClaims:
        try:
            claims.require(capability)
        except RuntimeTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(exc),
            ) from exc

        return claims

    return dependency
