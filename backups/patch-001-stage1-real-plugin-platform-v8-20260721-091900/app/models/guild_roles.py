from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.core import Base

class DiscordGuildRole(Base):
    __tablename__ = "guild_roles"
    __table_args__ = (
        UniqueConstraint("guild_id", "discord_role_id", name="uq_discord_guild_roles_guild_role"),
        {"schema": "discord"},
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("discord.guilds.guild_id", ondelete="CASCADE"))
    discord_role_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(String(255))
    position: Mapped[int] = mapped_column(Integer, server_default="0")
    color: Mapped[int] = mapped_column(Integer, server_default="0")
    permissions: Mapped[int] = mapped_column(BigInteger, server_default="0")
    managed: Mapped[bool] = mapped_column(Boolean, server_default="false")
    assignable: Mapped[bool] = mapped_column(Boolean, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
