"""Read-only user endpoints for the QuestMaster API."""

from flask import Blueprint, g, jsonify, request

from website.api.auth import api_login_required
from website.api.pagination import paginated_response, parse_pagination_args
from website.services.game import GameService
from website.services.trophy import TrophyService
from website.services.user import UserService

users_bp = Blueprint("api_users", __name__)

# Service instances
user_service = UserService()
trophy_service = TrophyService()
game_service = GameService()


@users_bp.route("/users/me/", methods=["GET"])
@api_login_required
def get_current_user():
    """Get the current authenticated user's profile.

    Returns:
        JSON user object.
    """
    user = user_service.get_by_id(g.current_user["sub"])
    return jsonify(user.to_dict())


@users_bp.route("/users/<user_id>/", methods=["GET"])
@api_login_required
def get_user(user_id):
    """Get a user by ID.

    Args:
        user_id: Discord user ID.

    Returns:
        JSON user object.

    Raises:
        NotFoundError: If user does not exist.
    """
    user = user_service.get_by_id(user_id)
    return jsonify(user.to_dict())


@users_bp.route("/users/<user_id>/badges/", methods=["GET"])
@api_login_required
def get_user_badges(user_id):
    """Get badges/trophies for a user.

    Args:
        user_id: Discord user ID.

    Returns:
        JSON array of badge objects with name, icon, and quantity.

    Raises:
        NotFoundError: If user does not exist.
    """
    # Verify user exists
    user_service.get_by_id(user_id)
    badges = trophy_service.get_user_badges(user_id)
    return jsonify(badges)


@users_bp.route("/users/me/games/", methods=["GET"])
@api_login_required
def get_my_games():
    """Get games where the current user is a registered player.

    Query parameters:
        status: One or more statuses (default: open, closed).
        type: One or more types (oneshot, campaign).
        page: Page number (default: 1).
        per_page: Items per page (default: 20, max: 100).

    Returns:
        Paginated list of game objects.
    """
    page, per_page = parse_pagination_args()
    user_id = g.current_user["sub"]

    filters = {"player_id": user_id}
    status = request.args.getlist("status")
    if status:
        filters["status"] = status
    game_type = request.args.getlist("type")
    if game_type:
        filters["game_type"] = game_type

    user_payload = {
        "user_id": user_id,
        "is_admin": g.current_user.get("is_admin", False),
    }

    games, total = game_service.search(filters, page, per_page, user_payload)
    return paginated_response(
        [game.to_dict(include_relationships=True) for game in games],
        total,
        page,
        per_page,
    )


@users_bp.route("/users/me/games/gm/", methods=["GET"])
@api_login_required
def get_my_gm_games():
    """Get games where the current user is the GM.

    Query parameters:
        status: One or more statuses (default: open, closed, draft).
        type: One or more types (oneshot, campaign).
        page: Page number (default: 1).
        per_page: Items per page (default: 20, max: 100).

    Returns:
        Paginated list of game objects.
    """
    page, per_page = parse_pagination_args()
    user_id = g.current_user["sub"]

    filters = {"gm_id": user_id}
    status = request.args.getlist("status")
    if status:
        filters["status"] = status
    game_type = request.args.getlist("type")
    if game_type:
        filters["game_type"] = game_type

    user_payload = {
        "user_id": user_id,
        "is_admin": g.current_user.get("is_admin", False),
    }

    games, total = game_service.search(filters, page, per_page, user_payload)
    return paginated_response(
        [game.to_dict(include_relationships=True) for game in games],
        total,
        page,
        per_page,
    )
