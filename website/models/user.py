from website import db, bot
from sqlalchemy import orm
from flask import current_app

AVATAR_BASE_URL = "https://cdn.discordapp.com/avatars/{}/{}"


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.String(), primary_key=True)
    games_gm = db.relationship("Game", backref="gm")

    def __init__(self, id):
        self.id = id

    @orm.reconstructor
    def init_on_load(self):
        """
        Get informations from Discord API not the database when the oject is loaded.
        """
        result = bot.get_user(self.id)
        if result["nick"] == None:
            self.name = result["user"]["username"]
        else:
            self.name = result["nick"]
        self.is_gm = current_app.config["DISCORD_GM_ROLE_ID"] in result["roles"]
        self.avatar = AVATAR_BASE_URL.format(self.id, result["user"]["avatar"])

    def serialize(self) -> object:
        return {
            "id": self.id,
            "username": self.name,
            "gm": self.is_gm,
            "avatar": self.avatar,
        }
