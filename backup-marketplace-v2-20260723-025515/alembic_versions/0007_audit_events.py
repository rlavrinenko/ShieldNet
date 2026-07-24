from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0007_audit_events"
down_revision: Union[str, None] = "0006_guild_roles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("guild_id", sa.BigInteger()),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("target_type", sa.String(64)),
        sa.Column("target_id", sa.String(255)),
        sa.Column("payload", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("result", sa.String(32), server_default="created", nullable=False),
        sa.Column("message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["core.users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        schema="audit",
    )
    op.create_index(
        "ix_audit_events_guild_created",
        "audit_events",
        ["guild_id", "created_at"],
        schema="audit",
    )


def downgrade() -> None:
    op.drop_table("audit_events", schema="audit")
