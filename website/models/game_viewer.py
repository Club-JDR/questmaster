"""GameViewer model: a user following a game's sessions as a spectator."""

from website.extensions import db
from website.models.base import SerializableMixin


class GameViewer(db.Model, SerializableMixin):
    """A user following a game as a spectator (not a player).

    Purely a personal-agenda signal, feeding the follower's own dashboard
    agenda and the ``/mon-agenda`` Discord command. It does nothing else — no
    notification to the GM, no addition to the game's roster, role, or
    channel. Mirrors the shape of ``players_table`` but as a full entity so
    it carries its own ``created_at`` and can be queried directly.

    Attributes:
        game_id: Foreign key to Game.
        user_id: Foreign key to User.
        created_at: When the user started following the game.
    """

    __tablename__ = "game_viewer"

    _exclude_fields = []
    _relationship_fields = ["game", "user"]

    game_id = db.Column(db.BigInteger(), db.ForeignKey("game.id"), primary_key=True)
    user_id = db.Column(db.String(), db.ForeignKey("user.id"), primary_key=True)
    created_at = db.Column(db.DateTime(), nullable=False, server_default=db.func.now())

    game = db.relationship("Game")
    user = db.relationship("User")

    @classmethod
    def from_dict(cls, data):
        """
        Create a GameViewer instance from a Python dict.
        """
        return cls(game_id=data.get("game_id"), user_id=data.get("user_id"))

    def __repr__(self):
        return f"<GameViewer game_id={self.game_id} user_id={self.user_id}>"

    def __eq__(self, other):
        if not isinstance(other, GameViewer):
            return NotImplemented
        return self.game_id == other.game_id and self.user_id == other.user_id

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result
