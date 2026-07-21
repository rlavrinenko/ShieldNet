import uuid
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.core import Base

class SetupSession(Base):
    __tablename__ = "setup_sessions"
    __table_args__ = (
        Index("ix_discord_setup_sessions_guild_status", "guild_id", "status"),
        {"schema": "discord"},
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("discord.guilds.guild_id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, server_default="draft")
    template_key: Mapped[str] = mapped_column(String(32), nullable=False, server_default="standard")
    preferred_language: Mapped[str] = mapped_column(String(16), nullable=False, server_default="en")
    features: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    diagnostics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    configuration: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class SetupItem(Base):
    __tablename__ = "setup_items"
    __table_args__ = (
        UniqueConstraint("session_id", "item_key", name="uq_discord_setup_item_key"),
        Index("ix_discord_setup_items_session", "session_id", "position"),
        {"schema": "discord"},
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("discord.setup_sessions.id", ondelete="CASCADE"), nullable=False)
    item_key: Mapped[str] = mapped_column(String(64), nullable=False)
    object_type: Mapped[str] = mapped_column(String(24), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    position: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    change_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("discord.structure_changes.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(24), nullable=False, server_default="planned")
    discord_object_id: Mapped[int | None] = mapped_column(BigInteger)
    error_message: Mapped[str | None] = mapped_column(Text)
