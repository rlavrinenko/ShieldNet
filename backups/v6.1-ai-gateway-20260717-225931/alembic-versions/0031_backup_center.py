"""ShieldNet v4.6 Backup Center.

Revision ID: 0031_backups
Revises: 0030_permsim
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision="0031_backups"
down_revision="0030_permsim"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table(
        "guild_backups",
        sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
        sa.Column("guild_id",sa.BigInteger(),sa.ForeignKey("discord.guilds.guild_id",ondelete="CASCADE"),nullable=False),
        sa.Column("name",sa.String(160),nullable=False),
        sa.Column("description",sa.Text()),
        sa.Column("status",sa.String(24),nullable=False,server_default="ready"),
        sa.Column("format_version",sa.Integer(),nullable=False,server_default="1"),
        sa.Column("object_count",sa.Integer(),nullable=False,server_default="0"),
        sa.Column("size_bytes",sa.Integer(),nullable=False,server_default="0"),
        sa.Column("snapshot",postgresql.JSONB(astext_type=sa.Text()),nullable=False,server_default="{}"),
        sa.Column("created_by",postgresql.UUID(as_uuid=True),sa.ForeignKey("core.users.id",ondelete="SET NULL")),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
        schema="system",
    )
    op.create_index("ix_system_guild_backups_guild_created","guild_backups",["guild_id","created_at"],schema="system")

def downgrade():
    op.drop_index("ix_system_guild_backups_guild_created",table_name="guild_backups",schema="system")
    op.drop_table("guild_backups",schema="system")
