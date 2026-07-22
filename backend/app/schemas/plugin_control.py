from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

class PermissionItem(BaseModel):
    permission_key: str
    description: str | None = None
    risk_level: str = "low"
    granted: bool = False

class PermissionUpdate(BaseModel):
    permissions: dict[str, bool]

class PermissionAuditItem(BaseModel):
    plugin_key: str
    permission_key: str
    action: str
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

class SecretCreate(BaseModel):
    secret_name: str
    value: str
    scope: str = "plugin"
    scope_key: str = ""

class SecretMetadata(BaseModel):
    secret_name: str
    scope: str
    scope_key: str
    key_version: int
    created_at: datetime
    updated_at: datetime

class ActivationResponse(BaseModel):
    plugin_key: str
    state: str
    enabled: bool
    maintenance: bool
    restart_count: int
    pid: int | None = None
    last_heartbeat_at: datetime | None = None
    last_error: str | None = None
    updated_at: datetime

class MaintenanceRequest(BaseModel):
    enabled: bool

class VersionHistoryItem(BaseModel):
    plugin_key: str
    version: str
    previous_version: str | None = None
    action: str
    status: str
    checksum_sha256: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
