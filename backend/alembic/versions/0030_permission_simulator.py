"""ShieldNet v4.3 Permission Simulator.

Revision ID: 0030_permsim
Revises: 0029_inspector
"""
from alembic import op
import sqlalchemy as sa

revision = "0030_permsim"
down_revision = "0029_inspector"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "channel_permission_overwrites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), sa.ForeignKey("discord.guilds.guild_id", ondelete="CASCADE"), nullable=False),
        sa.Column("discord_channel_id", sa.BigInteger(), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=False),
        sa.Column("target_type", sa.String(16), nullable=False),
        sa.Column("allow_permissions", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("deny_permissions", sa.BigInteger(), nullable=False, server_default="0"),
        sa.UniqueConstraint("guild_id", "discord_channel_id", "target_id", "target_type", name="uq_channel_permission_overwrite"),
        schema="discord",
    )
    op.create_index("ix_channel_overwrites_guild_channel", "channel_permission_overwrites", ["guild_id", "discord_channel_id"], schema="discord")
    op.create_index("ix_channel_overwrites_target", "channel_permission_overwrites", ["guild_id", "target_type", "target_id"], schema="discord")


def downgrade():
    op.drop_index("ix_channel_overwrites_target", table_name="channel_permission_overwrites", schema="discord")
    op.drop_index("ix_channel_overwrites_guild_channel", table_name="channel_permission_overwrites", schema="discord")
    op.drop_table("channel_permission_overwrites", schema="discord")
