"""Add system description/reference_url and user_system_interest table

Gives each System a public page that doubles as passive matchmaking:
``description``/``reference_url`` let a system carry its own blurb or a
link to an external reference page, and ``user_system_interest`` records a
user's declared interest in playing or running a system (not a
registration — purely a demand signal).

Revision ID: b1c2d3e4f5a6
Revises: 9c1d2e3f4a5b
Create Date: 2026-08-15 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b1c2d3e4f5a6"
down_revision = "9c1d2e3f4a5b"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("system", schema=None) as batch_op:
        batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("reference_url", sa.String(), nullable=True))

    op.create_table(
        "user_system_interest",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("system_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("player", "gm", name="system_interest_role_enum"),
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["system_id"], ["system.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("user_id", "system_id", "role"),
    )


def downgrade():
    op.drop_table("user_system_interest")
    sa.Enum(name="system_interest_role_enum").drop(op.get_bind(), checkfirst=True)

    with op.batch_alter_table("system", schema=None) as batch_op:
        batch_op.drop_column("reference_url")
        batch_op.drop_column("description")
