"""rename_metadata_to_meta_in_captures

Revision ID: a27f6d4becae
Revises: 8d3e0fed9597
Create Date: 2025-10-16 12:13:11.612179

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a27f6d4becae'
down_revision: Union[str, None] = '8d3e0fed9597'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename metadata column to meta to avoid SQLAlchemy reserved name
    op.alter_column('captures', 'metadata', new_column_name='meta')


def downgrade() -> None:
    # Rename meta back to metadata
    op.alter_column('captures', 'meta', new_column_name='metadata')
