"""create ShieldNet module registry

Revision ID: 0003_modules_core
Revises: 0002_discord_guilds
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_modules_core"
down_revision: Union[str, None] = "0002_discord_guilds"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "catalog",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("module_key", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("icon", sa.String(32)),
        sa.Column("version", sa.String(32), server_default="0.1.0", nullable=False),
        sa.Column("is_core", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_available", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="100", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_modules_catalog"),
        sa.UniqueConstraint("module_key", name="uq_modules_catalog_module_key"),
        schema="modules",
    )

    op.create_table(
        "guild_modules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("configuration", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True)),
        sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["guild_id"], ["discord.guilds.guild_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["module_id"], ["modules.catalog.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by"], ["core.users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_modules_guild_modules"),
        sa.UniqueConstraint("guild_id", "module_id", name="uq_modules_guild_module"),
        schema="modules",
    )

    catalog = sa.table(
        "catalog",
        sa.column("module_key", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("icon", sa.String),
        sa.column("version", sa.String),
        sa.column("is_core", sa.Boolean),
        sa.column("is_available", sa.Boolean),
        sa.column("sort_order", sa.Integer),
        schema="modules",
    )

    op.bulk_insert(
        catalog,
        [
            {
                "module_key": "core",
                "name": "ShieldNet Core",
                "description": "Core synchronization and platform services.",
                "icon": "🛡",
                "version": "0.1.0",
                "is_core": True,
                "is_available": True,
                "sort_order": 1,
            },
            {
                "module_key": "welcome",
                "name": "Welcome",
                "description": "Welcome messages and member onboarding.",
                "icon": "👋",
                "version": "0.1.0",
                "is_core": False,
                "is_available": True,
                "sort_order": 10,
            },
            {
                "module_key": "verification",
                "name": "Verification",
                "description": "Verification workflows, roles and nicknames.",
                "icon": "✅",
                "version": "0.1.0",
                "is_core": False,
                "is_available": True,
                "sort_order": 20,
            },
            {
                "module_key": "moderation",
                "name": "Moderation",
                "description": "Warnings, timeouts, kicks and bans.",
                "icon": "⚖️",
                "version": "0.1.0",
                "is_core": False,
                "is_available": True,
                "sort_order": 30,
            },
            {
                "module_key": "translator",
                "name": "Translator",
                "description": "Multilingual channel and message translation.",
                "icon": "🌐",
                "version": "0.1.0",
                "is_core": False,
                "is_available": True,
                "sort_order": 40,
            },
            {
                "module_key": "logging",
                "name": "Logging",
                "description": "Discord event and administration logs.",
                "icon": "📋",
                "version": "0.1.0",
                "is_core": False,
                "is_available": True,
                "sort_order": 50,
            },
            {
                "module_key": "reaction_roles",
                "name": "Reaction Roles",
                "description": "Self-service roles through buttons and reactions.",
                "icon": "🎭",
                "version": "0.1.0",
                "is_core": False,
                "is_available": True,
                "sort_order": 60,
            },
            {
                "module_key": "tickets",
                "name": "Tickets",
                "description": "Private support and administration tickets.",
                "icon": "🎫",
                "version": "0.1.0",
                "is_core": False,
                "is_available": True,
                "sort_order": 70,
            },
            {
                "module_key": "analytics",
                "name": "Analytics",
                "description": "Server activity and module statistics.",
                "icon": "📊",
                "version": "0.1.0",
                "is_core": False,
                "is_available": True,
                "sort_order": 80,
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("guild_modules", schema="modules")
    op.drop_table("catalog", schema="modules")
