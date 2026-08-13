"""Set discord_message.sent_at server-side default

Revision ID: 2e25be8292ad
Revises: bcc54b903cb3
Create Date: 2026-08-13 15:05:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2e25be8292ad"
down_revision = "bcc54b903cb3"
branch_labels = None
depends_on = None


def upgrade():
    # Moves the default from Python-side (datetime.utcnow, deprecated) to a
    # DB-side default so the column keeps working without app-side changes.
    op.alter_column(
        "discord_message",
        "sent_at",
        server_default=sa.func.now(),
        existing_type=sa.DateTime(),
        existing_nullable=False,
    )


def downgrade():
    op.alter_column(
        "discord_message",
        "sent_at",
        server_default=None,
        existing_type=sa.DateTime(),
        existing_nullable=False,
    )
