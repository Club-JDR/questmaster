from flask import redirect, url_for
from flask import current_app
from flask_discord import Unauthorized
from api import app


@app.route("/login/")
def login():
    return current_app.discord.create_session()


@app.route("/callback/")
def callback():
    current_app.discord.callback()
    return redirect(url_for("health"))


@app.errorhandler(Unauthorized)
def redirect_unauthorized(e):
    return redirect(url_for("login"))
