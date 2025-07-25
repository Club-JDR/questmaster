from website.extensions import db, cache
from sqlalchemy import orm
from flask import current_app
from website.bot import get_bot
import re, requests

AVATAR_BASE_URL = "https://cdn.discordapp.com/avatars/{}/{}"


def get_user_profile(user_id):
    """
    Returns profile info (name/avatar), cached for 24 hours.
    """
    cache_key = f"user_profile_{user_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    bot = get_bot()
    user_data = bot.get_user(user_id)
    profile = {
        "nick": user_data.get("nick"),
        "username": user_data["user"].get("username"),
        "global_name": user_data["user"].get("global_name"),
        "avatar": user_data["user"].get("avatar"),
    }
    cache.set(cache_key, profile, timeout=60 * 60 * 24)  # 24 hours
    return profile


def get_user_roles(user_id):
    """
    Returns roles, cached for 5 minutes.
    """
    cache_key = f"user_roles_{user_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    bot = get_bot()
    user_data = bot.get_user(user_id)
    roles = user_data.get("roles", [])
    cache.set(cache_key, roles, timeout=300)  # 5 minutes
    return roles


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.String(), primary_key=True)
    name = db.Column(db.String(), nullable=False, index=True)
    games_gm = db.relationship("Game", back_populates="gm")
    trophies = db.relationship(
        "UserTrophy", back_populates="user", cascade="all, delete-orphan"
    )

    def __init__(self, id, name="Inconnu"):
        if not re.fullmatch(r"\d{17,21}", id):
            raise ValueError(f"{id} is not a valid Discord UID.")
        self.id = id
        self.name = name

    def __repr__(self):
        return f"{self.name} <{self.id}>"

    @property
    def display_name(self):
        if not self.name or self.name == "Inconnu":
            try:
                profile = get_user_profile(self.id)
                if profile["nick"]:
                    return profile["nick"]
                return profile["global_name"] or profile["username"]
            except Exception:
                return f"<{self.id}>"
        return self.name

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
        Load lightweight user data: name and avatar only.
        """
        profile = get_user_profile(self.id)
        self.avatar = "/static/img/avatar.webp"
        try:
            if profile["nick"] is None:
                self.name = profile["global_name"] or profile["username"]
            else:
                self.name = profile["nick"]

            avatar_url = AVATAR_BASE_URL.format(self.id, profile["avatar"])
            try:
                response = requests.head(avatar_url)
                if response.status_code == 200:
                    self.avatar = avatar_url
            except requests.RequestException:
                pass
        except Exception:
            self.name = "Inconnu"

    def refresh_roles(self):
        """
        Refresh role info from Discord (cached for 5 minutes).
        """
        try:
            roles = get_user_roles(self.id)
            self.is_gm = current_app.config["DISCORD_GM_ROLE_ID"] in roles
            self.is_admin = current_app.config["DISCORD_ADMIN_ROLE_ID"] in roles
            self.is_player = current_app.config["DISCORD_PLAYER_ROLE_ID"] in roles
        except Exception:
            self.is_gm = False
            self.is_admin = False
            self.is_player = False
