from alembic import op
import sqlalchemy as sa

revision = "0013_verif_notify"
down_revision = "0012_verification"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        "requests",
        sa.Column(
            "notification_status",
            sa.String(32),
            nullable=False,
            server_default="none",
        ),
        schema="verification",
    )
    op.add_column(
        "requests",
        sa.Column("notification_message", sa.Text()),
        schema="verification",
    )
    op.add_column(
        "requests",
        sa.Column("notified_at", sa.DateTime(timezone=True)),
        schema="verification",
    )
    op.execute(
        "UPDATE verification.requests "
        "SET notification_status='pending', "
        "notification_message=decision_reason "
        "WHERE status='rejected' "
        "AND decision_reason IS NOT NULL"
    )
    op.create_index(
        "ix_verification_notification_queue",
        "requests",
        ["guild_id", "notification_status", "created_at"],
        schema="verification",
    )

def downgrade() -> None:
    op.drop_index(
        "ix_verification_notification_queue",
        table_name="requests",
        schema="verification",
    )
    op.drop_column("requests", "notified_at", schema="verification")
    op.drop_column("requests", "notification_message", schema="verification")
    op.drop_column("requests", "notification_status", schema="verification")
