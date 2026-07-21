from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True, frozen=True)
class PluginContext:
    plugin_key: str
    plugin_root: Path
    manifest: dict[str, Any]
