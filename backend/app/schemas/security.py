from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.security import SecuritySeverity


class SecuritySnapshotIn(BaseModel):
    guild_id: int
    collected_at: datetime
    roles: list[dict[str, Any]] = Field(default_factory=list)
    channels: list[dict[str, Any]] = Field(default_factory=list)
    webhooks: list[dict[str, Any]] = Field(default_factory=list)
    bot_permissions: dict[str, bool] = Field(default_factory=dict)


class SecurityFindingOut(BaseModel):
    id: UUID
    finding_key: str
    category: str
    severity: SecuritySeverity
    title: str
    description: str
    resource_type: str | None = None
    resource_id: str | None = None
    resource_name: str | None = None
    recommendation: str | None = None
    status: str
    details: dict[str, Any]
    created_at: datetime


class SecuritySummaryOut(BaseModel):
    guild_id: int
    snapshot_id: UUID | None = None
    collected_at: datetime | None = None
    role_count: int = 0
    channel_count: int = 0
    webhook_count: int = 0
    risk_score: int = 0
    counts: dict[str, int] = Field(default_factory=dict)
    findings: list[SecurityFindingOut] = Field(default_factory=list)
