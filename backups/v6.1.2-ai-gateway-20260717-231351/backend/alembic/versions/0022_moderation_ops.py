"""moderation operations center

Revision ID: 0022_ops
Revises: 0021_evidence
"""
from alembic import op
import sqlalchemy as sa

revision = "0022_ops"
down_revision = "0021_evidence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("member_cases", sa.Column("priority", sa.String(length=16), server_default="normal", nullable=False), schema="discord")
    op.add_column("member_cases", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True), schema="discord")
    op.add_column("member_cases", sa.Column("first_response_at", sa.DateTime(timezone=True), nullable=True), schema="discord")
    op.create_index("ix_member_cases_guild_priority", "member_cases", ["guild_id", "priority"], schema="discord")
    op.create_index("ix_member_cases_guild_due", "member_cases", ["guild_id", "due_at"], schema="discord")


def downgrade() -> None:
    op.drop_index("ix_member_cases_guild_due", table_name="member_cases", schema="discord")
    op.drop_index("ix_member_cases_guild_priority", table_name="member_cases", schema="discord")
    op.drop_column("member_cases", "first_response_at", schema="discord")
    op.drop_column("member_cases", "due_at", schema="discord")
    op.drop_column("member_cases", "priority", schema="discord")
