"""verification manual approval workflow"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0012_verification"
down_revision = "0011_verification_stabilization"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "requests",
        sa.Column("decided_by", postgresql.UUID(as_uuid=True), nullable=True),
        schema="verification",
    )
    op.add_column(
        "requests",
        sa.Column("decision_reason", sa.Text(), nullable=True),
        schema="verification",
    )
    op.add_column(
        "requests",
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        schema="verification",
    )

    op.create_foreign_key(
        "fk_verification_requests_decided_by",
        "requests",
        "users",
        ["decided_by"],
        ["id"],
        source_schema="verification",
        referent_schema="core",
        ondelete="SET NULL",
    )

    op.execute(
        "UPDATE verification.requests "
        "SET status = 'completed' "
        "WHERE status = 'approved'"
    )

    op.execute(
        "DROP INDEX IF EXISTS "
        "verification.uq_verification_one_pending_per_user"
    )

    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS "
        "uq_verification_one_active_per_user "
        "ON verification.requests (guild_id, discord_user_id) "
        "WHERE status IN ('pending', 'approved', 'processing')"
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS "
        "ix_verification_requests_review_queue "
        "ON verification.requests (guild_id, status, created_at)"
    )


def downgrade() -> None:
    op.execute(
        "DROP INDEX IF EXISTS "
        "verification.ix_verification_requests_review_queue"
    )
    op.execute(
        "DROP INDEX IF EXISTS "
        "verification.uq_verification_one_active_per_user"
    )
    op.drop_constraint(
        "fk_verification_requests_decided_by",
        "requests",
        schema="verification",
        type_="foreignkey",
    )
    op.drop_column("requests", "decided_at", schema="verification")
    op.drop_column("requests", "decision_reason", schema="verification")
    op.drop_column("requests", "decided_by", schema="verification")
