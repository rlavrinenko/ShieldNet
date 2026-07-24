"""Plugin API audit logs.

Revision ID: 0052
Revises: 0051
"""

from alembic import op
import sqlalchemy as sa


revision = "0052"
down_revision = "b8d4e2000051"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_audit_logs",
        sa.Column(
            "id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "request_id",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "plugin_key",
            sa.String(length=128),
            nullable=True,
        ),
        sa.Column(
            "guild_id",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "generation",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "token_id",
            sa.String(length=64),
            nullable=True,
        ),
        sa.Column(
            "capability",
            sa.String(length=128),
            nullable=True,
        ),
        sa.Column(
            "method",
            sa.String(length=16),
            nullable=False,
        ),
        sa.Column(
            "path",
            sa.String(length=512),
            nullable=False,
        ),
        sa.Column(
            "status_code",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "duration_ms",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "authenticated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "allowed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "client_ip",
            sa.String(length=64),
            nullable=True,
        ),
        sa.Column(
            "user_agent",
            sa.String(length=512),
            nullable=True,
        ),
        sa.Column(
            "error_detail",
            sa.String(length=1000),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        schema="plugins",
    )

    op.create_index(
        "ix_plugins_api_audit_logs_created_at",
        "api_audit_logs",
        ["created_at"],
        schema="plugins",
    )

    op.create_index(
        "ix_plugins_api_audit_logs_plugin_guild",
        "api_audit_logs",
        ["plugin_key", "guild_id"],
        schema="plugins",
    )

    op.create_index(
        "ix_plugins_api_audit_logs_request_id",
        "api_audit_logs",
        ["request_id"],
        schema="plugins",
    )

    op.create_index(
        "ix_plugins_api_audit_logs_status",
        "api_audit_logs",
        ["status_code"],
        schema="plugins",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_plugins_api_audit_logs_status",
        table_name="api_audit_logs",
        schema="plugins",
    )

    op.drop_index(
        "ix_plugins_api_audit_logs_request_id",
        table_name="api_audit_logs",
        schema="plugins",
    )

    op.drop_index(
        "ix_plugins_api_audit_logs_plugin_guild",
        table_name="api_audit_logs",
        schema="plugins",
    )

    op.drop_index(
        "ix_plugins_api_audit_logs_created_at",
        table_name="api_audit_logs",
        schema="plugins",
    )

    op.drop_table(
        "api_audit_logs",
        schema="plugins",
    )
