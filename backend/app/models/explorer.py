from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.core import Base

class GuildChannel(Base):
 __tablename__="guild_channels"; __table_args__=(UniqueConstraint("guild_id","discord_channel_id",name="uq_explorer_channel"),{"schema":"discord"})
 id:Mapped[int]=mapped_column(Integer,primary_key=True); guild_id:Mapped[int]=mapped_column(BigInteger,ForeignKey("discord.guilds.guild_id",ondelete="CASCADE")); discord_channel_id:Mapped[int]=mapped_column(BigInteger); parent_id:Mapped[int|None]=mapped_column(BigInteger); name:Mapped[str]=mapped_column(String(255)); channel_type:Mapped[str]=mapped_column(String(32)); position:Mapped[int]=mapped_column(Integer,server_default="0"); nsfw:Mapped[bool]=mapped_column(Boolean,server_default="false"); topic:Mapped[str|None]=mapped_column(Text); permissions_synced:Mapped[bool]=mapped_column(Boolean,server_default="false"); updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
class GuildWebhook(Base):
 __tablename__="guild_webhooks"; __table_args__=(UniqueConstraint("guild_id","discord_webhook_id",name="uq_explorer_webhook"),{"schema":"discord"})
 id:Mapped[int]=mapped_column(Integer,primary_key=True); guild_id:Mapped[int]=mapped_column(BigInteger,ForeignKey("discord.guilds.guild_id",ondelete="CASCADE")); discord_webhook_id:Mapped[int]=mapped_column(BigInteger); channel_id:Mapped[int|None]=mapped_column(BigInteger); name:Mapped[str|None]=mapped_column(String(255)); webhook_type:Mapped[str]=mapped_column(String(32),server_default="incoming"); owner_id:Mapped[int|None]=mapped_column(BigInteger); updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
class GuildEmoji(Base):
 __tablename__="guild_emojis"; __table_args__=(UniqueConstraint("guild_id","discord_emoji_id",name="uq_explorer_emoji"),{"schema":"discord"})
 id:Mapped[int]=mapped_column(Integer,primary_key=True); guild_id:Mapped[int]=mapped_column(BigInteger,ForeignKey("discord.guilds.guild_id",ondelete="CASCADE")); discord_emoji_id:Mapped[int]=mapped_column(BigInteger); name:Mapped[str]=mapped_column(String(255)); animated:Mapped[bool]=mapped_column(Boolean,server_default="false"); managed:Mapped[bool]=mapped_column(Boolean,server_default="false"); available:Mapped[bool]=mapped_column(Boolean,server_default="true")
class GuildInvite(Base):
 __tablename__="guild_invites"; __table_args__=(UniqueConstraint("guild_id","code",name="uq_explorer_invite"),{"schema":"discord"})
 id:Mapped[int]=mapped_column(Integer,primary_key=True); guild_id:Mapped[int]=mapped_column(BigInteger,ForeignKey("discord.guilds.guild_id",ondelete="CASCADE")); code:Mapped[str]=mapped_column(String(64)); channel_id:Mapped[int|None]=mapped_column(BigInteger); inviter_id:Mapped[int|None]=mapped_column(BigInteger); uses:Mapped[int]=mapped_column(Integer,server_default="0"); max_uses:Mapped[int]=mapped_column(Integer,server_default="0"); temporary:Mapped[bool]=mapped_column(Boolean,server_default="false"); expires_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))

class ChannelPermissionOverwrite(Base):
    __tablename__ = "channel_permission_overwrites"
    __table_args__ = (
        UniqueConstraint("guild_id", "discord_channel_id", "target_id", "target_type", name="uq_channel_permission_overwrite"),
        {"schema": "discord"},
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("discord.guilds.guild_id", ondelete="CASCADE"), nullable=False)
    discord_channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    target_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    target_type: Mapped[str] = mapped_column(String(16), nullable=False)
    allow_permissions: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    deny_permissions: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
