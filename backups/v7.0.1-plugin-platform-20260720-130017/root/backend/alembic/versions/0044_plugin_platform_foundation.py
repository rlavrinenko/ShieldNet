"""Add plugin platform registry foundation.

Revision ID: 0044_plugin_platform_foundation
Revises: 0043_server_ai_gateway
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0044_plugin_platform_foundation"
down_revision = "0043_server_ai_gateway"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS plugins")
    op.create_table(
        "registry",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plugin_key", sa.String(96), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("author", sa.String(160)),
        sa.Column("min_core_version", sa.String(40)),
        sa.Column("manifest_path", sa.String(500), nullable=False),
        sa.Column("manifest", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("checksum", sa.String(128)),
        sa.Column("signature_status", sa.String(32), nullable=False, server_default="unsigned"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("healthy", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_error", sa.Text()),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("plugin_key", name="uq_plugins_registry_plugin_key"),
        schema="plugins",
    )
    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plugin_key", sa.String(96), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="success"),
        sa.Column("message", sa.Text()),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="plugins",
    )
    op.create_index("ix_plugins_events_plugin_key", "events", ["plugin_key"], schema="plugins")
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='shieldnet_backend') THEN
        GRANT USAGE ON SCHEMA plugins TO shieldnet_backend;
        GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA plugins TO shieldnet_backend;
        ALTER DEFAULT PRIVILEGES FOR ROLE shieldnet_owner IN SCHEMA plugins
          GRANT SELECT,INSERT,UPDATE,DELETE ON TABLES TO shieldnet_backend;
      END IF;
    END $$;""")


def downgrade() -> None:
    op.drop_index("ix_plugins_events_plugin_key", table_name="events", schema="plugins")
    op.drop_table("events", schema="plugins")
    op.drop_table("registry", schema="plugins")
    op.execute("DROP SCHEMA IF EXISTS plugins")
