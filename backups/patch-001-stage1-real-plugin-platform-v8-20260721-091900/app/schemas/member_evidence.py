import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

EvidenceType = Literal["link", "screenshot", "message", "document", "other"]
AppealStatus = Literal["submitted", "under_review", "accepted", "rejected", "withdrawn"]


class CaseEvidenceCreate(BaseModel):
    evidence_type: EvidenceType = "link"
    title: str = Field(min_length=2, max_length=255)
    source_url: HttpUrl | None = None
    notes: str | None = Field(default=None, max_length=10000)


class CaseEvidenceResponse(BaseModel):
    id: uuid.UUID
    guild_id: int
    case_id: uuid.UUID
    evidence_type: EvidenceType
    title: str
    source_url: str | None
    notes: str | None
    created_by: uuid.UUID | None
    created_at: datetime


class CaseAppealCreate(BaseModel):
    statement: str = Field(min_length=5, max_length=20000)
    submitted_by_name: str | None = Field(default=None, max_length=255)


class CaseAppealUpdate(BaseModel):
    status: AppealStatus | None = None
    decision: str | None = Field(default=None, max_length=20000)


class CaseAppealResponse(BaseModel):
    id: uuid.UUID
    guild_id: int
    case_id: uuid.UUID
    status: AppealStatus
    statement: str
    decision: str | None
    submitted_by_name: str | None
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
