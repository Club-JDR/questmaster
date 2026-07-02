"""DiscordMessage model recording messages sent via the admin panel."""

from datetime import datetime

from website.extensions import db
from website.models.base import SerializableMixin


class DiscordMessage(db.Model, SerializableMixin):
    """A message sent to a Discord channel by an admin.

    Persisted so admins can find and edit previously-sent messages without
    needing to remember Discord message IDs. The target channel is resolved at
    send time from the settings allowlist; only the raw Discord channel ID is
    stored (no foreign key), with a human label kept for display/audit.

    A message is composed of any combination of plain ``content``, a list of
    ``embeds`` and a row of link ``buttons`` — these are independent and may all
    appear together. There is no separate "type": a message is considered an embed
    message when it carries embeds. Embeds are stored as a JSON list (each item a
    ``{"title", "description", "color", "footer", "image_url"}`` dict); buttons as
    a JSON list of ``{"label", "url"}`` dicts.

    Attributes:
        id: Primary key.
        discord_msg_id: Discord's own ID for the sent message.
        channel_id: Discord channel ID the message was sent to.
        channel_label: Human label of the target channel (snapshot, for display).
        content: Plain-text body (optional; may accompany embeds).
        embeds: List of embed dicts (None when there are no embeds).
        buttons: List of ``{"label", "url"}`` link buttons (None if no buttons).
        sent_at: Timestamp of the original send (UTC).
    """

    __tablename__ = "discord_message"

    _exclude_fields = []
    _relationship_fields = []

    id = db.Column(db.Integer, primary_key=True)
    discord_msg_id = db.Column(db.String(32), nullable=False, unique=True)
    channel_id = db.Column(db.String(32), nullable=False)
    channel_label = db.Column(db.String(128), nullable=True)
    content = db.Column(db.Text, nullable=True)
    embeds = db.Column(db.JSON, nullable=True)
    buttons = db.Column(db.JSON, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @property
    def is_embed(self) -> bool:
        """Whether this message carries at least one embed."""
        return bool(self.embeds)

    @property
    def embed_list(self) -> list:
        """Return the embeds as a list (empty when there are none)."""
        return self.embeds or []

    @property
    def preview(self) -> str:
        """Return a short text preview for list views.

        Uses the plain content if present, otherwise the first embed's title or
        description.

        Returns:
            A preview string (possibly empty).
        """
        if self.content:
            return self.content
        for embed in self.embed_list:
            if embed.get("title") or embed.get("description"):
                return embed.get("title") or embed.get("description") or ""
        return ""

    @classmethod
    def from_dict(cls, data):
        """Create a DiscordMessage instance from a Python dict."""
        return cls(
            id=data.get("id"),
            discord_msg_id=data.get("discord_msg_id"),
            channel_id=data.get("channel_id"),
            channel_label=data.get("channel_label"),
            content=data.get("content"),
            embeds=data.get("embeds"),
            buttons=data.get("buttons"),
        )

    def __repr__(self):
        return f"<DiscordMessage id={self.id} channel='{self.channel_id}'>"
