from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class Event:
    name: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    guild_id: int | None = None
    actor_id: int | None = None
    source: str = "core"
    correlation_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        normalized_name = self.name.strip()
        normalized_source = self.source.strip()
        if not normalized_name:
            raise ValueError("Event name must not be empty")
        if not normalized_source:
            raise ValueError("Event source must not be empty")

        object.__setattr__(self, "name", normalized_name)
        object.__setattr__(self, "source", normalized_source)
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))
