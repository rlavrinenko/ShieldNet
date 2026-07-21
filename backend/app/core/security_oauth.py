import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import HTTPException
from jwt import InvalidTokenError

from app.core.config import settings


def create_oauth_state() -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "type": "discord_oauth_state",
            "nonce": secrets.token_urlsafe(32),
            "iat": now,
            "exp": now + timedelta(minutes=10),
        },
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_oauth_state(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError as exc:
        raise HTTPException(status_code=400, detail="Invalid OAuth state") from exc

    if payload.get("type") != "discord_oauth_state":
        raise HTTPException(status_code=400, detail="Invalid OAuth state type")
    return payload
