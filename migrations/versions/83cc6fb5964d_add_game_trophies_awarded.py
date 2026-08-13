"""add game trophies_awarded

Revision ID: 83cc6fb5964d
Revises: 2e25be8292ad
Create Date: 2026-08-13 17:44:04.157401

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "83cc6fb5964d"
down_revision = "2e25be8292ad"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("game", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "trophies_awarded", sa.Boolean(), nullable=False, server_default=sa.text("false")
            )
        )

    # Backfill from the audit trail: archive() has always logged a "delete"
    # GameEvent whose description ends with "Badges distribués." when the GM
    # opted to award trophies, "Badges non-distribués." otherwise. That log
    # message is the only record of the decision predating this column.
    op.execute(
        """
        UPDATE game
        SET trophies_awarded = TRUE
        WHERE id IN (
            SELECT game_id
            FROM game_event
            WHERE action = 'delete' AND description LIKE '%Badges distribués.%'
        )
        """
    )


def downgrade():
    with op.batch_alter_table("game", schema=None) as batch_op:
        batch_op.drop_column("trophies_awarded")
