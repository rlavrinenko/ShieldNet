"""case evidence and appeals

Revision ID: 0021_evidence
Revises: 0020_cases
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0021_evidence"
down_revision = "0020_cases"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "member_case_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evidence_type", sa.String(length=24), server_default="link", nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["discord.member_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["core.users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["guild_id"], ["discord.guilds.guild_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="discord",
    )
    op.create_index("ix_case_evidence_case_created", "member_case_evidence", ["case_id", "created_at"], schema="discord")

    op.create_table(
        "member_case_appeals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="submitted", nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("decision", sa.Text(), nullable=True),
        sa.Column("submitted_by_name", sa.String(length=255), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["discord.member_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["core.users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["guild_id"], ["discord.guilds.guild_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["core.users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        schema="discord",
    )
    op.create_index("ix_case_appeals_case_status", "member_case_appeals", ["case_id", "status"], schema="discord")
    op.create_index("ix_case_appeals_guild_created", "member_case_appeals", ["guild_id", "created_at"], schema="discord")


def downgrade() -> None:
    op.drop_index("ix_case_appeals_guild_created", table_name="member_case_appeals", schema="discord")
    op.drop_index("ix_case_appeals_case_status", table_name="member_case_appeals", schema="discord")
    op.drop_table("member_case_appeals", schema="discord")
    op.drop_index("ix_case_evidence_case_created", table_name="member_case_evidence", schema="discord")
    op.drop_table("member_case_evidence", schema="discord")
