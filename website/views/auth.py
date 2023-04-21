from flask import redirect, url_for, current_app, session
from website import app, db
from website.models import User
import functools


def who():
    """
    Init session with user information from Discord API.
    """
    payload = {}
    if "username" in session:
        payload["user_id"] = session["user_id"]
        payload["username"] = session["username"]
        payload["avatar"] = session["avatar"]
        payload["is_gm"] = session["is_gm"]
    return session


def login_required(view):
    """
    View decorator that redirects unauthoried users to the login page.
    """

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not current_app.discord.authorized:
            return redirect(url_for("login"))
        return view(**kwargs)

    return wrapped_view


@app.route("/login/")
def login():
    """
    Login using Discord OAuth2.
    """
    session.permanent = True
    return current_app.discord.create_session()


@app.route("/logout/")
def logout():
    """
    Logout by removing username from session.
    """
    session.clear()
    current_app.discord.revoke()
    return redirect(url_for("open_games"))


@app.route("/callback/")
def callback():
    """
    Login callback redirect to homepage.
    """
    current_app.discord.callback()
    if current_app.discord.authorized:
        uid = current_app.discord.fetch_user().id
        user = User.query.get(str(uid))
        if user == None:
            user = User(id=str(uid))
            db.session.add(user)
            db.session.commit()
        session["user_id"] = user.id
        session["username"] = user.name
        session["avatar"] = user.avatar
        session["is_gm"] = user.is_gm
    return redirect(url_for("open_games"))
