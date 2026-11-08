"""Add event-scoped browser push subscriptions and delivery audit.

Revision ID: 20261008dqpn
Revises: 20261007dqas
Create Date: 2026-10-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20261008dqpn"
down_revision: Union[str, Sequence[str], None] = "20261007dqas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "event_push_subscription",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("registration_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("endpoint_hash", sa.String(length=64), nullable=False),
        sa.Column("p256dh", sa.Text(), nullable=False),
        sa.Column("auth", sa.Text(), nullable=False),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column(
            "active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(length=100), nullable=True),
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
            name="fk_event_push_subscription_registration_event",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "event_id",
            "endpoint_hash",
            name="uq_event_push_subscription_event_endpoint",
        ),
        sa.UniqueConstraint(
            "id", "event_id", name="uq_event_push_subscription_id_event"
        ),
    )
    op.create_index(
        "ix_event_push_subscription_event_active",
        "event_push_subscription",
        ["event_id", "active"],
        unique=False,
    )
    op.create_index(
        "ix_event_push_subscription_registration",
        "event_push_subscription",
        ["registration_id"],
        unique=False,
    )

    op.create_table(
        "event_notification_delivery",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("notification_key", sa.String(length=100), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'queued'"),
            nullable=False,
        ),
        sa.Column("attempts", sa.Integer(), server_default="1", nullable=False),
        sa.Column("provider_status", sa.Integer(), nullable=True),
        sa.Column("error", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'sent', 'failed', 'skipped')",
            name="ck_event_notification_delivery_status",
        ),
        sa.ForeignKeyConstraint(["event_id"], ["event.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["subscription_id", "event_id"],
            ["event_push_subscription.id", "event_push_subscription.event_id"],
            name="fk_event_notification_delivery_subscription_event",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "subscription_id",
            "notification_key",
            name="uq_event_notification_delivery_subscription_key",
        ),
    )
    op.create_index(
        "ix_event_notification_delivery_event_status",
        "event_notification_delivery",
        ["event_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_event_notification_delivery_event_status",
        table_name="event_notification_delivery",
    )
    op.drop_table("event_notification_delivery")
    op.drop_index(
        "ix_event_push_subscription_registration",
        table_name="event_push_subscription",
    )
    op.drop_index(
        "ix_event_push_subscription_event_active",
        table_name="event_push_subscription",
    )
    op.drop_table("event_push_subscription")
