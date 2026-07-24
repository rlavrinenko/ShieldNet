"""verification control center

Revision ID: 0017_verif_control
Revises: 0016_verif_ops
"""

from alembic import op

revision = "0017_verif_control"
down_revision = "0016_verif_ops"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE verification.requests
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ
        NOT NULL DEFAULT now()
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS
        ix_verification_search
        ON verification.requests
        (guild_id, discord_user_id, alliance, status)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS
        ix_verification_stale_processing
        ON verification.requests
        (guild_id, status, updated_at)
    """)


def downgrade() -> None:
    pass
