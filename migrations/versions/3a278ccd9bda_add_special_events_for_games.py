"""Add special events for games

Revision ID: 3a278ccd9bda
Revises: d93dbbe1bddb
Create Date: 2025-10-04 10:10:37.933192

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3a278ccd9bda"
down_revision = "d93dbbe1bddb"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "special_event",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), unique=True, nullable=False),
        sa.Column("emoji", sa.String(), nullable=True),
        sa.Column("color", sa.Integer(), nullable=True),
        sa.Column(
            "active", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )
    with op.batch_alter_table("game", schema=None) as batch_op:
        batch_op.add_column(sa.Column("special_event_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, "special_event", ["special_event_id"], ["id"])


def downgrade():
    with op.batch_alter_table("game", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_special_event_name"))
        batch_op.drop_column("special_event_id")
    op.drop_table("special_event")
