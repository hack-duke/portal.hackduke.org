"""Reconcile the form builder metadata already present in production.

Revision ID: 1a2b3c4d5e6f
Revises: eb4fd79a5e2f
Create Date: 2026-02-20 12:00:00.000000

Production was upgraded to this revision from the FormBuilder branch after the
main-line ``eb4fd79a5e2f`` migration had already run. Keeping the production
revision ID and attaching it to that main-line parent restores a single,
upgradeable migration history. Existing production databases will not replay
this migration; new databases will receive the same form-builder columns.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "1a2b3c4d5e6f"
down_revision: Union[str, Sequence[str], None] = "eb4fd79a5e2f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("form", sa.Column("title", sa.String(), nullable=True))
    op.add_column(
        "form", sa.Column("closed_message_title", sa.String(), nullable=True)
    )
    op.add_column(
        "form", sa.Column("closed_message_body", sa.Text(), nullable=True)
    )
    op.add_column(
        "form",
        sa.Column(
            "is_db_driven",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
    )

    op.add_column("question", sa.Column("label", sa.Text(), nullable=True))
    op.add_column("question", sa.Column("placeholder", sa.String(), nullable=True))
    op.add_column("question", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "question",
        sa.Column(
            "required",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.add_column(
        "question",
        sa.Column(
            "page_number",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
    )
    op.add_column("question", sa.Column("page_title", sa.String(), nullable=True))
    op.add_column(
        "question",
        sa.Column(
            "order_in_page",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )
    op.add_column(
        "question",
        sa.Column(
            "config", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )

    op.create_index(
        "idx_question_form_order",
        "question",
        ["form_key", "page_number", "order_in_page"],
    )
    op.create_index("idx_form_year", "form", ["year"])


def downgrade() -> None:
    op.drop_index("idx_form_year", table_name="form")
    op.drop_index("idx_question_form_order", table_name="question")

    op.drop_column("question", "config")
    op.drop_column("question", "order_in_page")
    op.drop_column("question", "page_title")
    op.drop_column("question", "page_number")
    op.drop_column("question", "required")
    op.drop_column("question", "description")
    op.drop_column("question", "placeholder")
    op.drop_column("question", "label")

    op.drop_column("form", "is_db_driven")
    op.drop_column("form", "closed_message_body")
    op.drop_column("form", "closed_message_title")
    op.drop_column("form", "title")
