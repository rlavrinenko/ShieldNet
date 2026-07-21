"""create core authentication tables

Revision ID: 0001_core_auth
Revises:
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_core_auth"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_status = postgresql.ENUM(
        "active",
        "blocked",
        "pending_email",
        "deleted",
        name="user_status",
        schema="core",
    )
    global_role = postgresql.ENUM(
        "superadmin",
        "admin",
        "moderator",
        "advertising_partner",
        name="global_role",
        schema="core",
    )
    two_factor_type = postgresql.ENUM(
        "google",
        "telegram",
        name="two_factor_type",
        schema="core",
    )

    bind = op.get_bind()
    user_status.create(bind, checkfirst=True)
    global_role.create(bind, checkfirst=True)
    two_factor_type.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("login", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("display_name", sa.String(length=128), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("discord_user_id", sa.BigInteger(), nullable=True),
        sa.Column("status", user_status, server_default="pending_email", nullable=False),
        sa.Column("email_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("discord_user_id", name="uq_core_users_discord_user_id"),
        sa.UniqueConstraint("email", name="uq_core_users_email"),
        sa.UniqueConstraint("login", name="uq_core_users_login"),
        schema="core",
    )
    op.create_index("ix_core_users_status", "users", ["status"], schema="core")

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("permission_key", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=64), server_default="system", nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_permissions"),
        sa.UniqueConstraint("permission_key", name="uq_core_permissions_key"),
        schema="core",
    )

    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", global_role, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["core.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_user_roles"),
        sa.UniqueConstraint("user_id", "role", name="uq_core_user_roles_user_role"),
        schema="core",
    )

    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("role", global_role, nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["core.permissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_role_permissions"),
        sa.UniqueConstraint(
            "role",
            "permission_id",
            name="uq_core_role_permissions_role_permission",
        ),
        schema="core",
    )

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["core.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_sessions"),
        sa.UniqueConstraint("token_hash", name="uq_core_sessions_token_hash"),
        schema="core",
    )
    op.create_index("ix_core_sessions_user_id", "sessions", ["user_id"], schema="core")
    op.create_index("ix_core_sessions_expires_at", "sessions", ["expires_at"], schema="core")

    op.create_table(
        "two_factor_methods",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("method_type", two_factor_type, nullable=False),
        sa.Column("secret_encrypted", sa.Text(), nullable=True),
        sa.Column("telegram_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["core.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_two_factor_methods"),
        sa.UniqueConstraint("user_id", "method_type", name="uq_core_two_factor_user_method"),
        schema="core",
    )

    op.create_table(
        "login_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("successful", sa.Boolean(), nullable=False),
        sa.Column("failure_reason", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["core.users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_login_attempts"),
        schema="core",
    )
    op.create_index("ix_core_login_attempts_created_at", "login_attempts", ["created_at"], schema="core")
    op.create_index("ix_core_login_attempts_email", "login_attempts", ["email"], schema="core")

    for table_name in ("email_verification_tokens", "password_reset_tokens"):
        op.create_table(
            table_name,
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("token_hash", sa.String(length=255), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["core.users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id", name=f"pk_{table_name}"),
            schema="core",
        )

    op.create_index(
        "ix_core_email_verification_expires_at",
        "email_verification_tokens",
        ["expires_at"],
        schema="core",
    )
    op.create_index(
        "ix_core_password_reset_expires_at",
        "password_reset_tokens",
        ["expires_at"],
        schema="core",
    )


def downgrade() -> None:
    for table_name in (
        "password_reset_tokens",
        "email_verification_tokens",
        "login_attempts",
        "two_factor_methods",
        "sessions",
        "role_permissions",
        "user_roles",
        "permissions",
        "users",
    ):
        op.drop_table(table_name, schema="core")

    bind = op.get_bind()
    postgresql.ENUM(name="two_factor_type", schema="core").drop(bind, checkfirst=True)
    postgresql.ENUM(name="global_role", schema="core").drop(bind, checkfirst=True)
    postgresql.ENUM(name="user_status", schema="core").drop(bind, checkfirst=True)
