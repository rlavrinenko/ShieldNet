import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

CaseCategory = Literal["warning", "spam", "harassment", "security", "appeal", "other"]
CaseSeverity = Literal["low", "medium", "high", "critical"]
CaseStatus = Literal["open", "investigating", "resolved", "dismissed"]
CasePriority = Literal["low", "normal", "high", "urgent"]


class MemberCaseCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    category: CaseCategory = "other"
    severity: CaseSeverity = "medium"
    priority: CasePriority = "normal"
    description: str | None = Field(default=None, max_length=10000)
    assigned_to: uuid.UUID | None = None
    due_at: datetime | None = None


class MemberCaseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    category: CaseCategory | None = None
    severity: CaseSeverity | None = None
    priority: CasePriority | None = None
    status: CaseStatus | None = None
    description: str | None = Field(default=None, max_length=10000)
    resolution: str | None = Field(default=None, max_length=10000)
    assigned_to: uuid.UUID | None = None
    due_at: datetime | None = None


class MemberCaseResponse(BaseModel):
    id: uuid.UUID
    guild_id: int
    discord_user_id: int
    title: str
    category: CaseCategory
    severity: CaseSeverity
    status: CaseStatus
    priority: CasePriority
    description: str | None
    resolution: str | None
    assigned_to: uuid.UUID | None
    created_by: uuid.UUID | None
    due_at: datetime | None
    first_response_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime
