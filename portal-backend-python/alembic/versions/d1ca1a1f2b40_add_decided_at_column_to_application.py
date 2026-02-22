"""add decided_at column to application

Revision ID: d1ca1a1f2b40
Revises: eb4fd79a5e2f
Create Date: 2026-01-07 00:20:21.359946

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1ca1a1f2b40'
down_revision: Union[str, Sequence[str], None] = 'eb4fd79a5e2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # This migration was already applied by eb4fd79a5e2f, so this is a no-op
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # This migration was already applied by eb4fd79a5e2f, so this is a no-op
    pass
