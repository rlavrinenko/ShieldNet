import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ViolationTypeCreate(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=160)
    description: str | None = None
    severity: str = "medium"
    recommended_action: str | None = None


class ViolationTypeResponse(ORMModel):
    id: uuid.UUID
    guild_id: int
    code: str
    name: str
    description: str | None
    severity: str
    recommended_action: str | None
    active: bool
    created_at: datetime


class ReportCreate(BaseModel):
    reported_discord_user_id: int
    reporter_discord_user_id: int | None = None
    violation_type_id: uuid.UUID | None = None
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=3)
    priority: str = "normal"
    message_url: str | None = None
    channel_id: int | None = None
    evidence_urls: list[str] = Field(default_factory=list, max_length=20)


class ReportDecision(BaseModel):
    reason: str | None = None


class ReportResponse(ORMModel):
    id: uuid.UUID
    guild_id: int
    reporter_discord_user_id: int | None
    reported_discord_user_id: int
    violation_type_id: uuid.UUID | None
    title: str
    description: str
    priority: str
    status: str
    assigned_to: uuid.UUID | None
    rejection_reason: str | None
    created_at: datetime
    updated_at: datetime


class CaseCreate(BaseModel):
    reported_discord_user_id: int
    report_id: uuid.UUID | None = None
    violation_type_id: uuid.UUID | None = None
    title: str = Field(min_length=3, max_length=255)
    description: str | None = None
    severity: str = "medium"
    priority: str = "normal"


class CaseUpdate(BaseModel):
    status: str | None = None
    severity: str | None = None
    priority: str | None = None
    assigned_to: uuid.UUID | None = None
    resolution: str | None = None


class CaseResponse(ORMModel):
    id: uuid.UUID
    guild_id: int
    report_id: uuid.UUID | None
    reported_discord_user_id: int
    violation_type_id: uuid.UUID | None
    title: str
    description: str | None
    severity: str
    priority: str
    status: str
    assigned_to: uuid.UUID | None
    resolution: str | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime


class NoteCreate(BaseModel):
    body: str = Field(min_length=1)
    visibility: str = "private"


class NoteResponse(ORMModel):
    id: uuid.UUID
    case_id: uuid.UUID
    visibility: str
    body: str
    author_user_id: uuid.UUID | None
    created_at: datetime


class ActionCreate(BaseModel):
    action_type: str
    reason: str | None = None
    duration_seconds: int | None = Field(default=None, ge=1, le=2_592_000)
    payload: dict = Field(default_factory=dict)


class ActionResponse(ORMModel):
    id: uuid.UUID
    case_id: uuid.UUID
    guild_id: int
    discord_user_id: int
    action_type: str
    reason: str | None
    duration_seconds: int | None
    status: str
    member_action_id: uuid.UUID | None
    result_message: str | None
    created_at: datetime
    completed_at: datetime | None


class AppealCreate(BaseModel):
    appellant_discord_user_id: int
    body: str = Field(min_length=3)


class AppealDecision(BaseModel):
    status: str
    reason: str | None = None


class AppealResponse(ORMModel):
    id: uuid.UUID
    case_id: uuid.UUID
    appellant_discord_user_id: int
    body: str
    status: str
    decision_reason: str | None
    decided_by: uuid.UUID | None
    decided_at: datetime | None
    created_at: datetime


class TemplateCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    action_type: str
    reason_template: str | None = None
    duration_seconds: int | None = None


class TemplateResponse(ORMModel):
    id: uuid.UUID
    guild_id: int
    name: str
    action_type: str
    reason_template: str | None
    duration_seconds: int | None
    active: bool
    created_at: datetime


class ModerationStats(BaseModel):
    reports_pending: int
    cases_open: int
    cases_resolved: int
    actions_pending: int
    appeals_pending: int
