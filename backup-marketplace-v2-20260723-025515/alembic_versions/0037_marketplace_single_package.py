"""Marketplace single current package.

Revision ID: 0037_marketplace_single_package
Revises: 0036_members_center
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision='0037_marketplace_single_package'
down_revision='0036_members_center'
branch_labels=None
depends_on=None

def upgrade():
    for name, column in [
        ('version', sa.Column('version', sa.String(40))),
        ('min_core_version', sa.Column('min_core_version', sa.String(40))),
        ('package_url', sa.Column('package_url', sa.String(500))),
        ('checksum_sha256', sa.Column('checksum_sha256', sa.String(64))),
        ('signature', sa.Column('signature', sa.Text())),
        ('release_notes', sa.Column('release_notes', sa.Text())),
    ]:
        op.add_column('marketplace_items', column, schema='plugins')
    op.add_column('marketplace_items', sa.Column('manifest', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")), schema='plugins')
    op.add_column('marketplace_items', sa.Column('status', sa.String(24), nullable=False, server_default='draft'), schema='plugins')
    op.execute("""
    UPDATE plugins.marketplace_items i
    SET version=v.version, min_core_version=v.min_core_version,
        package_url=v.package_url, checksum_sha256=v.checksum_sha256,
        signature=v.signature, release_notes=v.changelog, manifest=v.manifest,
        status=CASE WHEN i.published THEN 'published' WHEN i.verified THEN 'verified' ELSE 'draft' END
    FROM LATERAL (
        SELECT * FROM plugins.marketplace_versions mv
        WHERE mv.marketplace_item_id=i.id
        ORDER BY mv.released_at DESC LIMIT 1
    ) v
    """)
    op.execute("""UPDATE plugins.marketplace_items SET status=CASE WHEN published THEN 'published' WHEN verified THEN 'verified' ELSE 'draft' END WHERE version IS NULL""")

def downgrade():
    for name in ['status','manifest','release_notes','signature','checksum_sha256','package_url','min_core_version','version']:
        op.drop_column('marketplace_items', name, schema='plugins')
