from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field

class PluginRuntimeInstanceResponse(BaseModel):
    id: UUID
    guild_id: int
    plugin_key: str
    state: str
    generation: int
    package_version: str | None = None
    package_path: str | None = None
    manifest_json: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    stopped_at: datetime | None = None
    last_heartbeat_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime
