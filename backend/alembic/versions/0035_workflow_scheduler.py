"""ShieldNet v5.0 Workflow Scheduler.

Revision ID: 0035_scheduler
Revises: 0034_autmonitor
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="0035_scheduler"
down_revision="0034_autmonitor"
branch_labels=None
depends_on=None
def upgrade():
    op.create_table("automation_schedules",
      sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
      sa.Column("rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("system.automation_rules.id", ondelete="CASCADE"), nullable=False, unique=True),
      sa.Column("guild_id", sa.BigInteger(), sa.ForeignKey("discord.guilds.guild_id", ondelete="CASCADE"), nullable=False),
      sa.Column("schedule_type", sa.String(24), nullable=False, server_default="daily"),
      sa.Column("timezone", sa.String(64), nullable=False, server_default="UTC"),
      sa.Column("hour", sa.Integer(), nullable=False, server_default="9"),
      sa.Column("minute", sa.Integer(), nullable=False, server_default="0"),
      sa.Column("days_of_week", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
      sa.Column("interval_minutes", sa.Integer()),
      sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
      sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=False),
      sa.Column("last_run_at", sa.DateTime(timezone=True)),
      sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="SET NULL")),
      sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
      sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
      schema="system")
    op.create_index("ix_automation_schedules_guild", "automation_schedules", ["guild_id"], schema="system")
    op.create_index("ix_automation_schedules_due", "automation_schedules", ["enabled", "next_run_at"], schema="system")
def downgrade():
    op.drop_index("ix_automation_schedules_due", table_name="automation_schedules", schema="system")
    op.drop_index("ix_automation_schedules_guild", table_name="automation_schedules", schema="system")
    op.drop_table("automation_schedules", schema="system")
