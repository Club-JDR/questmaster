from website import db


class Session(db.Model):
    __tablename__ = "session"

    id = db.Column(db.BigInteger, primary_key=True)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
