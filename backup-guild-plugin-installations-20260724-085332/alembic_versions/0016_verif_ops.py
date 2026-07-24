from alembic import op
revision = "0016_verif_ops"
down_revision = "0015_verif_buttons"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("ALTER TABLE verification.requests ADD COLUMN IF NOT EXISTS retry_count INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE verification.requests ADD COLUMN IF NOT EXISTS last_error TEXT")
    op.execute("CREATE INDEX IF NOT EXISTS ix_verification_request_operations ON verification.requests (guild_id, status, created_at)")

def downgrade() -> None:
    pass
