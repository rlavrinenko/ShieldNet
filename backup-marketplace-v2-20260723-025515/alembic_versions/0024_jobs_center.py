"""System jobs center

Revision ID: 0024_jobs
Revises: 0023_registry
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0024_jobs"
down_revision: Union[str, None] = "0023_registry"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_key", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=24), server_default="queued", nullable=False),
        sa.Column("trigger", sa.String(length=24), server_default="manual", nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="system",
    )
    op.create_index("ix_system_job_runs_job_created", "job_runs", ["job_key", "created_at"], schema="system")
    op.create_index("ix_system_job_runs_status_created", "job_runs", ["status", "created_at"], schema="system")


def downgrade() -> None:
    op.drop_index("ix_system_job_runs_status_created", table_name="job_runs", schema="system")
    op.drop_index("ix_system_job_runs_job_created", table_name="job_runs", schema="system")
    op.drop_table("job_runs", schema="system")
