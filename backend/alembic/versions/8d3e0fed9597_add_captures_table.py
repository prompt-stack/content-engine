"""add_captures_table

Revision ID: 8d3e0fed9597
Revises: ac4b2ff42914
Create Date: 2025-10-16 11:54:29.510008

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8d3e0fed9597'
down_revision: Union[str, None] = 'ac4b2ff42914'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create captures table
    op.create_table(
        'captures',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index(op.f('ix_captures_user_id'), 'captures', ['user_id'], unique=False)
    op.create_index(op.f('ix_captures_created_at'), 'captures', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_captures_created_at'), table_name='captures')
    op.drop_index(op.f('ix_captures_user_id'), table_name='captures')

    # Drop table
    op.drop_table('captures')
