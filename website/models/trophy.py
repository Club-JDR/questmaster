from collections import Counter
from sqlalchemy.orm import object_session
from website.extensions import db
from website.utils.logger import logger
from .user import User

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

def add_trophy_to_user(user_id, trophy_id, amount=1):
    trophy = Trophy.query.get(trophy_id)
    if not trophy:
        return

    user_trophy = UserTrophy.query.filter_by(user_id=user_id, trophy_id=trophy_id).first()

    if trophy.unique:
        if user_trophy is None:
            user_trophy = UserTrophy(user_id=user_id, trophy_id=trophy_id, quantity=1)
            db.session.add(user_trophy)
        else:
            # Do nothing if already has it
            return
    else:
        if user_trophy:
            user_trophy.quantity += amount
        else:
            user_trophy = UserTrophy(user_id=user_id, trophy_id=trophy_id, quantity=amount)
            db.session.add(user_trophy)

    db.session.commit()
