import uuid
from pydantic import BaseModel, Field
from app.models.permissions import PermissionEffect, PermissionName


class PermissionRuleUpsert(BaseModel):
    effect: PermissionEffect = PermissionEffect.ALLOW
    subject_type: str = Field(pattern="^(everyone|shieldnet_role|discord_role|discord_user)$")
    subject_value: str = Field(min_length=1, max_length=128)
    enabled: bool = True
    priority: int = Field(default=100, ge=0, le=10000)


class PermissionRuleResponse(BaseModel):
    id: uuid.UUID
    guild_id: int
    module_key: str
    permission: PermissionName
    effect: PermissionEffect
    subject_type: str
    subject_value: str
    enabled: bool
    priority: int


class PermissionCheckRequest(BaseModel):
    guild_id: int
    module_key: str
    permission: PermissionName
    discord_user_id: int
    discord_role_ids: list[int] = Field(default_factory=list)


class PermissionCheckResponse(BaseModel):
    allowed: bool
    matched_rule_id: uuid.UUID | None = None
    reason: str
