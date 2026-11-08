"""Add event teams, source preferences, and registration linkage.

Revision ID: 20261018dqtm
Revises: 20261008dqpn
Create Date: 2026-10-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20261018dqtm"
down_revision: Union[str, Sequence[str], None] = "20261008dqpn"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "event_team",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("team_number", sa.String(length=50), nullable=True),
        sa.Column("track_preference", sa.String(length=100), nullable=True),
        sa.Column("assigned_track", sa.String(length=100), nullable=True),
        sa.Column(
            "challenge_preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("assigned_challenge", sa.String(length=500), nullable=True),
        sa.Column("sponsor_name", sa.String(length=255), nullable=True),
        sa.Column("sponsor_contact_name", sa.String(length=255), nullable=True),
        sa.Column("sponsor_contact_email", sa.String(length=320), nullable=True),
        sa.Column("requested_additional_teammates", sa.Integer(), nullable=True),
        sa.Column(
            "source",
            sa.String(length=100),
            server_default=sa.text("'google_forms_xlsx'"),
            nullable=False,
        ),
        sa.Column("source_record_id", sa.String(length=64), nullable=False),
        sa.Column("source_submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
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
        sa.CheckConstraint(
            "requested_additional_teammates IS NULL OR "
            "requested_additional_teammates BETWEEN 0 AND 4",
            name="ck_event_team_additional_teammates",
        ),
        sa.ForeignKeyConstraint(["event_id"], ["event.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "event_id", name="uq_event_team_id_event"),
        sa.UniqueConstraint(
            "event_id", "normalized_name", name="uq_event_team_event_name"
        ),
    )
    op.create_index(
        "ix_event_team_event_active",
        "event_team",
        ["event_id", "active"],
        unique=False,
    )
    op.create_index(
        "ix_event_team_event_name",
        "event_team",
        ["event_id", "normalized_name"],
        unique=False,
    )

    op.create_table(
        "event_team_member",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("registration_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("member_position", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("normalized_email", sa.String(length=320), nullable=True),
        sa.Column("discord_username", sa.String(length=255), nullable=True),
        sa.Column(
            "match_status",
            sa.String(length=20),
            server_default=sa.text("'unmatched'"),
            nullable=False,
        ),
        sa.Column("match_method", sa.String(length=50), nullable=True),
        sa.Column("match_detail", sa.String(length=100), nullable=False),
        sa.Column("source_row_number", sa.Integer(), nullable=False),
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
        sa.CheckConstraint(
            "member_position BETWEEN 1 AND 4",
            name="ck_event_team_member_position",
        ),
        sa.CheckConstraint(
            "match_status IN ('matched', 'unmatched', 'ambiguous')",
            name="ck_event_team_member_match_status",
        ),
        sa.CheckConstraint(
            "match_method IS NULL OR match_method IN "
            "('email', 'name', 'exact_unique_name_email_mismatch')",
            name="ck_event_team_member_match_method",
        ),
        sa.ForeignKeyConstraint(
            ["team_id", "event_id"],
            ["event_team.id", "event_team.event_id"],
            name="fk_event_team_member_team_event",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["registration_id", "event_id"],
            ["event_registration.id", "event_registration.event_id"],
            name="fk_event_team_member_registration_event",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "team_id", "member_position", name="uq_event_team_member_position"
        ),
        sa.UniqueConstraint(
            "event_id", "registration_id", name="uq_event_team_member_registration"
        ),
    )
    op.create_index(
        "ix_event_team_member_team",
        "event_team_member",
        ["team_id"],
        unique=False,
    )
    op.create_index(
        "ix_event_team_member_registration",
        "event_team_member",
        ["registration_id"],
        unique=False,
    )
    op.create_index(
        "ix_event_team_member_event_status",
        "event_team_member",
        ["event_id", "match_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_event_team_member_event_status", table_name="event_team_member"
    )
    op.drop_index(
        "ix_event_team_member_registration", table_name="event_team_member"
    )
    op.drop_index("ix_event_team_member_team", table_name="event_team_member")
    op.drop_table("event_team_member")
    op.drop_index("ix_event_team_event_name", table_name="event_team")
    op.drop_index("ix_event_team_event_active", table_name="event_team")
    op.drop_table("event_team")
