"""Add delete cascade on game_events

Revision ID: d93dbbe1bddb
Revises: 2ec87b2c0974
Create Date: 2025-09-01 14:55:56.856850

"""

from alembic import op
import sqlalchemy as sa

revision = "d93dbbe1bddb"
down_revision = "2ec87b2c0974"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("game_event", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("game_event_game_id_fkey"), type_="foreignkey")
        batch_op.create_foreign_key(None, "game", ["game_id"], ["id"], ondelete="CASCADE")
