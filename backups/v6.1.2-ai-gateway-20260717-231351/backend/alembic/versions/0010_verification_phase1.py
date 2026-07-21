from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0010_verification_phase1"
down_revision = "0009_permissions_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS verification AUTHORIZATION shieldnet_owner")

    op.create_table(
        "settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("verified_role_id", sa.BigInteger()),
        sa.Column("nickname_template", sa.String(128), server_default="[{alliance}] {nickname}", nullable=False),
        sa.Column("auto_approve", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("alliance_min_length", sa.Integer(), server_default="2", nullable=False),
        sa.Column("alliance_max_length", sa.Integer(), server_default="8", nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["guild_id"], ["discord.guilds.guild_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by"], ["core.users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("guild_id", name="uq_verification_settings_guild"),
        schema="verification",
    )

    op.create_table(
        "requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("discord_user_id", sa.BigInteger(), nullable=False),
        sa.Column("alliance", sa.String(32), nullable=False),
        sa.Column("nickname", sa.String(64), nullable=False),
        sa.Column("requested_nickname", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), server_default="pending", nullable=False),
        sa.Column("result_message", sa.Text()),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["guild_id"], ["discord.guilds.guild_id"], ondelete="CASCADE"),
        schema="verification",
    )


def downgrade() -> None:
    op.drop_table("requests", schema="verification")
    op.drop_table("settings", schema="verification")
