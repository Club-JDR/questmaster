from flask import Flask
from flask_discord import DiscordOAuth2Session
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from datetime import timedelta
from website.utils.discord import Discord
import os

app = Flask(__name__)

# Configuration
app.secret_key = os.environ.get("FLASK_AUTH_SECRET")
app.config["DISCORD_CLIENT_ID"] = os.environ.get("DISCORD_CLIENT_ID")
app.config["DISCORD_CLIENT_SECRET"] = os.environ.get("DISCORD_CLIENT_SECRET")
app.config["DISCORD_BOT_TOKEN"] = os.environ.get("DISCORD_BOT_TOKEN")
app.config["DISCORD_REDIRECT_URI"] = os.environ.get("DISCORD_REDIRECT_URI")
app.config["DISCORD_GUILD_NAME"] = os.environ.get("DISCORD_GUILD_NAME")
app.config["DISCORD_GUILD_ID"] = os.environ.get("DISCORD_GUILD_ID")
app.config["DISCORD_GM_ROLE_ID"] = os.environ.get("DISCORD_GM_ROLE_ID")
app.config["DISCORD_ADMIN_ROLE_ID"] = os.environ.get("DISCORD_ADMIN_ROLE_ID")
app.config["DISCORD_PLAYER_ROLE_ID"] = os.environ.get("DISCORD_PLAYER_ROLE_ID")
app.config["POSTS_CHANNEL_ID"] = os.environ.get("POSTS_CHANNEL_ID")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"""postgresql://{os.environ.get("POSTGRES_USER")}:{os.environ.get("POSTGRES_PASSWORD")}@{os.environ.get("POSTGRES_HOST")}:5432/{os.environ.get("POSTGRES_DB")}"""
app.config["CACHE_TYPE"] = "RedisCache"
app.config["CACHE_REDIS_HOST"] = os.environ.get("REDIS_HOST")
app.config["CACHE_REDIS_PORT"] = 6379
app.config["CACHE_REDIS_DB"] = 0
app.json.compact = False

# Database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Cache
cache = Cache(app)
cache.init_app(app)

# OAuth
discord = DiscordOAuth2Session(app)
global bot
bot = Discord(app.config["DISCORD_GUILD_ID"], app.config["DISCORD_BOT_TOKEN"])

# OAuth2 must make use of HTTPS in production environment.
os.environ[
    "OAUTHLIB_INSECURE_TRANSPORT"
] = "true"  # !! Remove on production or if not using a reverse proxy as cert bearer.

# CSRF
csrf = CSRFProtect()
csrf.init_app(app)

# API import
from website.views import auth, health, games, systems, vtts, filters, errors, stats, channels
