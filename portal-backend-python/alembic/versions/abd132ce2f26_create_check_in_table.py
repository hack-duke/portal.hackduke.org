"""create check in table

Revision ID: abd132ce2f26
Revises: 78d9dac87570
Create Date: 2026-01-18 21:49:05.078529

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abd132ce2f26'
down_revision: Union[str, Sequence[str], None] = '78d9dac87570'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'check_in',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, unique=True),
        sa.Column('user_id', sa.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('check_in_time', sa.DateTime(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())"))
    )
    # Create indexes
    op.create_index(op.f('ix_check_in_event_type'), 'check_in', ['event_type'], unique=False)
    op.create_index(op.f('ix_check_in_user_id'), 'check_in', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_check_in_user_id'), table_name='check_in')
    op.drop_index(op.f('ix_check_in_event_type'), table_name='check_in')
    op.drop_table('check_in')
