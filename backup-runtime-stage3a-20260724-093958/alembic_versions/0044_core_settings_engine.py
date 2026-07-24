"""core settings engine

Revision ID: 0044_core_settings_engine
Revises: 0043_server_ai_gateway
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0044_core_settings_engine"
down_revision = "0043_server_ai_gateway"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "module_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("module", sa.String(length=64), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("value_type", sa.String(length=32), server_default="json", nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("guild_id", "module", "key", name="uq_core_module_settings_scope"),
        schema="core",
    )
    op.create_index(
        "ix_core_module_settings_guild_module",
        "module_settings",
        ["guild_id", "module"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_module_settings_guild_module",
        table_name="module_settings",
        schema="core",
    )
    op.drop_table("module_settings", schema="core")
