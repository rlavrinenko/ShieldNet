from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005_member_actions"
down_revision: Union[str, None] = "0004_members_core"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    postgresql.ENUM(
        "send_dm", "rename", "kick", "ban", "add_role", "remove_role",
        "shieldnet_block", "shieldnet_unblock",
        name="member_action_type", schema="discord"
    ).create(bind, checkfirst=True)
    postgresql.ENUM(
        "pending", "processing", "completed", "failed",
        name="member_action_status", schema="discord"
    ).create(bind, checkfirst=True)

    action_type = postgresql.ENUM(
        "send_dm", "rename", "kick", "ban", "add_role", "remove_role",
        "shieldnet_block", "shieldnet_unblock",
        name="member_action_type", schema="discord", create_type=False
    )
    action_status = postgresql.ENUM(
        "pending", "processing", "completed", "failed",
        name="member_action_status", schema="discord", create_type=False
    )

    op.create_table(
        "member_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("discord_user_id", sa.BigInteger(), nullable=False),
        sa.Column("action_type", action_type, nullable=False),
        sa.Column("payload", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("status", action_status, server_default="pending", nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True)),
        sa.Column("result_message", sa.Text()),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["requested_by"], ["core.users.id"], ondelete="SET NULL"),
        schema="discord",
    )
    op.create_index(
        "ix_discord_member_actions_queue",
        "member_actions",
        ["guild_id", "status", "created_at"],
        schema="discord",
    )


def downgrade() -> None:
    op.drop_table("member_actions", schema="discord")
