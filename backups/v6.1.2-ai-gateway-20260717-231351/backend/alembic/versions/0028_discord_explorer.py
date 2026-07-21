"""ShieldNet v4.1 Discord Explorer.

Revision ID: 0028_explorer
Revises: 0027_alerts
"""
from alembic import op
import sqlalchemy as sa

revision="0028_explorer"
down_revision="0027_alerts"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table("guild_channels",
      sa.Column("id",sa.Integer(),primary_key=True), sa.Column("guild_id",sa.BigInteger(),sa.ForeignKey("discord.guilds.guild_id",ondelete="CASCADE"),nullable=False),
      sa.Column("discord_channel_id",sa.BigInteger(),nullable=False), sa.Column("parent_id",sa.BigInteger()), sa.Column("name",sa.String(255),nullable=False),
      sa.Column("channel_type",sa.String(32),nullable=False), sa.Column("position",sa.Integer(),nullable=False,server_default="0"),
      sa.Column("nsfw",sa.Boolean(),nullable=False,server_default=sa.text("false")), sa.Column("topic",sa.Text()),
      sa.Column("permissions_synced",sa.Boolean(),nullable=False,server_default=sa.text("false")), sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
      sa.UniqueConstraint("guild_id","discord_channel_id",name="uq_explorer_channel"), schema="discord")
    op.create_index("ix_explorer_channels_guild_type","guild_channels",["guild_id","channel_type"],schema="discord")
    op.create_table("guild_webhooks",
      sa.Column("id",sa.Integer(),primary_key=True), sa.Column("guild_id",sa.BigInteger(),sa.ForeignKey("discord.guilds.guild_id",ondelete="CASCADE"),nullable=False),
      sa.Column("discord_webhook_id",sa.BigInteger(),nullable=False), sa.Column("channel_id",sa.BigInteger()), sa.Column("name",sa.String(255)),
      sa.Column("webhook_type",sa.String(32),nullable=False,server_default="incoming"), sa.Column("owner_id",sa.BigInteger()),
      sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
      sa.UniqueConstraint("guild_id","discord_webhook_id",name="uq_explorer_webhook"), schema="discord")
    op.create_table("guild_emojis",
      sa.Column("id",sa.Integer(),primary_key=True), sa.Column("guild_id",sa.BigInteger(),sa.ForeignKey("discord.guilds.guild_id",ondelete="CASCADE"),nullable=False),
      sa.Column("discord_emoji_id",sa.BigInteger(),nullable=False), sa.Column("name",sa.String(255),nullable=False), sa.Column("animated",sa.Boolean(),nullable=False,server_default=sa.text("false")),
      sa.Column("managed",sa.Boolean(),nullable=False,server_default=sa.text("false")), sa.Column("available",sa.Boolean(),nullable=False,server_default=sa.text("true")),
      sa.UniqueConstraint("guild_id","discord_emoji_id",name="uq_explorer_emoji"), schema="discord")
    op.create_table("guild_invites",
      sa.Column("id",sa.Integer(),primary_key=True), sa.Column("guild_id",sa.BigInteger(),sa.ForeignKey("discord.guilds.guild_id",ondelete="CASCADE"),nullable=False),
      sa.Column("code",sa.String(64),nullable=False), sa.Column("channel_id",sa.BigInteger()), sa.Column("inviter_id",sa.BigInteger()), sa.Column("uses",sa.Integer(),nullable=False,server_default="0"),
      sa.Column("max_uses",sa.Integer(),nullable=False,server_default="0"), sa.Column("temporary",sa.Boolean(),nullable=False,server_default=sa.text("false")), sa.Column("expires_at",sa.DateTime(timezone=True)),
      sa.UniqueConstraint("guild_id","code",name="uq_explorer_invite"), schema="discord")

def downgrade():
    op.drop_table("guild_invites",schema="discord"); op.drop_table("guild_emojis",schema="discord"); op.drop_table("guild_webhooks",schema="discord")
    op.drop_index("ix_explorer_channels_guild_type",table_name="guild_channels",schema="discord"); op.drop_table("guild_channels",schema="discord")
