"""Add game_defaults to user

Stores per-user default values for the game creation form (e.g. description,
complement) as JSONB, rather than a dedicated column per possible field. Only
a whitelisted subset of keys is ever read back (see
website.utils.game_form_defaults); the column is nullable so existing users
are unaffected until they save a preference.

Revision ID: bcc54b903cb3
Revises: b9c0d1e2f3a4
Create Date: 2026-08-12 18:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "bcc54b903cb3"
down_revision = "b9c0d1e2f3a4"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("game_defaults", postgresql.JSONB(), nullable=True))


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("game_defaults")
