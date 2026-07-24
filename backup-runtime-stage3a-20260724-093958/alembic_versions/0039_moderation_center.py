"""ShieldNet v5.4 Moderation Center.

Revision ID: 0039_moderation_center
Revises: 0038_leadership_apps
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0039_moderation_center"
down_revision = "0038_leadership_apps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS moderation")
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not insp.has_table("violation_types", schema="moderation"):
        op.create_table("violation_types",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("guild_id", sa.BigInteger(), sa.ForeignKey("discord.guilds.guild_id", ondelete="CASCADE"), nullable=False),
            sa.Column("code", sa.String(64), nullable=False), sa.Column("name", sa.String(160), nullable=False),
            sa.Column("description", sa.Text()), sa.Column("severity", sa.String(16), nullable=False, server_default="medium"),
            sa.Column("recommended_action", sa.String(32)), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="SET NULL")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("guild_id", "code", name="uq_moderation_violation_type_code"), schema="moderation")

    if not insp.has_table("reports", schema="moderation"):
        op.create_table("reports",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("guild_id", sa.BigInteger(), sa.ForeignKey("discord.guilds.guild_id", ondelete="CASCADE"), nullable=False),
            sa.Column("reporter_discord_user_id", sa.BigInteger()),
            sa.Column("reporter_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="SET NULL")),
            sa.Column("reported_discord_user_id", sa.BigInteger(), nullable=False),
            sa.Column("violation_type_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("moderation.violation_types.id", ondelete="SET NULL")),
            sa.Column("title", sa.String(255), nullable=False), sa.Column("description", sa.Text(), nullable=False),
            sa.Column("priority", sa.String(16), nullable=False, server_default="normal"),
            sa.Column("status", sa.String(24), nullable=False, server_default="pending"),
            sa.Column("message_url", sa.Text()), sa.Column("channel_id", sa.BigInteger()),
            sa.Column("assigned_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="SET NULL")),
            sa.Column("rejection_reason", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), schema="moderation")

    if not insp.has_table("cases", schema="moderation"):
        op.create_table("cases",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("guild_id", sa.BigInteger(), sa.ForeignKey("discord.guilds.guild_id", ondelete="CASCADE"), nullable=False),
            sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("moderation.reports.id", ondelete="SET NULL")),
            sa.Column("reported_discord_user_id", sa.BigInteger(), nullable=False),
            sa.Column("violation_type_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("moderation.violation_types.id", ondelete="SET NULL")),
            sa.Column("title", sa.String(255), nullable=False), sa.Column("description", sa.Text()),
            sa.Column("severity", sa.String(16), nullable=False, server_default="medium"),
            sa.Column("priority", sa.String(16), nullable=False, server_default="normal"),
            sa.Column("status", sa.String(24), nullable=False, server_default="open"),
            sa.Column("assigned_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="SET NULL")),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="SET NULL")),
            sa.Column("resolution", sa.Text()), sa.Column("resolved_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), schema="moderation")

    if not insp.has_table("attachments", schema="moderation"):
        op.create_table("attachments",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("moderation.reports.id", ondelete="CASCADE")),
            sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("moderation.cases.id", ondelete="CASCADE")),
            sa.Column("url", sa.Text(), nullable=False), sa.Column("media_type", sa.String(64)), sa.Column("file_name", sa.String(255)),
            sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="SET NULL")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), schema="moderation")

    if not insp.has_table("case_notes", schema="moderation"):
        op.create_table("case_notes",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("moderation.cases.id", ondelete="CASCADE"), nullable=False),
            sa.Column("visibility", sa.String(24), nullable=False, server_default="private"), sa.Column("body", sa.Text(), nullable=False),
            sa.Column("author_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="SET NULL")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), schema="moderation")

    if not insp.has_table("actions", schema="moderation"):
        op.create_table("actions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("moderation.cases.id", ondelete="CASCADE"), nullable=False),
            sa.Column("guild_id", sa.BigInteger(), nullable=False), sa.Column("discord_user_id", sa.BigInteger(), nullable=False),
            sa.Column("action_type", sa.String(32), nullable=False), sa.Column("reason", sa.Text()), sa.Column("duration_seconds", sa.Integer()),
            sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("status", sa.String(24), nullable=False, server_default="pending"),
            sa.Column("member_action_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("discord.member_actions.id", ondelete="SET NULL")),
            sa.Column("result_message", sa.Text()),
            sa.Column("requested_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="SET NULL")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("completed_at", sa.DateTime(timezone=True)), schema="moderation")

    if not insp.has_table("appeals", schema="moderation"):
        op.create_table("appeals",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("moderation.cases.id", ondelete="CASCADE"), nullable=False),
            sa.Column("appellant_discord_user_id", sa.BigInteger(), nullable=False), sa.Column("body", sa.Text(), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="pending"), sa.Column("decision_reason", sa.Text()),
            sa.Column("decided_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="SET NULL")),
            sa.Column("decided_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), schema="moderation")

    if not insp.has_table("templates", schema="moderation"):
        op.create_table("templates",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("guild_id", sa.BigInteger(), sa.ForeignKey("discord.guilds.guild_id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(160), nullable=False), sa.Column("action_type", sa.String(32), nullable=False),
            sa.Column("reason_template", sa.Text()), sa.Column("duration_seconds", sa.Integer()),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="SET NULL")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("guild_id", "name", name="uq_moderation_template_name"), schema="moderation")

    indexes = [
        ("ix_moderation_reports_guild_status", "reports", ["guild_id", "status", "created_at"]),
        ("ix_moderation_reports_target", "reports", ["guild_id", "reported_discord_user_id"]),
        ("ix_moderation_cases_guild_status", "cases", ["guild_id", "status", "created_at"]),
        ("ix_moderation_cases_target", "cases", ["guild_id", "reported_discord_user_id"]),
        ("ix_moderation_actions_case", "actions", ["case_id", "created_at"]),
        ("ix_moderation_appeals_case_status", "appeals", ["case_id", "status"]),
    ]
    for name, table, columns in indexes:
        existing = {x["name"] for x in sa.inspect(bind).get_indexes(table, schema="moderation")}
        if name not in existing:
            op.create_index(name, table, columns, schema="moderation")


def downgrade() -> None:
    for table in ["templates", "appeals", "actions", "case_notes", "attachments", "cases", "reports", "violation_types"]:
        op.drop_table(table, schema="moderation")
