"""Add the infraction table for in-app moderation infractions

Tracks moderation events in QuestMaster (replacing Mee6 ``!warn`` /
``!infractions``), preserving the historical warning format. Severity is an
integer so new levels can be inserted between existing ones without an enum
migration.

Revision ID: b9c0d1e2f3a4
Revises: a8b9c0d1e2f3
Create Date: 2026-07-21 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b9c0d1e2f3a4"
down_revision = "a8b9c0d1e2f3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "infraction",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("rule_article", sa.String(), nullable=True),
        sa.Column("severity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("message_link", sa.String(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("admin_id", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["admin_id"], ["user.id"]),
    )
    op.create_index("ix_infraction_user_id", "infraction", ["user_id"])
    op.create_index("ix_infraction_created_at", "infraction", ["created_at"])


def downgrade():
    op.drop_index("ix_infraction_created_at", table_name="infraction")
    op.drop_index("ix_infraction_user_id", table_name="infraction")
    op.drop_table("infraction")
