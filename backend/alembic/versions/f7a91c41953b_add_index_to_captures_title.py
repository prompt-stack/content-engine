"""add_index_to_captures_title

Revision ID: f7a91c41953b
Revises: a27f6d4becae
Create Date: 2025-10-16 17:15:44.687451

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f7a91c41953b'
down_revision: Union[str, None] = 'a27f6d4becae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add index to title column for better search performance
    op.create_index('ix_captures_title', 'captures', ['title'], unique=False)


def downgrade() -> None:
    # Remove index from title column
    op.drop_index('ix_captures_title', table_name='captures')
