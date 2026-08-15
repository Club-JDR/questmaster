"""Add impersonator_id/impersonator_username to app_log

While an admin is impersonating another user (admin "view-as"), the app
behaves exactly as it would for the target — so ``user_id``/``username``
on the log record are the *impersonated* user's. These two new columns
carry the real admin's identity in that case, so the audit trail never
loses track of who actually performed the action.

Revision ID: 9c1d2e3f4a5b
Revises: 83cc6fb5964d
Create Date: 2026-08-15 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9c1d2e3f4a5b"
down_revision = "83cc6fb5964d"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("app_log", schema=None) as batch_op:
        batch_op.add_column(sa.Column("impersonator_id", sa.String(), nullable=True))
        batch_op.add_column(
            sa.Column("impersonator_username", sa.String(length=128), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("app_log", schema=None) as batch_op:
        batch_op.drop_column("impersonator_username")
        batch_op.drop_column("impersonator_id")
