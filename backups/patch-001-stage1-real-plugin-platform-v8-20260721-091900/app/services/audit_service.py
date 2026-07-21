from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent
from app.schemas.audit import AuditEventResponse, AuditListResponse


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        *,
        event_type: str,
        guild_id: int | None = None,
        actor_user_id: Any | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        payload: dict[str, Any] | None = None,
        result: str = "created",
        message: str | None = None,
    ) -> AuditEvent:
        """Add an audit event to the current transaction.

        The caller owns commit/rollback. This keeps the business operation and
        its audit row atomic and prevents partial writes.
        """
        event = AuditEvent(
            guild_id=guild_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            target_type=target_type,
            target_id=target_id,
            payload=payload or {},
            result=result,
            message=message,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def list_for_guild(
        self,
        guild_id: int,
        page: int,
        page_size: int,
    ) -> AuditListResponse:
        total = int(
            (
                await self.session.execute(
                    select(func.count(AuditEvent.id)).where(
                        AuditEvent.guild_id == guild_id
                    )
                )
            ).scalar_one()
        )

        result = await self.session.execute(
            select(AuditEvent)
            .where(AuditEvent.guild_id == guild_id)
            .order_by(AuditEvent.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        return AuditListResponse(
            items=[
                AuditEventResponse(
                    id=str(item.id),
                    guild_id=item.guild_id,
                    event_type=item.event_type,
                    target_type=item.target_type,
                    target_id=item.target_id,
                    payload=item.payload,
                    result=item.result,
                    message=item.message,
                    created_at=item.created_at,
                )
                for item in result.scalars().all()
            ],
            total=total,
        )
