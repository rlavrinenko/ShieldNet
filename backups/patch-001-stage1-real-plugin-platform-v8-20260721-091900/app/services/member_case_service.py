from datetime import UTC, datetime
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member_cases import MemberCase
from app.models.members import DiscordMember
from app.schemas.member_cases import MemberCaseCreate, MemberCaseResponse, MemberCaseUpdate


class MemberCaseService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _member(self, guild_id: int, discord_user_id: int) -> DiscordMember:
        member = (await self.session.execute(
            select(DiscordMember).where(
                DiscordMember.guild_id == guild_id,
                DiscordMember.discord_user_id == discord_user_id,
            )
        )).scalar_one_or_none()
        if member is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        return member

    @staticmethod
    def serialize(item: MemberCase, discord_user_id: int) -> MemberCaseResponse:
        return MemberCaseResponse(
            id=item.id,
            guild_id=item.guild_id,
            discord_user_id=discord_user_id,
            title=item.title,
            category=item.category,
            severity=item.severity,
            status=item.status,
            priority=item.priority,
            description=item.description,
            resolution=item.resolution,
            assigned_to=item.assigned_to,
            created_by=item.created_by,
            due_at=item.due_at,
            first_response_at=item.first_response_at,
            resolved_at=item.resolved_at,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    async def list(self, guild_id: int, discord_user_id: int) -> list[MemberCaseResponse]:
        member = await self._member(guild_id, discord_user_id)
        items = (await self.session.execute(
            select(MemberCase)
            .where(MemberCase.guild_id == guild_id, MemberCase.member_id == member.id)
            .order_by(MemberCase.created_at.desc())
        )).scalars().all()
        return [self.serialize(item, discord_user_id) for item in items]

    async def create(self, guild_id: int, discord_user_id: int, user_id: uuid.UUID, payload: MemberCaseCreate) -> MemberCaseResponse:
        member = await self._member(guild_id, discord_user_id)
        item = MemberCase(
            guild_id=guild_id,
            member_id=member.id,
            title=payload.title.strip(),
            category=payload.category,
            severity=payload.severity,
            priority=payload.priority,
            description=payload.description.strip() if payload.description else None,
            assigned_to=payload.assigned_to,
            due_at=payload.due_at,
            created_by=user_id,
        )
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return self.serialize(item, discord_user_id)

    async def update(self, guild_id: int, discord_user_id: int, case_id: uuid.UUID, payload: MemberCaseUpdate) -> MemberCaseResponse:
        member = await self._member(guild_id, discord_user_id)
        item = (await self.session.execute(
            select(MemberCase).where(
                MemberCase.id == case_id,
                MemberCase.guild_id == guild_id,
                MemberCase.member_id == member.id,
            )
        )).scalar_one_or_none()
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

        changes = payload.model_dump(exclude_unset=True)
        for key, value in changes.items():
            if key in {"title", "description", "resolution"} and isinstance(value, str):
                value = value.strip() or None
            setattr(item, key, value)

        if payload.status == "investigating" and item.first_response_at is None:
            item.first_response_at = datetime.now(UTC)

        if payload.status in {"resolved", "dismissed"} and item.resolved_at is None:
            item.resolved_at = datetime.now(UTC)
        elif payload.status in {"open", "investigating"}:
            item.resolved_at = None

        await self.session.commit()
        await self.session.refresh(item)
        return self.serialize(item, discord_user_id)
