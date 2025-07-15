from website.extensions import db
from .user import User


BADGE_OS_ID = 1
BADGE_OS_GM_ID = 2
BADGE_CAMPAIGN_ID = 3
BADGE_CAMPAIGN_GM_ID = 4


class Trophy(db.Model):
    __tablename__ = "trophy"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    unique = db.Column(db.Boolean, default=False)
    icon = db.Column(db.String(), nullable=True)

    def __str__(self):
        return self.name


class UserTrophy(db.Model):
    __tablename__ = "user_trophy"

    user_id = db.Column(db.String(), db.ForeignKey("user.id"), primary_key=True)
    trophy_id = db.Column(db.Integer, db.ForeignKey("trophy.id"), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    user = db.relationship("User", back_populates="trophies")
    trophy = db.relationship("Trophy")
