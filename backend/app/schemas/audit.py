from datetime import datetime
from typing import Any
from pydantic import BaseModel


class AuditEventResponse(BaseModel):
    id: str
    guild_id: int | None
    event_type: str
    target_type: str | None
    target_id: str | None
    payload: dict[str, Any]
    result: str
    message: str | None
    created_at: datetime


class AuditListResponse(BaseModel):
    items: list[AuditEventResponse]
    total: int
