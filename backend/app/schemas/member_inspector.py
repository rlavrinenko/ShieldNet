from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.members import MemberDetailResponse


class MemberInspectorSummary(BaseModel):
    open_cases: int = 0
    resolved_cases: int = 0
    appeals: int = 0
    evidence: int = 0
    actions: int = 0
    verification_requests: int = 0


class MemberTimelineItem(BaseModel):
    id: str
    kind: str
    title: str
    detail: str | None = None
    status: str | None = None
    severity: str | None = None
    occurred_at: datetime
    metadata: dict = Field(default_factory=dict)


class MemberInspectorResponse(BaseModel):
    member: MemberDetailResponse
    summary: MemberInspectorSummary
    permissions: list[str] = Field(default_factory=list)
    verification: list[dict] = Field(default_factory=list)
    timeline: list[MemberTimelineItem] = Field(default_factory=list)
