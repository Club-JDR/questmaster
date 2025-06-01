from website.extensions import db, cache


class Vtt(db.Model):
    __tablename__ = "vtt"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(), nullable=False, unique=True)
    icon = db.Column(db.String(), nullable=True)
    games_vtt = db.relationship("Game", backref="vtt")

    @staticmethod
    @cache.memoize()
    def get_vtts():
        """
        Wrapper to get vtt list from cache before DB.
        """
        return Vtt.query.order_by("name").all()
