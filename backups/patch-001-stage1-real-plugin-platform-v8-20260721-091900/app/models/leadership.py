import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.core import Base


class LeadershipApplicationSettings(Base):
    __tablename__ = "application_settings"
    __table_args__ = (UniqueConstraint("guild_id", name="uq_leadership_application_settings_guild"), {"schema": "leadership"})

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("discord.guilds.guild_id", ondelete="CASCADE"), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    review_channel_id: Mapped[int | None] = mapped_column(BigInteger)
    r5_role_id: Mapped[int | None] = mapped_column(BigInteger)
    r4_role_id: Mapped[int | None] = mapped_column(BigInteger)
    require_evidence: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    language_role_mode: Mapped[str] = mapped_column(String(24), nullable=False, server_default="configured")
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class LeadershipLanguageRole(Base):
    __tablename__ = "language_roles"
    __table_args__ = (UniqueConstraint("guild_id", "language_code", "leadership_rank", name="uq_leadership_language_role"), {"schema": "leadership"})

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("discord.guilds.guild_id", ondelete="CASCADE"), nullable=False)
    language_code: Mapped[str] = mapped_column(String(16), nullable=False)
    leadership_rank: Mapped[str] = mapped_column(String(8), nullable=False)
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class LeadershipApplication(Base):
    __tablename__ = "applications"
    __table_args__ = {"schema": "leadership"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("discord.guilds.guild_id", ondelete="CASCADE"), nullable=False)
    discord_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    alliance_tag: Mapped[str] = mapped_column(String(32), nullable=False)
    game_nickname: Mapped[str] = mapped_column(String(64), nullable=False)
    requested_rank: Mapped[str] = mapped_column(String(8), nullable=False)
    language_code: Mapped[str] = mapped_column(String(16), nullable=False)
    evidence_url: Mapped[str | None] = mapped_column(String(1000))
    applicant_comment: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="pending")
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="SET NULL"))
    decision_reason: Mapped[str | None] = mapped_column(Text)
    decided_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="SET NULL"))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processing_error: Mapped[str | None] = mapped_column(Text)
    role_sync_status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="none")
    role_sync_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    role_sync_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class LeadershipApplicationDecision(Base):
    __tablename__ = "application_decisions"
    __table_args__ = {"schema": "leadership"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("leadership.applications.id", ondelete="CASCADE"), nullable=False)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("discord.guilds.guild_id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
