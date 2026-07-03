"""Add permission_grant table for granular admin permissions (RBAC)

Stores one row per (capability, subject) grant. A subject is either a Discord
role or an individual user; the capability key references the code-defined
catalog (not a DB foreign key). A unique constraint keeps grants idempotent.

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-06-24 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d5e6f7a8b9c0"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "permission_grant",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("permission_key", sa.String(), nullable=False),
        sa.Column("subject_type", sa.String(), nullable=False),
        sa.Column("subject_id", sa.String(), nullable=False),
        sa.Column("granted_by_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "permission_key",
            "subject_type",
            "subject_id",
            name="uq_permission_grant_subject",
        ),
    )
    op.create_index("ix_permission_grant_permission_key", "permission_grant", ["permission_key"])
    op.create_index("ix_permission_grant_subject_id", "permission_grant", ["subject_id"])


def downgrade():
    op.drop_index("ix_permission_grant_subject_id", table_name="permission_grant")
    op.drop_index("ix_permission_grant_permission_key", table_name="permission_grant")
    op.drop_table("permission_grant")
