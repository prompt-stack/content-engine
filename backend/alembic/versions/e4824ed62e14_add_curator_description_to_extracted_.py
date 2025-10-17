"""add_curator_description_to_extracted_links

Revision ID: e4824ed62e14
Revises: 25b39fc0adaa
Create Date: 2025-10-17 18:11:30.174867

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4824ed62e14'
down_revision: Union[str, None] = '25b39fc0adaa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add curator_description column to extracted_links table
    op.add_column('extracted_links', sa.Column('curator_description', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove curator_description column from extracted_links table
    op.drop_column('extracted_links', 'curator_description')
