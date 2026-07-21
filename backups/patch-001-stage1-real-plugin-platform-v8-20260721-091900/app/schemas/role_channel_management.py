from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator

class StructureChangeRequest(BaseModel):
    object_type: Literal["role", "channel", "category"]
    operation: Literal["create", "update", "delete"]
    target_id: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    preview_only: bool = True

    @model_validator(mode="after")
    def validate_target(self):
        if self.operation in {"update", "delete"} and not self.target_id:
            raise ValueError("target_id is required for update and delete")
        return self

class StructureChangeApplyRequest(BaseModel):
    confirmation: Literal["APPLY"]

class BulkRoleRequest(BaseModel):
    discord_role_id: int
    operation: Literal["add", "remove"]
    member_ids: list[int] = Field(min_length=1, max_length=500)

class StructureResultRequest(BaseModel):
    status: Literal["completed", "failed"]
    message: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)

class BulkRoleResultRequest(BaseModel):
    status: Literal["completed", "failed"]
    processed_count: int = 0
    failed_count: int = 0
    result: dict[str, Any] = Field(default_factory=dict)
