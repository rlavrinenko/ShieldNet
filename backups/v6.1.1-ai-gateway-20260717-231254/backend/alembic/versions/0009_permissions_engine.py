"""create permissions engine

Revision ID: 0009_permissions_engine
Revises: 0007_audit_events
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0009_permissions_engine"
down_revision: Union[str, None] = "0007_audit_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    op.execute("CREATE SCHEMA IF NOT EXISTS permissions")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    permission_name_enum = postgresql.ENUM(
        "view",
        "manage",
        "execute",
        "configure",
        name="permission_name",
        schema="permissions",
    )
    permission_name_enum.create(bind, checkfirst=True)

    permission_effect_enum = postgresql.ENUM(
        "allow",
        "deny",
        name="permission_effect",
        schema="permissions",
    )
    permission_effect_enum.create(bind, checkfirst=True)

    permission_name = postgresql.ENUM(
        "view",
        "manage",
        "execute",
        "configure",
        name="permission_name",
        schema="permissions",
        create_type=False,
    )

    permission_effect = postgresql.ENUM(
        "allow",
        "deny",
        name="permission_effect",
        schema="permissions",
        create_type=False,
    )

    inspector = sa.inspect(bind)

    if "permission_rules" not in inspector.get_table_names(
        schema="permissions"
    ):
        op.create_table(
            "permission_rules",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
            ),
            sa.Column(
                "guild_id",
                sa.BigInteger(),
                nullable=False,
            ),
            sa.Column(
                "module_key",
                sa.String(64),
                nullable=False,
            ),
            sa.Column(
                "permission",
                permission_name,
                nullable=False,
            ),
            sa.Column(
                "effect",
                permission_effect,
                server_default="allow",
                nullable=False,
            ),
            sa.Column(
                "subject_type",
                sa.String(32),
                nullable=False,
            ),
            sa.Column(
                "subject_value",
                sa.String(128),
                nullable=False,
            ),
            sa.Column(
                "enabled",
                sa.Boolean(),
                server_default=sa.text("true"),
                nullable=False,
            ),
            sa.Column(
                "priority",
                sa.Integer(),
                server_default="100",
                nullable=False,
            ),
            sa.Column(
                "created_by",
                postgresql.UUID(as_uuid=True),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["guild_id"],
                ["discord.guilds.guild_id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["created_by"],
                ["core.users.id"],
                ondelete="SET NULL",
            ),
            sa.PrimaryKeyConstraint(
                "id",
                name="pk_permissions_rules",
            ),
            sa.UniqueConstraint(
                "guild_id",
                "module_key",
                "permission",
                "subject_type",
                "subject_value",
                name="uq_permissions_rule",
            ),
            schema="permissions",
        )

    indexes = {
        item["name"]
        for item in inspector.get_indexes(
            "permission_rules",
            schema="permissions",
        )
    }

    if "ix_permissions_lookup" not in indexes:
        op.create_index(
            "ix_permissions_lookup",
            "permission_rules",
            ["guild_id", "module_key", "permission"],
            schema="permissions",
        )

    op.execute(
        """
        INSERT INTO permissions.permission_rules (
            id,
            guild_id,
            module_key,
            permission,
            effect,
            subject_type,
            subject_value,
            enabled,
            priority
        )
        SELECT
            gen_random_uuid(),
            guild_id,
            '*',
            permission_name,
            'allow',
            'shieldnet_role',
            'moderator',
            true,
            100
        FROM discord.guilds
        CROSS JOIN (
            VALUES
                ('view'::permissions.permission_name),
                ('execute'::permissions.permission_name)
        ) AS default_permissions(permission_name)
        ON CONFLICT (
            guild_id,
            module_key,
            permission,
            subject_type,
            subject_value
        ) DO NOTHING
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "permission_rules" in inspector.get_table_names(
        schema="permissions"
    ):
        indexes = {
            item["name"]
            for item in inspector.get_indexes(
                "permission_rules",
                schema="permissions",
            )
        }

        if "ix_permissions_lookup" in indexes:
            op.drop_index(
                "ix_permissions_lookup",
                table_name="permission_rules",
                schema="permissions",
            )

        op.drop_table(
            "permission_rules",
            schema="permissions",
        )

    postgresql.ENUM(
        name="permission_effect",
        schema="permissions",
    ).drop(bind, checkfirst=True)

    postgresql.ENUM(
        name="permission_name",
        schema="permissions",
    ).drop(bind, checkfirst=True)
