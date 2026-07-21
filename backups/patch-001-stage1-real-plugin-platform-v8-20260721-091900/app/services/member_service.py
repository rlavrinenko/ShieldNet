from __future__ import annotations
from datetime import UTC, datetime, timedelta
import uuid

from fastapi import HTTPException, status
from sqlalchemy import String, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member_actions import MemberAction, MemberActionStatus
from app.models.members import DiscordMember, DiscordMemberRole
from app.schemas.members import (
    MemberBatchSyncRequest,
    MemberDetailResponse,
    MemberListResponse,
    MemberProfileUpdate,
    MemberResponse,
    MemberRoleResponse,
    MemberStatsResponse,
)


class MemberService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def batch_sync(self, guild_id: int, payload: MemberBatchSyncRequest) -> int:
        seen: set[int] = set()
        now = datetime.now(UTC)

        for item in payload.members:
            seen.add(item.discord_user_id)
            result = await self.session.execute(
                select(DiscordMember).where(
                    DiscordMember.guild_id == guild_id,
                    DiscordMember.discord_user_id == item.discord_user_id,
                )
            )
            member = result.scalar_one_or_none()
            if member is None:
                member = DiscordMember(guild_id=guild_id, discord_user_id=item.discord_user_id, username=item.username)
                self.session.add(member)
                await self.session.flush()

            member.username = item.username
            member.global_name = item.global_name
            member.nickname = item.nickname
            member.avatar_url = item.avatar_url
            member.bot = item.bot
            member.pending = item.pending
            member.is_active = True
            member.joined_at = item.joined_at
            member.left_at = None
            member.communication_disabled_until = item.communication_disabled_until
            member.presence_status = item.presence_status
            member.activity_type = item.activity_type
            member.activity_name = item.activity_name
            member.voice_channel_id = item.voice_channel_id
            member.voice_channel_name = item.voice_channel_name
            member.client_desktop = item.client_desktop
            member.client_mobile = item.client_mobile
            member.client_web = item.client_web
            member.last_presence_at = item.last_presence_at
            member.updated_at = now

            await self.session.execute(delete(DiscordMemberRole).where(DiscordMemberRole.member_id == member.id))
            for role in item.roles:
                self.session.add(DiscordMemberRole(
                    member_id=member.id, guild_id=guild_id,
                    discord_role_id=role.discord_role_id, role_name=role.role_name,
                    role_position=role.role_position, role_color=role.role_color,
                ))

        if payload.complete_snapshot:
            query = update(DiscordMember).where(DiscordMember.guild_id == guild_id, DiscordMember.is_active.is_(True))
            if seen:
                query = query.where(DiscordMember.discord_user_id.not_in(seen))
            await self.session.execute(query.values(is_active=False, left_at=now, updated_at=now))

        await self.session.commit()
        return len(payload.members)

    async def activity(self, guild_id: int, discord_user_id: int, at) -> None:
        await self.session.execute(
            update(DiscordMember)
            .where(DiscordMember.guild_id == guild_id, DiscordMember.discord_user_id == discord_user_id)
            .values(last_activity_at=at or datetime.now(UTC), updated_at=datetime.now(UTC))
        )
        await self.session.commit()

    async def left(self, guild_id: int, discord_user_id: int, at) -> None:
        await self.session.execute(
            update(DiscordMember)
            .where(DiscordMember.guild_id == guild_id, DiscordMember.discord_user_id == discord_user_id)
            .values(is_active=False, left_at=at or datetime.now(UTC), updated_at=datetime.now(UTC))
        )
        await self.session.commit()

    def _filters(self, guild_id: int, query: str | None, member_type: str, status_filter: str, role_id: int | None, tag: str | None):
        now = datetime.now(UTC)
        filters = [DiscordMember.guild_id == guild_id]
        if status_filter != "left":
            filters.append(DiscordMember.is_active.is_(True))
        else:
            filters.append(DiscordMember.is_active.is_(False))
        if query:
            pattern = f"%{query.strip()}%"
            filters.append(or_(
                DiscordMember.username.ilike(pattern), DiscordMember.global_name.ilike(pattern),
                DiscordMember.nickname.ilike(pattern), func.cast(DiscordMember.discord_user_id, String).ilike(pattern),
                DiscordMember.admin_note.ilike(pattern), DiscordMember.game_nickname.ilike(pattern),
                DiscordMember.alliance_tag.ilike(pattern), DiscordMember.preferred_language.ilike(pattern),
            ))
        if member_type == "human": filters.append(DiscordMember.bot.is_(False))
        if member_type == "bot": filters.append(DiscordMember.bot.is_(True))
        if status_filter == "pending": filters.append(DiscordMember.pending.is_(True))
        if status_filter == "timed_out": filters.append(DiscordMember.communication_disabled_until > now)
        if status_filter == "blocked": filters.append(DiscordMember.shieldnet_blocked.is_(True))
        if status_filter == "inactive": filters.append(or_(DiscordMember.last_activity_at.is_(None), DiscordMember.last_activity_at < now - timedelta(days=30)))
        if status_filter == "watchlist": filters.append(DiscordMember.watchlisted.is_(True))
        if status_filter == "review_due": filters.append(DiscordMember.review_due_at.is_not(None)); filters.append(DiscordMember.review_due_at <= now)
        if role_id is not None:
            filters.append(DiscordMember.id.in_(select(DiscordMemberRole.member_id).where(DiscordMemberRole.discord_role_id == role_id)))
        if tag:
            filters.append(DiscordMember.tags.any(tag.strip().lower()))
        return filters

    async def _serialize(self, member: DiscordMember, detail: bool = False):
        roles = (await self.session.execute(
            select(DiscordMemberRole).where(DiscordMemberRole.member_id == member.id).order_by(DiscordMemberRole.role_position.desc())
        )).scalars().all()
        data = dict(
            discord_user_id=str(member.discord_user_id), username=member.username, global_name=member.global_name,
            nickname=member.nickname, avatar_url=member.avatar_url, bot=member.bot, pending=member.pending,
            is_active=member.is_active, joined_at=member.joined_at, left_at=member.left_at,
            last_activity_at=member.last_activity_at, communication_disabled_until=member.communication_disabled_until,
            presence_status=member.presence_status, activity_type=member.activity_type, activity_name=member.activity_name,
            voice_channel_id=str(member.voice_channel_id) if member.voice_channel_id is not None else None, voice_channel_name=member.voice_channel_name,
            client_desktop=member.client_desktop, client_mobile=member.client_mobile, client_web=member.client_web,
            last_presence_at=member.last_presence_at,
            admin_note=member.admin_note, game_nickname=member.game_nickname, alliance_tag=member.alliance_tag,
            leadership_rank=member.leadership_rank, preferred_language=member.preferred_language,
            verification_status=member.verification_status, verification_updated_at=member.verification_updated_at,
            tags=member.tags or [], shieldnet_blocked=member.shieldnet_blocked,
            watchlisted=member.watchlisted, risk_level=member.risk_level, review_due_at=member.review_due_at, review_reason=member.review_reason,
            roles=[MemberRoleResponse(discord_role_id=str(r.discord_role_id), role_name=r.role_name, role_position=r.role_position, role_color=r.role_color) for r in roles],
        )
        if detail:
            return MemberDetailResponse(**data, created_at=member.created_at, updated_at=member.updated_at, profile_updated_at=member.profile_updated_at)
        return MemberResponse(**data)

    async def list(self, guild_id: int, query: str | None, page: int, page_size: int, member_type: str = "all", status_filter: str = "active", role_id: int | None = None, tag: str | None = None, sort: str = "activity") -> MemberListResponse:
        filters = self._filters(guild_id, query, member_type, status_filter, role_id, tag)
        total = int((await self.session.execute(select(func.count(DiscordMember.id)).where(*filters))).scalar_one())
        order = {
            "name": (DiscordMember.username.asc(),),
            "joined": (DiscordMember.joined_at.desc().nullslast(),),
            "oldest": (DiscordMember.joined_at.asc().nullsfirst(),),
        }.get(sort, (DiscordMember.last_activity_at.desc().nullslast(), DiscordMember.username.asc()))
        result = await self.session.execute(select(DiscordMember).where(*filters).order_by(*order).offset((page - 1) * page_size).limit(page_size))
        return MemberListResponse(items=[await self._serialize(m) for m in result.scalars().all()], total=total, page=page, page_size=page_size)

    async def get(self, guild_id: int, discord_user_id: int) -> MemberDetailResponse:
        member = (await self.session.execute(select(DiscordMember).where(DiscordMember.guild_id == guild_id, DiscordMember.discord_user_id == discord_user_id))).scalar_one_or_none()
        if member is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        return await self._serialize(member, detail=True)

    async def update_profile(self, guild_id: int, discord_user_id: int, user_id: uuid.UUID, payload: MemberProfileUpdate) -> MemberDetailResponse:
        member = (await self.session.execute(select(DiscordMember).where(DiscordMember.guild_id == guild_id, DiscordMember.discord_user_id == discord_user_id))).scalar_one_or_none()
        if member is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        member.game_nickname = payload.game_nickname.strip() if payload.game_nickname else None
        member.alliance_tag = payload.alliance_tag.strip().upper() if payload.alliance_tag else None
        member.leadership_rank = payload.leadership_rank
        member.preferred_language = payload.preferred_language.strip().lower() if payload.preferred_language else None
        if member.verification_status != payload.verification_status:
            member.verification_status = payload.verification_status
            member.verification_updated_at = datetime.now(UTC)
        member.admin_note = payload.admin_note.strip() if payload.admin_note else None
        member.tags = payload.tags
        member.watchlisted = payload.watchlisted
        member.risk_level = payload.risk_level
        member.review_due_at = payload.review_due_at
        member.review_reason = payload.review_reason.strip() if payload.review_reason else None
        member.profile_updated_by = user_id
        member.profile_updated_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(member)
        return await self._serialize(member, detail=True)

    async def stats(self, guild_id: int) -> MemberStatsResponse:
        now = datetime.now(UTC)
        base = [DiscordMember.guild_id == guild_id, DiscordMember.is_active.is_(True)]
        async def count(*extra):
            return int((await self.session.execute(select(func.count(DiscordMember.id)).where(*base, *extra))).scalar_one())
        return MemberStatsResponse(
            total=await count(), humans=await count(DiscordMember.bot.is_(False)), bots=await count(DiscordMember.bot.is_(True)),
            pending=await count(DiscordMember.pending.is_(True)), timed_out=await count(DiscordMember.communication_disabled_until > now),
            blocked=await count(DiscordMember.shieldnet_blocked.is_(True)), active_24h=await count(DiscordMember.last_activity_at >= now - timedelta(days=1)),
            inactive_30d=await count(or_(DiscordMember.last_activity_at.is_(None), DiscordMember.last_activity_at < now - timedelta(days=30))),
            watchlisted=await count(DiscordMember.watchlisted.is_(True)),
            high_risk=await count(DiscordMember.risk_level.in_(["high", "critical"])),
            review_due=await count(DiscordMember.review_due_at.is_not(None), DiscordMember.review_due_at <= now),
        )

    async def action_history(self, guild_id: int, discord_user_id: int, limit: int = 50) -> list[MemberAction]:
        return (await self.session.execute(
            select(MemberAction).where(MemberAction.guild_id == guild_id, MemberAction.discord_user_id == discord_user_id)
            .order_by(MemberAction.created_at.desc()).limit(limit)
        )).scalars().all()
