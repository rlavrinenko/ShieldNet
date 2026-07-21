from alembic import op

revision = "0014_verif_review"
down_revision = "0013_verif_notify"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("ALTER TABLE verification.settings ADD COLUMN IF NOT EXISTS review_channel_id BIGINT")
    op.execute("ALTER TABLE verification.requests ADD COLUMN IF NOT EXISTS review_notification_status VARCHAR(32) NOT NULL DEFAULT 'pending'")
    op.execute("ALTER TABLE verification.requests ADD COLUMN IF NOT EXISTS review_message_id BIGINT")
    op.execute("ALTER TABLE verification.requests ADD COLUMN IF NOT EXISTS review_notified_at TIMESTAMPTZ")
    op.execute("CREATE INDEX IF NOT EXISTS ix_verification_review_notification_queue ON verification.requests (guild_id, review_notification_status, created_at)")

def downgrade() -> None:
    pass
