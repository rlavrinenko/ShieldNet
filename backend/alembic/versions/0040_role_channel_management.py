"""ShieldNet v5.5 Role & Channel Management."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="0040_role_channel_management"
down_revision="0039_moderation_center"
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind(); insp=sa.inspect(bind)
    if not insp.has_table("structure_changes", schema="discord"):
        op.create_table("structure_changes",
            sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True,server_default=sa.text("gen_random_uuid()")),
            sa.Column("guild_id",sa.BigInteger(),nullable=False),
            sa.Column("object_type",sa.String(32),nullable=False),
            sa.Column("operation",sa.String(32),nullable=False),
            sa.Column("target_id",sa.BigInteger()),
            sa.Column("payload",postgresql.JSONB(),nullable=False,server_default=sa.text("'{}'::jsonb")),
            sa.Column("preview",postgresql.JSONB(),nullable=False,server_default=sa.text("'{}'::jsonb")),
            sa.Column("status",sa.String(24),nullable=False,server_default="pending"),
            sa.Column("requested_by",postgresql.UUID(as_uuid=True),sa.ForeignKey("core.users.id",ondelete="SET NULL")),
            sa.Column("result_message",sa.Text()),
            sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
            sa.Column("started_at",sa.DateTime(timezone=True)),sa.Column("completed_at",sa.DateTime(timezone=True)),
            schema="discord")
        op.create_index("ix_discord_structure_changes_queue","structure_changes",["guild_id","status","created_at"],schema="discord")
    if not insp.has_table("bulk_role_operations", schema="discord"):
        op.create_table("bulk_role_operations",
            sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True,server_default=sa.text("gen_random_uuid()")),
            sa.Column("guild_id",sa.BigInteger(),nullable=False),sa.Column("discord_role_id",sa.BigInteger(),nullable=False),
            sa.Column("operation",sa.String(16),nullable=False),
            sa.Column("member_ids",postgresql.JSONB(),nullable=False,server_default=sa.text("'[]'::jsonb")),
            sa.Column("status",sa.String(24),nullable=False,server_default="pending"),
            sa.Column("requested_by",postgresql.UUID(as_uuid=True),sa.ForeignKey("core.users.id",ondelete="SET NULL")),
            sa.Column("processed_count",sa.Integer(),nullable=False,server_default="0"),
            sa.Column("failed_count",sa.Integer(),nullable=False,server_default="0"),
            sa.Column("result",postgresql.JSONB(),nullable=False,server_default=sa.text("'{}'::jsonb")),
            sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
            sa.Column("completed_at",sa.DateTime(timezone=True)),schema="discord")
        op.create_index("ix_discord_bulk_role_operations_queue","bulk_role_operations",["guild_id","status","created_at"],schema="discord")

def downgrade():
    op.drop_table("bulk_role_operations",schema="discord")
    op.drop_table("structure_changes",schema="discord")
