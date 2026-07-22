"""Add plugin runtime validation state.

Revision ID: 7c4fa8300047
Revises: 6b3e9c2f0046
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "7c4fa8300047"
down_revision = "6b3e9c2f0046"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "runtime_state",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plugin_key", sa.String(96), nullable=False),
        sa.Column("prepared_version", sa.String(40)),
        sa.Column("package_path", sa.String(500)),
        sa.Column(
            "manifest_json",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("state", sa.String(24), nullable=False, server_default="empty"),
        sa.Column("last_job_id", postgresql.UUID(as_uuid=True)),
        sa.Column("last_error", sa.Text()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "plugin_key",
            name="uq_plugins_runtime_state_plugin_key",
        ),
        schema="plugins",
    )

    op.create_table(
        "runtime_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plugin_key", sa.String(96), nullable=False),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plugins.install_jobs.id", ondelete="SET NULL"),
        ),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="plugins",
    )
    op.create_index(
        "ix_plugins_runtime_events_plugin_key",
        "runtime_events",
        ["plugin_key"],
        schema="plugins",
    )
    op.create_index(
        "ix_plugins_runtime_events_job_id",
        "runtime_events",
        ["job_id"],
        schema="plugins",
    )

    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='shieldnet_backend') THEN
        GRANT SELECT,INSERT,UPDATE,DELETE ON
          plugins.runtime_state,
          plugins.runtime_events
        TO shieldnet_backend;
      END IF;
    END $$;""")


def downgrade() -> None:
    op.drop_index(
        "ix_plugins_runtime_events_job_id",
        table_name="runtime_events",
        schema="plugins",
    )
    op.drop_index(
        "ix_plugins_runtime_events_plugin_key",
        table_name="runtime_events",
        schema="plugins",
    )
    op.drop_table("runtime_events", schema="plugins")
    op.drop_table("runtime_state", schema="plugins")
