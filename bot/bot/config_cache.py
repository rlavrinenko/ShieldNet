import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class GuildModuleState:
    guild_id: int
    configuration_revision: int = 0
    modules: dict[str, dict[str, Any]] = field(default_factory=dict)
    loaded_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def enabled(self, key: str) -> bool:
        item = self.modules.get(key)
        return bool(item and item.get("enabled"))


class GuildConfigCache:
    def __init__(self) -> None:
        self._states: dict[int, GuildModuleState] = {}
        self._locks: dict[int, asyncio.Lock] = {}

    def get(self, guild_id: int) -> GuildModuleState | None:
        return self._states.get(guild_id)

    def set(self, state: GuildModuleState) -> None:
        self._states[state.guild_id] = state

    def clear(self, guild_id: int | None = None) -> None:
        if guild_id is None:
            self._states.clear()
        else:
            self._states.pop(guild_id, None)

    def lock(self, guild_id: int) -> asyncio.Lock:
        self._locks.setdefault(guild_id, asyncio.Lock())
        return self._locks[guild_id]
