"""ShieldNet v3.2 notification center.

Revision ID: 0027_alerts
Revises: 0026_infra
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0027_alerts"
down_revision = "0026_infra"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=True),
        sa.Column("severity", sa.String(length=16), nullable=False, server_default="info"),
        sa.Column("category", sa.String(length=48), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="platform"),
        sa.Column("fingerprint", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="open"),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("acknowledged_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="SET NULL")),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="SET NULL")),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="system",
    )
    op.create_index("ix_system_notifications_status_created", "notifications", ["status", "created_at"], schema="system")
    op.create_index("ix_system_notifications_severity_status", "notifications", ["severity", "status"], schema="system")
    op.create_index("ix_system_notifications_guild_status", "notifications", ["guild_id", "status"], schema="system")
    op.create_index("ux_system_notifications_fingerprint", "notifications", ["fingerprint"], unique=True, schema="system")


def downgrade() -> None:
    op.drop_index("ux_system_notifications_fingerprint", table_name="notifications", schema="system")
    op.drop_index("ix_system_notifications_guild_status", table_name="notifications", schema="system")
    op.drop_index("ix_system_notifications_severity_status", table_name="notifications", schema="system")
    op.drop_index("ix_system_notifications_status_created", table_name="notifications", schema="system")
    op.drop_table("notifications", schema="system")
