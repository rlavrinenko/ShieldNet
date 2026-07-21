import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.core import Base


class PermissionName(str, enum.Enum):
    VIEW = "view"
    MANAGE = "manage"
    EXECUTE = "execute"
    CONFIGURE = "configure"


class PermissionEffect(str, enum.Enum):
    ALLOW = "allow"
    DENY = "deny"


class GuildPermissionRule(Base):
    __tablename__ = "permission_rules"
    __table_args__ = (
        UniqueConstraint(
            "guild_id", "module_key", "permission", "subject_type", "subject_value",
            name="uq_permissions_rule",
        ),
        Index("ix_permissions_lookup", "guild_id", "module_key", "permission"),
        {"schema": "permissions"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("discord.guilds.guild_id", ondelete="CASCADE"), nullable=False)
    module_key: Mapped[str] = mapped_column(String(64), nullable=False)
    permission: Mapped[PermissionName] = mapped_column(
        Enum(PermissionName, name="permission_name", schema="permissions", values_callable=lambda c: [i.value for i in c]),
        nullable=False,
    )
    effect: Mapped[PermissionEffect] = mapped_column(
        Enum(PermissionEffect, name="permission_effect", schema="permissions", values_callable=lambda c: [i.value for i in c]),
        nullable=False,
        default=PermissionEffect.ALLOW,
        server_default="allow",
    )
    subject_type: Mapped[str] = mapped_column(String(32), nullable=False)
    subject_value: Mapped[str] = mapped_column(String(128), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
