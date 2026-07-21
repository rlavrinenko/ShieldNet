import uuid
from pydantic import BaseModel, Field

class LeadershipSettingsInput(BaseModel):
    enabled: bool = False
    review_channel_id: int | None = None
    r5_role_id: int | None = None
    r4_role_id: int | None = None
    require_evidence: bool = True
    language_role_mode: str = Field(default="configured", pattern="^(configured|disabled)$")

class LeadershipLanguageRoleInput(BaseModel):
    language_code: str = Field(min_length=2, max_length=16)
    leadership_rank: str = Field(pattern="^(R5|R4)$")
    role_id: int

class LeadershipApplicationCreate(BaseModel):
    discord_user_id: int
    alliance_tag: str = Field(min_length=1, max_length=32)
    game_nickname: str = Field(min_length=1, max_length=64)
    requested_rank: str = Field(pattern="^(R5|R4)$")
    language_code: str = Field(min_length=2, max_length=16)
    evidence_url: str | None = Field(default=None, max_length=1000)
    applicant_comment: str | None = Field(default=None, max_length=2000)

class LeadershipDecisionInput(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)

class LeadershipAssignInput(BaseModel):
    assigned_to: uuid.UUID | None = None

class LeadershipSyncResult(BaseModel):
    status: str = Field(pattern="^(completed|failed)$")
    message: str | None = Field(default=None, max_length=2000)
