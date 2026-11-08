"""Preserve organizer-approved team sizes from the final master roster."""
from alembic import op
import sqlalchemy as sa

revision = "20261024dqsz"
down_revision = "20261019dqft"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_event_team_member_position", "event_team_member", type_="check")
    op.create_check_constraint("ck_event_team_member_position", "event_team_member", "member_position >= 1")


def downgrade():
    if op.get_bind().execute(sa.text("SELECT count(*) FROM event_team_member WHERE member_position > 4")).scalar():
        raise RuntimeError("Cannot restore a four-person limit while larger teams exist")
    op.drop_constraint("ck_event_team_member_position", "event_team_member", type_="check")
    op.create_check_constraint("ck_event_team_member_position", "event_team_member", "member_position BETWEEN 1 AND 4")
