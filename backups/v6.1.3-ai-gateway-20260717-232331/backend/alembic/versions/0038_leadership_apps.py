"""ShieldNet v5.3 R5/R4 Applications.

Revision ID: 0038_leadership_apps
Revises: 0037_verification_center
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="0038_leadership_apps"
down_revision="0037_verification_center"
branch_labels=None
depends_on=None

def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS leadership")
    bind=op.get_bind();insp=sa.inspect(bind)
    if not insp.has_table("application_settings",schema="leadership"):
        op.create_table("application_settings",sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True,server_default=sa.text("gen_random_uuid()")),sa.Column("guild_id",sa.BigInteger(),sa.ForeignKey("discord.guilds.guild_id",ondelete="CASCADE"),nullable=False),sa.Column("enabled",sa.Boolean(),nullable=False,server_default=sa.text("false")),sa.Column("review_channel_id",sa.BigInteger()),sa.Column("r5_role_id",sa.BigInteger()),sa.Column("r4_role_id",sa.BigInteger()),sa.Column("require_evidence",sa.Boolean(),nullable=False,server_default=sa.text("true")),sa.Column("language_role_mode",sa.String(24),nullable=False,server_default="configured"),sa.Column("updated_by",postgresql.UUID(as_uuid=True),sa.ForeignKey("core.users.id",ondelete="SET NULL")),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),sa.UniqueConstraint("guild_id",name="uq_leadership_application_settings_guild"),schema="leadership")
    if not insp.has_table("language_roles",schema="leadership"):
        op.create_table("language_roles",sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True,server_default=sa.text("gen_random_uuid()")),sa.Column("guild_id",sa.BigInteger(),sa.ForeignKey("discord.guilds.guild_id",ondelete="CASCADE"),nullable=False),sa.Column("language_code",sa.String(16),nullable=False),sa.Column("leadership_rank",sa.String(8),nullable=False),sa.Column("role_id",sa.BigInteger(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),sa.UniqueConstraint("guild_id","language_code","leadership_rank",name="uq_leadership_language_role"),schema="leadership")
    if not insp.has_table("applications",schema="leadership"):
        op.create_table("applications",sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True,server_default=sa.text("gen_random_uuid()")),sa.Column("guild_id",sa.BigInteger(),sa.ForeignKey("discord.guilds.guild_id",ondelete="CASCADE"),nullable=False),sa.Column("discord_user_id",sa.BigInteger(),nullable=False),sa.Column("alliance_tag",sa.String(32),nullable=False),sa.Column("game_nickname",sa.String(64),nullable=False),sa.Column("requested_rank",sa.String(8),nullable=False),sa.Column("language_code",sa.String(16),nullable=False),sa.Column("evidence_url",sa.String(1000)),sa.Column("applicant_comment",sa.Text()),sa.Column("status",sa.String(32),nullable=False,server_default="pending"),sa.Column("assigned_to",postgresql.UUID(as_uuid=True),sa.ForeignKey("core.users.id",ondelete="SET NULL")),sa.Column("decision_reason",sa.Text()),sa.Column("decided_by",postgresql.UUID(as_uuid=True),sa.ForeignKey("core.users.id",ondelete="SET NULL")),sa.Column("decided_at",sa.DateTime(timezone=True)),sa.Column("processing_error",sa.Text()),sa.Column("role_sync_status",sa.String(32),nullable=False,server_default="none"),sa.Column("role_sync_requested_at",sa.DateTime(timezone=True)),sa.Column("role_sync_completed_at",sa.DateTime(timezone=True)),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),schema="leadership")
    if not insp.has_table("application_decisions",schema="leadership"):
        op.create_table("application_decisions",sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True,server_default=sa.text("gen_random_uuid()")),sa.Column("application_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("leadership.applications.id",ondelete="CASCADE"),nullable=False),sa.Column("guild_id",sa.BigInteger(),sa.ForeignKey("discord.guilds.guild_id",ondelete="CASCADE"),nullable=False),sa.Column("action",sa.String(32),nullable=False),sa.Column("reason",sa.Text()),sa.Column("actor_user_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("core.users.id",ondelete="SET NULL")),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),schema="leadership")
    for name,table,cols in [("ix_leadership_applications_guild_status","applications",["guild_id","status"]),("ix_leadership_applications_user","applications",["guild_id","discord_user_id"]),("ix_leadership_decisions_application","application_decisions",["application_id"])]:
        existing={x['name'] for x in sa.inspect(bind).get_indexes(table,schema="leadership")}
        if name not in existing:op.create_index(name,table,cols,schema="leadership")

def downgrade():
    for table in ["application_decisions","applications","language_roles","application_settings"]:
        op.drop_table(table,schema="leadership")
