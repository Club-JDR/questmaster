"""System model for tabletop RPG game systems."""

from website.extensions import db
from website.models.base import SerializableMixin


class System(db.Model, SerializableMixin):
    """
    Represents a game system (e.g., D&D 5e, Call of Cthulhu).

    Attributes:
        id: Primary key.
        name: Unique system name.
        icon: Path or URL to the system icon.
        description: Optional local blurb (Markdown source), rendered on the
            system's public page. Independent of ``reference_url`` — either,
            both, or neither may be set.
        reference_url: Optional canonical external page for the system
            (legrog.org, official site, publisher, etc.).
    """

    __tablename__ = "system"

    _exclude_fields = []
    _relationship_fields = ["games_system"]

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(), nullable=False, unique=True)
    icon = db.Column(db.String(), nullable=True)
    description = db.Column(db.Text(), nullable=True)
    reference_url = db.Column(db.String(), nullable=True)

    games_system = db.relationship("Game", backref="system")

    @staticmethod
    def get_systems():
        """Return a list of all Systems, ordered by name."""
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
            description=data.get("description"),
            reference_url=data.get("reference_url"),
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
        return (
            self.id == other.id
            and self.name == other.name
            and self.icon == other.icon
            and self.description == other.description
            and self.reference_url == other.reference_url
        )

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result
