"""Add per-guild Server AI Gateway foundation.

Revision ID: 0043_server_ai_gateway
Revises: 0042_runtime_database_grants
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0043_server_ai_gateway"
down_revision = "0042_runtime_database_grants"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS ai")
    op.create_table("providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False), sa.Column("provider_type", sa.String(40), nullable=False),
        sa.Column("api_base_url", sa.String(500)), sa.Column("encrypted_api_key", sa.Text(), nullable=False), sa.Column("key_hint", sa.String(32)),
        sa.Column("organization_id", sa.String(255)), sa.Column("project_id", sa.String(255)), sa.Column("default_model", sa.String(255)),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")), sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default="30"), sa.Column("max_retries", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("capabilities", postgresql.JSONB(), nullable=False, server_default="[]"), sa.Column("settings", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("last_health_status", sa.String(32)), sa.Column("last_health_latency_ms", sa.Integer()), sa.Column("last_health_check_at", sa.DateTime(timezone=True)), sa.Column("last_error", sa.Text()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["guild_id"],["discord.guilds.guild_id"],ondelete="CASCADE"), sa.ForeignKeyConstraint(["created_by"],["core.users.id"],ondelete="SET NULL"), sa.UniqueConstraint("guild_id","name",name="uq_ai_provider_guild_name"), schema="ai")
    op.create_index("ix_ai_providers_guild_id","providers",["guild_id"],schema="ai")
    op.create_table("module_settings", sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),sa.Column("guild_id",sa.BigInteger(),nullable=False),sa.Column("module_key",sa.String(80),nullable=False),sa.Column("capability",sa.String(80),nullable=False),sa.Column("provider_id",postgresql.UUID(as_uuid=True)),sa.Column("model",sa.String(255)),sa.Column("fallback_provider_ids",postgresql.JSONB(),nullable=False,server_default="[]"),sa.Column("enabled",sa.Boolean(),nullable=False,server_default=sa.text("true")),sa.Column("configuration",postgresql.JSONB(),nullable=False,server_default="{}"),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),sa.ForeignKeyConstraint(["guild_id"],["discord.guilds.guild_id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["provider_id"],["ai.providers.id"],ondelete="SET NULL"),sa.UniqueConstraint("guild_id","module_key","capability",name="uq_ai_module_capability"),schema="ai")
    op.create_table("usage",sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),sa.Column("guild_id",sa.BigInteger(),nullable=False),sa.Column("provider_id",postgresql.UUID(as_uuid=True)),sa.Column("module_key",sa.String(80)),sa.Column("capability",sa.String(80),nullable=False),sa.Column("model",sa.String(255)),sa.Column("request_count",sa.Integer(),nullable=False,server_default="1"),sa.Column("input_units",sa.Integer(),nullable=False,server_default="0"),sa.Column("output_units",sa.Integer(),nullable=False,server_default="0"),sa.Column("estimated_cost",sa.Numeric(14,6),nullable=False,server_default="0"),sa.Column("occurred_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),sa.ForeignKeyConstraint(["guild_id"],["discord.guilds.guild_id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["provider_id"],["ai.providers.id"],ondelete="SET NULL"),schema="ai")
    op.create_index("ix_ai_usage_guild_id","usage",["guild_id"],schema="ai")
    op.create_table("request_logs",sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),sa.Column("guild_id",sa.BigInteger(),nullable=False),sa.Column("provider_id",postgresql.UUID(as_uuid=True)),sa.Column("module_key",sa.String(80)),sa.Column("capability",sa.String(80),nullable=False),sa.Column("model",sa.String(255)),sa.Column("status",sa.String(32),nullable=False),sa.Column("latency_ms",sa.Integer()),sa.Column("error_code",sa.String(100)),sa.Column("error_message",sa.Text()),sa.Column("metadata_json",postgresql.JSONB(),nullable=False,server_default="{}"),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),sa.ForeignKeyConstraint(["guild_id"],["discord.guilds.guild_id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["provider_id"],["ai.providers.id"],ondelete="SET NULL"),schema="ai")
    op.create_index("ix_ai_request_logs_guild_id","request_logs",["guild_id"],schema="ai")
    op.execute("""DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='shieldnet_backend') THEN GRANT USAGE ON SCHEMA ai TO shieldnet_backend; GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA ai TO shieldnet_backend; ALTER DEFAULT PRIVILEGES FOR ROLE shieldnet_owner IN SCHEMA ai GRANT SELECT,INSERT,UPDATE,DELETE ON TABLES TO shieldnet_backend; END IF; END $$;""")


def downgrade() -> None:
    op.drop_table("request_logs",schema="ai"); op.drop_table("usage",schema="ai"); op.drop_table("module_settings",schema="ai"); op.drop_table("providers",schema="ai"); op.execute("DROP SCHEMA IF EXISTS ai")
