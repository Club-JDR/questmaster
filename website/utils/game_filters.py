"""Checkbox/query-string filter translation for game search views.

All query-building (status visibility, ordering) lives in
``GameRepository.search()`` — this module's only job is translating a
request's checkbox-style args into the ``filters`` dict that
``GameService.search()`` expects, so views and the API share one search
implementation.
"""

from website.exceptions import ValidationError
from website.repositories.base import Pagination


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
    extra_filters=None,
    default_status=None,
    default_type=None,
    default_restriction=None,
) -> tuple[Pagination, dict]:
    """Build a GameService.search() filters dict from request args and run it.

    Args:
        request_args_source: Flask request.args or similar mapping.
        user_payload: Auth payload dict with 'user_id' and 'is_admin'.
        extra_filters: Optional dict merged into the filters verbatim (e.g.
            ``{"special_event_id": ...}``, ``{"gm_id": ...}``,
            ``{"player_id": ...}``) — for views scoping the search beyond
            what checkboxes express.
        default_status: Default status filter if none selected.
        default_type: Default game type filter if none selected.
        default_restriction: Default restriction filter if none selected.

    Returns:
        Tuple of (Pagination, request_args dict for URL generation).
    """
    from website.services.game import GameService
    from website.services.setting import SettingsService

    request_args = {}

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

    filters = {"status": status, "game_type": game_type, "restriction": restriction}

    name = request_args_source.get("name", type=str)
    if name:
        request_args["name"] = name
        filters["name"] = name

    system = request_args_source.get("system", type=int)
    if system:
        request_args["system"] = system
        filters["system_id"] = system

    vtt = request_args_source.get("vtt", type=int)
    if vtt:
        request_args["vtt"] = vtt
        filters["vtt_id"] = vtt

    if extra_filters:
        filters.update(extra_filters)

    per_page = SettingsService().get_games_per_page()
    page = request_args_source.get("page", 1, type=int)

    games = GameService().search(filters, page=page, per_page=per_page, user_payload=user_payload)

    return games, request_args


def get_filtered_user_games(request_args_source, user_id, user_payload, role="gm"):
    """Build filtered game query scoped to a specific user.

    Args:
        request_args_source: Flask request.args or similar mapping.
        user_id: User ID to filter by.
        user_payload: Auth payload dict with 'user_id' and 'is_admin'.
        role: Filter role - 'gm' for games as GM, 'player' for games as player.

    Returns:
        Tuple of (Pagination, request_args dict for URL generation).

    Raises:
        NotFoundError: If the user does not exist.
        ValidationError: If role is invalid.
    """
    from website.services.user import UserService

    UserService().get_by_id(user_id)

    if role == "gm":
        extra_filters = {"gm_id": user_id}
    elif role == "player":
        extra_filters = {"player_id": user_id}
    else:
        raise ValidationError("Invalid role.", field="role")

    return get_filtered_games(
        request_args_source,
        user_payload,
        extra_filters=extra_filters,
        default_status=["draft", "open", "closed", "archived"],
    )
