"""Authentication views and helpers for Discord OAuth2."""

import functools
from urllib.parse import urljoin, urlparse

import requests as http_requests
from flask import Blueprint, current_app, redirect, request, session, url_for

from config.constants import MSG_ADMIN_ACCESS_REQUIRED, SEARCH_GAMES_ROUTE
from website.exceptions import UnauthorizedError
from website.extensions import oauth
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
        session["permissions"] = sorted(user.permissions)
    return session


def login_required(view):
    """View decorator that redirects to login if not authenticated."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view


def admin_only(view):
    """View decorator restricting access to superuser admins.

    Used for admin sections that have no delegated capability (e.g. games,
    settings); delegated users that pass the blueprint guard via another
    capability are still rejected here.

    Args:
        view: The view function to protect.

    Returns:
        The wrapped view.
    """

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        if session.get("is_admin"):
            return view(**kwargs)
        raise UnauthorizedError(MSG_ADMIN_ACCESS_REQUIRED, action="admin")

    return wrapped_view


def require_permission(key):
    """View decorator requiring a specific RBAC capability (admins bypass).

    Redirects anonymous users to login; raises ``UnauthorizedError`` for an
    authenticated user lacking the capability.

    Args:
        key: Permission key the view requires.

    Returns:
        The view decorator.
    """

    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if "user_id" not in session:
                return redirect(url_for("auth.login"))
            if session.get("is_admin") or key in session.get("permissions", []):
                return view(**kwargs)
            raise UnauthorizedError(MSG_ADMIN_ACCESS_REQUIRED, action=key)

        return wrapped_view

    return decorator


@auth_bp.route("/login/", methods=["GET"])
def login():
    """Initiate Discord OAuth2 login flow."""
    session.permanent = True
    next_url = session.get("next_url") or request.referrer or url_for(SEARCH_GAMES_ROUTE)
    session["next_url"] = next_url
    redirect_uri = current_app.config["DISCORD_REDIRECT_URI"]
    return oauth.discord.authorize_redirect(redirect_uri)


@auth_bp.route("/logout/", methods=["GET"])
def logout():
    """Clear session and revoke Discord OAuth2 token."""
    token = session.get("_discord_token", {})
    access_token = token.get("access_token")
    session.clear()
    if access_token:
        _revoke_discord_token(access_token)
    return redirect(url_for(SEARCH_GAMES_ROUTE))


def _revoke_discord_token(access_token: str) -> None:
    """Revoke a Discord OAuth2 access token.

    Best-effort: failures are silently ignored so logout always succeeds.

    Args:
        access_token: The OAuth2 access token to revoke.
    """
    try:
        http_requests.post(
            "https://discord.com/api/oauth2/token/revoke",
            data={
                "token": access_token,
                "token_type_hint": "access_token",
                "client_id": current_app.config["DISCORD_CLIENT_ID"],
                "client_secret": current_app.config["DISCORD_CLIENT_SECRET"],
            },
            timeout=5,
        )
    except http_requests.RequestException:
        pass


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


@auth_bp.route("/callback/", methods=["GET"])
def callback():
    """Handle Discord OAuth2 callback and create user session."""
    token = oauth.discord.authorize_access_token()
    if token:
        resp = oauth.discord.get("users/@me", token=token)
        resp.raise_for_status()
        discord_user = resp.json()
        uid = discord_user["id"]
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
        session["permissions"] = sorted(user.permissions)
        session["_discord_token"] = dict(token)
    redirect_url = session.pop("next_url", url_for(SEARCH_GAMES_ROUTE))
    if not is_safe_url(redirect_url):
        redirect_url = url_for(SEARCH_GAMES_ROUTE)
    return redirect(redirect_url)
