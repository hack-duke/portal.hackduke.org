"""Support the authoritative DuQuantum final-team workbook.

Revision ID: 20261019dqft
Revises: 20261018dqtm
Create Date: 2026-10-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261019dqft"
down_revision: Union[str, Sequence[str], None] = "20261018dqtm"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "event_team", sa.Column("formation_source", sa.String(100), nullable=True)
    )
    op.add_column(
        "event_team",
        sa.Column("additional_teammates_detail", sa.String(500), nullable=True),
    )
    op.alter_column(
        "event_team",
        "source_submitted_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )
    op.create_unique_constraint(
        "uq_event_team_event_number", "event_team", ["event_id", "team_number"]
    )
    op.add_column(
        "event_team_member", sa.Column("display_name", sa.String(500), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("event_team_member", "display_name")
    op.drop_constraint("uq_event_team_event_number", "event_team", type_="unique")
    op.execute(
        "UPDATE event_team SET source_submitted_at = created_at "
        "WHERE source_submitted_at IS NULL"
    )
    op.alter_column(
        "event_team",
        "source_submitted_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.drop_column("event_team", "additional_teammates_detail")
    op.drop_column("event_team", "formation_source")
