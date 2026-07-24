"""ShieldNet v3.0 core infrastructure runtime heartbeats.

Revision ID: 0026_infra
Revises: 0025_security
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0026_infra"
down_revision = "0025_security"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "runtime_heartbeats",
        sa.Column("worker_name", sa.String(length=128), primary_key=True),
        sa.Column("worker_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="online"),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="system",
    )
    op.create_index("ix_system_runtime_heartbeats_type_seen", "runtime_heartbeats", ["worker_type", "last_seen_at"], schema="system")

def downgrade() -> None:
    op.drop_index("ix_system_runtime_heartbeats_type_seen", table_name="runtime_heartbeats", schema="system")
    op.drop_table("runtime_heartbeats", schema="system")
