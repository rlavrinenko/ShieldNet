from typing import Literal
from pydantic import BaseModel, Field

class SetupCreateRequest(BaseModel):
    template_key: Literal["minimal", "standard", "full"] = "standard"
    preferred_language: str = Field(default="en", min_length=2, max_length=16)
    enable_verification: bool = True
    enable_leadership: bool = True
    enable_moderation: bool = True
    create_welcome_channel: bool = True
    create_language_channel: bool = True

class SetupApplyRequest(BaseModel):
    confirmation: Literal["APPLY"]

class SetupImportRequest(BaseModel):
    configuration: dict
