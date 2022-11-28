from flask import Flask
from flask_discord import DiscordOAuth2Session
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from api.utils.discord import Discord
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
app.config["CATEGORIES_CHANNEL_ID"] = os.environ.get("CATEGORIES_CHANNEL_ID")
app.config["POSTS_CHANNEL_ID"] = os.environ.get("POSTS_CHANNEL_ID")
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"""postgresql://{os.environ.get("POSTGRES_USER")}:{os.environ.get("POSTGRES_PASSWORD")}@{os.environ.get("POSTGRES_HOST")}:5432/{os.environ.get("POSTGRES_DB")}"""
app.json.compact = False

# Database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# OAuth
discord = DiscordOAuth2Session(app)
global bot
bot = Discord(app.config["DISCORD_GUILD_ID"], app.config["DISCORD_BOT_TOKEN"])

if "https" not in app.config["DISCORD_REDIRECT_URI"]:
    # OAuth2 must make use of HTTPS in production environment.
    os.environ[
        "OAUTHLIB_INSECURE_TRANSPORT"
    ] = "true"  # !! Only in development environment.

# CSRF
csrf = CSRFProtect()
csrf.init_app(app)

# API import
from api.routes import auth, health, users, games
