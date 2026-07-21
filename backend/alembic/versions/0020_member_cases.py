"""member cases and incident timeline

Revision ID: 0020_cases
Revises: 0019_watchlist
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0020_cases"
down_revision = "0019_watchlist"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "member_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=32), server_default="other", nullable=False),
        sa.Column("severity", sa.String(length=16), server_default="medium", nullable=False),
        sa.Column("status", sa.String(length=16), server_default="open", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assigned_to"], ["core.users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["core.users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["guild_id"], ["discord.guilds.guild_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["member_id"], ["discord.members.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="discord",
    )
    op.create_index("ix_member_cases_guild_member_status", "member_cases", ["guild_id", "member_id", "status"], schema="discord")
    op.create_index("ix_member_cases_guild_severity", "member_cases", ["guild_id", "severity"], schema="discord")


def downgrade() -> None:
    op.drop_index("ix_member_cases_guild_severity", table_name="member_cases", schema="discord")
    op.drop_index("ix_member_cases_guild_member_status", table_name="member_cases", schema="discord")
    op.drop_table("member_cases", schema="discord")
