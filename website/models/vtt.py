from website import db


class Vtt(db.Model):
    __tablename__ = "vtt"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(), nullable=False, unique=True)
    icon = db.Column(db.String(), nullable=True)
    games_vtt = db.relationship("Game", backref="vtt")
