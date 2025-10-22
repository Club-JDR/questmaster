from website.extensions import db, cache


class Vtt(db.Model):
    """
    Represents a Virtual Tabletop (VTT) platform used in games.
    """

    __tablename__ = "vtt"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(), nullable=False, unique=True)
    icon = db.Column(db.String(), nullable=True)

    games_vtt = db.relationship("Game", backref="vtt")

    @staticmethod
    @cache.memoize()
    def get_vtts():
        """
        Return a list of all VTTs, cached for performance.
        """
        return Vtt.query.order_by("name").all()

    def to_dict(self):
        """
        Serialize the VTT instance into a Python dict.
        """
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
        }

    def to_json(self):
        """
        Alias for to_dict() for API compatibility.
        """
        return self.to_dict()

    @property
    def json(self):
        """
        Property alias for JSON serialization.
        """
        return self.to_dict()

    @classmethod
    def from_dict(cls, data):
        """
        Create a VTT instance from a Python dict.
        """
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            icon=data.get("icon"),
        )

    @classmethod
    def from_json(cls, data):
        """
        Alias for from_dict() for API compatibility.
        """
        return cls.from_dict(data)

    def update_from_dict(self, data):
        """
        Update the VTT instance from a dict (in place).
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self

    def __repr__(self):
        return f"<Vtt id={self.id} name='{self.name}' icon='{self.icon}'>"

    def __eq__(self, other):
        if not isinstance(other, Vtt):
            return NotImplemented
        return (
            self.id == other.id and self.name == other.name and self.icon == other.icon
        )

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result
