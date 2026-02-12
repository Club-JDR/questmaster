import re

import requests
from flask import current_app, has_request_context, request
from sqlalchemy import orm

from config.constants import AVATAR_BASE_URL, DEFAULT_AVATAR
from website.bot import get_bot
from website.exceptions import ValidationError
from website.extensions import cache, db
from website.models.base import SerializableMixin


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

        profile = {"name": name, "avatar": avatar_url}
        cache.set(cache_key, profile, timeout=60 * 60 * 24)
        return profile

    except Exception as e:
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


class User(db.Model, SerializableMixin):
    __tablename__ = "user"

    _exclude_fields = []
    _relationship_fields = ["games_gm", "trophies"]

    id = db.Column(db.String(), primary_key=True)
    name = db.Column(db.String(), nullable=False, index=True)
    games_gm = db.relationship("Game", back_populates="gm")
    trophies = db.relationship("UserTrophy", back_populates="user", cascade="all, delete-orphan")

    def __init__(self, id, name="Inconnu"):
        if not re.fullmatch(r"\d{17,21}", id):
            raise ValidationError("Invalid Discord UID.", field="id", details={"value": id})
        self.id = id
        self.name = name

    @property
    def display_name(self):
        """Display-friendly name, fetching from Discord if necessary."""
        if not self.name or self.name == "Inconnu":
            try:
                profile = get_user_profile(self.id)
                self.name = profile["name"]
            except Exception:
                return f"<@{self.id}>"
        return f"{self.name} <@{self.id}>"

    @property
    def trophy_summary(self):
        """Return a list summarizing all trophies of the user."""
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
        Initialize user data after loading from the database.

        Skips expensive Discord lookups when in admin context.
        """
        self.avatar = getattr(self, "avatar", DEFAULT_AVATAR)
        self.is_gm = False
        self.is_admin = False
        self.is_player = False

        if not has_request_context():
            profile = get_user_profile(self.id)
            self.name = profile["name"]
            self.avatar = profile["avatar"]
            return

        if request.path.startswith("/admin"):
            if not getattr(self, "name", None):
                self.name = "Inconnu"
            return

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

    def _serialize_relationship(self, rel_value):
        """Helper to serialize a relationship value (single object or list)."""
        if rel_value is None:
            return None
        if isinstance(rel_value, list):
            return [
                item.to_dict() if hasattr(item, "to_dict") else str(item) for item in rel_value
            ]
        if hasattr(rel_value, "to_dict"):
            return rel_value.to_dict()
        return str(rel_value)

    def _add_relationships_to_dict(self, data):
        """Add relationship data to the dictionary."""
        for rel_name in self._relationship_fields:
            rel_value = getattr(self, rel_name, None)
            data[rel_name] = self._serialize_relationship(rel_value)

    def to_dict(self, include_relationships=False):
        """
        Serialize the User instance into a Python dict.
        Includes dynamic attributes (avatar, roles) not stored in the database.
        """
        data = {
            "id": self.id,
            "name": self.name,
            "avatar": getattr(self, "avatar", DEFAULT_AVATAR),
            "is_gm": getattr(self, "is_gm", False),
            "is_admin": getattr(self, "is_admin", False),
            "is_player": getattr(self, "is_player", False),
        }

        if include_relationships:
            self._add_relationships_to_dict(data)

        return data

    @classmethod
    def from_dict(cls, data: dict):
        """
        Create a User object from a dictionary.

        Expected keys: "id" (required), "name" (optional).
        Additional keys (avatar/is_gm/is_admin/is_player) will be set as attributes
        on the created instance if present.
        """
        if "id" not in data:
            raise ValidationError("Missing id when creating User from dict.", field="id")
        user = cls(id=str(data["id"]), name=data.get("name", "Inconnu"))

        # Optional attrs that are convenient to set from API payloads
        if "avatar" in data:
            user.avatar = data["avatar"]
        if "is_gm" in data:
            user.is_gm = bool(data["is_gm"])
        if "is_admin" in data:
            user.is_admin = bool(data["is_admin"])
        if "is_player" in data:
            user.is_player = bool(data["is_player"])

        return user

    @classmethod
    def from_json(cls, data):
        """
        Alias for from_dict() for API compatibility.
        """
        return cls.from_dict(data)

    def update_from_dict(self, data: dict):
        """Update the user from a dictionary of fields."""
        for field in ["name"]:
            if field in data:
                setattr(self, field, data[field])

    def __repr__(self):
        return f"{self.name} <{self.id}>"

    def __eq__(self, other):
        if not isinstance(other, User):
            return NotImplemented
        return self.id == other.id and self.name == other.name

    def __ne__(self, other):
        return not self.__eq__(other)
