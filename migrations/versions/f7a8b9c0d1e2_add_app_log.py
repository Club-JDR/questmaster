"""Add the app_log table for persisted application logs

Application log records at ``QM_DB_LOG_LEVEL`` and above are written here by
``DatabaseLogHandler`` so the admin "Journaux applicatifs" page can filter
them with plain SQL. ``user_id`` is intentionally not a foreign key: log
writes must stay decoupled from the rest of the schema.

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-07-03 09:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f7a8b9c0d1e2"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "app_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("level_no", sa.Integer(), nullable=False),
        sa.Column("logger", sa.String(length=128), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.String(length=36), nullable=True),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("username", sa.String(length=128), nullable=True),
        sa.Column("endpoint", sa.String(length=128), nullable=True),
        sa.Column("module", sa.String(length=128), nullable=True),
        sa.Column("func", sa.String(length=128), nullable=True),
        sa.Column("line", sa.Integer(), nullable=True),
    )
    op.create_index("ix_app_log_timestamp", "app_log", ["timestamp"])
    op.create_index("ix_app_log_level", "app_log", ["level"])


def downgrade():
    op.drop_index("ix_app_log_level", table_name="app_log")
    op.drop_index("ix_app_log_timestamp", table_name="app_log")
    op.drop_table("app_log")
