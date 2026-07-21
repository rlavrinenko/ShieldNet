"""merge plugin platform and settings engine heads

Revision ID: 220823d910b2
Revises: 0044_core_settings_engine, 0044_plugin_platform_foundation
Create Date: 2026-07-20 14:32:41.148441
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '220823d910b2'
down_revision: Union[str, None] = ('0044_core_settings_engine', '0044_plugin_platform_foundation')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
