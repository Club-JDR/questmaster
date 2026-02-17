"""Add user_id to game_event

Revision ID: b7f8a9c0d1e2
Revises: a1b2c3d4e5f6
Create Date: 2026-02-17 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b7f8a9c0d1e2"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("game_event", schema=None) as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.String(), nullable=True))
        batch_op.create_foreign_key("fk_gameevent_user_id", "user", ["user_id"], ["id"])
        batch_op.create_index("ix_gameevent_user", ["user_id"], unique=False)


def downgrade():
    with op.batch_alter_table("game_event", schema=None) as batch_op:
        batch_op.drop_index("ix_gameevent_user")
        batch_op.drop_constraint("fk_gameevent_user_id", type_="foreignkey")
        batch_op.drop_column("user_id")
