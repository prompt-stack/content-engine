"""ensure captures table exists

Revision ID: 1efe193e2389
Revises: e4824ed62e14
Create Date: 2025-10-17 19:04:23.475013

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '1efe193e2389'
down_revision: Union[str, None] = 'e4824ed62e14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create captures table if it doesn't exist."""
    conn = op.get_bind()
    inspector = inspect(conn)

    # Check if captures table exists
    if 'captures' not in inspector.get_table_names():
        # Create captures table with final schema
        op.create_table(
            'captures',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=True),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('meta', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

        # Create indexes
        op.create_index('ix_captures_user_id', 'captures', ['user_id'], unique=False)
        op.create_index('ix_captures_created_at', 'captures', ['created_at'], unique=False)
        op.create_index('ix_captures_title', 'captures', ['title'], unique=False)

        print("✅ Created captures table with all indexes")
    else:
        print("ℹ️  captures table already exists, skipping creation")


def downgrade() -> None:
    """Drop captures table if it exists."""
    conn = op.get_bind()
    inspector = inspect(conn)

    if 'captures' in inspector.get_table_names():
        # Drop indexes
        op.drop_index('ix_captures_title', table_name='captures')
        op.drop_index('ix_captures_created_at', table_name='captures')
        op.drop_index('ix_captures_user_id', table_name='captures')

        # Drop table
        op.drop_table('captures')

        print("✅ Dropped captures table and all indexes")
    else:
        print("ℹ️  captures table doesn't exist, skipping drop")
