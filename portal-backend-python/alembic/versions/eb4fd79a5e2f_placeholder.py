"""Placeholder migration for database state

This migration file represents a migration that was applied to the database
but the file was not committed to version control. This is a placeholder to
establish the migration chain.

Revision ID: eb4fd79a5e2f
Revises: c767c615424d
Create Date: 2025-02-20 12:00:00.000000

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = 'eb4fd79a5e2f'
down_revision: Union[str, Sequence[str], None] = 'c767c615424d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # This is a placeholder migration - no changes needed
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # This is a placeholder migration - no changes needed
    pass
