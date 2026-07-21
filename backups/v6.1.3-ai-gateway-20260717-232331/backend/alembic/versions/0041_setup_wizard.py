"""ShieldNet v5.6 Server Setup Wizard."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="0041_setup_wizard"
down_revision="0040_role_channel_management"
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind(); insp=sa.inspect(bind)
    if not insp.has_table("setup_sessions",schema="discord"):
        op.create_table("setup_sessions",
          sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True,server_default=sa.text("gen_random_uuid()")),
          sa.Column("guild_id",sa.BigInteger(),sa.ForeignKey("discord.guilds.guild_id",ondelete="CASCADE"),nullable=False),
          sa.Column("status",sa.String(24),nullable=False,server_default="draft"),
          sa.Column("template_key",sa.String(32),nullable=False,server_default="standard"),
          sa.Column("preferred_language",sa.String(16),nullable=False,server_default="en"),
          sa.Column("features",postgresql.JSONB(),nullable=False,server_default=sa.text("'{}'::jsonb")),
          sa.Column("diagnostics",postgresql.JSONB(),nullable=False,server_default=sa.text("'{}'::jsonb")),
          sa.Column("configuration",postgresql.JSONB(),nullable=False,server_default=sa.text("'{}'::jsonb")),
          sa.Column("created_by",postgresql.UUID(as_uuid=True),sa.ForeignKey("core.users.id",ondelete="SET NULL")),
          sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
          sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
          sa.Column("completed_at",sa.DateTime(timezone=True)),schema="discord")
        op.create_index("ix_discord_setup_sessions_guild_status","setup_sessions",["guild_id","status"],schema="discord")
    if not insp.has_table("setup_items",schema="discord"):
        op.create_table("setup_items",
          sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True,server_default=sa.text("gen_random_uuid()")),
          sa.Column("session_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("discord.setup_sessions.id",ondelete="CASCADE"),nullable=False),
          sa.Column("item_key",sa.String(64),nullable=False),sa.Column("object_type",sa.String(24),nullable=False),
          sa.Column("display_name",sa.String(128),nullable=False),
          sa.Column("payload",postgresql.JSONB(),nullable=False,server_default=sa.text("'{}'::jsonb")),
          sa.Column("required",sa.Boolean(),nullable=False,server_default=sa.text("true")),
          sa.Column("position",sa.Integer(),nullable=False,server_default="0"),
          sa.Column("change_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("discord.structure_changes.id",ondelete="SET NULL")),
          sa.Column("status",sa.String(24),nullable=False,server_default="planned"),
          sa.Column("discord_object_id",sa.BigInteger()),sa.Column("error_message",sa.Text()),
          sa.UniqueConstraint("session_id","item_key",name="uq_discord_setup_item_key"),schema="discord")
        op.create_index("ix_discord_setup_items_session","setup_items",["session_id","position"],schema="discord")
def downgrade():
    op.drop_table("setup_items",schema="discord"); op.drop_table("setup_sessions",schema="discord")
