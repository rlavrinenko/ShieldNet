import uuid
from typing import Any
from pydantic import BaseModel, Field
from app.models.member_actions import MemberActionStatus, MemberActionType


class MemberActionCreate(BaseModel):
    action_type: MemberActionType
    payload: dict[str, Any] = Field(default_factory=dict)


class MemberActionResponse(BaseModel):
    id: uuid.UUID
    guild_id: int
    discord_user_id: int
    action_type: MemberActionType
    payload: dict[str, Any]
    status: MemberActionStatus
    result_message: str | None
    attempt_count: int


class MemberActionResult(BaseModel):
    status: MemberActionStatus
    result_message: str | None = None
