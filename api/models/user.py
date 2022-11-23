from api import db, bot
from sqlalchemy import orm
from flask import current_app


AVATAR_BASE_URL = "https://cdn.discordapp.com/avatars/{}/{}"


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.String(), primary_key=True)
    games_gm = db.relationship("Game", backref="game")

    def __init__(self, id):
        self.id = id

    @orm.reconstructor
    def init_on_load(self):
        """
        Get informations from Discord API not the database
        """
        results = bot.get_user(self.id)
        self.name = results["user"]["username"]
        self.is_gm = current_app.config["DISCORD_GM_ROLE_ID"] in results["roles"]
        self.avatar = AVATAR_BASE_URL.format(self.id, results["user"]["avatar"])

    def __repr__(self) -> str:
        return "<id {self.id}>"

    def to_json(self) -> object:
        return {
            "id": self.id,
            "username": self.name,
            "gm": self.is_gm,
            "avatar": self.avatar,
        }
