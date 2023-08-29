from website import db, bot
from sqlalchemy import orm
from flask import current_app


class System(db.Model):
    __tablename__ = "system"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(), nullable=False, unique=True)
    icon = db.Column(db.String(), nullable=True)
    games_system = db.relationship("Game", backref="system")
