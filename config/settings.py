"""Flask application settings loaded from environment variables."""

import os
from datetime import timedelta

GAMES_PER_PAGE = 12


class Settings:
    """Flask configuration class.

    All values are read from environment variables at import time.
    """

    DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID")
    DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET")
    DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
    DISCORD_REDIRECT_URI = os.environ.get("DISCORD_REDIRECT_URI")
    DISCORD_GUILD_NAME = os.environ.get("DISCORD_GUILD_NAME")
    DISCORD_GUILD_ID = os.environ.get("DISCORD_GUILD_ID")
    DISCORD_GM_ROLE_ID = os.environ.get("DISCORD_GM_ROLE_ID")
    DISCORD_ADMIN_ROLE_ID = os.environ.get("DISCORD_ADMIN_ROLE_ID")
    DISCORD_PLAYER_ROLE_ID = os.environ.get("DISCORD_PLAYER_ROLE_ID")
    POSTS_CHANNEL_ID = os.environ.get("POSTS_CHANNEL_ID")
    ADMIN_CHANNEL_ID = os.environ.get("ADMIN_CHANNEL_ID")
    SQLALCHEMY_DATABASE_URI = f"""postgresql://{os.environ.get("POSTGRES_USER")}:{os.environ.get("POSTGRES_PASSWORD")}@{os.environ.get("POSTGRES_HOST")}:5432/{os.environ.get("POSTGRES_DB")}"""
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_HOST = os.environ.get("REDIS_HOST")
    CACHE_REDIS_PORT = 6379
    CACHE_REDIS_DB = 0
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    CACHE_KEY_PREFIX = "QuestMaster:"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
