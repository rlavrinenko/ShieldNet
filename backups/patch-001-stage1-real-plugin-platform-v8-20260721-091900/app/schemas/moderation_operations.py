import uuid
from datetime import datetime
from pydantic import BaseModel


class ModerationCaseItem(BaseModel):
    id: uuid.UUID
    guild_id: int
    discord_user_id: int
    member_name: str
    member_avatar_url: str | None
    title: str
    category: str
    severity: str
    priority: str
    status: str
    assigned_to: uuid.UUID | None
    assignee_name: str | None
    due_at: datetime | None
    first_response_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime
    overdue: bool


class ModerationCaseList(BaseModel):
    items: list[ModerationCaseItem]
    total: int
    page: int
    page_size: int


class ModerationStats(BaseModel):
    total_open: int
    investigating: int
    overdue: int
    urgent: int
    unassigned: int
    due_today: int
    resolved_7d: int


class ModeratorWorkload(BaseModel):
    user_id: uuid.UUID | None
    display_name: str
    open_cases: int
    overdue_cases: int
    urgent_cases: int
