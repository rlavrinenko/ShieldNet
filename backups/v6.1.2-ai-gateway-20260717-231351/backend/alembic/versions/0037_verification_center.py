"""ShieldNet v5.2 Verification Center.

Revision ID: 0037_verification_center
Revises: 0036_members_center
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "0037_verification_center"
down_revision = "0036_members_center"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("requests", sa.Column("evidence_url", sa.String(1000)), schema="verification")
    op.add_column("requests", sa.Column("submitted_language", sa.String(16)), schema="verification")
    op.add_column("requests", sa.Column("applicant_comment", sa.Text()), schema="verification")
    op.add_column("requests", sa.Column("change_request_reason", sa.Text()), schema="verification")
    op.add_column("requests", sa.Column("revision_count", sa.Integer(), nullable=False, server_default="0"), schema="verification")
    op.add_column("requests", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), schema="verification")
    op.create_table("decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("verification.requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), sa.ForeignKey("discord.guilds.guild_id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="verification")
    op.create_index("ix_verification_decisions_request", "decisions", ["request_id"], schema="verification")
    op.create_index("ix_verification_decisions_guild", "decisions", ["guild_id"], schema="verification")
    op.create_index("ix_verification_requests_guild_updated", "requests", ["guild_id", "updated_at"], schema="verification")

def downgrade():
    op.drop_index("ix_verification_requests_guild_updated", table_name="requests", schema="verification")
    op.drop_index("ix_verification_decisions_guild", table_name="decisions", schema="verification")
    op.drop_index("ix_verification_decisions_request", table_name="decisions", schema="verification")
    op.drop_table("decisions", schema="verification")
    for name in ["updated_at", "revision_count", "change_request_reason", "applicant_comment", "submitted_language", "evidence_url"]:
        op.drop_column("requests", name, schema="verification")
