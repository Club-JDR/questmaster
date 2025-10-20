from website.extensions import db, cache
from sqlalchemy import orm
from flask import current_app, has_request_context, request
from website.bot import get_bot
import re, requests

AVATAR_BASE_URL = "https://cdn.discordapp.com/avatars/{}/{}"
DEFAULT_AVATAR = "/static/img/avatar.webp"


def get_user_profile(user_id, force_refresh=False):
    """
    Returns parsed profile info (name and avatar_url), cached for 24h.

    If force_refresh=True, ignores the cache and fetches fresh data from Discord.
    """
    cache_key = f"user_profile_{user_id}"

    if not force_refresh:
        cached = cache.get(cache_key)
        if cached:
            return cached

    bot = get_bot()
    try:
        user_data = bot.get_user(user_id)
        if not user_data or "user" not in user_data:
            raise ValueError(f"Invalid user data for {user_id}: {user_data}")

        user = user_data["user"]

        if user_data.get("nick"):
            name = user_data["nick"]
        else:
            name = user.get("global_name") or user.get("username") or "Inconnu"

        avatar_url = DEFAULT_AVATAR
        avatar_hash = user.get("avatar")
        if avatar_hash:
            potential_url = AVATAR_BASE_URL.format(user_id, avatar_hash)
            try:
                response = requests.head(potential_url)
                if response.status_code == 200:
                    avatar_url = potential_url
            except requests.RequestException:
                pass

        profile = {
            "name": name,
            "avatar": avatar_url,
        }

        cache.set(cache_key, profile, timeout=60 * 60 * 24)
        return profile

    except Exception as e:
        from flask import current_app

        current_app.logger.warning(f"[get_user_profile] Failed for user {user_id}: {e}")
        return {"name": "Inconnu", "avatar": DEFAULT_AVATAR, "raw": None}


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
                self.name = profile["name"]
            except Exception:
                return f"<@{self.id}>"
        return f"{self.name} <@{self.id}>"

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
        Initialize user data. Skip expensive Discord lookups inside admin views.
        """
        # Always ensure safe defaults
        self.avatar = getattr(self, "avatar", DEFAULT_AVATAR)
        self.is_gm = False
        self.is_admin = False
        self.is_player = False

        # If not in a request context (CLI, background task), do normal behavior
        if not has_request_context():
            profile = get_user_profile(self.id)
            self.name = profile["name"]
            self.avatar = profile["avatar"]
            return

        # If in admin: skip network/cache calls to speed up
        if request.path.startswith("/admin"):
            # Don’t call Redis or Discord
            if not getattr(self, "name", None):
                self.name = "Inconnu"
            return

        # Otherwise (normal frontend routes, API, etc.): do normal cached profile lookup
        try:
            profile = get_user_profile(self.id)
            self.name = profile["name"]
            self.avatar = profile["avatar"]
        except Exception:
            if not getattr(self, "name", None):
                self.name = "Inconnu"
            self.avatar = DEFAULT_AVATAR

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
