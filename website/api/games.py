"""Game endpoints for the QuestMaster API (read + CRUD)."""

from flask import Blueprint, g, jsonify, request
from marshmallow import ValidationError as MarshmallowValidationError

from website.api.auth import api_login_required, load_current_user
from website.api.pagination import paginated_response, parse_pagination_args
from website.api.schemas import game_schema
from website.exceptions import UnauthorizedError, ValidationError
from website.services.game import GameService

games_bp = Blueprint("api_games", __name__)

# Service instance
game_service = GameService()


def _validate_game_payload(*, partial: bool) -> dict:
    """Validate the JSON request body against the game schema.

    Args:
        partial: If True, allow a subset of fields (for PATCH updates).

    Returns:
        Validated data with clean field names.

    Raises:
        ValidationError: If the body is missing or fails validation.
    """
    payload = request.get_json(silent=True)
    if payload is None:
        raise ValidationError("Request body must be valid JSON.")
    try:
        return game_schema.load(payload, partial=partial)
    except MarshmallowValidationError as err:
        raise ValidationError("Invalid game data.", details={"fields": err.messages})


def _clean_to_service_data(clean: dict) -> dict:
    """Map a validated, clean payload onto the form-shaped dict the service expects.

    ``GameService.create`` / ``.update`` were written against form data, so
    they read ``system``/``vtt`` keys, ``class-<key>`` entries, individual
    ambience flags, and treat ``party_selection`` as a presence check. This
    helper localises that translation in the API layer.

    Args:
        clean: Validated data using clean field names.

    Returns:
        Dict shaped like the legacy form submission.
    """
    data = {}

    # Type: special events are encoded as "specialevent-<id>" oneshots.
    special_event_id = clean.get("special_event_id")
    data["type"] = f"specialevent-{special_event_id}" if special_event_id else clean["type"]

    data["name"] = clean["name"]
    data["length"] = clean["length"]
    data["system"] = clean["system_id"]
    if clean.get("vtt_id"):
        data["vtt"] = clean["vtt_id"]
    data["description"] = clean["description"]
    data["restriction"] = clean["restriction"]
    if clean.get("restriction_tags"):
        data["restriction_tags"] = clean["restriction_tags"]
    data["party_size"] = clean["party_size"]
    if clean.get("party_selection"):
        data["party_selection"] = True
    data["xp"] = clean["xp"]
    date_value = clean["date"]
    data["date"] = date_value.isoformat() if hasattr(date_value, "isoformat") else date_value
    data["session_length"] = clean["session_length"]
    if clean.get("frequency"):
        data["frequency"] = clean["frequency"]
    data["characters"] = clean["characters"]
    if clean.get("complement"):
        data["complement"] = clean["complement"]
    if clean.get("img"):
        data["img"] = clean["img"]

    for key, value in (clean.get("classification") or {}).items():
        data[f"class-{key}"] = value
    for ambience in clean.get("ambience") or []:
        data[ambience] = True

    return data


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


def _require_game_editor(slug):
    """Load a game and ensure the current user may modify it.

    Authorization mirrors the server-rendered views: the game's GM or any
    admin. Roles are checked live (cache-backed) rather than from JWT claims.

    Args:
        slug: URL-safe game identifier.

    Returns:
        Tuple of (Game, User) — the game and the authenticated user.

    Raises:
        NotFoundError: If the game does not exist.
        UnauthorizedError: If the user is neither the GM nor an admin.
    """
    user = load_current_user()
    game = game_service.get_by_slug(slug)
    if game.gm_id != user.id and not user.is_admin:
        raise UnauthorizedError(
            "Only the game's GM or an admin can modify this game.",
            action="modify_game",
        )
    return game, user


@games_bp.route("/games/", methods=["POST"])
@api_login_required
def create_game():
    """Create a new game as a draft.

    The authenticated user becomes the GM. Discord resources are not created
    and the game is not published — use the lifecycle endpoints for that.

    Returns:
        JSON game object with relationships, HTTP 201.

    Raises:
        UnauthorizedError: If the user is not a GM or admin.
        ValidationError: If the request body is invalid.
    """
    user = load_current_user()
    if not (user.is_gm or user.is_admin):
        raise UnauthorizedError(
            "GM or admin role required to create a game.", action="create_game"
        )

    validated = _validate_game_payload(partial=False)
    service_data = _clean_to_service_data(validated)

    game = game_service.create(service_data, user.id)
    return jsonify(game.to_dict(include_relationships=True)), 201


@games_bp.route("/games/<slug>/", methods=["PATCH"])
@api_login_required
def update_game(slug):
    """Update an existing game.

    Accepts a partial body; omitted fields keep their current values. Note
    that the service only applies name/type changes while the game is a draft.

    Args:
        slug: URL-safe game identifier.

    Returns:
        JSON game object with relationships, HTTP 200.

    Raises:
        NotFoundError: If the game does not exist.
        UnauthorizedError: If the user is neither the GM nor an admin.
        ValidationError: If the request body is invalid.
    """
    game, user = _require_game_editor(slug)

    validated = _validate_game_payload(partial=True)
    editable_keys = set(game_schema.fields.keys())
    current = {k: v for k, v in game.to_dict().items() if k in editable_keys}
    service_data = _clean_to_service_data({**current, **validated})

    updated = game_service.update(slug, service_data, user_id=user.id)
    return jsonify(updated.to_dict(include_relationships=True)), 200


@games_bp.route("/games/<slug>/", methods=["DELETE"])
@api_login_required
def delete_game(slug):
    """Permanently delete a game.

    Args:
        slug: URL-safe game identifier.

    Returns:
        Empty body, HTTP 204.

    Raises:
        NotFoundError: If the game does not exist.
        UnauthorizedError: If the user is neither the GM nor an admin.
    """
    _require_game_editor(slug)
    game_service.delete(slug)
    return "", 204
