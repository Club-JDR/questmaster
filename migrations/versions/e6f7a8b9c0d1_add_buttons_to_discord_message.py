"""Multi-embed and link-button support for discord_message

Replaces the per-embed scalar columns (title, description, color, footer,
image_url) with a single ``embeds`` JSON list, and adds a ``buttons`` JSON list.
Drops the ``type`` discriminator: a message is now simply the combination of
content, embeds and buttons it carries. Existing embed rows are migrated into the
new ``embeds`` list before the old columns are dropped.

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-06-28 09:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e6f7a8b9c0d1"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("discord_message", sa.Column("embeds", sa.JSON(), nullable=True))
    op.add_column("discord_message", sa.Column("buttons", sa.JSON(), nullable=True))

    # Migrate existing single-embed rows into the new embeds list.
    op.execute("""
        UPDATE discord_message
        SET embeds = json_build_array(
            json_strip_nulls(
                json_build_object(
                    'title', title,
                    'description', description,
                    'color', color,
                    'footer', footer,
                    'image_url', image_url
                )
            )
        )
        WHERE type = 'embed'
        """)

    op.drop_column("discord_message", "title")
    op.drop_column("discord_message", "description")
    op.drop_column("discord_message", "color")
    op.drop_column("discord_message", "footer")
    op.drop_column("discord_message", "image_url")
    op.drop_column("discord_message", "type")


def downgrade():
    op.add_column(
        "discord_message",
        sa.Column("type", sa.String(length=8), nullable=False, server_default="plain"),
    )
    op.add_column("discord_message", sa.Column("title", sa.String(length=256), nullable=True))
    op.add_column("discord_message", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("discord_message", sa.Column("color", sa.Integer(), nullable=True))
    op.add_column("discord_message", sa.Column("footer", sa.String(length=256), nullable=True))
    op.add_column("discord_message", sa.Column("image_url", sa.String(length=512), nullable=True))

    # Restore the type discriminator and the first embed into the scalar columns.
    op.execute("""
        UPDATE discord_message
        SET type = CASE
                WHEN embeds IS NOT NULL AND json_array_length(embeds) > 0 THEN 'embed'
                ELSE 'plain'
            END,
            title = embeds->0->>'title',
            description = embeds->0->>'description',
            color = (embeds->0->>'color')::int,
            footer = embeds->0->>'footer',
            image_url = embeds->0->>'image_url'
        WHERE embeds IS NOT NULL AND json_array_length(embeds) > 0
        """)

    op.drop_column("discord_message", "buttons")
    op.drop_column("discord_message", "embeds")
