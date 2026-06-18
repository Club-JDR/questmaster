"""Add discord_message table for admin-sent Discord messages

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-06-17 09:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f2a3b4c5d6e7"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "discord_message",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("discord_msg_id", sa.String(length=32), nullable=False),
        sa.Column("channel_id", sa.String(length=32), nullable=False),
        sa.Column("channel_label", sa.String(length=128), nullable=True),
        sa.Column("type", sa.String(length=8), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("title", sa.String(length=256), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("color", sa.Integer(), nullable=True),
        sa.Column("footer", sa.String(length=256), nullable=True),
        sa.Column("image_url", sa.String(length=512), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("discord_msg_id"),
    )


def downgrade():
    op.drop_table("discord_message")
