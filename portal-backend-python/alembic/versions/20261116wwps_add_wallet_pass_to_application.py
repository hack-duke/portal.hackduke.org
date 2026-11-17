"""Add WalletWallet check-in pass columns to application.

Revision ID: 20261116wwps
Revises: 20261024dqsz
Create Date: 2026-11-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261116wwps"
down_revision: Union[str, Sequence[str], None] = "20261024dqsz"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("application", sa.Column("wallet_pass_serial", sa.String(), nullable=True))
    op.add_column("application", sa.Column("wallet_pass_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("application", "wallet_pass_url")
    op.drop_column("application", "wallet_pass_serial")
