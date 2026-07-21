from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SettingWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: Any = Field(...)


class SettingValue(BaseModel):
    guild_id: int
    module: str
    key: str
    value: Any


class ModuleSettings(BaseModel):
    guild_id: int
    module: str
    values: dict[str, Any]
