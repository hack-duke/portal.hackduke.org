"""add integer to questiontype enum

Revision ID: c2e4ff554c6a
Revises: 2661667c6cf6
Create Date: 2026-01-24 19:55:57.973129

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2e4ff554c6a'
down_revision: Union[str, Sequence[str], None] = '2661667c6cf6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE questiontype ADD VALUE 'INTEGER'")
    op.execute("ALTER TYPE questiontype ADD VALUE 'FLOAT'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
