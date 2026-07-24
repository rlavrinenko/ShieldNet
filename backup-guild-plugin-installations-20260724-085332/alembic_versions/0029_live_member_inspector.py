"""ShieldNet v4.2 Live Member Inspector.

Revision ID: 0029_inspector
Revises: 0028_explorer
"""
from alembic import op
import sqlalchemy as sa

revision = "0029_inspector"
down_revision = "0028_explorer"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("members", sa.Column("presence_status", sa.String(16), nullable=False, server_default="offline"), schema="discord")
    op.add_column("members", sa.Column("activity_type", sa.String(32)), schema="discord")
    op.add_column("members", sa.Column("activity_name", sa.String(255)), schema="discord")
    op.add_column("members", sa.Column("voice_channel_id", sa.BigInteger()), schema="discord")
    op.add_column("members", sa.Column("voice_channel_name", sa.String(255)), schema="discord")
    op.add_column("members", sa.Column("client_desktop", sa.Boolean(), nullable=False, server_default=sa.text("false")), schema="discord")
    op.add_column("members", sa.Column("client_mobile", sa.Boolean(), nullable=False, server_default=sa.text("false")), schema="discord")
    op.add_column("members", sa.Column("client_web", sa.Boolean(), nullable=False, server_default=sa.text("false")), schema="discord")
    op.add_column("members", sa.Column("last_presence_at", sa.DateTime(timezone=True)), schema="discord")
    op.create_index("ix_discord_members_guild_presence", "members", ["guild_id", "presence_status"], schema="discord")
    op.create_index("ix_discord_members_guild_voice", "members", ["guild_id", "voice_channel_id"], schema="discord")


def downgrade():
    op.drop_index("ix_discord_members_guild_voice", table_name="members", schema="discord")
    op.drop_index("ix_discord_members_guild_presence", table_name="members", schema="discord")
    for name in ["last_presence_at", "client_web", "client_mobile", "client_desktop", "voice_channel_name", "voice_channel_id", "activity_name", "activity_type", "presence_status"]:
        op.drop_column("members", name, schema="discord")
