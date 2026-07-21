import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class MemberRolePayload(BaseModel):
    discord_role_id: int
    role_name: str
    role_position: int = 0
    role_color: int = 0


class MemberSyncPayload(BaseModel):
    discord_user_id: int
    username: str
    global_name: str | None = None
    nickname: str | None = None
    avatar_url: str | None = None
    bot: bool = False
    pending: bool = False
    joined_at: datetime | None = None
    communication_disabled_until: datetime | None = None
    presence_status: Literal["online", "idle", "dnd", "offline", "invisible"] = "offline"
    activity_type: str | None = None
    activity_name: str | None = None
    voice_channel_id: str | None = None
    voice_channel_name: str | None = None
    client_desktop: bool = False
    client_mobile: bool = False
    client_web: bool = False
    last_presence_at: datetime | None = None
    roles: list[MemberRolePayload] = Field(default_factory=list)


class MemberBatchSyncRequest(BaseModel):
    members: list[MemberSyncPayload]
    complete_snapshot: bool = False


class MemberActivityRequest(BaseModel):
    discord_user_id: int
    activity_at: datetime | None = None


class MemberLeftRequest(BaseModel):
    discord_user_id: int
    left_at: datetime | None = None


class MemberRoleResponse(BaseModel):
    # Discord snowflakes must be returned as strings so browsers do not lose precision.
    discord_role_id: str
    role_name: str
    role_position: int
    role_color: int


class MemberResponse(BaseModel):
    # Discord snowflakes exceed JavaScript Number.MAX_SAFE_INTEGER.
    discord_user_id: str
    username: str
    global_name: str | None
    nickname: str | None
    avatar_url: str | None
    bot: bool
    pending: bool
    is_active: bool
    joined_at: datetime | None
    left_at: datetime | None
    last_activity_at: datetime | None
    communication_disabled_until: datetime | None
    presence_status: str = "offline"
    activity_type: str | None = None
    activity_name: str | None = None
    voice_channel_id: int | None = None
    voice_channel_name: str | None = None
    client_desktop: bool = False
    client_mobile: bool = False
    client_web: bool = False
    last_presence_at: datetime | None = None
    admin_note: str | None = None
    game_nickname: str | None = None
    alliance_tag: str | None = None
    leadership_rank: Literal["R5", "R4", "member"] | None = None
    preferred_language: str | None = None
    verification_status: Literal["not_verified", "pending", "verified", "rejected", "expired"] = "not_verified"
    verification_updated_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    shieldnet_blocked: bool = False
    watchlisted: bool = False
    risk_level: Literal["low", "medium", "high", "critical"] = "low"
    review_due_at: datetime | None = None
    review_reason: str | None = None
    roles: list[MemberRoleResponse]


class MemberDetailResponse(MemberResponse):
    created_at: datetime
    updated_at: datetime
    profile_updated_at: datetime | None = None


class MemberListResponse(BaseModel):
    items: list[MemberResponse]
    total: int
    page: int
    page_size: int


class MemberStatsResponse(BaseModel):
    total: int
    humans: int
    bots: int
    pending: int
    timed_out: int
    blocked: int
    active_24h: int
    inactive_30d: int
    watchlisted: int
    high_risk: int
    review_due: int


class MemberProfileUpdate(BaseModel):
    game_nickname: str | None = Field(default=None, max_length=255)
    alliance_tag: str | None = Field(default=None, max_length=32)
    leadership_rank: Literal["R5", "R4", "member"] | None = None
    preferred_language: str | None = Field(default=None, max_length=16)
    verification_status: Literal["not_verified", "pending", "verified", "rejected", "expired"] = "not_verified"
    admin_note: str | None = Field(default=None, max_length=4000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    watchlisted: bool = False
    risk_level: Literal["low", "medium", "high", "critical"] = "low"
    review_due_at: datetime | None = None
    review_reason: str | None = Field(default=None, max_length=4000)

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, value: list[str]) -> list[str]:
        result: list[str] = []
        for item in value:
            tag = item.strip().lower()[:64]
            if tag and tag not in result:
                result.append(tag)
        return result


class MemberBulkActionRequest(BaseModel):
    discord_user_ids: list[int] = Field(min_length=1, max_length=100)
    action_type: Literal["send_dm", "add_role", "remove_role", "shieldnet_block", "shieldnet_unblock"]
    payload: dict = Field(default_factory=dict)
