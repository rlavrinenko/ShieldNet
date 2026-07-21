import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class VerificationSettingsInput(BaseModel):
    enabled: bool = False
    verified_role_id: int | None = None
    review_channel_id: int | None = None
    nickname_template: str = Field(
        default="[{alliance}] {nickname}",
        min_length=3,
        max_length=128,
    )
    auto_approve: bool = False
    alliance_min_length: int = Field(
        default=2,
        ge=1,
        le=16,
    )
    alliance_max_length: int = Field(
        default=8,
        ge=1,
        le=32,
    )


class VerificationRequestCreate(BaseModel):
    discord_user_id: int
    alliance: str = Field(
        min_length=1,
        max_length=32,
    )
    nickname: str = Field(
        min_length=1,
        max_length=64,
    )


class VerificationDecisionInput(BaseModel):
    reason: str | None = Field(
        default=None,
        max_length=1000,
    )


class VerificationRequestResult(BaseModel):
    status: str = Field(
        pattern="^(completed|failed)$",
    )
    result_message: str | None = Field(
        default=None,
        max_length=2000,
    )


class VerificationRequestResponse(BaseModel):
    id: uuid.UUID
    guild_id: int
    discord_user_id: int
    alliance: str
    nickname: str
    requested_nickname: str
    status: str
    result_message: str | None
    decision_reason: str | None
    decided_at: datetime | None
    processed_at: datetime | None
    created_at: datetime



class VerificationBulkInput(BaseModel):
    request_ids: list[uuid.UUID] = Field(
        min_length=1,
        max_length=200,
    )


class VerificationRecoverInput(BaseModel):
    older_than_minutes: int = Field(
        default=10,
        ge=1,
        le=1440,
    )


class VerificationChangesInput(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)


class VerificationResubmitInput(BaseModel):
    alliance: str = Field(min_length=1, max_length=32)
    nickname: str = Field(min_length=1, max_length=64)
    evidence_url: str | None = Field(default=None, max_length=1000)
    submitted_language: str | None = Field(default=None, max_length=16)
    applicant_comment: str | None = Field(default=None, max_length=2000)
