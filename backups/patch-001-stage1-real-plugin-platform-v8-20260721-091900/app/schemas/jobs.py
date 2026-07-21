from datetime import datetime
from typing import Any

from pydantic import BaseModel


class JobDefinitionResponse(BaseModel):
    key: str
    name: str
    description: str
    category: str
    safe_manual_run: bool
    last_status: str | None = None
    last_run_at: datetime | None = None
    last_duration_ms: int | None = None


class JobRunResponse(BaseModel):
    id: str
    job_key: str
    status: str
    trigger: str
    started_at: datetime | None
    finished_at: datetime | None
    duration_ms: int | None
    result: dict[str, Any]
    error_message: str | None
    created_at: datetime


class JobsOverviewResponse(BaseModel):
    generated_at: datetime
    totals: dict[str, int]
    jobs: list[JobDefinitionResponse]
    recent_runs: list[JobRunResponse]
    health: dict[str, Any]
