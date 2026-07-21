from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004_members_core"
down_revision: Union[str, None] = "0003_modules_core"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "members",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("discord_user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("global_name", sa.String(255)),
        sa.Column("nickname", sa.String(255)),
        sa.Column("avatar_url", sa.Text()),
        sa.Column("bot", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("pending", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True)),
        sa.Column("left_at", sa.DateTime(timezone=True)),
        sa.Column("last_activity_at", sa.DateTime(timezone=True)),
        sa.Column("communication_disabled_until", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["guild_id"], ["discord.guilds.guild_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("guild_id", "discord_user_id", name="uq_discord_members_guild_user"),
        schema="discord",
    )
    op.create_index("ix_discord_members_guild_active", "members", ["guild_id", "is_active"], schema="discord")

    op.create_table(
        "member_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("discord_role_id", sa.BigInteger(), nullable=False),
        sa.Column("role_name", sa.String(255), nullable=False),
        sa.Column("role_position", sa.Integer(), server_default="0", nullable=False),
        sa.Column("role_color", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["member_id"], ["discord.members.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("member_id", "discord_role_id", name="uq_discord_member_roles_member_role"),
        schema="discord",
    )

def downgrade() -> None:
    op.drop_table("member_roles", schema="discord")
    op.drop_table("members", schema="discord")
