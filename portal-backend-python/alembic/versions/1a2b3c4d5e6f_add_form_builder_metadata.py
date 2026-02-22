"""Add form builder metadata fields to form table

Revision ID: 1a2b3c4d5e6f
Revises: d1ca1a1f2b40
Create Date: 2026-02-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a2b3c4d5e6f'
down_revision: Union[str, Sequence[str], None] = 'd1ca1a1f2b40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add title, closed_message_title, closed_message_body, is_db_driven columns."""
    op.add_column('form', sa.Column('title', sa.String(), nullable=True))
    op.add_column('form', sa.Column('closed_message_title', sa.String(), nullable=True))
    op.add_column('form', sa.Column('closed_message_body', sa.Text(), nullable=True))
    op.add_column('form', sa.Column('is_db_driven', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade() -> None:
    """Downgrade schema - remove the new columns."""
    op.drop_column('form', 'is_db_driven')
    op.drop_column('form', 'closed_message_body')
    op.drop_column('form', 'closed_message_title')
    op.drop_column('form', 'title')
