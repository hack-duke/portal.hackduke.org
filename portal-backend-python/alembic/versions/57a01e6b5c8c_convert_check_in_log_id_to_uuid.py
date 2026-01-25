"""convert_check_in_log_id_to_uuid

Revision ID: 57a01e6b5c8c
Revises: c2e4ff554c6a
Create Date: 2026-01-24 20:32:57.083648

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '57a01e6b5c8c'
down_revision: Union[str, Sequence[str], None] = 'c2e4ff554c6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.drop_column('check_in_log', 'id')
    
    op.add_column('check_in_log', 
        sa.Column('id', postgresql.UUID(as_uuid=True), 
                  server_default=sa.text("uuid_generate_v4()"), 
                  nullable=False)
    )
    op.create_primary_key('check_in_log_pkey', 'check_in_log', ['id'])


def downgrade() -> None:
    pass