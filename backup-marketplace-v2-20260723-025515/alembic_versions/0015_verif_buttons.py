from alembic import op

revision = "0015_verif_buttons"
down_revision = "0014_verif_review"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("ALTER TABLE verification.requests ADD COLUMN IF NOT EXISTS decided_by_discord_user_id BIGINT")
    op.execute("CREATE INDEX IF NOT EXISTS ix_verification_decided_by_discord ON verification.requests (guild_id, decided_by_discord_user_id)")

def downgrade() -> None:
    pass
