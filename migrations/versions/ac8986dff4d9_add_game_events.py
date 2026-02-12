"""Add event logs

Revision ID: ac8986dff4d9
Revises: 1ea698e20845
Create Date: 2025-07-15 10:25:35.790751

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ac8986dff4d9"
down_revision = "1ea698e20845"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "game_event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "action",
            sa.Enum(
                "create",
                "edit",
                "delete",
                "create-session",
                "edit-session",
                "delete-session",
                "register",
                "unregister",
                "alert",
                name="action_type_enum",
            ),
            nullable=False,
        ),
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["game_id"],
            ["game.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    with op.batch_alter_table("game_event") as batch_op:
        batch_op.create_index("ix_gameevent_game", ["game_id"], unique=False)
        batch_op.create_index("ix_gameevent_timestamp", ["timestamp"], unique=False)


def downgrade():
    with op.batch_alter_table("game_event") as batch_op:
        batch_op.drop_index("ix_gameevent_timestamp")
        batch_op.drop_index("ix_gameevent_game")

    op.drop_table("game_event")

    sa.Enum(name="action_type_enum").drop(op.get_bind(), checkfirst=True)
