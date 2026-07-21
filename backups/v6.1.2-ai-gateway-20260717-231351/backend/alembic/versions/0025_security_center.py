"""Security center

Revision ID: 0025_security
Revises: 0024_jobs
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0025_security"
down_revision: Union[str, None] = "0024_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS security")
    severity_type = postgresql.ENUM("info", "low", "medium", "high", "critical", name="security_severity", schema="security")
    severity_type.create(op.get_bind(), checkfirst=True)
    severity = postgresql.ENUM("info", "low", "medium", "high", "critical", name="security_severity", schema="security", create_type=False)
    op.create_table(
        "snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("role_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("channel_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("webhook_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["guild_id"], ["discord.guilds.guild_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="security",
    )
    op.create_index("ix_security_snapshots_guild_created", "snapshots", ["guild_id", "created_at"], schema="security")
    op.create_table(
        "findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("finding_key", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("severity", severity, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=True),
        sa.Column("resource_id", sa.String(length=64), nullable=True),
        sa.Column("resource_name", sa.String(length=255), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="open", nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["guild_id"], ["discord.guilds.guild_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["snapshot_id"], ["security.snapshots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="security",
    )
    op.create_index("ix_security_findings_guild_status", "findings", ["guild_id", "status"], schema="security")
    op.create_index("ix_security_findings_guild_severity", "findings", ["guild_id", "severity"], schema="security")


def downgrade() -> None:
    op.drop_index("ix_security_findings_guild_severity", table_name="findings", schema="security")
    op.drop_index("ix_security_findings_guild_status", table_name="findings", schema="security")
    op.drop_table("findings", schema="security")
    op.drop_index("ix_security_snapshots_guild_created", table_name="snapshots", schema="security")
    op.drop_table("snapshots", schema="security")
    postgresql.ENUM(name="security_severity", schema="security").drop(op.get_bind(), checkfirst=True)
