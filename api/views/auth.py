from flask import redirect, url_for, render_template, request
from flask import current_app, make_response, session
from flask_discord import DiscordOAuth2Session, requires_authorization, Unauthorized
from api import app


@app.route("/login/")
def login():
    return current_app.discord.create_session()


@app.route("/callback/")
def callback():
    current_app.discord.callback()
    return redirect(url_for(".me"))


@app.errorhandler(Unauthorized)
def redirect_unauthorized(e):
    return redirect(url_for("login"))
