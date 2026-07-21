from typing import Any

from pydantic import BaseModel, Field


class ModuleResponse(BaseModel):
    module_key: str
    name: str
    description: str | None
    icon: str | None
    version: str
    is_core: bool
    enabled: bool
    configuration: dict[str, Any]
    revision: int


class ModuleUpdateRequest(BaseModel):
    enabled: bool
    configuration: dict[str, Any] | None = None


class ModuleUpdateResponse(ModuleResponse):
    guild_id: int
    sync_required: bool = True


class BotModuleStateResponse(BaseModel):
    guild_id: int
    modules: list[ModuleResponse]
    configuration_revision: int = Field(ge=0)
