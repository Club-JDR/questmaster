"""Game filtering and search query helpers.

Extracted from views to enable reuse across views and future API endpoints.
"""

from datetime import datetime, timezone

from sqlalchemy import case
from sqlalchemy.sql import func, or_, and_

from config.constants import GAMES_PER_PAGE
from website.exceptions import ValidationError
from website.models import Game
from website.services.user import UserService


def parse_multi_checkbox_filter(source, keys):
    """Parse multi-checkbox filters from a request source.

    Args:
        source: Flask request.args or similar mapping.
        keys: List of checkbox keys to check.

    Returns:
        Tuple of (selected_filters list, args dict for URL generation).
    """
    filters = []
    args = {}
    for key in keys:
        if source.get(key, type=bool):
            filters.append(key)
            args[key] = "on"
    return filters, args


def build_base_filters(request_args, name, system, vtt):
    """Build base SQLAlchemy filter conditions for name, system, and VTT.

    Args:
        request_args: Mutable dict to store active filter args for pagination URLs.
        name: Game name search string (or None).
        system: System ID filter (or None).
        vtt: VTT ID filter (or None).

    Returns:
        List of SQLAlchemy filter expressions.
    """
    filters = []
    if name:
        request_args["name"] = name
        filters.append(Game.name.ilike(f"%{name}%"))
    if system:
        request_args["system"] = system
        filters.append(Game.system_id == system)
    if vtt:
        request_args["vtt"] = vtt
        filters.append(Game.vtt_id == vtt)
    return filters


def build_status_filters(statuses, user_payload):
    """Build status filter with draft visibility rules.

    Draft games are only visible to their GM (or to admins).

    Args:
        statuses: List of status strings to include.
        user_payload: Dict with 'user_id' and 'is_admin' keys.

    Returns:
        SQLAlchemy OR expression combining status filters.
    """
    filters = []
    for s in statuses:
        if s != "draft":
            filters.append(Game.status == s)
        elif user_payload.get("is_admin"):
            filters.append(Game.status == "draft")
        else:
            filters.append(
                and_(Game.status == "draft", Game.gm_id == user_payload.get("user_id"))
            )
    return or_(*filters)


def normalize_search_defaults(
    status,
    game_type,
    restriction,
    default_status=None,
    default_type=None,
    default_restriction=None,
):
    """Fill in defaults for empty filter selections.

    Args:
        status: Selected status list (may be empty).
        game_type: Selected game type list (may be empty).
        restriction: Selected restriction list (may be empty).
        default_status: Default status list if none selected.
        default_type: Default game type list if none selected.
        default_restriction: Default restriction list if none selected.

    Returns:
        Tuple of (status, game_type, restriction) with defaults applied.
    """
    if not status:
        status = default_status or ["open"]
    if not game_type:
        game_type = default_type or ["oneshot", "campaign"]
    if not restriction:
        restriction = default_restriction or ["all", "16+", "18+"]
    return status, game_type, restriction


def get_filtered_games(
    request_args_source,
    user_payload,
    base_query=None,
    default_status=None,
    default_type=None,
    default_restriction=None,
):
    """Build and execute a paginated, filtered game query.

    Args:
        request_args_source: Flask request.args or similar mapping.
        user_payload: Auth payload dict with 'user_id' and 'is_admin'.
        base_query: Optional base SQLAlchemy query to extend.
        default_status: Default status filter if none selected.
        default_type: Default game type filter if none selected.
        default_restriction: Default restriction filter if none selected.

    Returns:
        Tuple of (pagination object, request_args dict for URL generation).
    """
    request_args = {}
    now = datetime.now(timezone.utc)

    status, status_args = parse_multi_checkbox_filter(
        request_args_source, ["open", "closed", "archived", "draft"]
    )
    game_type, type_args = parse_multi_checkbox_filter(
        request_args_source, ["oneshot", "campaign"]
    )
    restriction, restriction_args = parse_multi_checkbox_filter(
        request_args_source, ["all", "16+", "18+"]
    )
    request_args.update(status_args)
    request_args.update(type_args)
    request_args.update(restriction_args)

    status, game_type, restriction = normalize_search_defaults(
        status,
        game_type,
        restriction,
        default_status=default_status,
        default_type=default_type,
        default_restriction=default_restriction,
    )

    name = request_args_source.get("name", type=str)
    system = request_args_source.get("system", type=int)
    vtt = request_args_source.get("vtt", type=int)

    queries = [
        Game.restriction.in_(restriction),
        Game.type.in_(game_type),
    ]
    queries += build_base_filters(request_args, name, system, vtt)
    queries.append(build_status_filters(status, user_payload))

    status_order = case(
        (Game.status == "draft", 0),
        (Game.status == "open", 1),
        (Game.status == "closed", 2),
        (Game.status == "archived", 3),
    )
    is_future = case((Game.date >= now, 0), else_=1)
    time_distance = func.abs(func.extract("epoch", Game.date - now))

    page = request_args_source.get("page", 1, type=int)
    query = base_query or Game.query
    games = (
        query.filter(*queries)
        .order_by(status_order, is_future, time_distance)
        .paginate(page=page, per_page=GAMES_PER_PAGE, error_out=False)
    )

    return games, request_args


def get_filtered_user_games(request_args_source, user_id, user_payload, role="gm"):
    """Build filtered game query scoped to a specific user.

    Args:
        request_args_source: Flask request.args or similar mapping.
        user_id: User ID to filter by.
        user_payload: Auth payload dict with 'user_id' and 'is_admin'.
        role: Filter role - 'gm' for games as GM, 'player' for games as player.

    Returns:
        Tuple of (pagination object, request_args dict for URL generation).

    Raises:
        ValidationError: If role is invalid.
    """
    user = UserService().repo.get_by_id(user_id)
    if not user:
        return [], {}

    if role == "gm":
        base_query = Game.query.filter(Game.gm_id == user_id)
    elif role == "player":
        game_ids = [game.id for game in user.games]
        base_query = Game.query.filter(Game.id.in_(game_ids))
    else:
        raise ValidationError("Invalid role.", field="role")

    return get_filtered_games(
        request_args_source,
        user_payload,
        base_query,
        default_status=["draft", "open", "closed", "archived"],
    )
