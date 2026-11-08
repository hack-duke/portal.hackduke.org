"""Add single-use event account setup tokens.

Revision ID: 20261007dqas
Revises: 20261006dqe1
Create Date: 2026-10-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20261007dqas"
down_revision: Union[str, Sequence[str], None] = "20261006dqe1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "event_account_setup",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("registration_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("auth0_user_id", sa.String(length=255), nullable=False),
        sa.Column("token_digest", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["event_id"], ["event.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["registration_id", "event_id"],
            ["event_registration.id", "event_registration.event_id"],
            name="fk_event_account_setup_registration_event",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_digest"),
        sa.UniqueConstraint(
            "event_id",
            "registration_id",
            name="uq_event_account_setup_registration",
        ),
    )
    op.create_index(
        "ix_event_account_setup_expires_at",
        "event_account_setup",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_event_account_setup_expires_at", table_name="event_account_setup"
    )
    op.drop_table("event_account_setup")
