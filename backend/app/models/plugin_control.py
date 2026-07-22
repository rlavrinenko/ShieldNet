import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.core import Base


class PluginPermission(Base):
    __tablename__ = "permissions"
    __table_args__ = (UniqueConstraint("permission_key", name="uq_plugins_permissions_key"), {"schema": "plugins"})
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    permission_key: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False, default="low", server_default="low")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PluginPermissionGrant(Base):
    __tablename__ = "plugin_permissions"
    __table_args__ = (UniqueConstraint("plugin_key", "permission_key", name="uq_plugins_plugin_permission"), {"schema": "plugins"})
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plugin_key: Mapped[str] = mapped_column(String(96), nullable=False)
    permission_key: Mapped[str] = mapped_column(String(120), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    granted_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class PluginPermissionAudit(Base):
    __tablename__ = "permission_audit"
    __table_args__ = ({"schema": "plugins"},)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plugin_key: Mapped[str] = mapped_column(String(96), nullable=False)
    permission_key: Mapped[str] = mapped_column(String(120), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PluginSecret(Base):
    __tablename__ = "secrets"
    __table_args__ = (UniqueConstraint("plugin_key", "scope", "scope_key", "secret_name", name="uq_plugins_secret_scope"), {"schema": "plugins"})
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plugin_key: Mapped[str] = mapped_column(String(96), nullable=False)
    scope: Mapped[str] = mapped_column(String(24), nullable=False, default="plugin", server_default="plugin")
    scope_key: Mapped[str] = mapped_column(String(160), nullable=False, default="", server_default="")
    secret_name: Mapped[str] = mapped_column(String(120), nullable=False)
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    key_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class PluginSecretAudit(Base):
    __tablename__ = "secret_audit"
    __table_args__ = ({"schema": "plugins"},)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plugin_key: Mapped[str] = mapped_column(String(96), nullable=False)
    secret_name: Mapped[str] = mapped_column(String(120), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PluginActivationState(Base):
    __tablename__ = "activation_state"
    __table_args__ = (UniqueConstraint("plugin_key", name="uq_plugins_activation_state_key"), {"schema": "plugins"})
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plugin_key: Mapped[str] = mapped_column(String(96), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False, default="stopped", server_default="stopped")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    maintenance: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    restart_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    pid: Mapped[int | None] = mapped_column(Integer)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class PluginActivationHistory(Base):
    __tablename__ = "activation_history"
    __table_args__ = ({"schema": "plugins"},)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plugin_key: Mapped[str] = mapped_column(String(96), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    previous_state: Mapped[str | None] = mapped_column(String(24))
    new_state: Mapped[str] = mapped_column(String(24), nullable=False)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PluginPackageHistory(Base):
    __tablename__ = "package_history"
    __table_args__ = ({"schema": "plugins"},)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plugin_key: Mapped[str] = mapped_column(String(96), nullable=False)
    version: Mapped[str] = mapped_column(String(40), nullable=False)
    previous_version: Mapped[str | None] = mapped_column(String(40))
    action: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="success", server_default="success")
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
