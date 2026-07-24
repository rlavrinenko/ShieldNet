"""ShieldNet v4.8 Automation Runtime Engine.

Revision ID: 0033_autorun
Revises: 0032_automation
"""
from alembic import op
import sqlalchemy as sa

revision = "0033_autorun"
down_revision = "0032_automation"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("automation_rules", sa.Column("max_failures", sa.Integer(), nullable=False, server_default="5"), schema="system")
    op.add_column("automation_rules", sa.Column("disabled_reason", sa.Text()), schema="system")
    op.add_column("automation_runs", sa.Column("idempotency_key", sa.String(64)), schema="system")
    op.add_column("automation_runs", sa.Column("event_type", sa.String(64)), schema="system")
    op.add_column("automation_runs", sa.Column("event_id", sa.String(160)), schema="system")
    op.add_column("automation_runs", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"), schema="system")
    op.create_index("uq_system_automation_runs_idempotency", "automation_runs", ["idempotency_key"], unique=True, schema="system")


def downgrade():
    op.drop_index("uq_system_automation_runs_idempotency", table_name="automation_runs", schema="system")
    for col in ("attempt_count", "event_id", "event_type", "idempotency_key"):
        op.drop_column("automation_runs", col, schema="system")
    op.drop_column("automation_rules", "disabled_reason", schema="system")
    op.drop_column("automation_rules", "max_failures", schema="system")
