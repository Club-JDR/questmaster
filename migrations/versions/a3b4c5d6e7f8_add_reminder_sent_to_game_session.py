"""add reminder_sent to game_session

Revision ID: a3b4c5d6e7f8
Revises: f0453966f7c6
Create Date: 2026-08-26 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a3b4c5d6e7f8"
down_revision = "f0453966f7c6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("game_session", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "reminder_sent", sa.Boolean(), nullable=False, server_default=sa.text("false")
            )
        )


def downgrade():
    with op.batch_alter_table("game_session", schema=None) as batch_op:
        batch_op.drop_column("reminder_sent")
