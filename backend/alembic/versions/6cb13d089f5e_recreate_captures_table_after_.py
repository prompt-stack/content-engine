"""recreate_captures_table_after_accidental_drop

Revision ID: 6cb13d089f5e
Revises: 3c6812937dfb
Create Date: 2025-10-18 08:44:42.973743

This migration recreates the captures table that was accidentally dropped
in migration 3c6812937dfb due to an auto-generation error.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '6cb13d089f5e'
down_revision: Union[str, None] = '3c6812937dfb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Recreate captures table if it doesn't exist."""
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

        print("✅ Recreated captures table with all indexes")
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
