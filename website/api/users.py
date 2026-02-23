"""Read-only user endpoints for the QuestMaster API."""

from flask import Blueprint, g, jsonify

from website.api.auth import api_login_required
from website.services.trophy import TrophyService
from website.services.user import UserService

users_bp = Blueprint("api_users", __name__)

# Service instances
user_service = UserService()
trophy_service = TrophyService()


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
