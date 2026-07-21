import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.core import Base


class DiscordMember(Base):
    __tablename__ = "members"
    __table_args__ = (
        UniqueConstraint("guild_id", "discord_user_id", name="uq_discord_members_guild_user"),
        Index("ix_discord_members_guild_active", "guild_id", "is_active"),
        {"schema": "discord"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("discord.guilds.guild_id", ondelete="CASCADE"), nullable=False)
    discord_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    global_name: Mapped[str | None] = mapped_column(String(255))
    nickname: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    bot: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    pending: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    communication_disabled_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    presence_status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="offline")
    activity_type: Mapped[str | None] = mapped_column(String(32))
    activity_name: Mapped[str | None] = mapped_column(String(255))
    voice_channel_id: Mapped[int | None] = mapped_column(BigInteger)
    voice_channel_name: Mapped[str | None] = mapped_column(String(255))
    client_desktop: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    client_mobile: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    client_web: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    last_presence_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    admin_note: Mapped[str | None] = mapped_column(Text)
    game_nickname: Mapped[str | None] = mapped_column(String(255))
    alliance_tag: Mapped[str | None] = mapped_column(String(32))
    leadership_rank: Mapped[str | None] = mapped_column(String(8))
    preferred_language: Mapped[str | None] = mapped_column(String(16))
    verification_status: Mapped[str] = mapped_column(String(24), nullable=False, server_default="not_verified")
    verification_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(64)), nullable=False, default=list, server_default="{}")
    shieldnet_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    watchlisted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False, server_default="low")
    review_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_reason: Mapped[str | None] = mapped_column(Text)
    profile_updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="SET NULL"))
    profile_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DiscordMemberRole(Base):
    __tablename__ = "member_roles"
    __table_args__ = (
        UniqueConstraint("member_id", "discord_role_id", name="uq_discord_member_roles_member_role"),
        {"schema": "discord"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("discord.members.id", ondelete="CASCADE"), nullable=False)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    discord_role_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    role_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_position: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    role_color: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
