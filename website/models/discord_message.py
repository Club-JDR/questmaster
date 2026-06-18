"""DiscordMessage model recording messages sent via the admin panel."""

from datetime import datetime

from website.extensions import db
from website.models.base import SerializableMixin


class DiscordMessage(db.Model, SerializableMixin):
    """A message (plain text or embed) sent to a Discord channel by an admin.

    Persisted so admins can find and edit previously-sent messages without
    needing to remember Discord message IDs. The target channel is resolved at
    send time from the settings allowlist; only the raw Discord channel ID is
    stored (no foreign key), with the originating setting key kept for
    display/audit.

    Attributes:
        id: Primary key.
        discord_msg_id: Discord's own ID for the sent message.
        channel_id: Discord channel ID the message was sent to.
        channel_label: Human label of the target channel (snapshot, for display).
        type: Message kind, ``"plain"`` or ``"embed"``.
        content: Plain-text body (None for embeds).
        title: Embed title (None for plain messages).
        description: Embed description (None for plain messages).
        color: Embed color as an integer (None for plain messages).
        footer: Embed footer text (None for plain messages).
        image_url: Embed image URL (None for plain messages).
        sent_at: Timestamp of the original send (UTC).
    """

    __tablename__ = "discord_message"

    TYPE_PLAIN = "plain"
    TYPE_EMBED = "embed"

    _exclude_fields = []
    _relationship_fields = []

    id = db.Column(db.Integer, primary_key=True)
    discord_msg_id = db.Column(db.String(32), nullable=False, unique=True)
    channel_id = db.Column(db.String(32), nullable=False)
    channel_label = db.Column(db.String(128), nullable=True)
    type = db.Column(db.String(8), nullable=False)
    content = db.Column(db.Text, nullable=True)
    title = db.Column(db.String(256), nullable=True)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.Integer, nullable=True)
    footer = db.Column(db.String(256), nullable=True)
    image_url = db.Column(db.String(512), nullable=True)
    sent_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @property
    def is_embed(self) -> bool:
        """Whether this message is an embed."""
        return self.type == self.TYPE_EMBED

    @classmethod
    def from_dict(cls, data):
        """Create a DiscordMessage instance from a Python dict."""
        return cls(
            id=data.get("id"),
            discord_msg_id=data.get("discord_msg_id"),
            channel_id=data.get("channel_id"),
            channel_label=data.get("channel_label"),
            type=data.get("type"),
            content=data.get("content"),
            title=data.get("title"),
            description=data.get("description"),
            color=data.get("color"),
            footer=data.get("footer"),
            image_url=data.get("image_url"),
        )

    def __repr__(self):
        return f"<DiscordMessage id={self.id} type='{self.type}' channel='{self.channel_id}'>"
