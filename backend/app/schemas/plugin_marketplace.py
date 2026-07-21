from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MarketplaceVersionResponse(BaseModel):
    id: str
    version: str
    min_core_version: str | None = None
    package_url: str
    checksum_sha256: str
    changelog: str | None = None
    manifest: dict[str, Any] = Field(default_factory=dict)
    released_at: datetime


class MarketplaceItemResponse(BaseModel):
    id: str
    plugin_key: str
    name: str
    summary: str | None = None
    category: str
    author: str | None = None
    homepage_url: str | None = None
    repository_url: str | None = None
    icon_url: str | None = None
    verified: bool
    published: bool
    downloads: int
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    latest_version: MarketplaceVersionResponse | None = None
    created_at: datetime
    updated_at: datetime


class MarketplacePageResponse(BaseModel):
    items: list[MarketplaceItemResponse]
    total: int
    limit: int
    offset: int
