"""merge heads

Revision ID: 8e3af3c9c590
Revises: abd132ce2f26, 31748bd66d0b
Create Date: 2026-01-24 06:11:08.452926

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e3af3c9c590'
down_revision: Union[str, Sequence[str], None] = ('abd132ce2f26', '31748bd66d0b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
