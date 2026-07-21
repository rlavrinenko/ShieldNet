from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastapi.responses import ORJSONResponse


# JavaScript Number can represent integers exactly only within this range.
MAX_SAFE_JAVASCRIPT_INTEGER = 9_007_199_254_740_991


def stringify_unsafe_integers(value: Any) -> Any:
    """Recursively convert integers unsafe for JavaScript into JSON strings.

    Discord Snowflake identifiers are stored as BIGINT values in PostgreSQL.
    Returning them as JSON numbers causes browsers to round them. Converting
    only unsafe integers keeps ordinary counters and status values numeric.
    """
    if value is None or isinstance(value, (str, bytes, bytearray, bool, float)):
        return value

    if isinstance(value, int):
        if abs(value) > MAX_SAFE_JAVASCRIPT_INTEGER:
            return str(value)
        return value

    if isinstance(value, Mapping):
        return {
            key: stringify_unsafe_integers(item)
            for key, item in value.items()
        }

    if isinstance(value, tuple):
        return tuple(stringify_unsafe_integers(item) for item in value)

    if isinstance(value, list):
        return [stringify_unsafe_integers(item) for item in value]

    if isinstance(value, set):
        return [stringify_unsafe_integers(item) for item in value]

    return value


class SnowflakeORJSONResponse(ORJSONResponse):
    """ORJSON response that preserves Discord Snowflake precision."""

    def render(self, content: Any) -> bytes:
        return super().render(stringify_unsafe_integers(content))
