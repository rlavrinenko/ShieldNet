"""ShieldNet v1.7 Member Watchlist & Risk Review.

Revision ID: 0019_watchlist
Revises: 0018_members_control_center
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0019_watchlist"
down_revision: Union[str, None] = "0018_members_control_center"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("members", sa.Column("watchlisted", sa.Boolean(), server_default=sa.text("false"), nullable=False), schema="discord")
    op.add_column("members", sa.Column("risk_level", sa.String(length=16), server_default="low", nullable=False), schema="discord")
    op.add_column("members", sa.Column("review_due_at", sa.DateTime(timezone=True), nullable=True), schema="discord")
    op.add_column("members", sa.Column("review_reason", sa.Text(), nullable=True), schema="discord")
    op.create_check_constraint("ck_discord_members_risk_level", "members", "risk_level IN ('low','medium','high','critical')", schema="discord")
    op.create_index("ix_discord_members_guild_watchlisted", "members", ["guild_id", "watchlisted"], schema="discord")
    op.create_index("ix_discord_members_guild_review_due", "members", ["guild_id", "review_due_at"], schema="discord")


def downgrade() -> None:
    op.drop_index("ix_discord_members_guild_review_due", table_name="members", schema="discord")
    op.drop_index("ix_discord_members_guild_watchlisted", table_name="members", schema="discord")
    op.drop_constraint("ck_discord_members_risk_level", "members", schema="discord", type_="check")
    op.drop_column("members", "review_reason", schema="discord")
    op.drop_column("members", "review_due_at", schema="discord")
    op.drop_column("members", "risk_level", schema="discord")
    op.drop_column("members", "watchlisted", schema="discord")
