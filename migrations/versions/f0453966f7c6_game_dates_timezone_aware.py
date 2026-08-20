"""Make Game.date and GameSession.start/end timezone-aware

Game.date / GameSession.start / GameSession.end were naive
TIMESTAMP columns, but "now" was computed three different ways across the
codebase (naive container-local, aware UTC, and Europe/Paris wall time
entered by users) with nothing to keep them consistent — the past-date
publish guard and the dashboard's future/past agenda split could disagree
by 1-2h depending on DST.

Existing values are naive local wall-clock time (Europe/Paris, since that's
what users enter and nothing ever converted it) with no column-level
timezone info. Reinterpret each one in that zone and store it as a UTC-based
``timestamptz``, so application code can stop mixing naive and aware
datetimes when comparing "now" against these columns.

Revision ID: f0453966f7c6
Revises: c1d2e3f4a5b6
Create Date: 2026-08-20 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "f0453966f7c6"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE game ALTER COLUMN date TYPE timestamptz "
        "USING date AT TIME ZONE 'Europe/Paris'"
    )
    op.execute(
        "ALTER TABLE game_session ALTER COLUMN start TYPE timestamptz "
        "USING start AT TIME ZONE 'Europe/Paris'"
    )
    op.execute(
        'ALTER TABLE game_session ALTER COLUMN "end" TYPE timestamptz '
        "USING \"end\" AT TIME ZONE 'Europe/Paris'"
    )


def downgrade():
    op.execute(
        "ALTER TABLE game ALTER COLUMN date TYPE timestamp USING date AT TIME ZONE 'Europe/Paris'"
    )
    op.execute(
        "ALTER TABLE game_session ALTER COLUMN start TYPE timestamp "
        "USING start AT TIME ZONE 'Europe/Paris'"
    )
    op.execute(
        'ALTER TABLE game_session ALTER COLUMN "end" TYPE timestamp '
        "USING \"end\" AT TIME ZONE 'Europe/Paris'"
    )
