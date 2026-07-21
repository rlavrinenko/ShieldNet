from datetime import UTC, datetime
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member_actions import MemberAction, MemberActionStatus, MemberActionType
from app.models.members import DiscordMember
from app.schemas.member_actions import MemberActionCreate, MemberActionResponse


class MemberActionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def serialize(action: MemberAction) -> MemberActionResponse:
        return MemberActionResponse(
            id=action.id,
            guild_id=action.guild_id,
            discord_user_id=action.discord_user_id,
            action_type=action.action_type,
            payload=action.payload,
            status=action.status,
            result_message=action.result_message,
            attempt_count=action.attempt_count,
        )

    async def create(self, guild_id: int, discord_user_id: int, requested_by: uuid.UUID, data: MemberActionCreate) -> MemberActionResponse:
        action = MemberAction(
            guild_id=guild_id,
            discord_user_id=discord_user_id,
            action_type=data.action_type,
            payload=data.payload,
            requested_by=requested_by,
        )
        self.session.add(action)
        if data.action_type in (MemberActionType.SHIELDNET_BLOCK, MemberActionType.SHIELDNET_UNBLOCK):
            await self.session.execute(
                update(DiscordMember)
                .where(DiscordMember.guild_id == guild_id, DiscordMember.discord_user_id == discord_user_id)
                .values(shieldnet_blocked=data.action_type == MemberActionType.SHIELDNET_BLOCK)
            )
        await self.session.commit()
        await self.session.refresh(action)
        return self.serialize(action)

    async def pending(self, guild_id: int) -> list[MemberActionResponse]:
        result = await self.session.execute(
            select(MemberAction)
            .where(MemberAction.guild_id == guild_id, MemberAction.status == MemberActionStatus.PENDING)
            .order_by(MemberAction.created_at)
            .limit(50)
            .with_for_update(skip_locked=True)
        )
        actions = result.scalars().all()
        for action in actions:
            action.status = MemberActionStatus.PROCESSING
            action.started_at = datetime.now(UTC)
            action.attempt_count += 1
        await self.session.commit()
        return [self.serialize(action) for action in actions]

    async def complete(self, action_id: uuid.UUID, status: MemberActionStatus, message: str | None) -> None:
        await self.session.execute(
            update(MemberAction)
            .where(MemberAction.id == action_id)
            .values(status=status, result_message=message, completed_at=datetime.now(UTC))
        )
        await self.session.commit()
