from website.extensions import cache, db
from website.models.base import SerializableMixin


class System(db.Model, SerializableMixin):
    """
    Represents a game system (e.g., D&D 5e, Call of Cthulhu).
    """

    __tablename__ = "system"

    _exclude_fields = []
    _relationship_fields = ["games_system"]

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(), nullable=False, unique=True)
    icon = db.Column(db.String(), nullable=True)

    games_system = db.relationship("Game", backref="system")

    @staticmethod
    @cache.memoize()
    def get_systems():
        """
        Return a list of all Systems, cached for performance.
        """
        return System.query.order_by("name").all()

    @classmethod
    def from_dict(cls, data):
        """
        Create a System instance from a Python dict.
        """
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            icon=data.get("icon"),
        )

    def update_from_dict(self, data):
        """
        Update the System instance from a dict (in place).
        """
        super().update_from_dict(data)
        return self

    def __repr__(self):
        return f"<System id={self.id} name='{self.name}' icon='{self.icon}'>"

    def __eq__(self, other):
        if not isinstance(other, System):
            return NotImplemented
        return self.id == other.id and self.name == other.name and self.icon == other.icon

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result
