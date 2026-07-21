import re
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.settings import SettingsRepository

_NAME_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")


class InvalidSettingName(ValueError):
    pass


class SettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = SettingsRepository(session)

    @staticmethod
    def validate_name(value: str, *, max_length: int) -> str:
        value = value.strip().lower()
        if len(value) > max_length or not _NAME_RE.fullmatch(value):
            raise InvalidSettingName(value)
        return value

    @staticmethod
    def detect_type(value: Any) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        if isinstance(value, str):
            return "string"
        if isinstance(value, list):
            return "list"
        if isinstance(value, dict):
            return "object"
        return "json"

    async def list_module(self, guild_id: int, module: str) -> dict[str, Any]:
        module = self.validate_name(module, max_length=64)
        items = await self.repository.list_module(guild_id, module)
        return {item.key: item.value for item in items}

    async def get(self, guild_id: int, module: str, key: str, default: Any = None) -> Any:
        module = self.validate_name(module, max_length=64)
        key = self.validate_name(key, max_length=128)
        item = await self.repository.get(guild_id, module, key)
        return default if item is None else item.value

    async def set(
        self,
        *,
        guild_id: int,
        module: str,
        key: str,
        value: Any,
        updated_by: uuid.UUID | None = None,
    ) -> Any:
        module = self.validate_name(module, max_length=64)
        key = self.validate_name(key, max_length=128)
        item = await self.repository.upsert(
            guild_id=guild_id,
            module=module,
            key=key,
            value=value,
            value_type=self.detect_type(value),
            updated_by=updated_by,
        )
        await self.session.commit()
        return item.value

    async def delete(self, guild_id: int, module: str, key: str) -> bool:
        module = self.validate_name(module, max_length=64)
        key = self.validate_name(key, max_length=128)
        removed = await self.repository.remove(guild_id, module, key)
        await self.session.commit()
        return removed
