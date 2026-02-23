"""JWT authentication for the QuestMaster API.

Provides token encode/decode, auth decorators, and token exchange endpoints.
"""

import functools
import logging
from datetime import datetime, timezone

import jwt
import requests
from flask import Blueprint, current_app, g, jsonify, request

from config.constants import DISCORD_API_BASE_URL
from website.exceptions import UnauthorizedError, ValidationError
from website.services.user import UserService

logger = logging.getLogger(__name__)

auth_bp = Blueprint("api_auth", __name__, url_prefix="/auth")


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def encode_token(payload: dict) -> str:
    """Encode a JWT token with the configured secret and algorithm.

    Args:
        payload: Claims to include in the token.

    Returns:
        Encoded JWT string.
    """
    return jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )


def decode_token(token: str, *, allow_expired: bool = False) -> dict:
    """Decode and verify a JWT token.

    Args:
        token: Encoded JWT string.
        allow_expired: If True, accept expired tokens (for refresh flow).

    Returns:
        Decoded payload dictionary.

    Raises:
        UnauthorizedError: If token is invalid or expired.
    """
    options = {}
    if allow_expired:
        options["verify_exp"] = False
    try:
        return jwt.decode(
            token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=[current_app.config["JWT_ALGORITHM"]],
            options=options,
        )
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Token has expired", action="decode_token")
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError(f"Invalid token: {exc}", action="decode_token")


def _mint_token(user, user_service: UserService) -> dict:
    """Mint a JWT access token for the given user.

    Roles are included in the token for client-side convenience (e.g. UI
    decisions), but are **not** trusted for server-side authorization.
    Role-gated decorators verify roles live against the 5-minute Discord
    cache via ``refresh_roles()`` / ``get_user_roles()``, matching the
    monolith behaviour.

    Args:
        user: User ORM instance (must have refresh_roles called beforehand).
        user_service: UserService instance (unused, reserved for future claims).

    Returns:
        Dict with ``access_token`` and ``expires_in`` keys.
    """
    expires_delta = current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "is_gm": getattr(user, "is_gm", False),
        "is_admin": getattr(user, "is_admin", False),
        "is_player": getattr(user, "is_player", False),
        "iat": now,
        "exp": now + expires_delta,
    }
    token = encode_token(payload)
    return {"access_token": token, "expires_in": int(expires_delta.total_seconds())}


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------


def api_login_required(fn):
    """Require a valid JWT Bearer token and populate ``g.current_user``.

    Stores the decoded JWT payload in ``g.current_user`` (no DB hit).

    Raises:
        UnauthorizedError: If the Authorization header is missing or invalid.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise UnauthorizedError("Missing or invalid Authorization header", action="api_auth")
        token = auth_header[7:]
        g.current_user = decode_token(token)
        return fn(*args, **kwargs)

    return wrapper


def _load_and_refresh_user():
    """Load the full User from DB and refresh roles via the 5-min cache.

    Calls ``user.refresh_roles()`` which delegates to
    ``get_user_roles()`` — a function that caches Discord role data for
    5 minutes in Redis.  Within the cache window this is effectively
    free; only after expiry does it hit the Discord API.

    Returns:
        User ORM instance with up-to-date roles.

    Raises:
        UnauthorizedError: If the user no longer exists.
    """
    user_service = UserService()
    user = user_service.get_by_id(g.current_user["sub"])
    user.refresh_roles()
    return user


def require_gm(fn):
    """Require the authenticated user to have the GM role.

    Must be applied **after** ``@api_login_required``.  Performs a live
    role check using ``refresh_roles()`` (backed by a 5-minute Redis
    cache), so role changes are picked up even if the JWT has stale claims.

    Raises:
        UnauthorizedError: If the user is not a GM.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        user = _load_and_refresh_user()
        if not user.is_gm:
            raise UnauthorizedError("GM role required", action="require_gm")
        g.current_user_obj = user
        return fn(*args, **kwargs)

    return wrapper


def require_admin(fn):
    """Require the authenticated user to have the admin role.

    Must be applied **after** ``@api_login_required``.  Performs a live
    role check using ``refresh_roles()`` (backed by a 5-minute Redis
    cache), so role changes are picked up even if the JWT has stale claims.

    Raises:
        UnauthorizedError: If the user is not an admin.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        user = _load_and_refresh_user()
        if not user.is_admin:
            raise UnauthorizedError("Admin role required", action="require_admin")
        g.current_user_obj = user
        return fn(*args, **kwargs)

    return wrapper


# ---------------------------------------------------------------------------
# Discord user lookup
# ---------------------------------------------------------------------------


def _fetch_discord_user(discord_access_token: str) -> dict:
    """Fetch the current user from the Discord API using an OAuth2 token.

    Args:
        discord_access_token: OAuth2 access token obtained by the client.

    Returns:
        Discord user object dict (id, username, global_name, avatar, ...).

    Raises:
        ValidationError: If the Discord API rejects the token.
    """
    resp = requests.get(
        f"{DISCORD_API_BASE_URL}/users/@me",
        headers={"Authorization": f"Bearer {discord_access_token}"},
        timeout=10,
    )
    if resp.status_code != 200:
        raise ValidationError(
            "Invalid Discord access token",
            field="discord_access_token",
            details={"discord_status": resp.status_code},
        )
    return resp.json()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@auth_bp.route("/token/", methods=["POST"])
def exchange_token():
    """Exchange a Discord OAuth2 access token for a QuestMaster JWT.

    Expects JSON body: ``{"discord_access_token": "..."}``

    Returns:
        JSON ``{"access_token": "<jwt>", "expires_in": <seconds>}``

    Raises:
        ValidationError: If body is missing or Discord token is invalid.
    """
    data = request.get_json(silent=True) or {}
    discord_access_token = data.get("discord_access_token")
    if not discord_access_token:
        raise ValidationError("Missing discord_access_token", field="discord_access_token")

    discord_user = _fetch_discord_user(discord_access_token)

    user_service = UserService()
    user, _ = user_service.get_or_create(
        user_id=str(discord_user["id"]),
        name=discord_user.get("global_name") or discord_user.get("username", "Inconnu"),
        username=discord_user.get("username"),
    )
    user.refresh_roles()

    return jsonify(_mint_token(user, user_service)), 200


@auth_bp.route("/refresh/", methods=["POST"])
def refresh_token():
    """Refresh an expired JWT (within the configured refresh window).

    Expects a Bearer token in the Authorization header. The token may be
    expired but must have been issued within ``JWT_REFRESH_WINDOW``.

    Returns:
        JSON ``{"access_token": "<jwt>", "expires_in": <seconds>}``

    Raises:
        UnauthorizedError: If the token is outside the refresh window.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise UnauthorizedError("Missing or invalid Authorization header", action="refresh")

    token = auth_header[7:]
    payload = decode_token(token, allow_expired=True)

    issued_at = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    refresh_window = current_app.config["JWT_REFRESH_WINDOW"]

    if now - issued_at > refresh_window:
        raise UnauthorizedError("Token is too old to refresh", action="refresh")

    user_service = UserService()
    user = user_service.get_by_id(payload["sub"])
    user.refresh_roles()

    return jsonify(_mint_token(user, user_service)), 200
