from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator


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


class MarketplaceItemCreate(BaseModel):
    plugin_key: str = Field(min_length=2, max_length=96)
    name: str = Field(min_length=2, max_length=160)
    summary: str | None = Field(default=None, max_length=4000)
    category: str = Field(default="other", min_length=2, max_length=64)
    author: str | None = Field(default=None, max_length=160)
    homepage_url: str | None = Field(default=None, max_length=500)
    repository_url: str | None = Field(default=None, max_length=500)
    icon_url: str | None = Field(default=None, max_length=500)
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    @field_validator("plugin_key")
    @classmethod
    def normalize_plugin_key(cls, value: str) -> str:
        normalized = value.strip().lower().replace(" ", "-")
        allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-_")
        if not normalized or any(char not in allowed for char in normalized):
            raise ValueError("plugin_key may contain only a-z, 0-9, hyphen and underscore")
        return normalized

    @field_validator("name", "category")
    @classmethod
    def strip_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value cannot be empty")
        return value


class MarketplaceItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    summary: str | None = Field(default=None, max_length=4000)
    category: str | None = Field(default=None, min_length=2, max_length=64)
    author: str | None = Field(default=None, max_length=160)
    homepage_url: str | None = Field(default=None, max_length=500)
    repository_url: str | None = Field(default=None, max_length=500)
    icon_url: str | None = Field(default=None, max_length=500)
    metadata_json: dict[str, Any] | None = None


class MarketplaceVersionCreate(BaseModel):
    version: str = Field(min_length=1, max_length=40)
    min_core_version: str | None = Field(default=None, max_length=40)
    package_url: str = Field(min_length=5, max_length=500)
    checksum_sha256: str = Field(min_length=64, max_length=64)
    signature: str | None = None
    changelog: str | None = None
    manifest: dict[str, Any] = Field(default_factory=dict)

    @field_validator("checksum_sha256")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        value = value.strip().lower()
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("checksum_sha256 must be a 64-character hexadecimal SHA-256")
        return value


class MarketplaceStateRequest(BaseModel):
    enabled: bool
