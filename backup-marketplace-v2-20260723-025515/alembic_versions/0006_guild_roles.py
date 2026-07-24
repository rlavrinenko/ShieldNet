from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0006_guild_roles"
down_revision: Union[str, None] = "0005_member_actions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "guild_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("discord_role_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.Column("color", sa.Integer(), server_default="0", nullable=False),
        sa.Column("permissions", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("managed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("assignable", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["guild_id"], ["discord.guilds.guild_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("guild_id", "discord_role_id", name="uq_discord_guild_roles_guild_role"),
        schema="discord",
    )

def downgrade() -> None:
    op.drop_table("guild_roles", schema="discord")
