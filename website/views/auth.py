"""Authentication views and helpers for Discord OAuth2."""

import functools
from urllib.parse import urljoin, urlparse

from flask import Blueprint, redirect, request, session, url_for

from config.constants import SEARCH_GAMES_ROUTE
from website.exceptions import UnauthorizedError
from website.extensions import discord
from website.services.user import UserService

auth_bp = Blueprint("auth", __name__)


def who():
    """Initialize session with user information from Discord API."""
    if "user_id" in session:
        user = UserService().get_by_id(str(session["user_id"]))
        user.refresh_roles()
        session["user_id"] = user.id
        session["username"] = user.name
        session["avatar"] = user.avatar
        session["is_gm"] = user.is_gm
        session["is_admin"] = user.is_admin
        session["is_player"] = user.is_player
    return session


def login_required(view):
    """View decorator that redirects to login if not authenticated."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view


@auth_bp.route("/login/")
def login():
    """Initiate Discord OAuth2 login flow."""
    session.permanent = True
    next_url = session.get("next_url") or request.referrer or url_for(SEARCH_GAMES_ROUTE)
    session["next_url"] = next_url
    return discord.create_session(scope=["identify"])


@auth_bp.route("/logout/")
def logout():
    """Clear session and revoke Discord OAuth2 token."""
    session.clear()
    discord.revoke()
    return redirect(url_for(SEARCH_GAMES_ROUTE))


def is_safe_url(target):
    """Check that the redirect target URL belongs to the same host.

    Args:
        target: URL string to validate.

    Returns:
        True if the URL is safe to redirect to.
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


@auth_bp.route("/callback/")
def callback():
    """Handle Discord OAuth2 callback and create user session."""
    discord.callback()
    if discord.authorized:
        uid = discord.fetch_user().id
        user, _ = UserService().get_or_create(str(uid))
        user.refresh_roles()
        if not user.is_player:
            raise UnauthorizedError(
                "User is not a player on the Discord server.",
                user_id=str(uid),
                action="login",
            )
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
