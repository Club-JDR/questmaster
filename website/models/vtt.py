from website.extensions import cache, db
from website.models.base import SerializableMixin


class Vtt(db.Model, SerializableMixin):
    __tablename__ = "vtt"

    _exclude_fields = []
    _relationship_fields = ["games_vtt"]

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(), nullable=False, unique=True)
    icon = db.Column(db.String(), nullable=True)

    games_vtt = db.relationship("Game", backref="vtt")

    @staticmethod
    @cache.memoize()
    def get_vtts():
        """
        Return a list of all Vtts, cached for performance.
        """
        return Vtt.query.order_by("name").all()

    @classmethod
    def from_dict(cls, data):
        """Create a Vtt instance from a Python dict."""
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            icon=data.get("icon"),
        )

    def update_from_dict(self, data):
        """Update the Vtt instance from a dict (in place)."""
        super().update_from_dict(data)
        return self

    def __repr__(self):
        return f"<Vtt id={self.id} name='{self.name}' icon='{self.icon}'>"

    def __eq__(self, other):
        if not isinstance(other, Vtt):
            return NotImplemented
        return (self.id, self.name, self.icon) == (other.id, other.name, other.icon)
