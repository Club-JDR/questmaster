from website.extensions import db, cache


class System(db.Model):
    __tablename__ = "system"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(), nullable=False, unique=True)
    icon = db.Column(db.String(), nullable=True)
    games_system = db.relationship("Game", backref="system")

    @staticmethod
    @cache.memoize()
    def get_systems():
        """
        Wrapper to get systems list from cache before DB.
        """
        return System.query.order_by("name").all()
