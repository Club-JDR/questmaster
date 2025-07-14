from website.extensions import db, cache
from sqlalchemy import orm
from flask import current_app
from website.bot import get_bot
from website.utils.logger import logger
import re, requests

AVATAR_BASE_URL = "https://cdn.discordapp.com/avatars/{}/{}"


@cache.memoize()
def get_user(user_id):
    bot = get_bot()
    return bot.get_user(user_id)


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.String(), primary_key=True)
    games_gm = db.relationship("Game", backref="gm")
    trophies = db.relationship(
        "UserTrophy", back_populates="user", cascade="all, delete-orphan"
    )

    def __init__(self, id):
        if not re.fullmatch(r"\d{17,21}", id):
            raise ValueError(f"{id} is not a valid Discord UID.")
        self.id = id

    @property
    def trophy_summary(self):
        summary = []
        for ut in self.trophies:
            summary.append(
                {
                    "name": ut.trophy.name,
                    "icon": ut.trophy.icon,
                    "quantity": ut.quantity,
                }
            )
        return summary

    @orm.reconstructor
    def init_on_load(self):
        """
        Retrieve distant data on user when the oject is loaded.
        """
        result = get_user(self.id)
        self.avatar = "/static/img/avatar.webp"
        try:
            if result["nick"] == None:
                if result["user"]["global_name"] == None:
                    self.name = result["user"]["username"]
                else:
                    self.name = result["user"]["global_name"]
            else:
                self.name = result["nick"]
            self.is_gm = current_app.config["DISCORD_GM_ROLE_ID"] in result["roles"]
            self.is_admin = (
                current_app.config["DISCORD_ADMIN_ROLE_ID"] in result["roles"]
            )
            self.is_player = (
                current_app.config["DISCORD_PLAYER_ROLE_ID"] in result["roles"]
            )
            avatar_url = AVATAR_BASE_URL.format(self.id, result["user"]["avatar"])
            try:
                response = requests.head(avatar_url)
                if response.status_code == 200:
                    self.avatar = avatar_url
            except requests.RequestException:
                pass
        except Exception:
            self.name = "Inconnu"
            self.is_gm = False
            self.is_admin = False
            self.is_player = False
