"""Add indexes backing the dashboard per-user stats queries

Indexes the foreign keys the dashboard aggregates filter/join on, which
PostgreSQL does not create automatically:

* ``game.gm_id``            — "games as GM" lookups.
* ``game_players.player_id``— "games as player" join (composite PK leads with
  ``game_id``, so player-side lookups are otherwise uncovered).
* ``game_session.game_id``  — per-game session loading and range scans.

Revision ID: c4d5e6f7a8b9
Revises: f2a3b4c5d6e7
Create Date: 2026-06-23 22:45:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "c4d5e6f7a8b9"
down_revision = "f2a3b4c5d6e7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_game_gm_id", "game", ["gm_id"])
    op.create_index("ix_game_players_player_id", "game_players", ["player_id"])
    op.create_index("ix_game_session_game_id", "game_session", ["game_id"])


def downgrade():
    op.drop_index("ix_game_session_game_id", table_name="game_session")
    op.drop_index("ix_game_players_player_id", table_name="game_players")
    op.drop_index("ix_game_gm_id", table_name="game")
