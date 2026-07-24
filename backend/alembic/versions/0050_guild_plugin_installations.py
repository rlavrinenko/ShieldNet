"""Guild plugin installations.
Revision ID: a7c3d1000050
Revises: 9f2a7c000049
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a7c3d1000050"
down_revision = "9f2a7c000049"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "guild_installations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("plugin_key", sa.String(96), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="installed"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("configuration", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("installed_by_user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("enabled_at", sa.DateTime(timezone=True)),
        sa.Column("disabled_at", sa.DateTime(timezone=True)),
        sa.Column("last_health_check_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("guild_id", "plugin_key", name="uq_plugins_guild_installation"),
        schema="plugins",
    )
    op.create_index("ix_plugins_guild_installations_guild", "guild_installations", ["guild_id"], schema="plugins")
    op.create_index("ix_plugins_guild_installations_plugin", "guild_installations", ["plugin_key"], schema="plugins")
    op.execute("""
    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='shieldnet_backend') THEN
        GRANT SELECT,INSERT,UPDATE,DELETE ON plugins.guild_installations TO shieldnet_backend;
      END IF;
    END $$;
    """)

def downgrade():
    op.drop_index("ix_plugins_guild_installations_plugin", table_name="guild_installations", schema="plugins")
    op.drop_index("ix_plugins_guild_installations_guild", table_name="guild_installations", schema="plugins")
    op.drop_table("guild_installations", schema="plugins")
