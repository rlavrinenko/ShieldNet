from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

class RuntimeHeartbeatIn(BaseModel):
    worker_name: str = Field(min_length=1, max_length=128)
    worker_type: str = Field(min_length=1, max_length=32)
    status: str = Field(default="online", max_length=24)
    metadata: dict[str, Any] = Field(default_factory=dict)

class RuntimeHeartbeatOut(BaseModel):
    worker_name: str
    worker_type: str
    status: str
    metadata: dict[str, Any]
    started_at: datetime
    last_seen_at: datetime
