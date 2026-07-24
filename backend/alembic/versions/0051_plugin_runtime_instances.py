"""Plugin runtime instances per guild.
Revision ID: b8d4e2000051
Revises: a7c3d1000050
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision="b8d4e2000051"
down_revision="a7c3d1000050"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table(
        "runtime_instances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("plugin_key", sa.String(96), nullable=False),
        sa.Column("state", sa.String(24), nullable=False, server_default="stopped"),
        sa.Column("generation", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("package_version", sa.String(40)),
        sa.Column("package_path", sa.String(500)),
        sa.Column("manifest_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("stopped_at", sa.DateTime(timezone=True)),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("guild_id","plugin_key",name="uq_plugins_runtime_instance"),
        schema="plugins",
    )
    op.create_index("ix_plugins_runtime_instances_guild","runtime_instances",["guild_id"],schema="plugins")
    op.create_index("ix_plugins_runtime_instances_state","runtime_instances",["state"],schema="plugins")
    op.execute("""
    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='shieldnet_backend') THEN
        GRANT SELECT,INSERT,UPDATE,DELETE ON plugins.runtime_instances TO shieldnet_backend;
      END IF;
    END $$;
    """)

def downgrade():
    op.drop_index("ix_plugins_runtime_instances_state",table_name="runtime_instances",schema="plugins")
    op.drop_index("ix_plugins_runtime_instances_guild",table_name="runtime_instances",schema="plugins")
    op.drop_table("runtime_instances",schema="plugins")
