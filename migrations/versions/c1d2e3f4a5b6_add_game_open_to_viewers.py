"""Add game open_to_viewers and game_viewer table

Lets a GM signal that spectators (people who don't want to play but want to
watch, in person or via the VTT) are welcome, and lets those viewers follow
the game so it shows up in their personal agenda. ``game_viewer`` is purely a
personal-agenda signal (not a registration) — it never adds anyone to the
game's roster, role, or channel. Practical details for spectators (seat
limits, observer links, ...) go in the existing ``game.complement`` field.

Revision ID: c1d2e3f4a5b6
Revises: b1c2d3e4f5a6
Create Date: 2026-08-15 15:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c1d2e3f4a5b6"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("game", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "open_to_viewers",
                sa.Boolean(),
                nullable=False,
                server_default="false",
            )
        )

    op.create_table(
        "game_viewer",
        sa.Column("game_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["game.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("game_id", "user_id"),
    )


def downgrade():
    op.drop_table("game_viewer")

    with op.batch_alter_table("game", schema=None) as batch_op:
        batch_op.drop_column("open_to_viewers")
