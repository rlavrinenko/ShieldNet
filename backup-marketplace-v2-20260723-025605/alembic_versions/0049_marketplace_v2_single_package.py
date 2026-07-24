"""Marketplace v2: one current package per plugin.

Revision ID: 9f2a7c000049
Revises: 8d5fb9400048
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = "9f2a7c000049"
down_revision = "8d5fb9400048"
branch_labels = None
depends_on = None


def _columns() -> set[str]:
    return {
        column["name"]
        for column in inspect(op.get_bind()).get_columns(
            "marketplace_items", schema="plugins"
        )
    }


def upgrade():
    existing = _columns()
    additions = {
        "version": sa.Column("version", sa.String(40)),
        "min_core_version": sa.Column("min_core_version", sa.String(40)),
        "package_url": sa.Column("package_url", sa.String(500)),
        "checksum_sha256": sa.Column("checksum_sha256", sa.String(64)),
        "signature": sa.Column("signature", sa.Text()),
        "release_notes": sa.Column("release_notes", sa.Text()),
        "manifest": sa.Column(
            "manifest",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        "status": sa.Column(
            "status", sa.String(24), nullable=False, server_default="draft"
        ),
    }
    for name, column in additions.items():
        if name not in existing:
            op.add_column(
                "marketplace_items", column, schema="plugins"
            )

    op.execute(
        """
        UPDATE plugins.marketplace_items AS mi
        SET version = mv.version,
            min_core_version = mv.min_core_version,
            package_url = mv.package_url,
            checksum_sha256 = mv.checksum_sha256,
            signature = mv.signature,
            release_notes = mv.changelog,
            manifest = COALESCE(mv.manifest, '{}'::jsonb)
        FROM (
            SELECT DISTINCT ON (marketplace_item_id)
                marketplace_item_id,
                version,
                min_core_version,
                package_url,
                checksum_sha256,
                signature,
                changelog,
                manifest
            FROM plugins.marketplace_versions
            ORDER BY marketplace_item_id, released_at DESC
        ) AS mv
        WHERE mv.marketplace_item_id = mi.id
          AND mi.version IS NULL
        """
    )

    op.execute(
        """
        UPDATE plugins.marketplace_items
        SET status = CASE
            WHEN published THEN 'published'
            WHEN verified THEN 'verified'
            ELSE 'draft'
        END
        """
    )


def downgrade():
    for name in (
        "status",
        "manifest",
        "release_notes",
        "signature",
        "checksum_sha256",
        "package_url",
        "min_core_version",
        "version",
    ):
        if name in _columns():
            op.drop_column(
                "marketplace_items", name, schema="plugins"
            )
