from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PluginManifestResponse(BaseModel):
    plugin_key: str
    name: str
    version: str
    description: str | None = None
    author: str | None = None
    min_core_version: str | None = None
    manifest_path: str
    signature_status: str
    enabled: bool
    healthy: bool
    last_error: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    components: dict[str, bool] = Field(default_factory=dict)
    manifest: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime


class PluginScanResponse(BaseModel):
    discovered: int
    updated: int
    missing: int
    errors: list[str] = Field(default_factory=list)


class PluginStateRequest(BaseModel):
    enabled: bool


class PluginEventResponse(BaseModel):
    plugin_key: str
    event_type: str
    status: str
    message: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
