"""ShieldNet v5.1 Members Control Center.

Revision ID: 0036_members_center
Revises: 0035_scheduler
"""
from alembic import op
import sqlalchemy as sa
revision="0036_members_center"
down_revision="0035_scheduler"
branch_labels=None
depends_on=None
def upgrade():
    op.add_column("members", sa.Column("game_nickname", sa.String(255)), schema="discord")
    op.add_column("members", sa.Column("alliance_tag", sa.String(32)), schema="discord")
    op.add_column("members", sa.Column("leadership_rank", sa.String(8)), schema="discord")
    op.add_column("members", sa.Column("preferred_language", sa.String(16)), schema="discord")
    op.add_column("members", sa.Column("verification_status", sa.String(24), nullable=False, server_default="not_verified"), schema="discord")
    op.add_column("members", sa.Column("verification_updated_at", sa.DateTime(timezone=True)), schema="discord")
    op.create_index("ix_members_guild_alliance", "members", ["guild_id", "alliance_tag"], schema="discord")
    op.create_index("ix_members_guild_verification", "members", ["guild_id", "verification_status"], schema="discord")
def downgrade():
    op.drop_index("ix_members_guild_verification", table_name="members", schema="discord")
    op.drop_index("ix_members_guild_alliance", table_name="members", schema="discord")
    for name in ["verification_updated_at","verification_status","preferred_language","leadership_rank","alliance_tag","game_nickname"]:
        op.drop_column("members", name, schema="discord")
