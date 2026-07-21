from datetime import UTC, datetime, timedelta
import uuid
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import User
from app.models.member_cases import MemberCase
from app.models.members import DiscordMember
from app.schemas.moderation_operations import ModerationCaseItem, ModerationCaseList, ModerationStats, ModeratorWorkload


class ModerationOperationsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_cases(self, guild_id: int, *, query: str | None, status_filter: str, priority: str, assignee: str, overdue_only: bool, page: int, page_size: int) -> ModerationCaseList:
        now = datetime.now(UTC)
        filters = [MemberCase.guild_id == guild_id]
        if status_filter != "all":
            filters.append(MemberCase.status == status_filter)
        if priority != "all":
            filters.append(MemberCase.priority == priority)
        if assignee == "unassigned":
            filters.append(MemberCase.assigned_to.is_(None))
        elif assignee not in {"all", ""}:
            try:
                filters.append(MemberCase.assigned_to == uuid.UUID(assignee))
            except ValueError:
                filters.append(MemberCase.assigned_to.is_(None))
        if overdue_only:
            filters.extend([MemberCase.due_at.is_not(None), MemberCase.due_at < now, MemberCase.status.in_(["open", "investigating"])])
        if query:
            q = f"%{query.strip()}%"
            filters.append(or_(MemberCase.title.ilike(q), DiscordMember.username.ilike(q), DiscordMember.global_name.ilike(q), DiscordMember.nickname.ilike(q)))

        base = (
            select(MemberCase, DiscordMember, User)
            .join(DiscordMember, DiscordMember.id == MemberCase.member_id)
            .outerjoin(User, User.id == MemberCase.assigned_to)
            .where(*filters)
        )
        total = int((await self.session.execute(select(func.count()).select_from(base.subquery()))).scalar_one())
        rows = (await self.session.execute(
            base.order_by(
                case((MemberCase.priority == "urgent", 0), (MemberCase.priority == "high", 1), (MemberCase.priority == "normal", 2), else_=3),
                MemberCase.due_at.asc().nulls_last(),
                MemberCase.updated_at.desc(),
            ).offset((page - 1) * page_size).limit(page_size)
        )).all()
        items = []
        for item, member, user in rows:
            name = member.nickname or member.global_name or member.username
            items.append(ModerationCaseItem(
                id=item.id, guild_id=item.guild_id, discord_user_id=member.discord_user_id,
                member_name=name, member_avatar_url=member.avatar_url, title=item.title,
                category=item.category, severity=item.severity, priority=item.priority,
                status=item.status, assigned_to=item.assigned_to,
                assignee_name=(user.display_name or user.login) if user else None,
                due_at=item.due_at, first_response_at=item.first_response_at,
                resolved_at=item.resolved_at, created_at=item.created_at, updated_at=item.updated_at,
                overdue=bool(item.due_at and item.due_at < now and item.status in {"open", "investigating"}),
            ))
        return ModerationCaseList(items=items, total=total, page=page, page_size=page_size)

    async def stats(self, guild_id: int) -> ModerationStats:
        now = datetime.now(UTC)
        tomorrow = now + timedelta(days=1)
        week_ago = now - timedelta(days=7)
        row = (await self.session.execute(select(
            func.count().filter(and_(MemberCase.guild_id == guild_id, MemberCase.status.in_(["open", "investigating"]))).label("total_open"),
            func.count().filter(and_(MemberCase.guild_id == guild_id, MemberCase.status == "investigating")).label("investigating"),
            func.count().filter(and_(MemberCase.guild_id == guild_id, MemberCase.due_at < now, MemberCase.status.in_(["open", "investigating"]))).label("overdue"),
            func.count().filter(and_(MemberCase.guild_id == guild_id, MemberCase.priority == "urgent", MemberCase.status.in_(["open", "investigating"]))).label("urgent"),
            func.count().filter(and_(MemberCase.guild_id == guild_id, MemberCase.assigned_to.is_(None), MemberCase.status.in_(["open", "investigating"]))).label("unassigned"),
            func.count().filter(and_(MemberCase.guild_id == guild_id, MemberCase.due_at >= now, MemberCase.due_at < tomorrow, MemberCase.status.in_(["open", "investigating"]))).label("due_today"),
            func.count().filter(and_(MemberCase.guild_id == guild_id, MemberCase.resolved_at >= week_ago)).label("resolved_7d"),
        ))).one()
        return ModerationStats(**row._mapping)

    async def workload(self, guild_id: int) -> list[ModeratorWorkload]:
        now = datetime.now(UTC)
        rows = (await self.session.execute(
            select(
                MemberCase.assigned_to,
                func.coalesce(User.display_name, User.login, "Unassigned").label("display_name"),
                func.count().filter(MemberCase.status.in_(["open", "investigating"])).label("open_cases"),
                func.count().filter(and_(MemberCase.due_at < now, MemberCase.status.in_(["open", "investigating"]))).label("overdue_cases"),
                func.count().filter(and_(MemberCase.priority == "urgent", MemberCase.status.in_(["open", "investigating"]))).label("urgent_cases"),
            )
            .outerjoin(User, User.id == MemberCase.assigned_to)
            .where(MemberCase.guild_id == guild_id)
            .group_by(MemberCase.assigned_to, User.display_name, User.login)
            .order_by(func.count().filter(MemberCase.status.in_(["open", "investigating"])).desc())
        )).all()
        return [ModeratorWorkload(**row._mapping) for row in rows]
