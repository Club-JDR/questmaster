from website.extensions import db


class SpecialEvent(db.Model):
    __tablename__ = "special_event"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)  # e.g. "Halloween 2025"
    color = db.Column(db.Integer, nullable=True)
    active = db.Column(db.Boolean, default=False, nullable=False)

    games = db.relationship("Game", back_populates="special_event")

    def __str__(self):
        hex_color = (
            f"#{self.color:06x}" if isinstance(self.color, int) else (self.color or "")
        )
        return f"{self.name} ({hex_color})"
