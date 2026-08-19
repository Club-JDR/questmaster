"""Flask application settings loaded from environment variables."""

import os
from datetime import timedelta

GAMES_PER_PAGE = 12

# Environment variables the app cannot safely start without. Without this
# check, a missing FLASK_AUTH_SECRET only surfaces on the first session write
# (deep inside Flask), and missing Postgres variables silently produce
# "postgresql+psycopg://None:None@None:5432/None" as the DB URI.
REQUIRED_ENV_VARS = (
    "FLASK_AUTH_SECRET",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_HOST",
    "POSTGRES_DB",
)


def check_required_env_vars() -> None:
    """Fail fast if required environment variables are missing.

    Raises:
        RuntimeError: If one or more variables in `REQUIRED_ENV_VARS` are
            unset or empty, naming each missing variable.
    """
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        raise RuntimeError(
            "Missing required environment variable(s): "
            f"{', '.join(missing)}. Set them before starting the app."
        )


class Settings:
    """Flask configuration class.

    All values are read from environment variables at import time.
    """

    DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID")
    DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET")
    # Ed25519 public key used to verify Discord interaction signatures
    DISCORD_PUBLIC_KEY = os.environ.get("DISCORD_PUBLIC_KEY")
    # Discord application ID (equals the client ID for a single-app setup)
    DISCORD_APP_ID = os.environ.get("DISCORD_APP_ID", os.environ.get("DISCORD_CLIENT_ID"))
    DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
    DISCORD_REDIRECT_URI = os.environ.get("DISCORD_REDIRECT_URI")
    DISCORD_GUILD_NAME = os.environ.get("DISCORD_GUILD_NAME")
    DISCORD_GUILD_ID = os.environ.get("DISCORD_GUILD_ID")
    DISCORD_GM_ROLE_ID = os.environ.get("DISCORD_GM_ROLE_ID")
    DISCORD_ADMIN_ROLE_ID = os.environ.get("DISCORD_ADMIN_ROLE_ID")
    DISCORD_PLAYER_ROLE_ID = os.environ.get("DISCORD_PLAYER_ROLE_ID")
    POSTS_CHANNEL_ID = os.environ.get("POSTS_CHANNEL_ID")
    ADMIN_CHANNEL_ID = os.environ.get("ADMIN_CHANNEL_ID")
    SQLALCHEMY_DATABASE_URI = f"""postgresql+psycopg://{os.environ.get("POSTGRES_USER")}:{os.environ.get("POSTGRES_PASSWORD")}@{os.environ.get("POSTGRES_HOST")}:5432/{os.environ.get("POSTGRES_DB")}"""
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_HOST = os.environ.get("REDIS_HOST")
    CACHE_REDIS_PORT = 6379
    CACHE_REDIS_DB = 0
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    CACHE_KEY_PREFIX = "QuestMaster:"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Session cookie hardening. The app sits behind a TLS-terminating proxy
    # (see ProxyFix in website/__init__.py), so SECURE defaults on; only
    # local `flask run`/docker dev over plain HTTP needs to opt out via
    # QM_SESSION_COOKIE_SECURE=0.
    SESSION_COOKIE_SECURE = os.environ.get("QM_SESSION_COOKIE_SECURE", "1") == "1"
    SESSION_COOKIE_SAMESITE = "Lax"

    # Logging (see website/logging_config/)
    LOG_FORMAT = os.environ.get("QM_LOG_FORMAT", "human")  # "human" or "json"
    LOG_LEVEL = os.environ.get("QM_LOG_LEVEL", "INFO")
    DB_LOG_LEVEL = os.environ.get("QM_DB_LOG_LEVEL", "INFO")
    LOG_RETENTION_DAYS = int(os.environ.get("QM_LOG_RETENTION_DAYS", "30"))
    DISCORD_ERROR_WEBHOOK_URL = os.environ.get("DISCORD_ERROR_WEBHOOK_URL")

    # Scheduler (see website/scheduler.py). Only one process should run
    # background jobs; opt in per-process rather than defaulting on, so the web
    # workers never do (see the dedicated `scheduler` docker-compose service).
    RUN_SCHEDULER = os.environ.get("QM_RUN_SCHEDULER", "0") == "1"

    # JWT settings
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", os.environ.get("FLASK_AUTH_SECRET"))
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_WINDOW = timedelta(hours=24)
