"""Add user name

Revision ID: 2ec87b2c0974
Revises: ac8986dff4d9
Create Date: 2025-07-15 16:11:45.462774

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2ec87b2c0974"
down_revision = "ac8986dff4d9"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("name", sa.String(), nullable=True))
        batch_op.create_index(batch_op.f("ix_user_name"), ["name"], unique=False)


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("name")
        batch_op.drop_index(batch_op.f("ix_user_name"))