"""Add plugin installation job foundation.

Revision ID: 6b3e9c2f0046
Revises: 4a1d8e7c0045
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "6b3e9c2f0046"
down_revision = "4a1d8e7c0045"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "install_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plugin_key", sa.String(96), nullable=False),
        sa.Column("requested_version", sa.String(40)),
        sa.Column("action", sa.String(24), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="queued"),
        sa.Column("requested_by_user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text()),
        sa.Column("payload_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        schema="plugins",
    )
    op.create_index("ix_plugins_install_jobs_status", "install_jobs", ["status"], schema="plugins")
    op.create_index("ix_plugins_install_jobs_plugin_key", "install_jobs", ["plugin_key"], schema="plugins")

    op.create_table(
        "install_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plugins.install_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("level", sa.String(16), nullable=False, server_default="info"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="plugins",
    )
    op.create_index("ix_plugins_install_logs_job_id", "install_logs", ["job_id"], schema="plugins")

    op.create_table(
        "installed_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plugin_key", sa.String(96), nullable=False),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("previous_version", sa.String(40)),
        sa.Column("install_path", sa.String(500), nullable=False),
        sa.Column("checksum_sha256", sa.String(64)),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("plugin_key", name="uq_plugins_installed_versions_plugin_key"),
        schema="plugins",
    )

    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='shieldnet_backend') THEN
        GRANT SELECT,INSERT,UPDATE,DELETE ON
          plugins.install_jobs,
          plugins.install_logs,
          plugins.installed_versions
        TO shieldnet_backend;
      END IF;
    END $$;""")


def downgrade() -> None:
    op.drop_table("installed_versions", schema="plugins")
    op.drop_index("ix_plugins_install_logs_job_id", table_name="install_logs", schema="plugins")
    op.drop_table("install_logs", schema="plugins")
    op.drop_index("ix_plugins_install_jobs_plugin_key", table_name="install_jobs", schema="plugins")
    op.drop_index("ix_plugins_install_jobs_status", table_name="install_jobs", schema="plugins")
    op.drop_table("install_jobs", schema="plugins")
