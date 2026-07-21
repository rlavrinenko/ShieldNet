"""Add plugin marketplace foundation.

Revision ID: 4a1d8e7c0045
Revises: 220823d910b2
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "4a1d8e7c0045"
down_revision = "220823d910b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "marketplace_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plugin_key", sa.String(96), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column("category", sa.String(64), nullable=False, server_default="other"),
        sa.Column("author", sa.String(160)),
        sa.Column("homepage_url", sa.String(500)),
        sa.Column("repository_url", sa.String(500)),
        sa.Column("icon_url", sa.String(500)),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("downloads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("plugin_key", name="uq_plugins_marketplace_items_plugin_key"),
        schema="plugins",
    )
    op.create_index(
        "ix_plugins_marketplace_items_category",
        "marketplace_items",
        ["category"],
        schema="plugins",
    )
    op.create_index(
        "ix_plugins_marketplace_items_published",
        "marketplace_items",
        ["published"],
        schema="plugins",
    )

    op.create_table(
        "marketplace_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "marketplace_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plugins.marketplace_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("min_core_version", sa.String(40)),
        sa.Column("package_url", sa.String(500), nullable=False),
        sa.Column("checksum_sha256", sa.String(64), nullable=False),
        sa.Column("signature", sa.Text()),
        sa.Column("changelog", sa.Text()),
        sa.Column("manifest", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "marketplace_item_id",
            "version",
            name="uq_plugins_marketplace_versions_item_version",
        ),
        schema="plugins",
    )
    op.create_index(
        "ix_plugins_marketplace_versions_item",
        "marketplace_versions",
        ["marketplace_item_id"],
        schema="plugins",
    )

    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='shieldnet_backend') THEN
        GRANT SELECT,INSERT,UPDATE,DELETE ON
          plugins.marketplace_items,
          plugins.marketplace_versions
        TO shieldnet_backend;
      END IF;
    END $$;""")


def downgrade() -> None:
    op.drop_index(
        "ix_plugins_marketplace_versions_item",
        table_name="marketplace_versions",
        schema="plugins",
    )
    op.drop_table("marketplace_versions", schema="plugins")
    op.drop_index(
        "ix_plugins_marketplace_items_published",
        table_name="marketplace_items",
        schema="plugins",
    )
    op.drop_index(
        "ix_plugins_marketplace_items_category",
        table_name="marketplace_items",
        schema="plugins",
    )
    op.drop_table("marketplace_items", schema="plugins")
