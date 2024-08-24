from flask import redirect, url_for, current_app, session, abort
from website import app, db
from website.models import User
import functools


def who():
    """
    Init session with user information from Discord API.
    """
    if "user_id" in session:
        user = db.get_or_404(User, str(session["user_id"]))
        session["user_id"] = user.id
        session["username"] = user.name
        session["avatar"] = user.avatar
        session["is_gm"] = user.is_gm
        session["is_admin"] = user.is_admin
        session["is_player"] = user.is_player
    return session


def login_required(view):
    """
    View decorator that redirects to 403 is not logged-in.
    """

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            abort(403)
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
    return redirect(url_for("search_games"))


@app.route("/callback/")
def callback():
    """
    Login callback redirect to homepage.
    """
    current_app.discord.callback()
    if current_app.discord.authorized:
        uid = current_app.discord.fetch_user().id
        try:
            user = db.get_or_404(User, str(uid))
        except Exception:
            user = User(id=str(uid))
            db.session.add(user)
            db.session.commit()
            user.init_on_load()
        if not user.is_player:
            abort(403)
        session["user_id"] = user.id
        session["username"] = user.name
        session["avatar"] = user.avatar
        session["is_gm"] = user.is_gm
        session["is_admin"] = user.is_admin
        session["is_player"] = user.is_player
    return redirect(url_for("search_games"))
