from flask import redirect, url_for, session, abort, Blueprint
from website.extensions import db, discord
from website.models import User
import functools

auth_bp = Blueprint("auth", __name__)


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
        print("Getting user ", user.id, user.name, user.is_admin)
    return session


def login_required(view):
    """
    View decorator that redirects to 403 if not logged-in.
    """

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            abort(403)
        return view(**kwargs)

    return wrapped_view


@auth_bp.route("/login/")
def login():
    """
    Login using Discord OAuth2.
    """
    session.permanent = True
    return discord.create_session()


@auth_bp.route("/logout/")
def logout():
    """
    Logout by removing username from session.
    """
    session.clear()
    discord.revoke()
    return redirect(url_for("annonces.search_games"))


@auth_bp.route("/callback/")
def callback():
    """
    Login callback redirect to homepage.
    """
    discord.callback()
    if discord.authorized:
        uid = discord.fetch_user().id
        try:
            user = db.get_or_404(User, str(uid))
        except Exception:
            user = User(id=str(uid))
            db.session.add(user)
            db.session.commit()
            user.init_on_load()
        if not user.is_player:
            abort(403, "Vous n'êtes pas un·e joueur·euse sur le Discord Club JDR")
        session["user_id"] = user.id
        session["username"] = user.name
        session["avatar"] = user.avatar
        session["is_gm"] = user.is_gm
        session["is_admin"] = user.is_admin
        session["is_player"] = user.is_player
    return redirect(url_for("annonces.search_games"))
