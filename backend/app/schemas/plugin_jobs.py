from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PluginJobCreate(BaseModel):
    version: str | None = Field(default=None, max_length=40)
    payload_json: dict[str, Any] = Field(default_factory=dict)


class PluginJobResponse(BaseModel):
    id: UUID
    plugin_key: str
    requested_version: str | None = None
    action: str
    status: str
    progress: int
    error: str | None = None
    payload_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class PluginJobLogResponse(BaseModel):
    id: UUID
    job_id: UUID
    level: str
    message: str
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class PluginJobDetailResponse(PluginJobResponse):
    logs: list[PluginJobLogResponse] = Field(default_factory=list)


class PluginJobPageResponse(BaseModel):
    items: list[PluginJobResponse]
    total: int
    limit: int
    offset: int
