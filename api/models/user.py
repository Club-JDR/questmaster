from api import db, bot
from sqlalchemy import orm

AVATAR_BASE_URL = "https://cdn.discordapp.com/avatars/{}/{}"


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.BigInteger, primary_key=True)
    # games_gm = db.relationship("Game", backref="game")

    def __init__(self, id):
        self.id = id

    @orm.reconstructor
    def init_on_load(self):
        """
        Get informations from Discord API not the database
        """
        results = bot.get_user(self.id)
        self.name = results["user"]["username"]
        self.is_gm = self.get_is_gm()
        self.avatar = AVATAR_BASE_URL.format(self.id, results["user"]["avatar"])

    def __repr__(self) -> str:
        return "<id {self.id}>"

    def get_avatar(self) -> str:
        avatar_id = bot.get_user(self.id)
        return AVATAR_BASE_URL.format(self.id, avatar_id)

    def get_is_gm(self) -> bool:
        return False

    def to_json(self):
        return {
            "id": self.id,
            "username": self.name,
            "gm": self.is_gm,
            "avatar": self.avatar,
        }
