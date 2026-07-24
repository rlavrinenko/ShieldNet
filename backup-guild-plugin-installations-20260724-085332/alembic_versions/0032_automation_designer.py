"""ShieldNet v4.7 Automation Designer.

Revision ID: 0032_automation
Revises: 0031_backups
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision="0032_automation"
down_revision="0031_backups"
branch_labels=None
depends_on=None


def upgrade():
    op.create_table(
        "automation_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), sa.ForeignKey("discord.guilds.guild_id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("trigger_type", sa.String(64), nullable=False),
        sa.Column("conditions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("actions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("stop_on_error", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("execution_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_executed_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="SET NULL")),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="system",
    )
    op.create_index("ix_system_automation_rules_guild_status", "automation_rules", ["guild_id", "status"], schema="system")
    op.create_table(
        "automation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("system.automation_rules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), sa.ForeignKey("discord.guilds.guild_id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="dry_run"),
        sa.Column("trigger_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("error", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("initiated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="SET NULL")),
        schema="system",
    )
    op.create_index("ix_system_automation_runs_rule_started", "automation_runs", ["rule_id", "started_at"], schema="system")


def downgrade():
    op.drop_index("ix_system_automation_runs_rule_started", table_name="automation_runs", schema="system")
    op.drop_table("automation_runs", schema="system")
    op.drop_index("ix_system_automation_rules_guild_status", table_name="automation_rules", schema="system")
    op.drop_table("automation_rules", schema="system")
