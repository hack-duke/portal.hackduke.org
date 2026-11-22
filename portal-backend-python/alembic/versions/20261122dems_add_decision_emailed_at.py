"""add decision_emailed_at column to application

Revision ID: 20261122dems
Revises: 20261024dqsz
Create Date: 2026-11-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20261122dems"
down_revision: Union[str, Sequence[str], None] = "20261024dqsz"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "application",
        sa.Column("decision_emailed_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("application", "decision_emailed_at")
