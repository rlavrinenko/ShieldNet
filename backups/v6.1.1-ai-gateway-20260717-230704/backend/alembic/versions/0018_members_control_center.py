"""ShieldNet v1.6 Members Control Center.

Revision ID: 0018_members_control_center
Revises: 0017_verif_control
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0018_members_control_center"
down_revision: Union[str, None] = "0017_verif_control"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("members", sa.Column("admin_note", sa.Text(), nullable=True), schema="discord")
    op.add_column(
        "members",
        sa.Column("tags", postgresql.ARRAY(sa.String(length=64)), server_default=sa.text("'{}'::varchar[]"), nullable=False),
        schema="discord",
    )
    op.add_column(
        "members",
        sa.Column("shieldnet_blocked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        schema="discord",
    )
    op.add_column("members", sa.Column("profile_updated_by", postgresql.UUID(as_uuid=True), nullable=True), schema="discord")
    op.add_column("members", sa.Column("profile_updated_at", sa.DateTime(timezone=True), nullable=True), schema="discord")
    op.create_foreign_key(
        "fk_discord_members_profile_updated_by",
        "members", "users", ["profile_updated_by"], ["id"],
        source_schema="discord", referent_schema="core", ondelete="SET NULL",
    )
    op.create_index("ix_discord_members_guild_blocked", "members", ["guild_id", "shieldnet_blocked"], schema="discord")
    op.create_index("ix_discord_members_tags_gin", "members", ["tags"], unique=False, schema="discord", postgresql_using="gin")


def downgrade() -> None:
    op.drop_index("ix_discord_members_tags_gin", table_name="members", schema="discord")
    op.drop_index("ix_discord_members_guild_blocked", table_name="members", schema="discord")
    op.drop_constraint("fk_discord_members_profile_updated_by", "members", schema="discord", type_="foreignkey")
    op.drop_column("members", "profile_updated_at", schema="discord")
    op.drop_column("members", "profile_updated_by", schema="discord")
    op.drop_column("members", "shieldnet_blocked", schema="discord")
    op.drop_column("members", "tags", schema="discord")
    op.drop_column("members", "admin_note", schema="discord")
