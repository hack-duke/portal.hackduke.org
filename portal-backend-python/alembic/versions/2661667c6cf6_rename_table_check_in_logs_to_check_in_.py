"""rename table check_in_logs to check_in_log

Revision ID: 2661667c6cf6
Revises: 8e3af3c9c590
Create Date: 2026-01-24 06:13:47.420770

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2661667c6cf6'
down_revision: Union[str, Sequence[str], None] = '8e3af3c9c590'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table("check_in_logs", "check_in_log")


def downgrade() -> None:
    """Downgrade schema."""
    op.rename_table("check_in_log", "check_in_logs")
