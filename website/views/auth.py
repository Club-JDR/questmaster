from flask import redirect, url_for, session, abort, request, Blueprint
from urllib.parse import urlparse, urljoin
from website.extensions import db, discord
from website.models import User
from config import SEARCH_GAMES_ROUTE
import functools

auth_bp = Blueprint("auth", __name__)


def who():
    """
    Init session with user information from Discord API.
    """
    if "user_id" in session:
        user = db.get_or_404(User, str(session["user_id"]))
        user.refresh_roles()
        session["user_id"] = user.id
        session["username"] = user.name
        session["avatar"] = user.avatar
        session["is_gm"] = user.is_gm
        session["is_admin"] = user.is_admin
        session["is_player"] = user.is_player
    return session


def login_required(view):
    """
    View decorator that redirects to 403 if not logged-in.
    """

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view


@auth_bp.route("/login/")
def login():
    """
    Login using Discord OAuth2.
    """
    session.permanent = True
    next_url = (
        session.get("next_url") or request.referrer or url_for(SEARCH_GAMES_ROUTE)
    )
    session["next_url"] = next_url
    return discord.create_session()


@auth_bp.route("/logout/")
def logout():
    """
    Logout by removing username from session.
    """
    session.clear()
    discord.revoke()
    return redirect(url_for(SEARCH_GAMES_ROUTE))


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


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
            user.refresh_roles()
        except Exception:
            user = User(id=str(uid))
            db.session.add(user)
            db.session.commit()
            user.init_on_load()
            user.refresh_roles()
        if not user.is_player:
            abort(403, "Vous n'êtes pas un·e joueur·euse sur le Discord Club JDR")
        session["user_id"] = user.id
        session["username"] = user.name
        session["avatar"] = user.avatar
        session["is_gm"] = user.is_gm
        session["is_admin"] = user.is_admin
        session["is_player"] = user.is_player
    redirect_url = session.pop("next_url", url_for(SEARCH_GAMES_ROUTE))
    if not is_safe_url(redirect_url):
        redirect_url = url_for(SEARCH_GAMES_ROUTE)
    return redirect(redirect_url)
