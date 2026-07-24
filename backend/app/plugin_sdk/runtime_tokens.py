from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
from jwt import InvalidTokenError

from app.plugin_sdk.capabilities import ALL_CAPABILITIES


class RuntimeTokenError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RuntimeTokenClaims:
    plugin_key: str
    guild_id: int
    generation: int
    permissions: frozenset[str]
    token_id: str
    issued_at: datetime
    expires_at: datetime

    def has(self, capability: str) -> bool:
        return capability in self.permissions

    def require(self, capability: str) -> None:
        if capability not in ALL_CAPABILITIES:
            raise RuntimeTokenError(
                f"Unknown ShieldNet capability: {capability}"
            )

        if capability not in self.permissions:
            raise RuntimeTokenError(
                f"Runtime token has no capability: {capability}"
            )


def _secret() -> str:
    value = os.getenv("PLUGIN_RUNTIME_TOKEN_SECRET", "")

    if len(value) < 48:
        raise RuntimeError(
            "PLUGIN_RUNTIME_TOKEN_SECRET is missing or too short"
        )

    return value


def _algorithm() -> str:
    algorithm = os.getenv(
        "PLUGIN_RUNTIME_TOKEN_ALGORITHM",
        "HS256",
    )

    if algorithm not in {"HS256", "HS384", "HS512"}:
        raise RuntimeError(
            "Unsupported runtime token algorithm"
        )

    return algorithm


def _lifetime_minutes() -> int:
    value = int(
        os.getenv("PLUGIN_RUNTIME_TOKEN_MINUTES", "10")
    )

    if value < 1 or value > 60:
        raise RuntimeError(
            "PLUGIN_RUNTIME_TOKEN_MINUTES must be between 1 and 60"
        )

    return value


def create_runtime_token(
    *,
    plugin_key: str,
    guild_id: int,
    generation: int,
    permissions: frozenset[str] | set[str] | list[str],
) -> str:
    normalized_permissions = frozenset(permissions)
    unknown = sorted(normalized_permissions - ALL_CAPABILITIES)

    if unknown:
        raise RuntimeTokenError(
            "Unknown capabilities: " + ", ".join(unknown)
        )

    now = datetime.now(UTC)
    expires_at = now + timedelta(
        minutes=_lifetime_minutes()
    )

    payload: dict[str, Any] = {
        "sub": f"plugin:{plugin_key}:{guild_id}",
        "type": "plugin_runtime",
        "plugin_key": plugin_key,
        "guild_id": guild_id,
        "generation": generation,
        "permissions": sorted(normalized_permissions),
        "jti": str(uuid4()),
        "iat": now,
        "nbf": now,
        "exp": expires_at,
        "iss": "shieldnet-plugin-runtime",
        "aud": "shieldnet-backend",
    }

    return jwt.encode(
        payload,
        _secret(),
        algorithm=_algorithm(),
    )


def decode_runtime_token(
    token: str,
) -> RuntimeTokenClaims:
    try:
        payload = jwt.decode(
            token,
            _secret(),
            algorithms=[_algorithm()],
            audience="shieldnet-backend",
            issuer="shieldnet-plugin-runtime",
        )
    except InvalidTokenError as exc:
        raise RuntimeTokenError(
            "Invalid or expired plugin runtime token"
        ) from exc

    if payload.get("type") != "plugin_runtime":
        raise RuntimeTokenError(
            "Invalid runtime token type"
        )

    plugin_key = payload.get("plugin_key")
    guild_id = payload.get("guild_id")
    generation = payload.get("generation")
    permissions = payload.get("permissions")
    token_id = payload.get("jti")

    if not isinstance(plugin_key, str) or not plugin_key:
        raise RuntimeTokenError(
            "Runtime token has invalid plugin_key"
        )

    if not isinstance(guild_id, int):
        raise RuntimeTokenError(
            "Runtime token has invalid guild_id"
        )

    if not isinstance(generation, int):
        raise RuntimeTokenError(
            "Runtime token has invalid generation"
        )

    if not isinstance(permissions, list) or any(
        not isinstance(item, str)
        for item in permissions
    ):
        raise RuntimeTokenError(
            "Runtime token has invalid permissions"
        )

    normalized_permissions = frozenset(permissions)
    unknown = sorted(normalized_permissions - ALL_CAPABILITIES)

    if unknown:
        raise RuntimeTokenError(
            "Runtime token contains unknown capabilities"
        )

    if not isinstance(token_id, str) or not token_id:
        raise RuntimeTokenError(
            "Runtime token has invalid jti"
        )

    issued_at_raw = payload.get("iat")
    expires_at_raw = payload.get("exp")

    return RuntimeTokenClaims(
        plugin_key=plugin_key,
        guild_id=guild_id,
        generation=generation,
        permissions=normalized_permissions,
        token_id=token_id,
        issued_at=datetime.fromtimestamp(
            int(issued_at_raw),
            tz=UTC,
        ),
        expires_at=datetime.fromtimestamp(
            int(expires_at_raw),
            tz=UTC,
        ),
    )
