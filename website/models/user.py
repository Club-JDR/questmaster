from website.extensions import db, cache
from sqlalchemy import orm
from flask import current_app
from website.bot import get_bot


AVATAR_BASE_URL = "https://cdn.discordapp.com/avatars/{}/{}"


@cache.memoize()
def get_user(user_id):
    """
    Wrapper to get user info from cache or Discord API.
    """
    bot = get_bot()
    return bot.get_user(user_id)


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.String(), primary_key=True)
    games_gm = db.relationship("Game", backref="gm")

    def __init__(self, id):
        self.id = id

    @orm.reconstructor
    def init_on_load(self):
        """
        Retrieve distant data on user when the oject is loaded.
        """
        result = get_user(self.id)
        try:
            if result["nick"] == None:
                self.name = result["user"]["username"]
            else:
                self.name = result["nick"]
            self.is_gm = current_app.config["DISCORD_GM_ROLE_ID"] in result["roles"]
            self.is_admin = (
                current_app.config["DISCORD_ADMIN_ROLE_ID"] in result["roles"]
            )
            self.is_player = (
                current_app.config["DISCORD_PLAYER_ROLE_ID"] in result["roles"]
            )
            self.avatar = AVATAR_BASE_URL.format(self.id, result["user"]["avatar"])
        except Exception:
            self.name = "Inconnu"
            self.is_gm = False
            self.is_admin = False
            self.is_player = False
            self.avatar = "/static/img/avatar.webp"
