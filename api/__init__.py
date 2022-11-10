from flask import Flask, redirect, url_for
from flask_discord import DiscordOAuth2Session, requires_authorization, Unauthorized
import os
import locale

app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_AUTH_SECRET")
app.config["DISCORD_CLIENT_ID"] = os.environ.get("DISCORD_CLIENT_ID")
app.config["DISCORD_CLIENT_SECRET"] = os.environ.get("DISCORD_CLIENT_SECRET")
app.config["DISCORD_BOT_TOKEN"] = os.environ.get("DISCORD_BOT_TOKEN")
app.config["DISCORD_REDIRECT_URI"] = os.environ.get("DISCORD_REDIRECT_URI")
app.config["DISCORD_GUILD_NAME"] = os.environ.get("DISCORD_GUILD_NAME")
app.config["DISCORD_GUILD_ID"] = os.environ.get("DISCORD_GUILD_ID")

discord = DiscordOAuth2Session(app)

if "https" not in app.config["DISCORD_REDIRECT_URI"]:
    # OAuth2 must make use of HTTPS in production environment.
    os.environ[
        "OAUTHLIB_INSECURE_TRANSPORT"
    ] = "true"  # !! Only in development environment.

from api.views import auth, health
from api.utils.discord import Discord
