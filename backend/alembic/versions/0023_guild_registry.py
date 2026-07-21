"""Guild registry hardening

Revision ID: 0023_registry
Revises: 0022_ops
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0023_registry"
down_revision: Union[str, None] = "0022_ops"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Repair legacy/orphan module rows only when a guild can be inferred.
    # The central runtime registry prevents new FK violations. No destructive
    # schema change is needed for existing installations.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_discord_guilds_last_sync "
        "ON discord.guilds (last_sync_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_discord_guilds_status_bot "
        "ON discord.guilds (status, bot_status)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS discord.ix_discord_guilds_status_bot")
    op.execute("DROP INDEX IF EXISTS discord.ix_discord_guilds_last_sync")
