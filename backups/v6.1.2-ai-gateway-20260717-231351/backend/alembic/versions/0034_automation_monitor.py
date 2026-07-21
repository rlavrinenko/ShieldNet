"""ShieldNet v4.9 Automation Monitor.

Revision ID: 0034_autmonitor
Revises: 0033_autorun
"""
from alembic import op

revision = "0034_autmonitor"
down_revision = "0033_autorun"
branch_labels = None
depends_on = None

def upgrade():
    op.create_index("ix_automation_runs_guild_started", "automation_runs", ["guild_id", "started_at"], schema="system")
    op.create_index("ix_automation_runs_guild_status", "automation_runs", ["guild_id", "status"], schema="system")

def downgrade():
    op.drop_index("ix_automation_runs_guild_status", table_name="automation_runs", schema="system")
    op.drop_index("ix_automation_runs_guild_started", table_name="automation_runs", schema="system")
