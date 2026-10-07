"""Add event-scoped registrations, passes, and check-ins.

Revision ID: 20261006dqe1
Revises: 1a2b3c4d5e6f
Create Date: 2026-10-06
"""

from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20261006dqe1"
down_revision: Union[str, Sequence[str], None] = "1a2b3c4d5e6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "event",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timezone", sa.String(length=100), nullable=False),
        sa.Column("support_email", sa.String(length=320), nullable=True),
        sa.Column("public_site_url", sa.String(length=2048), nullable=True),
        sa.Column("brand_key", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.Column("pass_eligibility", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "pass_eligibility IN ('accepted', 'confirmed')",
            name="ck_event_pass_eligibility",
        ),
        sa.CheckConstraint(
            "state IN ('draft', 'active', 'archived')", name="ck_event_state"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "event_registration",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("normalized_email", sa.String(length=320), nullable=False),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("preferred_name", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=100), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("university", sa.String(length=500), nullable=True),
        sa.Column("degree_program", sa.String(length=500), nullable=True),
        sa.Column("country", sa.String(length=255), nullable=True),
        sa.Column("attendance_commitment", sa.Boolean(), nullable=True),
        sa.Column("photo_release_consent", sa.Boolean(), nullable=True),
        sa.Column("mlh_code_of_conduct_consent", sa.Boolean(), nullable=True),
        sa.Column("mlh_privacy_policy_consent", sa.Boolean(), nullable=True),
        sa.Column("data_sharing_consent", sa.Boolean(), nullable=True),
        sa.Column("mlh_marketing_opt_in", sa.Boolean(), nullable=True),
        sa.Column("admission_status", sa.String(length=20), nullable=False),
        sa.Column("rsvp_status", sa.String(length=20), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=True),
        sa.Column(
            "source_data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "admission_status IN ('accepted', 'waitlisted', 'rejected', 'revoked')",
            name="ck_event_registration_admission_status",
        ),
        sa.CheckConstraint(
            "age IS NULL OR age >= 0", name="ck_event_registration_age"
        ),
        sa.CheckConstraint(
            "rsvp_status IN ('pending', 'confirmed', 'declined')",
            name="ck_event_registration_rsvp_status",
        ),
        sa.ForeignKeyConstraint(["event_id"], ["event.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "normalized_email", name="uq_event_registration_email"),
        sa.UniqueConstraint("event_id", "user_id", name="uq_event_registration_user"),
        sa.UniqueConstraint("id", "event_id", name="uq_event_registration_id_event"),
    )
    op.create_index(
        "ix_event_registration_event_id", "event_registration", ["event_id"], unique=False
    )
    op.create_index(
        "ix_event_registration_normalized_email",
        "event_registration",
        ["normalized_email"],
        unique=False,
    )
    op.create_index(
        "ix_event_registration_user_id", "event_registration", ["user_id"], unique=False
    )

    op.create_table(
        "event_pass",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("registration_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("public_id", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "issued_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("state IN ('active', 'revoked')", name="ck_event_pass_state"),
        sa.CheckConstraint("version >= 1", name="ck_event_pass_version"),
        sa.ForeignKeyConstraint(
            ["registration_id"], ["event_registration.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint("registration_id"),
    )

    op.create_table(
        "email_delivery",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("registration_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_key", sa.String(length=100), nullable=False),
        sa.Column("recipient_email", sa.String(length=320), nullable=False),
        sa.Column("template_version", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('queued', 'sent', 'failed')", name="ck_email_delivery_status"
        ),
        sa.ForeignKeyConstraint(["event_id"], ["event.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["registration_id", "event_id"],
            ["event_registration.id", "event_registration.event_id"],
            name="fk_email_delivery_registration_event",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "event_id",
            "registration_id",
            "campaign_key",
            name="uq_email_delivery_campaign_registration",
        ),
    )
    op.create_index(
        "ix_email_delivery_event_campaign",
        "email_delivery",
        ["event_id", "campaign_key"],
        unique=False,
    )
    op.create_index(
        "ix_email_delivery_status", "email_delivery", ["status"], unique=False
    )

    op.create_table(
        "event_check_in",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("registration_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("checkpoint", sa.String(length=100), nullable=False),
        sa.Column("checked_in_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "checked_in_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["checked_in_by"], ["user.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["registration_id", "event_id"],
            ["event_registration.id", "event_registration.event_id"],
            name="fk_event_check_in_registration_event",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "event_id",
            "registration_id",
            "checkpoint",
            name="uq_event_check_in_checkpoint",
        ),
    )
    op.create_index(
        "ix_event_check_in_event_checkpoint",
        "event_check_in",
        ["event_id", "checkpoint"],
        unique=False,
    )
    op.create_index(
        "ix_event_check_in_registration_id",
        "event_check_in",
        ["registration_id"],
        unique=False,
    )

    event_table = sa.table(
        "event",
        sa.column("slug", sa.String),
        sa.column("name", sa.String),
        sa.column("start_at", sa.DateTime(timezone=True)),
        sa.column("end_at", sa.DateTime(timezone=True)),
        sa.column("timezone", sa.String),
        sa.column("support_email", sa.String),
        sa.column("public_site_url", sa.String),
        sa.column("brand_key", sa.String),
        sa.column("state", sa.String),
        sa.column("pass_eligibility", sa.String),
    )
    op.bulk_insert(
        event_table,
        [
            {
                "slug": "duquantum-2026",
                "name": "DuQuantum 2026",
                "start_at": datetime.fromisoformat("2026-10-24T09:00:00-04:00"),
                "end_at": datetime.fromisoformat("2026-10-25T18:00:00-04:00"),
                "timezone": "America/New_York",
                "support_email": "organizers@duquantum.org",
                "public_site_url": "https://duquantum.org/",
                "brand_key": "duquantum-2026",
                "state": "active",
                "pass_eligibility": "confirmed",
            }
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_event_check_in_registration_id", table_name="event_check_in")
    op.drop_index("ix_event_check_in_event_checkpoint", table_name="event_check_in")
    op.drop_table("event_check_in")
    op.drop_index("ix_email_delivery_status", table_name="email_delivery")
    op.drop_index("ix_email_delivery_event_campaign", table_name="email_delivery")
    op.drop_table("email_delivery")
    op.drop_table("event_pass")
    op.drop_index("ix_event_registration_user_id", table_name="event_registration")
    op.drop_index(
        "ix_event_registration_normalized_email", table_name="event_registration"
    )
    op.drop_index("ix_event_registration_event_id", table_name="event_registration")
    op.drop_table("event_registration")
    op.drop_table("event")
