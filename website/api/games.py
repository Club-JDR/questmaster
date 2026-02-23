"""Read-only game endpoints for the QuestMaster API."""

from flask import Blueprint, g, jsonify, request

from website.api.auth import api_login_required
from website.api.pagination import paginated_response, parse_pagination_args
from website.services.game import GameService

games_bp = Blueprint("api_games", __name__)

# Service instance
game_service = GameService()


@games_bp.route("/games/", methods=["GET"])
@api_login_required
def list_games():
    """List games with filtering and pagination.

    Query parameters:
        status: One or more statuses (default: open, closed).
        type: One or more types (oneshot, campaign).
        restriction: One or more restrictions (all, 16+, 18+).
        name: Free-text name search.
        system_id: Filter by system ID.
        vtt_id: Filter by VTT ID.
        gm_id: Filter by GM user ID.
        player_id: Filter by player user ID.
        special_event_id: Filter by special event ID.
        page: Page number (default: 1).
        per_page: Items per page (default: 20, max: 100).

    Returns:
        Paginated list of game objects.
    """
    page, per_page = parse_pagination_args()

    filters = {}

    status = request.args.getlist("status")
    if status:
        filters["status"] = status

    game_type = request.args.getlist("type")
    if game_type:
        filters["game_type"] = game_type

    restriction = request.args.getlist("restriction")
    if restriction:
        filters["restriction"] = restriction

    if request.args.get("name"):
        filters["name"] = request.args["name"]

    if request.args.get("system_id"):
        filters["system_id"] = request.args.get("system_id", type=int)

    if request.args.get("vtt_id"):
        filters["vtt_id"] = request.args.get("vtt_id", type=int)

    if request.args.get("gm_id"):
        filters["gm_id"] = request.args["gm_id"]

    if request.args.get("player_id"):
        filters["player_id"] = request.args["player_id"]

    if request.args.get("special_event_id"):
        filters["special_event_id"] = request.args.get("special_event_id", type=int)

    # Map JWT claims to the user_payload format expected by the repository
    user_payload = {
        "user_id": g.current_user["sub"],
        "is_admin": g.current_user.get("is_admin", False),
    }

    games, total = game_service.search(filters, page, per_page, user_payload)
    return paginated_response([game.to_dict() for game in games], total, page, per_page)


@games_bp.route("/games/<slug>/", methods=["GET"])
@api_login_required
def get_game(slug):
    """Get a game by slug with full relationship data.

    Args:
        slug: URL-safe game identifier.

    Returns:
        JSON game object with relationships (gm, system, vtt, players, sessions).

    Raises:
        NotFoundError: If game does not exist.
    """
    game = game_service.get_by_slug(slug)
    return jsonify(game.to_dict(include_relationships=True))


@games_bp.route("/games/<slug>/sessions/", methods=["GET"])
@api_login_required
def list_game_sessions(slug):
    """List sessions for a game.

    Args:
        slug: URL-safe game identifier.

    Returns:
        JSON array of session objects.

    Raises:
        NotFoundError: If game does not exist.
    """
    game = game_service.get_by_slug(slug)
    return jsonify([s.to_dict() for s in game.sessions])


@games_bp.route("/games/<slug>/events/", methods=["GET"])
@api_login_required
def list_game_events(slug):
    """List audit events for a game.

    Args:
        slug: URL-safe game identifier.

    Returns:
        JSON array of game event objects.

    Raises:
        NotFoundError: If game does not exist.
    """
    game = game_service.get_by_slug(slug)
    return jsonify([e.to_dict() for e in game.events])
