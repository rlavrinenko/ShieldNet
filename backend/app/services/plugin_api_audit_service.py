from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import text

from app.db.session import AsyncSessionFactory


logger = logging.getLogger(
    "shieldnet.plugin_api.audit"
)


@dataclass(frozen=True, slots=True)
class PluginApiAuditEvent:
    request_id: str
    method: str
    path: str
    status_code: int
    duration_ms: int

    plugin_key: str | None = None
    guild_id: int | None = None
    generation: int | None = None
    token_id: str | None = None
    capability: str | None = None

    authenticated: bool = False
    allowed: bool = False

    client_ip: str | None = None
    user_agent: str | None = None
    error_detail: str | None = None


class PluginApiAuditService:
    @staticmethod
    async def write(
        event: PluginApiAuditEvent,
    ) -> None:
        logger.info(
            "Plugin API audit write start "
            "request_id=%s method=%s path=%s status=%s",
            event.request_id,
            event.method,
            event.path,
            event.status_code,
        )
        """
        Audit recording must never break the Plugin API.
        """

        try:
            async with AsyncSessionFactory() as session:
                await session.execute(
                    text("""
                        INSERT INTO plugins.api_audit_logs (
                            request_id,
                            plugin_key,
                            guild_id,
                            generation,
                            token_id,
                            capability,
                            method,
                            path,
                            status_code,
                            duration_ms,
                            authenticated,
                            allowed,
                            client_ip,
                            user_agent,
                            error_detail
                        )
                        VALUES (
                            :request_id,
                            :plugin_key,
                            :guild_id,
                            :generation,
                            :token_id,
                            :capability,
                            :method,
                            :path,
                            :status_code,
                            :duration_ms,
                            :authenticated,
                            :allowed,
                            :client_ip,
                            :user_agent,
                            :error_detail
                        )
                    """),
                    {
                        "request_id": event.request_id[:64],
                        "plugin_key": (
                            event.plugin_key[:128]
                            if event.plugin_key
                            else None
                        ),
                        "guild_id": event.guild_id,
                        "generation": event.generation,
                        "token_id": (
                            event.token_id[:64]
                            if event.token_id
                            else None
                        ),
                        "capability": (
                            event.capability[:128]
                            if event.capability
                            else None
                        ),
                        "method": event.method[:16],
                        "path": event.path[:512],
                        "status_code": event.status_code,
                        "duration_ms": max(
                            0,
                            event.duration_ms,
                        ),
                        "authenticated": (
                            event.authenticated
                        ),
                        "allowed": event.allowed,
                        "client_ip": (
                            event.client_ip[:64]
                            if event.client_ip
                            else None
                        ),
                        "user_agent": (
                            event.user_agent[:512]
                            if event.user_agent
                            else None
                        ),
                        "error_detail": (
                            event.error_detail[:1000]
                            if event.error_detail
                            else None
                        ),
                    },
                )

                await session.commit()

                logger.info(
                    "Plugin API audit write completed "
                    "request_id=%s",
                    event.request_id,
                )

        except Exception:
            logger.exception(
                "Unable to write Plugin API audit event "
                "request_id=%s method=%s path=%s status=%s",
                event.request_id,
                event.method,
                event.path,
                event.status_code,
            )
