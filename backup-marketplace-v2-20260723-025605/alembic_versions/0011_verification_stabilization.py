from alembic import op

revision = "0011_verification_stabilization"
down_revision = "0010_verification_phase1"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("ALTER TABLE verification.settings ALTER COLUMN id SET DEFAULT gen_random_uuid()")
    op.execute("ALTER TABLE verification.requests ALTER COLUMN id SET DEFAULT gen_random_uuid()")
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_verification_requests_guild_status_created
        ON verification.requests (guild_id, status, created_at)
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_verification_one_pending_per_user
        ON verification.requests (guild_id, discord_user_id)
        WHERE status IN ('pending', 'processing')
    """)

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS verification.uq_verification_one_pending_per_user")
    op.execute("DROP INDEX IF EXISTS verification.ix_verification_requests_guild_status_created")
